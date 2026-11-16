"""
PII and Secret Masking Module.
Uses Microsoft Presidio Analyzer & Anonymizer with custom secret recognizers,
plus deterministic regex masks for API keys, bearer tokens, passwords, and emails.
"""

import re
from typing import Tuple, List, Dict

try:
    from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
    from presidio_anonymizer import AnonymizerEngine
    _HAS_PRESIDIO = True
except ImportError:
    _HAS_PRESIDIO = False


# Deterministic high-precision regex patterns for secrets and PII
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{16,})(['\"]?)", r"\1<MASKED_API_KEY>\3"),
    (r"(?i)(secret[_-]?key\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{16,})(['\"]?)", r"\1<MASKED_SECRET_KEY>\3"),
    (r"(?i)(password\s*[:=]\s*['\"]?)([^'\"\s\n]{6,})(['\"]?)", r"\1<MASKED_PASSWORD>\3"),
    (r"(?i)(bearer\s+)([A-Za-z0-9_\-\.]{20,})", r"\1<MASKED_BEARER_TOKEN>"),
    (r"(AKIA[0-9A-Z]{16})", "<MASKED_AWS_KEY>"),
    (r"(sk-[A-Za-z0-9]{20,})", "<MASKED_OPENAI_KEY>"),
    (r"(AIza[0-9A-Za-z-_]{35})", "<MASKED_GOOGLE_KEY>"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "<MASKED_EMAIL>"),
]


class PIIMasker:
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        if _HAS_PRESIDIO:
            try:
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                self._add_custom_recognizers()
            except Exception:
                self.analyzer = None
                self.anonymizer = None

    def _add_custom_recognizers(self):
        if not self.analyzer:
            return
        # Add AWS Key recognizer
        aws_pattern = Pattern(name="aws_key_pattern", regex=r"AKIA[0-9A-Z]{16}", score=0.95)
        aws_recognizer = PatternRecognizer(supported_entity="AWS_KEY", patterns=[aws_pattern])
        self.analyzer.registry.add_recognizer(aws_recognizer)

        # Add Generic API Key recognizer
        api_pattern = Pattern(name="generic_api_key", regex=r"(?i)(?:key|token|secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", score=0.85)
        api_recognizer = PatternRecognizer(supported_entity="API_KEY", patterns=[api_pattern])
        self.analyzer.registry.add_recognizer(api_recognizer)

    def mask(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Masks all PII, secrets, API keys, and emails from the input text.
        Returns: (masked_text: str, detected_leaks: list)
        """
        if not text:
            return text, []

        detected = []
        masked_text = text

        # 1. Use Presidio if available for entities like EMAIL_ADDRESS, PERSON, PHONE_NUMBER, etc.
        has_potential_pii = bool(re.search(r"(?i)[@\d]|(key|token|secret|password|bearer|akia|email|phone)", masked_text))
        if has_potential_pii and self.analyzer and self.anonymizer:
            try:
                results = self.analyzer.analyze(
                    text=masked_text,
                    language="en",
                    entities=["EMAIL_ADDRESS", "IP_ADDRESS", "PHONE_NUMBER", "AWS_KEY", "API_KEY"]
                )
                if results:
                    for r in results:
                        detected.append({
                            "entity_type": r.entity_type,
                            "start": r.start,
                            "end": r.end,
                            "score": r.score
                        })
                    anonymized_result = self.anonymizer.anonymize(
                        text=masked_text,
                        analyzer_results=results
                    )
                    masked_text = anonymized_result.text
            except Exception:
                pass

        # 2. Always run deterministic regex scrubbing to guarantee 0 leaks on secrets & emails
        for pattern, replacement in SECRET_PATTERNS:
            matches = list(re.finditer(pattern, masked_text))
            if matches:
                for m in matches:
                    detected.append({
                        "entity_type": "SECRET_OR_PII",
                        "matched": m.group(0)[:10] + "...",
                        "span": m.span()
                    })
                masked_text = re.sub(pattern, replacement, masked_text)

        return masked_text, detected


_masker_singleton = None

def get_pii_masker() -> PIIMasker:
    global _masker_singleton
    if _masker_singleton is None:
        _masker_singleton = PIIMasker()
    return _masker_singleton

def mask_pii_and_secrets(text: str) -> Tuple[str, List[Dict[str, str]]]:
    return get_pii_masker().mask(text)
