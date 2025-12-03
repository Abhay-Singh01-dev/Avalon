from fastapi import APIRouter, HTTPException, Depends, status, Request, Body
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, OperationFailure
import logging
import json
import asyncio

from app.db.mongo import get_collection, get_database
from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    Conversation,
    Message,
    MessageInDB,
    MessageRole,
    ConversationList,
    PyObjectId
)
from app.agents.master_agent import master_agent
from app.agents.workers.internal_docs_agent import InternalDocsAgent
from app.config import settings
from app.services.rag.retriever import ProjectRetriever, get_rag_status
from app.rag.data_sources_retriever import data_source_retriever
import app.llm.lmstudio_client as lmstudio_mod
from app.utils.report_intent import should_generate_report

# Import new hybrid LLM architecture
from app.llm.llm_router import llm_router, LLMEngine
from app.llm.mode_classifier import (
    detect_research_mode,
    get_mode_explanation,
    ChatMode,
    ModeClassification
)
from app.llm.table_formatter import (
    enforce_table_quality,
    add_hallucination_protection,
    add_table_formatting_rules,
    clean_llm_table_output
)

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)

# MongoDB collection names
MESSAGES_COLLECTION = "messages"
CONVERSATIONS_COLLECTION = "conversations"

# Initialize InternalDocsAgent for DOCUMENT mode
internal_docs_agent = InternalDocsAgent("document_processor")

# Initialize Project RAG Retriever
project_retriever = ProjectRetriever()

# ============================================================================
# HYBRID LLM ARCHITECTURE - Smart mode detection and routing
# ============================================================================
# Uses new mode_classifier.py for enhanced detection
# ChatMode is now imported from mode_classifier

