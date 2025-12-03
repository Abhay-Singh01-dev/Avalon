"""
PHI (Protected Health Information) Detection Module

Hospital-Grade PHI Detection for Pilot Deployment
Ensures all PHI queries are routed to local model only.

HIPAA 18 Identifiers:
1. Names
2. Geographic data
3. Dates (except year)
4. Phone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers
13. Device identifiers
14. Web URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photos
18. Any other unique identifying number
"""

import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PHIType(str, Enum):
    """Types of PHI detected"""
    NAME = "name"
    SSN = "ssn"
    MRN = "medical_record_number"
    DOB = "date_of_birth"
    PHONE = "phone_number"
    EMAIL = "email"
    ADDRESS = "address"
    PATIENT_DATA = "patient_data"
    LAB_RESULTS = "lab_results"
    VITALS = "vital_signs"
    DIAGNOSIS = "diagnosis"
    MEDICATION_SPECIFIC = "medication_specific"
    UNKNOWN = "unknown"


@dataclass
class PHIDetectionResult:
    """Result of PHI detection analysis"""
    contains_phi: bool
    phi_types: List[PHIType]
    confidence: float  # 0.0 to 1.0
    matched_patterns: List[str]
    redacted_text: Optional[str] = None
    recommendation: str = "local"  # "local" or "block"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "contains_phi": self.contains_phi,
            "phi_types": [t.value for t in self.phi_types],
            "confidence": self.confidence,
            "matched_patterns": self.matched_patterns,
            "recommendation": self.recommendation
        }


