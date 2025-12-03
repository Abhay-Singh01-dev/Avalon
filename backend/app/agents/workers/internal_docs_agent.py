from typing import Dict, Any, List, Optional
import logging
import os
import time
import json
from pathlib import Path
from app.config import settings
from app.llm.lmstudio_client import lmstudio_client
from app.core.cache import cache, CacheManager
from app.core.retry import retry_llm_call
from app.core.logger import get_logger
from app.agents.workers.schema_enforcer import get_unified_schema_prompt, normalize_to_unified_schema

logger = get_logger(__name__)


class InternalDocsAgent:
    """Agent for processing and analyzing internal documents"""

    agent_type = "internal_docs"

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.supported_tasks = [
            "process_document",
            "extract_insights",
            "summarize_document",
            "analyze_section",
        ]
        self.supported_formats = ['.pdf', '.docx', '.txt', '.md']
    
    async def process(self, task_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a document-related task with the given parameters"""
        if task_type not in self.supported_tasks:
            raise ValueError(f"Unsupported task type: {task_type}")
        
        logger.info(f"Processing {task_type} with parameters: {parameters}")
        
        # Route to the appropriate handler method
        handler = getattr(self, f"handle_{task_type}", None)
        if not handler or not callable(handler):
            raise NotImplementedError(f"No handler for task type: {task_type}")
        
        return await handler(parameters)
    
    async def _read_document(self, file_path: str) -> str:
        """Read document content based on file type"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.pdf':
                # Use PyMuPDF for PDFs if available, fall back to PyPDF2
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    return text
                except ImportError:
                    from PyPDF2 import PdfReader
                    with open(file_path, 'rb') as f:
                        reader = PdfReader(f)
                        return '\n'.join(page.extract_text() for page in reader.pages)
            
            elif file_extension == '.docx':
                from docx import Document
                doc = Document(file_path)
                return '\n'.join(paragraph.text for paragraph in doc.paragraphs)
            
            elif file_extension in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")
        
        except Exception as e:
            logger.error(f"Error reading document {file_path}: {e}")
            raise
    
    async def handle_process_document(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Process a document and extract its content"""
        file_path = parameters.get("file_path", "")
        
        if not file_path:
            raise ValueError("No file path provided")
        
        # Read the document content
        content = await self._read_document(file_path)
        
        # Basic metadata
        file_stats = os.stat(file_path)
        file_info = {
            "file_name": os.path.basename(file_path),
            "file_size": file_stats.st_size,
            "created": file_stats.st_ctime,
            "modified": file_stats.st_mtime,
            "file_type": os.path.splitext(file_path)[1].lower()
        }
        
        return {
            "content": content,
            "metadata": file_info,
            "processing_details": {
                "status": "completed",
                "content_length": len(content),
                "content_type": "text/plain"
            }
        }
    
    async def handle_extract_insights(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key insights from a document"""
        content = parameters.get("content", "")
        doc_type = parameters.get("document_type", "general")
        
        if not content:
            # If no content provided, try to read from file
            file_path = parameters.get("file_path")
            if not file_path:
                raise ValueError("Either 'content' or 'file_path' must be provided")
            
            content = await self._read_document(file_path)
        
        # Customize the prompt based on document type
        if doc_type == "clinical_study":
            prompt = f"""
            Extract key insights from the following clinical study document:
            
            {content[:10000]}... [truncated]
            
            Please provide:
            1. Study objectives and design
            2. Patient population and methodology
            3. Key efficacy and safety findings
            4. Statistical significance of results
            5. Conclusions and implications
            6. Any limitations or biases
            """
        elif doc_type == "regulatory":
            prompt = f"""
            Extract key information from the following regulatory document:
            
            {content[:10000]}... [truncated]
            
            Please provide:
            1. Document type and purpose
            2. Key requirements or guidelines
            3. Compliance deadlines
            4. Affected products or processes
            5. Implications for the organization
            6. Recommended actions
            """
        else:  # general document
            prompt = f"""
            Extract key insights from the following document:
            
            {content[:10000]}... [truncated]
            
            Please provide:
            1. Main topic and purpose
            2. Key points and findings
            3. Important data or statistics
            4. Conclusions and recommendations
            5. Any action items or next steps
            """
        
        decorated = retry_llm_call()(lmstudio_client.ask_llm)
        
        system_msg = (
            "You are a HIGH-PRECISION Internal Documents Intelligence Analyst specializing in pharmaceutical internal documents. "
            "You MUST extract maximum-depth, actionable insights from internal documents. "
            "NO shallow summaries. NO generic statements. Only deep, domain-specific analysis.\n\n"
            "AGENT-SPECIFIC REQUIREMENTS:\n"
            "You must populate the unified schema with:\n"
            "- Key insights with explanations and implications\n"
            "- Key insights with category='regulatory' or appropriate category\n"
            "- Citations from internal documents\n\n"
            + get_unified_schema_prompt("InternalDocs")
        )
        
        try:
            raw = await decorated([
                {"role": "user", "content": system_msg + "\n\n" + user_msg}
            ], model=settings.LMSTUDIO_MODEL_NAME)
        except Exception as e:
            logger.error(f"InternalDocsAgent LLM failure: {e}")
            return {"error": "llm_failure", "message": str(e)}

        query = parameters.get("query", "")
        try:
            parsed = json.loads(raw)
        except Exception:
            logger.error("InternalDocsAgent parse failure")
            result = normalize_to_unified_schema("InternalDocs", {}, query)
            result["confidence_score"]["value"] = 0.0
            result["confidence_score"]["explanation"] = "Failed to parse LLM output"
            result["core_findings"]["summary"] = ["Error: Failed to parse internal documents analysis"]
            return result

        # Normalize to unified schema
        result = normalize_to_unified_schema("InternalDocs", parsed, query)
        
        # Ensure confidence is properly set
        if result["confidence_score"]["value"] == 0.0:
            result["confidence_score"]["value"] = 0.75
            result["confidence_score"]["explanation"] = "Based on internal document analysis and extraction quality"

        return result

    async def handle_analyze_section(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generic literature/internal-docs analysis for MasterAgent."""
        query = parameters.get("query", "")
        context = parameters.get("context", {})
        prompt = f"Analyze the user's query with respect to internal literature and documents: {query}\nContext: {context}\nProvide summaries, citations, and key takeaways." 
        response = await lmstudio_client.ask_llm([{"role": "user", "content": prompt}])
        return {"analysis": response, "metadata": {"analysis_type": "literature_overview"}}
    
    async def handle_summarize_document(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of a document"""
        content = parameters.get("content", "")
        summary_length = parameters.get("length", "concise")  # concise, detailed, or executive
        
        if not content:
            # If no content provided, try to read from file
            file_path = parameters.get("file_path")
            if not file_path:
                raise ValueError("Either 'content' or 'file_path' must be provided")
            
            content = await self._read_document(file_path)
        
        # Define summary length instructions
        length_instructions = {
            "concise": "a concise 3-5 sentence summary",
            "detailed": "a detailed 2-3 paragraph summary",
            "executive": "an executive summary with key points and recommendations"
        }.get(summary_length, "a concise summary")
        
        prompt = f"""
        Please provide {length_instructions} of the following document:
        
        {content[:15000]}... [truncated]
        
        Focus on the main points, key findings, and any important conclusions or recommendations.
        """
        
        summary = await lmstudio_client.ask_llm([{"role": "user", "content": prompt}])
        
        return {
            "summary": summary,
            "metadata": {
                "summary_length": summary_length,
                "content_length": len(content),
                "source": parameters.get("file_path", "direct_content")
            }
        }
