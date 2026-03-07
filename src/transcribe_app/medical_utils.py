import re

MEDICAL_TERMS = {
    "hypertension": "high blood pressure",
    "bronchitis": "lung infection",
    "bacterial pneumonia" :"lung infection",
    "diabetes": "high blood sugar condition",
    "myocardial infarction": "heart attack",
    "fracture": "broken bone",
    "infection": "germ-related illness",
}
RISK_WORDS = [
    "emergency",
    "critical",
    "urgent",
    "immediate",
    "serious",
    "surgery",
    "danger",
    "life threatening"
]

def simplify_medical_terms(text):
    """
    Replace complex medical terms with simplified explanations.
    Case-insensitive replacement.
    """
    for term, simple in MEDICAL_TERMS.items():
        pattern = re.compile(rf"\b{term}\b", re.IGNORECASE)
        text = pattern.sub(f"{term} ({simple})", text)
    return text


def extract_instructions(text):
    dosage_pattern = r"\b\d+\s?(mg|ml|g|grams?|tablets?|capsules?)\b"
    duration_pattern = r"\b\d+\s?(days?|weeks?|months?)\b"

    dosages = re.findall(dosage_pattern, text.lower())
    durations = re.findall(duration_pattern, text.lower())

    return {
        "dosages": dosages,
        "durations": durations
    }

def detect_risk(text):
    for word in RISK_WORDS:
        if word in text.lower():
            return True
    return False