class PHIDetector:
    """
    Comprehensive PHI Detection for Hospital-Grade Security.
    
    This detector uses multiple strategies:
    1. Regex patterns for structured data (SSN, MRN, dates, etc.)
    2. Keyword heuristics for patient-related terms
    3. Context analysis for medical measurements
    """
    
    # =========================================================================
    # REGEX PATTERNS FOR STRUCTURED PHI
    # =========================================================================
    
    # Social Security Number patterns
    SSN_PATTERNS = [
        r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',  # 123-45-6789 or 123 45 6789
        r'\bssn[:\s]*\d{9}\b',  # SSN: 123456789
        r'\bsocial\s*security[:\s#]*\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
    ]
    
    # Medical Record Number patterns
    MRN_PATTERNS = [
        r'\bmr[n#]?[:\s]*[a-z]?\d{6,10}\b',  # MRN: 12345678 or MR# A12345678
        r'\bmedical\s*record[:\s#]*\d{6,12}\b',
        r'\bpatient\s*id[:\s#]*\d{5,12}\b',
        r'\bchart[:\s#]*\d{5,10}\b',
        r'\baccount[:\s#]*\d{6,12}\b',
    ]
    
    # Date of Birth patterns (specific dates, not just years)
    DOB_PATTERNS = [
        r'\bdob[:\s]*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        r'\bdate\s*of\s*birth[:\s]*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        r'\bborn\s*(?:on\s*)?\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        r'\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}\b',
    ]
    
    # Phone number patterns
    PHONE_PATTERNS = [
        r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        r'\bphone[:\s]*\d{10,12}\b',
        r'\bcell[:\s]*\d{10,12}\b',
        r'\btel[:\s]*\d{10,12}\b',
    ]
    
    # Email patterns
    EMAIL_PATTERNS = [
        r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
    ]
    
    # Address patterns
    ADDRESS_PATTERNS = [
        r'\b\d{1,5}\s+\w+\s+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|court|ct|boulevard|blvd)\b',
        r'\baddress[:\s]*\d{1,5}\s+\w+',
    ]
    
    # =========================================================================
    # KEYWORD PATTERNS FOR PATIENT CONTEXT
    # =========================================================================
    
    PATIENT_INDICATORS = [
        # Direct patient references
        "my patient",
        "the patient",
        "patient name",
        "patient:",
        "pt:",
        "pt name",
        
        # Case-specific references
        "this case",
        "case study",
        "case report",
        "presented with",
        "was admitted",
        "was discharged",
        
        # Clinical notes style
        "chief complaint",
        "cc:",
        "hpi:",
        "history of present illness",
        "pmh:",
        "past medical history",
        "ros:",
        "review of systems",
        "physical exam",
        "pe:",
        "assessment:",
        "plan:",
        "a/p:",
        
        # Specific patient data
        "patient id",
        "medical record",
        "chart number",
        "admission date",
        "discharge date",
    ]
    
    # Lab results and vitals (with values)
    CLINICAL_MEASUREMENT_PATTERNS = [
        r'\bhba1c[:\s]*\d+\.?\d*\s*%',  # HbA1c 8.9%
        r'\bfasting\s*glucose[:\s]*\d+',
        r'\bblood\s*pressure[:\s]*\d+/\d+',
        r'\bbp[:\s]*\d+/\d+',
        r'\bhr[:\s]*\d+\s*bpm',
        r'\bheart\s*rate[:\s]*\d+',
        r'\bweight[:\s]*\d+\.?\d*\s*(?:kg|lbs?|pounds?)',
        r'\bheight[:\s]*\d+\.?\d*\s*(?:cm|m|ft|feet|inches?)',
        r'\bbmi[:\s]*\d+\.?\d*',
        r'\begfr[:\s]*\d+',
        r'\bcreatinine[:\s]*\d+\.?\d*',
        r'\balt[:\s]*\d+',
        r'\bast[:\s]*\d+',
        r'\bldl[:\s]*\d+',
        r'\bhdl[:\s]*\d+',
        r'\btriglycerides?[:\s]*\d+',
        r'\bhemoglobin[:\s]*\d+\.?\d*',
        r'\bplatelet[s]?[:\s]*\d+',
        r'\bwbc[:\s]*\d+\.?\d*',
        r'\brbc[:\s]*\d+\.?\d*',
        r'\binr[:\s]*\d+\.?\d*',
        r'\bptt[:\s]*\d+\.?\d*',
        r'\btemperature[:\s]*\d+\.?\d*\s*(?:°?[cf]|celsius|fahrenheit)',
        r'\btemp[:\s]*\d+\.?\d*',
        r'\bspo2[:\s]*\d+\s*%',
        r'\boxygen\s*sat[uration]*[:\s]*\d+',
        r'\brespiratory\s*rate[:\s]*\d+',
        r'\brr[:\s]*\d+',
    ]
    
    # Names pattern (common name indicators)
    NAME_INDICATORS = [
        r'\bname[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Name: John Smith
        r'\bpatient[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+',
        r'\bmr\.?\s+[A-Z][a-z]+',  # Mr. Smith
        r'\bmrs\.?\s+[A-Z][a-z]+',
        r'\bms\.?\s+[A-Z][a-z]+',
        r'\bdr\.?\s+[A-Z][a-z]+',
    ]
    
    # Common placeholder names (should still trigger PHI detection)
    PLACEHOLDER_NAMES = [
        "john doe",
        "jane doe",
        "john smith",
        "jane smith",
        "patient a",
        "patient b",
        "patient x",
        "patient y",
        "patient 1",
        "patient 2",
    ]
    
    def __init__(self):
        """Initialize PHI detector with compiled regex patterns."""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns for efficiency."""
        self.compiled_ssn = [re.compile(p, re.IGNORECASE) for p in self.SSN_PATTERNS]
        self.compiled_mrn = [re.compile(p, re.IGNORECASE) for p in self.MRN_PATTERNS]
        self.compiled_dob = [re.compile(p, re.IGNORECASE) for p in self.DOB_PATTERNS]
        self.compiled_phone = [re.compile(p, re.IGNORECASE) for p in self.PHONE_PATTERNS]
        self.compiled_email = [re.compile(p, re.IGNORECASE) for p in self.EMAIL_PATTERNS]
        self.compiled_address = [re.compile(p, re.IGNORECASE) for p in self.ADDRESS_PATTERNS]
        self.compiled_clinical = [re.compile(p, re.IGNORECASE) for p in self.CLINICAL_MEASUREMENT_PATTERNS]
        self.compiled_names = [re.compile(p, re.IGNORECASE) for p in self.NAME_INDICATORS]
    
    def detect(self, text: str) -> PHIDetectionResult:
        """
        Detect PHI in the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            PHIDetectionResult with detection details
        """
        if not text or not text.strip():
            return PHIDetectionResult(
                contains_phi=False,
                phi_types=[],
                confidence=1.0,
                matched_patterns=[],
                recommendation="local"
            )
        
        text_lower = text.lower()
        phi_types = []
        matched_patterns = []
        confidence = 0.0
        
        # Check structured patterns (HIGH confidence)
        
        # SSN detection
        for pattern in self.compiled_ssn:
            if pattern.search(text):
                phi_types.append(PHIType.SSN)
                matched_patterns.append("SSN pattern detected")
                confidence = max(confidence, 0.95)
                break
        
        # MRN detection
        for pattern in self.compiled_mrn:
            if pattern.search(text):
                phi_types.append(PHIType.MRN)
                matched_patterns.append("Medical Record Number pattern detected")
                confidence = max(confidence, 0.95)
                break
        
        # DOB detection
        for pattern in self.compiled_dob:
            if pattern.search(text):
                phi_types.append(PHIType.DOB)
                matched_patterns.append("Date of Birth pattern detected")
                confidence = max(confidence, 0.9)
                break
        
        # Phone detection
        for pattern in self.compiled_phone:
            if pattern.search(text):
                phi_types.append(PHIType.PHONE)
                matched_patterns.append("Phone number pattern detected")
                confidence = max(confidence, 0.85)
                break
        
        # Email detection
        for pattern in self.compiled_email:
            if pattern.search(text):
                phi_types.append(PHIType.EMAIL)
                matched_patterns.append("Email address detected")
                confidence = max(confidence, 0.85)
                break
        
        # Address detection
        for pattern in self.compiled_address:
            if pattern.search(text):
                phi_types.append(PHIType.ADDRESS)
                matched_patterns.append("Physical address pattern detected")
                confidence = max(confidence, 0.8)
                break
        
        # Name detection
        for pattern in self.compiled_names:
            if pattern.search(text):
                phi_types.append(PHIType.NAME)
                matched_patterns.append("Patient name pattern detected")
                confidence = max(confidence, 0.85)
                break
        
        # Check for placeholder names
        for name in self.PLACEHOLDER_NAMES:
            if name in text_lower:
                phi_types.append(PHIType.NAME)
                matched_patterns.append(f"Placeholder name '{name}' detected")
                confidence = max(confidence, 0.9)
                break
        
        # Check keyword patterns (MEDIUM confidence)
        for indicator in self.PATIENT_INDICATORS:
            if indicator in text_lower:
                if PHIType.PATIENT_DATA not in phi_types:
                    phi_types.append(PHIType.PATIENT_DATA)
                    matched_patterns.append(f"Patient indicator '{indicator}' detected")
                    confidence = max(confidence, 0.75)
                break
        
        # Check clinical measurements with values (HIGH confidence for patient context)
        for pattern in self.compiled_clinical:
            if pattern.search(text):
                # Clinical measurements WITH "patient" context = HIGH PHI confidence
                if any(ind in text_lower for ind in ["patient", "pt", "case", "admitted"]):
                    phi_types.append(PHIType.LAB_RESULTS)
                    matched_patterns.append("Clinical measurement with patient context detected")
                    confidence = max(confidence, 0.9)
                else:
                    # Generic clinical values without patient context = LOWER confidence
                    # (could be asking about normal ranges)
                    if PHIType.VITALS not in phi_types:
                        phi_types.append(PHIType.VITALS)
                        matched_patterns.append("Clinical measurement detected")
                        confidence = max(confidence, 0.5)
                break
        
        # Determine if PHI is present
        contains_phi = len(phi_types) > 0 and confidence >= 0.5
        
        # Log PHI detection for audit
        if contains_phi:
            logger.warning(
                f"[PHI_DETECTION] PHI detected with confidence {confidence:.2f}. "
                f"Types: {[t.value for t in phi_types]}. "
                f"Patterns: {matched_patterns}"
            )
        
        return PHIDetectionResult(
            contains_phi=contains_phi,
            phi_types=phi_types,
            confidence=confidence,
            matched_patterns=matched_patterns,
            recommendation="local" if contains_phi else "any"
        )
    
    def detect_in_document(self, text: str) -> PHIDetectionResult:
        """
        Detect PHI in uploaded document content.
        Uses stricter detection for documents.
        
        Args:
            text: Document text content
            
        Returns:
            PHIDetectionResult with detection details
        """
        # Use standard detection
        result = self.detect(text)
        
        # For documents, also check for multiple clinical values (suggests patient record)
        clinical_count = 0
        for pattern in self.compiled_clinical:
            if pattern.search(text):
                clinical_count += 1
        
        if clinical_count >= 3:
            # Multiple clinical values in document = likely patient record
            if not result.contains_phi:
                result.contains_phi = True
                result.phi_types.append(PHIType.LAB_RESULTS)
                result.matched_patterns.append(f"Multiple clinical values ({clinical_count}) detected in document")
                result.confidence = max(result.confidence, 0.85)
                result.recommendation = "local"
        
        return result


# Singleton instance
phi_detector = PHIDetector()


def detect_phi(text: str) -> PHIDetectionResult:
    """
    Convenience function for PHI detection.
    
    Args:
        text: Text to analyze
        
    Returns:
        PHIDetectionResult
    """
    return phi_detector.detect(text)


def detect_phi_in_document(text: str) -> PHIDetectionResult:
    """
    Convenience function for PHI detection in documents.
    
    Args:
        text: Document text to analyze
        
    Returns:
        PHIDetectionResult
    """
    return phi_detector.detect_in_document(text)


def contains_phi(text: str) -> bool:
    """
    Simple boolean check for PHI presence.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if PHI is detected
    """
    return phi_detector.detect(text).contains_phi
