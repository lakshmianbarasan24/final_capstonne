"""
Output Specification and JSON Schema Definition.
Defines the required finding structure for the Reviewer Agent:
fields: file, line, severity, comment.
"""

import json
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field

class CodeReviewFinding(BaseModel):
    file: str = Field(..., description="Target source code filepath being reviewed.")
    line: int = Field(..., ge=1, description="Exact 1-indexed line number in source code where issue occurs.")
    severity: Literal["info", "warning", "error", "critical"] = Field(
        ..., description="Severity level of the finding."
    )
    comment: str = Field(..., min_length=5, description="Clear, constructive explanation of defect and fix.")

class CodeReviewReport(BaseModel):
    findings: List[CodeReviewFinding] = Field(
        default_factory=list, description="List of review findings."
    )

def get_review_json_schema() -> Dict[str, Any]:
    """Return JSON Schema for validating Reviewer outputs."""
    return CodeReviewReport.model_json_schema()

def validate_review_output(data: Any) -> tuple[bool, str, List[Dict[str, Any]]]:
    """
    Validates dictionary or JSON string against CodeReviewReport schema.
    Returns: (is_valid, error_msg, validated_findings)
    """
    try:
        if isinstance(data, str):
            parsed = json.loads(data)
        elif isinstance(data, dict):
            parsed = data
        elif isinstance(data, list):
            parsed = {"findings": data}
        else:
            return False, "Input must be a JSON string, dict, or list", []

        report = CodeReviewReport(**parsed)
        return True, "", [f.model_dump() for f in report.findings]
    except Exception as e:
        return False, str(e), []

if __name__ == "__main__":
    schema = get_review_json_schema()
    print("JSON Schema for Reviewer Output:")
    print(json.dumps(schema, indent=2))
