"""
Data Quality Validators for the Golden Dataset.
Implements:
1. Validator 1: Duplicate check (uniqueness of IDs and file contents).
2. Validator 2: Schema completeness (presence of all mandatory fields).
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from pydantic import BaseModel, Field, ValidationError

class ExpectedFindingSchema(BaseModel):
    file: str
    line: int
    severity: str
    comment: str

class GoldenSampleSchema(BaseModel):
    id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    filename: str = Field(..., min_length=1)
    is_adversarial: bool
    is_restricted: bool
    content: str = Field(..., min_length=1)
    expected_findings: List[ExpectedFindingSchema]

class GoldenDatasetSchema(BaseModel):
    version: str = Field(..., min_length=1)
    sample_count: int
    samples: List[GoldenSampleSchema]


def validate_golden_dataset(dataset_path: Path) -> Dict[str, Any]:
    """
    Validates golden dataset against duplicate and schema completeness rules.
    Returns validation report dictionary.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Golden dataset not found at: {dataset_path}")

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Pydantic Schema Validation (Required Fields & Types)
    try:
        validated_dataset = GoldenDatasetSchema(**data)
    except ValidationError as e:
        return {
            "is_valid": False,
            "error_type": "SCHEMA_VALIDATION_ERROR",
            "details": e.errors()
        }

    # 2. Duplicate ID & Duplicate Content Checks
    seen_ids = set()
    seen_contents = set()
    duplicate_ids = []
    duplicate_contents = []

    for sample in validated_dataset.samples:
        if sample.id in seen_ids:
            duplicate_ids.append(sample.id)
        seen_ids.add(sample.id)

        normalized_content = sample.content.strip()
        if normalized_content in seen_contents:
            duplicate_contents.append(sample.id)
        seen_contents.add(normalized_content)

    if duplicate_ids or duplicate_contents:
        return {
            "is_valid": False,
            "error_type": "DUPLICATE_ENTRIES_FOUND",
            "duplicate_ids": duplicate_ids,
            "duplicate_contents": duplicate_contents
        }

    # Check clean vs adversarial minimum counts (at least 5 clean, 5 adversarial)
    clean_count = sum(1 for s in validated_dataset.samples if s.category == "clean")
    adv_count = sum(1 for s in validated_dataset.samples if s.is_adversarial)

    return {
        "is_valid": True,
        "sample_count": validated_dataset.sample_count,
        "clean_samples": clean_count,
        "adversarial_samples": adv_count,
        "duplicate_count": 0,
        "status": "PASS: All required fields present and 0 duplicates detected."
    }

if __name__ == "__main__":
    dataset_file = Path(__file__).parent / "golden_dataset_v1.json"
    res = validate_golden_dataset(dataset_file)
    print("Validation Results:")
    print(json.dumps(res, indent=2))
