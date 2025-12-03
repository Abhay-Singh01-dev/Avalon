"""
Timeline event definitions for agent execution visualization.

Hospital-Grade Timeline System for Pilot Deployment
- Full audit trail of all pipeline steps
- PHI routing visibility
- Document processing tracking
- Mode classification logging
"""
from typing import Dict, Any, Optional, Callable, AsyncGenerator
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TimelineEventType(str, Enum):
    """All timeline event types for the Avalon pipeline."""
    
    # Agent lifecycle events
    AGENT_START = "agent_start"
    AGENT_PROGRESS = "agent_progress"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    
    # Orchestration events
    DECOMPOSITION_START = "decomposition_start"
    DECOMPOSITION_COMPLETE = "decomposition_complete"
    SYNTHESIS_START = "synthesis_start"
    SYNTHESIS_COMPLETE = "synthesis_complete"
    
    # Mode classification events
    MODE_CLASSIFICATION = "mode_classification"
    MODE_SIMPLE = "mode_simple"
    MODE_RESEARCH = "mode_research"
    MODE_TABLE = "mode_table"
    MODE_DOCUMENT = "mode_document"
    MODE_SAFETY = "mode_safety"
    MODE_PATIENT = "mode_patient"
    MODE_EXPERT = "mode_expert"
    
    # PHI & Security events (CRITICAL for audit)
    PHI_DETECTED = "phi_detected"
    PHI_ROUTING = "phi_routing"
    LOCAL_ONLY_ENFORCED = "local_only_enforced"
    CLOUD_BLOCKED = "cloud_blocked"
    
    # Document processing events
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_EXTRACTION = "document_extraction"
    DOCUMENT_PHI_SCAN = "document_phi_scan"
    DOCUMENT_ANALYSIS = "document_analysis"
    
    # LLM routing events
    LLM_ROUTING = "llm_routing"
    LLM_LOCAL_CALL = "llm_local_call"
    LLM_LOCAL_RESPONSE = "llm_local_response"
    LLM_ERROR = "llm_error"
    LLM_FALLBACK = "llm_fallback"
    
    # Report events
    REPORT_GENERATION_START = "report_generation_start"
    REPORT_GENERATION_COMPLETE = "report_generation_complete"
    
    # Research insights
    INSIGHTS_COMPILATION = "insights_compilation"
    
    # Error and fallback events
    ERROR = "error"
    FALLBACK = "fallback"
    GRACEFUL_DEGRADATION = "graceful_degradation"