def detect_mode(prompt: str, has_files: bool = False, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Wrapper for backward compatibility - uses new mode_classifier.
    
    Returns just the mode string for compatibility with existing code.
    For full classification details, use detect_research_mode() directly.
    """
    meta = metadata or {}
    if has_files:
        meta["has_files"] = True
    
    classification = detect_research_mode(prompt, meta)
    return classification.mode

def get_safety_response() -> str:
    """Return the safety mode response for non-pharma queries"""
    return "I'm Avalon — Healthcare AI. I can help you with:\n\n• Drug information and mechanisms\n• Clinical trials and disease biology\n• Pharmacology and drug interactions\n• Market analysis and patents\n\nWhat would you like to know?"

# (No mock responses) Real orchestration uses MasterAgent and Mode Engine

@router.post("/ask", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def chat_endpoint(chat_request: ChatRequest, request: Request):
    """
    Process a chat message and return a response.
    
    This endpoint handles both new conversations and continuing existing ones.
    It saves the user message, generates a response, and saves that as well.
    """
    try:
        # Get database collections
        db = get_database()
        messages_collection = db[MESSAGES_COLLECTION]
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string IDs to ObjectId if they exist
        conversation_id = None
        if chat_request.conversation_id:
            try:
                conversation_id = PyObjectId(chat_request.conversation_id)
                # Verify conversation exists
                conversation = await conversations_collection.find_one({"_id": conversation_id})
                if not conversation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Conversation {chat_request.conversation_id} not found"
                    )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid conversation_id: {str(e)}"
                )
        
        # Create a new conversation if needed
        if not conversation_id:
            new_conversation = Conversation(
                title=chat_request.message[:50] + ("..." if len(chat_request.message) > 50 else ""),
                project_id=PyObjectId(chat_request.project_id) if chat_request.project_id else None,
                metadata={
                    "user_agent": request.headers.get("user-agent", ""),
                    "ip_address": request.client.host if request.client else None,
                    "created_via": "api"
                }
            )
            
            # Insert the new conversation
            result = await conversations_collection.insert_one(new_conversation.dict(by_alias=True, exclude={"id"}))
            conversation_id = result.inserted_id
        
        # Create and save the user message
        user_message = MessageInDB(
            role=MessageRole.USER,
            content=chat_request.message,
            metadata={
                "model": chat_request.model,
                "temperature": chat_request.temperature,
                "max_tokens": chat_request.max_tokens
            }
        )
        
        # Insert the user message
        message_result = await messages_collection.insert_one(
            user_message.dict(by_alias=True, exclude={"id"})
        )
        user_message.id = message_result.inserted_id
        
        # ===================================================================
        # HYBRID LLM ARCHITECTURE: Detect mode and choose engine
        # ===================================================================
        classification = detect_research_mode(
            chat_request.message, 
            metadata=chat_request.metadata if hasattr(chat_request, 'metadata') else None
        )
        mode = classification.mode
        
        # Choose LLM engine based on mode and prompt
        engine_choice = await llm_router.choose_engine(chat_request.message, mode)
        
        logger.info(f"[HYBRID_LLM] Mode: {mode} | Engine: {engine_choice['engine']} | Reason: {engine_choice['reason']}")
        
        if mode == ChatMode.PATIENT:
            # PATIENT MODE: Patient-specific queries with PHI (always local)
            logger.info(f"[HYBRID_LLM] PATIENT mode - PHI detected, using local only")
            
            patient_prompt = f"""{chat_request.message}

PATIENT MODE ACTIVATED:
- Provide patient-specific guidance
- Consider safety, dosing, and PK/PD factors
- Highlight contraindications and interactions
- Be concise and actionable
- Protect patient privacy (local processing only)"""
            
            system_prompt = add_hallucination_protection(
                "You are a clinical pharmaceutical assistant specializing in patient care."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": patient_prompt}
            ]
            
            # Always use local for PHI
            response_content = await llm_router.ask_local(
                messages=messages,
                temperature=0.3,  # Lower temp for clinical accuracy
                max_tokens=1000
            )
            
            orchestration = {
                "content": response_content,
                "mode": ChatMode.PATIENT,
                "engine": "local",
                "engine_reason": "PHI protection - local processing only",
                "required_agents": classification.required_agents
            }
        
        elif mode == ChatMode.SAFETY:
            # SAFETY MODE: Non-pharma query
            response_content = get_safety_response()
            orchestration = {
                "content": response_content,
                "mode": ChatMode.SAFETY,
                "engine": "none",
                "engine_reason": "Non-pharma query blocked"
            }
        
        elif mode == ChatMode.DOCUMENT:
            # DOCUMENT MODE: File-based analysis
            logger.info(f"[MODE_ENGINE] DOCUMENT mode - processing with InternalDocsAgent")
            
            # Check if document ID is provided in attachments or metadata
            doc_id = None
            if chat_request.attachments and len(chat_request.attachments) > 0:
                doc_id = chat_request.attachments[0]  # Use first attachment
            elif hasattr(chat_request, 'metadata') and chat_request.metadata:
                doc_id = chat_request.metadata.get("document_id")
            
            if not doc_id:
                # No document uploaded yet - instruct user
                response_content = (
                    "To analyze a document, please:\n\n"
                    "1. Upload your file (PDF, DOCX, TXT) using the upload endpoint\n\n"
                    "2. Use the returned document ID in your query\n\n"
                    "3. Or mention specific sections to analyze\n\n"
                    "**Supported file types:** PDF, DOCX, TXT\n"
                    "**Max file size:** 25MB"
                )
                orchestration = {
                    "content": response_content,
                    "mode": ChatMode.DOCUMENT
                }
            else:
                # Fetch document from database
                db = get_database()
                document = await db.internal_docs.find_one({"_id": PyObjectId(doc_id)})
                
                if not document:
                    response_content = f"Document with ID {doc_id} not found. Please upload the document first."
                    orchestration = {
                        "content": response_content,
                        "mode": ChatMode.DOCUMENT
                    }
                else:
                    # Process document with InternalDocsAgent
                    try:
                        result = await internal_docs_agent.handle_summarize_document({
                            "content": document.get("content", ""),
                            "file_path": document.get("filepath", ""),
                            "length": "detailed"  # or extract from user query
                        })
                        
                        # Format response
                        response_content = f"""## Document Analysis: {document.get('filename', 'Unknown')}

### Summary
{result.get('summary', 'No summary available')}

### Metadata
- **File**: {document.get('filename', 'Unknown')}
- **Size**: {document.get('size', 0)} bytes
- **Type**: {document.get('content_type', 'Unknown')}
- **Uploaded**: {document.get('created_at', 'Unknown')}
"""
                        
                        orchestration = {
                            "content": response_content,
                            "mode": ChatMode.DOCUMENT,
                            "document_id": doc_id,
                            "filename": document.get('filename')
                        }
                    except Exception as e:
                        logger.error(f"[MODE_ENGINE] Document processing error: {e}")
                        response_content = f"Error processing document: {str(e)}"
                        orchestration = {
                            "content": response_content,
                            "mode": ChatMode.DOCUMENT
                        }
        
        elif mode == ChatMode.TABLE:
            # TABLE MODE: Lightweight table generation with STRICT small-LLM formatting
            logger.info(f"[HYBRID_LLM] TABLE mode - using {engine_choice['engine']} engine with strict formatting")
            
            # Add STRICT formatting instructions for small LLMs
            table_prompt = f"""{chat_request.message}

CRITICAL TABLE RULES (MUST FOLLOW EXACTLY):

1. Format EXACTLY like this:
| Column A | Column B | Column C |
|----------|----------|----------|
| value    | value    | value    |

2. CELL CONTENT RULES:
   - Maximum 10 words per cell
   - NO line breaks inside cells
   - NO text wrapping
   - Use SHORT phrases only
   - Example: "Inhibits serotonin reuptake" NOT "This drug works by inhibiting the reuptake of serotonin in the neurons of the brain"

3. SIZE LIMITS:
   - Maximum 6 rows (excluding header)
   - Maximum 3 columns
   - If more data needed, summarize

4. OUTPUT ONLY THE TABLE:
   - NO paragraphs before table
   - NO explanatory text after table
   - ONLY output the Markdown table

5. If unable to create table, respond: "Insufficient data for table"

Now create the table:"""
            
            # Add strict table formatting rules to system prompt
            from app.llm.table_formatter import add_table_formatting_rules
            system_prompt = add_table_formatting_rules(
                "You are a pharmaceutical data assistant. Generate STRICT small-format Markdown tables ONLY."
            )
            system_prompt = add_hallucination_protection(system_prompt)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": table_prompt}
            ]
            
            # Route through LLM router
            response_content = await llm_router.ask(
                messages=messages,
                mode=mode,
                temperature=0.2,  # Very low temperature for strict formatting
                max_tokens=600,
                stream=False
            )
            
            # CRITICAL: Clean and fix table output
            from app.llm.table_formatter import clean_llm_table_output
            response_content = clean_llm_table_output(response_content)
            
            # Additional quality enforcement
            response_content = enforce_table_quality(response_content, chat_request.message)
            
            orchestration = {
                "content": response_content,
                "mode": ChatMode.TABLE,
                "engine": engine_choice['engine'],
                "engine_reason": engine_choice['reason']
            }
        
        elif mode == ChatMode.SIMPLE:
            # SIMPLE MODE: Quick informational query with hybrid LLM routing
            logger.info(f"[HYBRID_LLM] SIMPLE mode - using {engine_choice['engine']} engine")
            
            # Detect if this is a comprehensive/detailed request
            is_comprehensive = any(word in chat_request.message.lower() for word in [
                "comprehensive", "detailed analysis", "in depth", "cover the following",
                "lifecycle", "complete", "all aspects", "extensive"
            ])
            
            if is_comprehensive:
                # For comprehensive queries, use extended format
                simple_prompt = chat_request.message + """

CRITICAL INSTRUCTIONS - READ CAREFULLY:
This is a COMPREHENSIVE, IN-DEPTH analysis request. You MUST provide extensive detail.

LENGTH REQUIREMENT: Generate AT LEAST 2500-3500 words. This is NOT a summary.

FORMATTING RULES (MANDATORY - FOLLOW EXACTLY):

1. Use markdown headings for main sections:
   - # 1. Introduction
   - # 2. Mechanism of Action
   - # 3. Clinical Evidence

2. Under EACH main section, create NUMBERED SUB-POINTS:
   - **2.1 AMPK Activation:**
   - **2.2 Glucose Regulation:**
   - **2.3 Transcriptional Effects:**

3. Each sub-point MUST have:
   - Bold sub-heading with colon and number
   - 3-5 well-developed sentences explaining the concept
   - Specific examples with data
   - NO PARENTHETICAL CITATIONS like (1) (2) (3)

4. Add blank lines between:
   - Main sections (2 blank lines)
   - Sub-points (1 blank line)
   - Paragraphs within sub-points (1 blank line)

5. References section:
   - Must be a numbered list at the END
   - Format: 1. Author et al. (Year). Title. Journal.

ABSOLUTE PROHIBITIONS:
- NEVER use (1), (2), (3) style citations within text
- NEVER write wall-of-text paragraphs
- NEVER skip the numbered sub-point structure
- NEVER put references inline

Follow this ChatGPT-style format for ALL sections with proper spacing."""
                max_tokens_limit = 4000
            else:
                # Standard simple query
                simple_prompt = chat_request.message + """

Provide a clear, accurate answer. Format your response appropriately:

- For simple questions (definitions, facts): Give a direct, concise answer (1-3 sentences)
- For questions needing explanation: Use bullet points or numbered lists with brief descriptions
- For complex topics: Break into clear sections with headings

Be conversational and match the complexity of your answer to the question."""
                max_tokens_limit = 800
            
            # Add hallucination protection
            system_prompt = add_hallucination_protection(
                "You are a helpful pharmaceutical assistant. Provide clear, accurate answers that match the complexity of the question."
            )
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": simple_prompt}
            ]
            
            # Route through LLM router
            response_content = await llm_router.ask(
                messages=messages,
                mode=mode,
                temperature=0.5,
                max_tokens=max_tokens_limit,
                stream=False
            )
            
            orchestration = {
                "content": response_content,
                "mode": ChatMode.SIMPLE,
                "engine": engine_choice['engine'],
                "engine_reason": engine_choice['reason']
            }
        
        elif mode == ChatMode.EXPERT:
            # EXPERT MODE: Expert network and collaboration queries
            logger.info(f"[AUTO_MODE] EXPERT mode - routing to expert network graph")
            
            # Add mode explanation to user context
            mode_explanation = get_mode_explanation(classification, engine_choice['engine'])
            
            user_context = {
                "project_id": chat_request.project_id,
                "conversation_id": str(conversation_id) if conversation_id else None,
                "mode_info": {
                    "mode": mode,
                    "engine": engine_choice['engine'],
                    "reason": engine_choice['reason'],
                    "explanation": mode_explanation,
                    "required_agents": ["ExpertNetworkAgent"],
                    "needs_synthesis": False,
                    "needs_cloud": False
                }
            }
            
            # Route to MasterAgent with expert focus
            orchestration = await master_agent.run(chat_request.message, user_context=user_context)
            
            # Add engine info to orchestration
            if isinstance(orchestration, dict):
                orchestration["engine"] = engine_choice['engine']
                orchestration["engine_reason"] = engine_choice['reason']
                orchestration["mode"] = ChatMode.EXPERT
        
        else:  # mode == ChatMode.RESEARCH
            # RESEARCH MODE: Full multi-agent orchestration with hybrid LLM routing
            logger.info(f"[HYBRID_LLM] RESEARCH mode - using {engine_choice['engine']} engine with MasterAgent")
            
            # Add mode explanation to user context
            mode_explanation = get_mode_explanation(classification, engine_choice['engine'])
            
            user_context = {
                "project_id": chat_request.project_id,
                "conversation_id": str(conversation_id) if conversation_id else None,
                "mode_info": {
                    "mode": mode,
                    "engine": engine_choice['engine'],
                    "reason": engine_choice['reason'],
                    "explanation": mode_explanation,
                    "required_agents": classification.required_agents,
                    "needs_synthesis": classification.needs_synthesis,
                    "needs_cloud": classification.needs_cloud
                }
            }
            
            orchestration = await master_agent.run(chat_request.message, user_context=user_context)
            
            # Add engine info to orchestration
            if isinstance(orchestration, dict):
                orchestration["engine"] = engine_choice['engine']
                orchestration["engine_reason"] = engine_choice['reason']

        response_content = orchestration.get("content") if isinstance(orchestration, dict) else str(orchestration)

        # Create and save the assistant's response
        assistant_message = MessageInDB(
            role=MessageRole.ASSISTANT,
            content=response_content,
            metadata={
                "model": chat_request.model or settings.LMSTUDIO_MODEL_NAME,
                "response_to": str(user_message.id),
                "mode": orchestration.get("mode") if isinstance(orchestration, dict) else None,
                "workers": orchestration.get("workers") if isinstance(orchestration, dict) else None,
                "usage": {
                    "prompt_tokens": len(chat_request.message.split()),
                    "completion_tokens": len(response_content.split()) if response_content else 0,
                    "total_tokens": len(chat_request.message.split()) + (len(response_content.split()) if response_content else 0)
                }
            }
        )
        
        # Insert the assistant's response
        assistant_result = await messages_collection.insert_one(
            assistant_message.dict(by_alias=True, exclude={"id"})
        )
        assistant_message.id = assistant_result.inserted_id
        
        # Update the conversation's updated_at timestamp
        await conversations_collection.update_one(
            {"_id": conversation_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            user_message.dict(by_alias=True),
                            assistant_message.dict(by_alias=True)
                        ]
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Return the response
        return ChatResponse(
            status="success",
            message="Message processed successfully",
            message_id=str(assistant_message.id),
            conversation_id=str(conversation_id),
            content=response_content,
            timestamp=assistant_message.timestamp,
            model=chat_request.model or settings.LMSTUDIO_MODEL_NAME,
            usage=assistant_message.metadata.get("usage")
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

async def stream_chat_response(chat_request: ChatRequest, request: Request) -> AsyncGenerator[str, None]:
    """
    Generator function that streams chat responses token-by-token.
    Yields JSON strings with format: {"delta": "<token>"} or {"final": true, "message_id": "<id>"}
    """
    try:
        db = get_database()
        messages_collection = db[MESSAGES_COLLECTION]
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string IDs to ObjectId if they exist
        conversation_id = None
        if chat_request.conversation_id:
            try:
                conversation_id = PyObjectId(chat_request.conversation_id)
                conversation = await conversations_collection.find_one({"_id": conversation_id})
                if not conversation:
                    yield json.dumps({"error": f"Conversation {chat_request.conversation_id} not found"}) + "\n"
                    return
            except Exception as e:
                yield json.dumps({"error": f"Invalid conversation_id: {str(e)}"}) + "\n"
                return
        
        # Create a new conversation if needed
        if not conversation_id:
            new_conversation = Conversation(
                title=chat_request.message[:50] + ("..." if len(chat_request.message) > 50 else ""),
                project_id=PyObjectId(chat_request.project_id) if chat_request.project_id else None,
                metadata={
                    "user_agent": request.headers.get("user-agent", ""),
                    "ip_address": request.client.host if request.client else None,
                    "created_via": "api"
                }
            )
            result = await conversations_collection.insert_one(new_conversation.dict(by_alias=True, exclude={"id"}))
            conversation_id = result.inserted_id
        
        # Create and save the user message
        # Include attachments in metadata so they persist and display after reload
        user_metadata = {
            "model": chat_request.model,
            "temperature": chat_request.temperature,
            "max_tokens": chat_request.max_tokens
        }
        
        # Add attachment information to metadata for UI display
        if chat_request.attachments and len(chat_request.attachments) > 0:
            # Get file details from uploads collection
            uploads_collection = db["uploads"]
            attached_files = []
            for file_id in chat_request.attachments:
                try:
                    file_doc = await uploads_collection.find_one({"_id": PyObjectId(file_id)})
                    if file_doc:
                        attached_files.append({
                            "id": file_id,
                            "name": file_doc.get("filename", "Unknown"),
                            "size": file_doc.get("file_size")
                        })
                except Exception as e:
                    logger.warning(f"Failed to get file details for {file_id}: {e}")
            
            if attached_files:
                user_metadata["attachedFiles"] = attached_files
        
        user_message = MessageInDB(
            role=MessageRole.USER,
            content=chat_request.message,
            metadata=user_metadata
        )
        message_result = await messages_collection.insert_one(
            user_message.dict(by_alias=True, exclude={"id"})
        )
        user_message.id = message_result.inserted_id
        
        # ===================================================================
        # HYBRID LLM ARCHITECTURE: Detect mode and choose engine (STREAMING)
        # ===================================================================
        classification = detect_research_mode(
            chat_request.message,
            metadata=chat_request.metadata if hasattr(chat_request, 'metadata') else None
        )
        mode = classification.mode
        
        # Choose LLM engine based on mode and prompt (includes PHI detection)
        engine_choice = await llm_router.choose_engine(chat_request.message, mode)
        
        logger.info(f"[HYBRID_LLM_STREAM] Mode: {mode} | Engine: {engine_choice['engine']}")
        
        # ===================================================================
        # THINKING PANEL: Emit routing decision FIRST (before ANY other events)
        # This MUST be the first event in the SSE stream
        # ===================================================================
        phi_detected = engine_choice.get("phi_detected", False)
        
        # Construct thinking message based on PHI detection
        if phi_detected:
            thinking_message = "PHI detected → Switching to Local Model"
            routing_mode = "local"
            routing_reason = "PHI detected"
        else:
            # During pilot, we always use local, but message reflects cloud would be used
            thinking_message = "No PHI detected → Using Cloud Model" if engine_choice.get("engine") == "cloud" else "No PHI detected → Using Local Model"
            routing_mode = str(engine_choice.get("engine", "local"))
            routing_reason = "No PHI detected"
        
        # FIRST EVENT: Thinking panel message (MUST be first)
        thinking_event = {
            "type": "thinking",
            "message": thinking_message
        }
        yield json.dumps(thinking_event) + "\n"
        logger.info(f"[THINKING_PANEL] Emitted: {thinking_message}")
        
        # SECOND EVENT: Routing decision with mode
        routing_event = {
            "type": "routing",
            "mode": routing_mode,
            "reason": routing_reason,
            "detected_mode": mode,
            "mode_reason": classification.reason
        }
        yield json.dumps(routing_event) + "\n"
        
        # Small delay to ensure thinking panel is visible before timeline events
        await asyncio.sleep(0.25)
        
        # ===================================================================
        # TIMELINE EVENTS: Mode and agent events (after thinking panel)
        # ===================================================================
        # Emit PHI detection timeline event if PHI was detected
        if phi_detected:
            phi_timeline_event = {
                "type": "timeline",
                "event": "phi_detected",
                "agent": "security",
                "message": f"⚠️ PHI DETECTED - LOCAL model enforced",
                "metadata": engine_choice.get("phi_details", {})
            }
            yield json.dumps(phi_timeline_event) + "\n"
            logger.warning(f"[PHI_AUDIT] PHI detected in query - routing to local model only")
        
        # Emit mode classification timeline event
        mode_event = {
            "type": "timeline",
            "event": f"mode_{mode}",
            "agent": "master",
            "message": f"🔍 {mode.upper()} MODE - {classification.reason}"
        }
        yield json.dumps(mode_event) + "\n"
        
        # Emit LLM routing timeline event
        llm_routing_event = {
            "type": "timeline",
            "event": "llm_routing",
            "agent": "master",
            "message": f"🖥️ Using {engine_choice['engine'].upper()} engine ({engine_choice['provider']})",
            "metadata": {"engine": engine_choice["engine"], "reason": engine_choice["reason"]}
        }
        yield json.dumps(llm_routing_event) + "\n"
        
        if mode == ChatMode.SAFETY:
            # SAFETY MODE: Non-pharma query (no streaming needed)
            response_content = get_safety_response()
            yield json.dumps({"type": "token", "delta": response_content}) + "\n"
            
            # Save assistant message
            assistant_message = MessageInDB(
                role=MessageRole.ASSISTANT,
                content=response_content,
                metadata={
                    "model": chat_request.model or settings.LMSTUDIO_MODEL_NAME,
                    "response_to": str(user_message.id),
                    "mode": ChatMode.SAFETY
                }
            )
            assistant_result = await messages_collection.insert_one(
                assistant_message.dict(by_alias=True, exclude={"id"})
            )
            assistant_message.id = assistant_result.inserted_id
            
            await conversations_collection.update_one(
                {"_id": conversation_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                user_message.dict(by_alias=True),
                                assistant_message.dict(by_alias=True)
                            ]
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            yield json.dumps({"final": True, "message_id": str(assistant_message.id)}) + "\n"
            return
        
        elif mode == ChatMode.DOCUMENT:
            # DOCUMENT MODE: File-based analysis with streaming
            logger.info(f"[MODE_ENGINE] DOCUMENT mode streaming - processing with InternalDocsAgent")
            
            # Check if document ID is provided in attachments or metadata
            doc_id = None
            if chat_request.attachments and len(chat_request.attachments) > 0:
                doc_id = chat_request.attachments[0]  # Use first attachment
            elif hasattr(chat_request, 'metadata') and chat_request.metadata:
                doc_id = chat_request.metadata.get("document_id")
            
            response_content = ""
            
            if not doc_id:
                # No document uploaded yet - instruct user
                response_content = (
                    "To analyze a document, please:\n\n"
                    "1. Upload your file (PDF, DOCX, TXT) using the upload endpoint\n\n"
                    "2. Use the returned document ID in your query\n\n"
                    "3. Or mention specific sections to analyze\n\n"
                    "**Supported file types:** PDF, DOCX, TXT\n"
                    "**Max file size:** 25MB"
                )
                
                # Stream the instruction message
                for char in response_content:
                    yield json.dumps({"type": "token", "delta": char}) + "\n"
                    await asyncio.sleep(0.01)  # Simulate streaming
            else:
                # Fetch document from database
                db = get_database()
                document = await db.internal_docs.find_one({"_id": PyObjectId(doc_id)})
                
                if not document:
                    response_content = f"Document with ID {doc_id} not found. Please upload the document first."
                    for char in response_content:
                        yield json.dumps({"type": "token", "delta": char}) + "\n"
                        await asyncio.sleep(0.01)
                else:
                    # Process document with InternalDocsAgent
                    try:
                        result = await internal_docs_agent.handle_summarize_document({
                            "content": document.get("content", ""),
                            "file_path": document.get("filepath", ""),
                            "length": "detailed"
                        })
                        
                        # Format and stream response
                        response_content = f"""## Document Analysis: {document.get('filename', 'Unknown')}

### Summary
{result.get('summary', 'No summary available')}

### Metadata
- **File**: {document.get('filename', 'Unknown')}
- **Size**: {document.get('size', 0)} bytes
- **Type**: {document.get('content_type', 'Unknown')}
- **Uploaded**: {document.get('created_at', 'Unknown')}
"""
                        
                        # Stream the response
                        for char in response_content:
                            yield json.dumps({"type": "token", "delta": char}) + "\n"
                            await asyncio.sleep(0.005)  # Faster streaming for formatted text
                        
                    except Exception as e:
                        logger.error(f"[MODE_ENGINE] Document processing error: {e}")
                        response_content = f"Error processing document: {str(e)}"
                        for char in response_content:
                            yield json.dumps({"type": "token", "delta": char}) + "\n"
                            await asyncio.sleep(0.01)
            
            # Save assistant message
            assistant_message = MessageInDB(
                role=MessageRole.ASSISTANT,
                content=response_content,
                metadata={
                    "model": chat_request.model or settings.LMSTUDIO_MODEL_NAME,
                    "response_to": str(user_message.id),
                    "mode": ChatMode.DOCUMENT,
                    "document_id": doc_id if doc_id else None
                }
            )
            assistant_result = await messages_collection.insert_one(
                assistant_message.dict(by_alias=True, exclude={"id"})
            )
            assistant_message.id = assistant_result.inserted_id
            
            await conversations_collection.update_one(
                {"_id": conversation_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                user_message.dict(by_alias=True),
                                assistant_message.dict(by_alias=True)
                            ]
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            yield json.dumps({"final": True, "message_id": str(assistant_message.id)}) + "\n"
            return
        
        elif mode == ChatMode.TABLE:
            # TABLE MODE: Lightweight table generation with streaming
            logger.info(f"[MODE_ENGINE] TABLE mode - streaming table generation")
            
            table_prompt = f"""{chat_request.message}

CRITICAL INSTRUCTIONS:
1. Create a SINGLE Markdown table ONLY
2. Use proper pipe (|) delimiters and separator lines (---)
3. Format EXACTLY like this:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |

4. NO paragraphs before or after the table
5. NO explanatory text
6. If you cannot create the table, respond: "Unable to generate table - insufficient data"
7. Keep it compact and focused"""
            
            messages = [{"role": "user", "content": table_prompt}]
            
            # Stream tokens from LM Studio
            full_content = ""
            async for token in lmstudio_mod.lmstudio_client.stream_llm(
                messages, 
                model=chat_request.model or settings.LMSTUDIO_MODEL_NAME,
                temperature=0.3,
                max_tokens=800
            ):
                full_content += token
                yield json.dumps({"type": "token", "delta": token}) + "\n"
            
            # Save assistant message
            assistant_message = MessageInDB(
                role=MessageRole.ASSISTANT,
                content=full_content,
                metadata={
                    "model": chat_request.model or settings.LMSTUDIO_MODEL_NAME,
                    "response_to": str(user_message.id),
                    "mode": ChatMode.TABLE
                }
            )
            assistant_result = await messages_collection.insert_one(
                assistant_message.dict(by_alias=True, exclude={"id"})
            )
            assistant_message.id = assistant_result.inserted_id
            
            await conversations_collection.update_one(
                {"_id": conversation_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                user_message.dict(by_alias=True),
                                assistant_message.dict(by_alias=True)
                            ]
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            yield json.dumps({"final": True, "message_id": str(assistant_message.id)}) + "\n"
            return
        
        elif mode == ChatMode.SIMPLE:
            # SIMPLE MODE: Quick informational query with streaming
            logger.info(f"[MODE_ENGINE] SIMPLE mode - streaming simple response")
            
            # Detect if this is a comprehensive/detailed request
            is_comprehensive = any(word in chat_request.message.lower() for word in [
                "comprehensive", "detailed analysis", "in depth", "cover the following",
                "lifecycle", "complete", "all aspects", "extensive"
            ])
            
            if is_comprehensive:
                # For comprehensive queries, use extended format
                simple_prompt = chat_request.message + """

CRITICAL INSTRUCTIONS - READ CAREFULLY:
This is a COMPREHENSIVE, IN-DEPTH analysis request. You MUST provide extensive detail.

LENGTH REQUIREMENT: Generate AT LEAST 2500-3500 words. This is NOT a summary.

FORMATTING RULES (MANDATORY - FOLLOW EXACTLY):

1. Use markdown headings for main sections:
   - # 1. Introduction
   - # 2. Mechanism of Action
   - # 3. Clinical Evidence

2. Under EACH main section, create NUMBERED SUB-POINTS:
   - **2.1 AMPK Activation:**
   - **2.2 Glucose Regulation:**
   - **2.3 Transcriptional Effects:**

3. Each sub-point MUST have:
   - Bold sub-heading with colon and number
   - 3-5 well-developed sentences explaining the concept
   - Specific examples with data
   - NO PARENTHETICAL CITATIONS like (1) (2) (3)

4. Add blank lines between:
   - Main sections (2 blank lines)
   - Sub-points (1 blank line)
   - Paragraphs within sub-points (1 blank line)

5. References section:
   - Must be a numbered list at the END
   - Format: 1. Author et al. (Year). Title. Journal.

ABSOLUTE PROHIBITIONS:
- NEVER use (1), (2), (3) style citations within text
- NEVER write wall-of-text paragraphs
- NEVER skip the numbered sub-point structure
- NEVER put references inline

Follow this ChatGPT-style format for ALL sections with proper spacing."""
                max_tokens_limit = 4000
            else:
                # Standard simple query
                simple_prompt = chat_request.message + """

Provide a clear, accurate answer. Format your response appropriately:

- For simple questions (definitions, facts): Give a direct, concise answer (1-3 sentences)
- For questions needing explanation: Use bullet points or numbered lists with brief descriptions
- For complex topics: Break into clear sections with headings

Be conversational and match the complexity of your answer to the question."""
            
            messages = [{"role": "user", "content": simple_prompt}]
            
            # Stream tokens from LM Studio
            full_content = ""
            async for token in lmstudio_mod.lmstudio_client.stream_llm(
                messages, 
                model=chat_request.model or settings.LMSTUDIO_MODEL_NAME
            ):
                full_content += token
                yield json.dumps({"type": "token", "delta": token}) + "\n"
            
            # Save assistant message after streaming completes
            assistant_message = MessageInDB(
                role=MessageRole.ASSISTANT,
                content=full_content,
                metadata={
                    "model": chat_request.model or settings.LMSTUDIO_MODEL_NAME,
                    "response_to": str(user_message.id),
                    "mode": "simple_llm_bypass"
                }
            )
            assistant_result = await messages_collection.insert_one(
                assistant_message.dict(by_alias=True, exclude={"id"})
            )
            assistant_message.id = assistant_result.inserted_id
            
            # Update conversation
            await conversations_collection.update_one(
                {"_id": conversation_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                user_message.dict(by_alias=True),
                                assistant_message.dict(by_alias=True)
                            ]
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            yield json.dumps({"final": True, "message_id": str(assistant_message.id)}) + "\n"
            return
        
        # RESEARCH MODE: Full multi-agent orchestration with streaming
        # This is the default mode for deep pharma research queries
        logger.info(f"[MODE_ENGINE] RESEARCH mode - full MasterAgent with streaming")
        
        # ===================================================================
        # PROJECT RAG CONTEXT: Retrieve relevant chunks if conversation has project_id
        # ===================================================================
        project_context = ""
        project_id_for_rag = None
        
        # Check if conversation has a project_id
        if conversation_id:
            conversation = await conversations_collection.find_one({"_id": conversation_id})
            if conversation and conversation.get("project_id"):
                project_id_for_rag = str(conversation["project_id"])
        
        # Also check request's project_id
        if not project_id_for_rag and chat_request.project_id:
            project_id_for_rag = chat_request.project_id
        
        # Retrieve project context if we have a project_id
        if project_id_for_rag:
            try:
                rag_result = await project_retriever.retrieve_with_context(
                    project_id=project_id_for_rag,
                    query=chat_request.message,
                    top_k=5
                )
                project_context = rag_result.get("context_text", "")
                
                if rag_result.get("rag_enabled") and project_context:
                    logger.info(f"[PROJECT_RAG] Retrieved {len(rag_result.get('chunks', []))} chunks for project {project_id_for_rag}")
                else:
                    logger.info(f"[PROJECT_RAG] RAG disabled or no relevant chunks for project {project_id_for_rag}")
            except Exception as e:
                logger.warning(f"[PROJECT_RAG] Failed to retrieve project context: {str(e)}")
                project_context = ""
        
        # ===================================================================
        # DATA SOURCE RAG: Retrieve relevant chunks from user-uploaded data sources
        # ===================================================================
        data_source_context = ""
        data_source_indicator = ""
        data_source_used = False
        
        if settings.DATA_SOURCE_RAG_ENABLED:
            try:
                ds_result = await data_source_retriever.retrieve_with_auto_detection(
                    query=chat_request.message,
                    top_k=settings.DATA_SOURCE_TOP_K
                )
                
                if ds_result.get("chunks"):
                    data_source_context = data_source_retriever.format_chunks_for_prompt(
                        ds_result["chunks"]
                    )
                    data_source_indicator = data_source_retriever.format_source_indicator(
                        ds_result["chunks"]
                    )
                    data_source_used = True
                    
                    logger.info(f"[DATA_SOURCE_RAG] Retrieved {len(ds_result['chunks'])} chunks, categories: {ds_result.get('categories', [])}")
                    
                    # Emit data source indicator event
                    yield json.dumps({
                        "type": "data_source_used",
                        "indicator": data_source_indicator,
                        "categories": ds_result.get("categories", []),
                        "source_restriction": ds_result.get("source_restriction")
                    }) + "\n"
                else:
                    logger.debug("[DATA_SOURCE_RAG] No relevant chunks found")
                    
            except Exception as e:
                logger.warning(f"[DATA_SOURCE_RAG] Failed to retrieve data source context: {str(e)}")
                data_source_context = ""
        
        # ===================================================================
        # REPORT INTENT DETECTION: Determine if report should be auto-generated
        # ===================================================================
        uploaded_files_count = 0
        if chat_request.metadata and "document_id" in chat_request.metadata:
            uploaded_files_count = 1  # Single document uploaded
        # Note: For multiple files, frontend should pass count in metadata
        if chat_request.metadata and "uploaded_files_count" in chat_request.metadata:
            uploaded_files_count = chat_request.metadata.get("uploaded_files_count", 0)
        
        generate_report = should_generate_report(
            prompt=chat_request.message,
            mode=mode,
            uploaded_files_count=uploaded_files_count
        )
        
        logger.info(f"[REPORT_INTENT] Generate report: {generate_report} | Mode: {mode} | Files: {uploaded_files_count}")
        
        # PHARMA RESEARCH MODE: Run orchestration with timeline events, then stream synthesis
        # Collect timeline events in a list
        timeline_events_list = []
        
        def timeline_callback(event: Dict[str, Any]):
            """Callback to collect timeline events"""
            timeline_events_list.append(event)
        
        # Prepare message with context (project + data sources)
        message_with_context = chat_request.message
        
        # Add data source context first (higher priority for user-uploaded data)
        if data_source_context:
            message_with_context = f"""Use the following organization-uploaded data (do NOT hallucinate, use ONLY this data when answering questions related to it):

{data_source_context}

USER QUERY:
{message_with_context}"""
        if project_context:
            message_with_context = f"{project_context}\n\nUSER QUERY:\n{chat_request.message}"
        
        # Run orchestration with timeline callback
        orchestration = None
        async for result in master_agent.run_stream(
            message_with_context,
            user_context={
                "project_id": chat_request.project_id or project_id_for_rag,
                "conversation_id": str(conversation_id) if conversation_id else None,
                "has_project_context": bool(project_context)
            },
            timeline_callback=timeline_callback,
            generate_report=generate_report
        ):
            orchestration = result
        
        # Emit all collected timeline events first
        for event in timeline_events_list:
            yield json.dumps(event) + "\n"
        
        if not orchestration:
            yield json.dumps({"error": "Orchestration failed"}) + "\n"
            return
        
        # Extract the full_text from orchestration for streaming
        full_text = ""
        if isinstance(orchestration, dict):
            full_text = orchestration.get("full_text", "")
            if not full_text:
                # Fallback: use content if full_text not available
                content = orchestration.get("content", {})
                if isinstance(content, dict):
                    full_text = content.get("full_text", "")
                else:
                    full_text = str(content)
        else:
            full_text = str(orchestration)
        
        # Stream the full_text using LM Studio streaming
        # If full_text is already generated, we can stream it directly
        # Otherwise, we need to generate it via streaming
        if full_text:
            # Stream the pre-generated text token by token (for now)
            # In future, we could regenerate via streaming LLM call
            words = full_text.split()
            for word in words:
                token = word + " "
                yield json.dumps({"type": "token", "delta": token}) + "\n"
                await asyncio.sleep(0.01)
        else:
            # If no full_text, generate it via streaming
            synth_messages = [
                {"role": "user", "content": f"As a pharmaceutical research synthesizer, generate a comprehensive summary of the following research findings:\n{json.dumps(orchestration.get('content', {}) if isinstance(orchestration, dict) else {})}"}
            ]
            async for token in lmstudio_mod.lmstudio_client.stream_llm(
                synth_messages,
                model=settings.LMSTUDIO_MODEL_NAME
            ):
                yield json.dumps({"type": "token", "delta": token}) + "\n"
                full_text += token
        
        # Save assistant message after streaming completes
        assistant_message = MessageInDB(
            role=MessageRole.ASSISTANT,
            content=full_text,
            metadata={
                "model": chat_request.model or settings.LMSTUDIO_MODEL_NAME,
                "response_to": str(user_message.id),
                "mode": orchestration.get("mode") if isinstance(orchestration, dict) else None,
                "workers": orchestration.get("workers") if isinstance(orchestration, dict) else None,
                "expert_graph_id": orchestration.get("expert_graph_id") if isinstance(orchestration, dict) else None,
                "timeline": orchestration.get("timeline") if isinstance(orchestration, dict) else None,
                "data_source_used": data_source_used,
                "data_source_indicator": data_source_indicator if data_source_used else None,
            }
        )
        assistant_result = await messages_collection.insert_one(
            assistant_message.dict(by_alias=True, exclude={"id"})
        )
        assistant_message.id = assistant_result.inserted_id
        
        # Update conversation
        await conversations_collection.update_one(
            {"_id": conversation_id},
            {
                "$push": {
                    "messages": {
                        "$each": [
                            user_message.dict(by_alias=True),
                            assistant_message.dict(by_alias=True)
                        ]
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        yield json.dumps({"final": True, "message_id": str(assistant_message.id)}) + "\n"
        
    except Exception as e:
        logger.error(f"Error in streaming chat endpoint: {str(e)}", exc_info=True)
        yield json.dumps({"error": f"An error occurred: {str(e)}"}) + "\n"

@router.post("/ask/stream")
async def chat_stream_endpoint(chat_request: ChatRequest, request: Request):
    """
    Streaming endpoint for chat messages.
    Returns Server-Sent Events (SSE) format with token-by-token streaming.
    """
    return StreamingResponse(
        stream_chat_response(chat_request, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/conversations", response_model=ConversationList)
async def list_conversations(
    project_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
):
    """
    List all conversations, optionally filtered by project_id.
    Returns paginated results.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Build query
        query = {}
        if project_id:
            try:
                query["project_id"] = PyObjectId(project_id)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid project_id: {str(e)}"
                )
        
        # Get total count for pagination
        total = await conversations_collection.count_documents(query)
        
        # Get paginated results
        skip = (page - 1) * page_size
        cursor = conversations_collection.find(query).sort("updated_at", -1).skip(skip).limit(page_size)
        
        # Convert to list of Conversation objects
        conversations = []
        async for doc in cursor:
            # Convert _id to id for frontend compatibility
            if "_id" in doc:
                doc["id"] = str(doc["_id"])
            
            # Keep _id as is for Pydantic validation (it expects ObjectId)
            if "project_id" in doc and doc["project_id"]:
                doc["project_id"] = str(doc["project_id"])
            
            # Convert message _id strings to ObjectId for Pydantic validation
            if "messages" in doc and doc["messages"]:
                for msg in doc["messages"]:
                    if "_id" in msg and isinstance(msg["_id"], str):
                        from bson import ObjectId
                        msg["_id"] = ObjectId(msg["_id"])
                    # Also add id field for messages
                    if "_id" in msg:
                        msg["id"] = str(msg["_id"])
            
            conversations.append(Conversation(**doc))
        
        return ConversationList(
            status="success",
            message="Conversations retrieved successfully",
            conversations=conversations,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving conversations: {str(e)}"
        )