def create_timeline_event(
    event_type: TimelineEventType,
    agent: str,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a timeline event dictionary with automatic timestamp."""
    event = {
        "type": "timeline",
        "event": event_type.value,
        "agent": agent,
        "timestamp": datetime.utcnow().isoformat()
    }
    if message:
        event["message"] = message
    if metadata:
        event["metadata"] = metadata
    
    # Log critical events for audit trail
    if event_type in [
        TimelineEventType.PHI_DETECTED,
        TimelineEventType.PHI_ROUTING,
        TimelineEventType.LOCAL_ONLY_ENFORCED,
        TimelineEventType.CLOUD_BLOCKED,
        TimelineEventType.ERROR
    ]:
        logger.warning(f"[AUDIT] {event_type.value}: {message} | Agent: {agent}")
    
    return event


def create_phi_event(
    phi_detected: bool,
    phi_types: list,
    confidence: float,
    action: str = "local_routing"
) -> Dict[str, Any]:
    """
    Create a PHI-specific timeline event for audit compliance.
    
    Args:
        phi_detected: Whether PHI was detected
        phi_types: List of PHI types found
        confidence: Detection confidence (0-1)
        action: Action taken (local_routing, blocked, etc.)
    
    Returns:
        Timeline event dictionary
    """
    if phi_detected:
        message = f"⚠️ PHI DETECTED (confidence: {confidence:.0%}) - Routing to LOCAL model only"
        event_type = TimelineEventType.PHI_DETECTED
    else:
        message = "✓ No PHI detected - Standard routing"
        event_type = TimelineEventType.LLM_ROUTING
    
    return create_timeline_event(
        event_type=event_type,
        agent="security",
        message=message,
        metadata={
            "phi_detected": phi_detected,
            "phi_types": phi_types,
            "confidence": confidence,
            "action": action,
            "audit_timestamp": datetime.utcnow().isoformat()
        }
    )


def create_mode_event(mode: str, reason: str) -> Dict[str, Any]:
    """
    Create a mode classification timeline event.
    
    Args:
        mode: Detected mode (simple, research, table, etc.)
        reason: Reason for mode selection
    
    Returns:
        Timeline event dictionary
    """
    mode_icons = {
        "simple": "💬",
        "research": "🔬",
        "table": "📊",
        "document": "📄",
        "safety": "🛡️",
        "patient": "🏥",
        "expert": "👥"
    }
    
    icon = mode_icons.get(mode.lower(), "⚙️")
    message = f"{icon} {mode.upper()} MODE - {reason}"
    
    # Map mode to event type
    mode_event_map = {
        "simple": TimelineEventType.MODE_SIMPLE,
        "research": TimelineEventType.MODE_RESEARCH,
        "table": TimelineEventType.MODE_TABLE,
        "document": TimelineEventType.MODE_DOCUMENT,
        "safety": TimelineEventType.MODE_SAFETY,
        "patient": TimelineEventType.MODE_PATIENT,
        "expert": TimelineEventType.MODE_EXPERT
    }
    
    event_type = mode_event_map.get(mode.lower(), TimelineEventType.MODE_CLASSIFICATION)
    
    return create_timeline_event(
        event_type=event_type,
        agent="master",
        message=message,
        metadata={
            "mode": mode,
            "reason": reason
        }
    )


def create_document_event(
    event_type: str,
    filename: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a document processing timeline event.
    
    Args:
        event_type: Type of document event (upload, extraction, phi_scan, analysis)
        filename: Name of the document
        message: Event message
        metadata: Additional metadata
    
    Returns:
        Timeline event dictionary
    """
    event_map = {
        "upload": TimelineEventType.DOCUMENT_UPLOAD,
        "extraction": TimelineEventType.DOCUMENT_EXTRACTION,
        "phi_scan": TimelineEventType.DOCUMENT_PHI_SCAN,
        "analysis": TimelineEventType.DOCUMENT_ANALYSIS
    }
    
    timeline_type = event_map.get(event_type, TimelineEventType.DOCUMENT_ANALYSIS)
    
    event_metadata = {"filename": filename}
    if metadata:
        event_metadata.update(metadata)
    
    return create_timeline_event(
        event_type=timeline_type,
        agent="internal_docs",
        message=message,
        metadata=event_metadata
    )


def create_error_event(
    agent: str,
    error_message: str,
    error_type: str = "unknown",
    fallback_action: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an error timeline event with optional fallback information.
    
    Args:
        agent: Agent that encountered the error
        error_message: Description of the error
        error_type: Type/category of error
        fallback_action: What fallback action was taken (if any)
    
    Returns:
        Timeline event dictionary
    """
    if fallback_action:
        message = f"⚠️ {error_message} - Fallback: {fallback_action}"
        event_type = TimelineEventType.GRACEFUL_DEGRADATION
    else:
        message = f"❌ {error_message}"
        event_type = TimelineEventType.ERROR
    
    return create_timeline_event(
        event_type=event_type,
        agent=agent,
        message=message,
        metadata={
            "error_type": error_type,
            "error_message": error_message,
            "fallback_action": fallback_action,
            "recoverable": fallback_action is not None
        }
    )

# Agent name mappings for display
AGENT_DISPLAY_NAMES = {
    "master": "MasterAgent",
    "market": "MarketAgent",
    "clinical": "ClinicalTrialsAgent",
    "clinical_trials": "ClinicalTrialsAgent",
    "patents": "PatentAgent",
    "patent": "PatentAgent",
    "exim": "EXIMAgent",
    "web": "WebIntelAgent",
    "web_intel": "WebIntelAgent",
    "safety": "SafetyPKPDAgent",
    "safety_pkpd": "SafetyPKPDAgent",
    "internal_docs": "InternalDocsAgent",
    "expert_network": "ExpertNetworkAgent",
    "report_generator": "ReportGeneratorAgent",
}

def get_agent_display_name(agent_type: str) -> str:
    """Get display name for agent type."""
    return AGENT_DISPLAY_NAMES.get(agent_type.lower(), agent_type)