@router.post("/conversations", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: Request,
    payload: Dict[str, Any] = Body(default={})
):
    """
    Create a new conversation.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Create new conversation
        title = payload.get("title", "New Conversation")
        project_id = payload.get("project_id")
        
        # Get request info
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else None
        
        new_conversation = Conversation(
            title=title,
            project_id=PyObjectId(project_id) if project_id else None,
            metadata={
                "user_agent": user_agent,
                "ip_address": ip_address,
                "created_via": "api"
            }
        )
        
        # Insert the new conversation
        result = await conversations_collection.insert_one(new_conversation.dict(by_alias=True, exclude={"id"}))
        conversation_id = result.inserted_id
        
        return {
            "status": "success",
            "message": "Conversation created successfully",
            "conversation_id": str(conversation_id),
            "title": title
        }
        
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the conversation: {str(e)}"
        )

@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """
    Get a single conversation by ID with its messages.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            conv_id = PyObjectId(conversation_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid conversation_id: {str(e)}"
            )
        
        # Find the conversation
        conversation = await conversations_collection.find_one({"_id": conv_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Convert project_id to string for frontend
        if "project_id" in conversation and conversation["project_id"]:
            conversation["project_id"] = str(conversation["project_id"])
        
        # Convert message _id strings to ObjectId for Pydantic validation
        if "messages" in conversation and conversation["messages"]:
            for msg in conversation["messages"]:
                if "_id" in msg and isinstance(msg["_id"], str):
                    try:
                        msg["_id"] = ObjectId(msg["_id"])
                    except:
                        # If conversion fails, generate a new ObjectId
                        msg["_id"] = ObjectId()
                elif "_id" not in msg:
                    msg["_id"] = ObjectId()
        
        return Conversation(**conversation)
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving the conversation: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/rename")
async def rename_conversation(conversation_id: str, payload: Dict[str, Any]):
    """
    Rename a conversation.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            conv_id = PyObjectId(conversation_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid conversation_id: {str(e)}"
            )
        
        # Verify conversation exists
        conversation = await conversations_collection.find_one({"_id": conv_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Update title
        new_title = payload.get("title")
        if not new_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title is required"
            )
        
        await conversations_collection.update_one(
            {"_id": conv_id},
            {"$set": {"title": new_title, "updated_at": datetime.utcnow()}}
        )
        
        return {
            "status": "success",
            "message": "Conversation renamed successfully",
            "conversation_id": conversation_id,
            "title": new_title
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error renaming conversation {conversation_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while renaming the conversation: {str(e)}"
        )

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all its messages.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        messages_collection = db[MESSAGES_COLLECTION]
        projects_collection = db["projects"]
        
        # Convert string ID to ObjectId
        try:
            conv_id = PyObjectId(conversation_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid conversation_id: {str(e)}"
            )
        
        # Verify conversation exists
        conversation = await conversations_collection.find_one({"_id": conv_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Get conversation's project_id before deletion
        project_id = conversation.get("project_id")
        
        # Delete all messages in this conversation from messages collection
        # Messages are stored both in the messages collection and embedded in the conversation
        if "messages" in conversation and conversation["messages"]:
            message_ids = []
            for msg in conversation["messages"]:
                msg_id = msg.get("id") or msg.get("_id")
                if msg_id:
                    # Convert to ObjectId if it's a string
                    try:
                        if isinstance(msg_id, str):
                            msg_id = PyObjectId(msg_id)
                        message_ids.append(msg_id)
                    except:
                        pass
            
            if message_ids:
                try:
                    await messages_collection.delete_many({"_id": {"$in": message_ids}})
                except Exception as e:
                    logger.warning(f"Error deleting messages: {str(e)}")
        
        # Remove conversation from project's chat_ids if it's in a project
        if project_id:
            try:
                await projects_collection.update_one(
                    {"_id": project_id},
                    {"$pull": {"chat_ids": conv_id}, "$set": {"updated_at": datetime.utcnow()}}
                )
            except Exception as e:
                logger.warning(f"Error removing chat from project: {str(e)}")
        
        # Delete the conversation
        result = await conversations_collection.delete_one({"_id": conv_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        return None
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the conversation: {str(e)}"
        )

@router.post("/conversations/{conversation_id}/group-chat")
async def create_group_chat_link(conversation_id: str):
    """
    Generate a shareable group chat link for a conversation.
    Returns a unique invite link that can be shared with others.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            conv_id = PyObjectId(conversation_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid conversation_id: {str(e)}"
            )
        
        # Verify conversation exists
        conversation = await conversations_collection.find_one({"_id": conv_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Generate a unique invite code
        import secrets
        invite_code = secrets.token_urlsafe(16)
        
        # Store the invite code in the conversation metadata
        await conversations_collection.update_one(
            {"_id": conv_id},
            {
                "$set": {
                    "metadata.group_chat": {
                        "enabled": True,
                        "invite_code": invite_code,
                        "created_at": datetime.utcnow(),
                        "participants": []
                    },
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "status": "success",
            "message": "Group chat link created successfully",
            "conversation_id": conversation_id,
            "invite_code": invite_code,
            "invite_link": f"/invite/{invite_code}"
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error creating group chat link for {conversation_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the group chat link: {str(e)}"
        )


@router.get("/invite/{invite_code}")
async def get_conversation_by_invite(invite_code: str):
    """
    Get a conversation by its invite code.
    Used when someone clicks on a shared group chat link.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Find conversation with this invite code
        conversation = await conversations_collection.find_one({
            "metadata.group_chat.invite_code": invite_code
        })
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid or expired invite link"
            )
        
        # Return conversation info
        return {
            "status": "success",
            "conversation_id": str(conversation["_id"]),
            "title": conversation.get("title", "Group Chat"),
            "created_at": conversation.get("created_at"),
            "participants_count": len(conversation.get("metadata", {}).get("group_chat", {}).get("participants", []))
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting conversation by invite {invite_code}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/project")
async def assign_project_to_conversation(conversation_id: str, payload: Dict[str, Any]):
    """
    Assign or unassign a project to a conversation.
    """
    try:
        db = get_database()
        conversations_collection = db[CONVERSATIONS_COLLECTION]
        
        # Convert string ID to ObjectId
        try:
            conv_id = PyObjectId(conversation_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid conversation_id: {str(e)}"
            )
        
        # Verify conversation exists
        conversation = await conversations_collection.find_one({"_id": conv_id})
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Update project_id
        project_id = payload.get("project_id")
        update_data = {"updated_at": datetime.utcnow()}
        
        if project_id is None:
            update_data["project_id"] = None
        else:
            try:
                update_data["project_id"] = PyObjectId(project_id)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid project_id: {str(e)}"
                )
        
        await conversations_collection.update_one(
            {"_id": conv_id},
            {"$set": update_data}
        )
        
        return {
            "status": "success",
            "message": "Project assignment updated successfully",
            "conversation_id": conversation_id,
            "project_id": project_id
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error assigning project to conversation {conversation_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while assigning the project: {str(e)}"
        )
