"""
Provenance and Reproducibility Hashing Module.
Calculates SHA-256 hashes for prompt templates, model checkpoints,
golden dataset files, and installed dependencies to ensure audit traceability.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict

def hash_text(text: str) -> str:
    """Calculate SHA-256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def hash_file(filepath: str) -> str:
    """Calculate SHA-256 hash of a file's contents."""
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_dependency_hash() -> str:
    """Hash the sorted list of installed packages or requirements.txt."""
    req_path = Path(__file__).parent.parent / "requirements.txt"
    if req_path.exists():
        return hash_file(str(req_path))
    # Fallback to python version + sys.modules
    info = f"{sys.version}_{sys.platform}"
    return hash_text(info)

class ProvenanceTracker:
    def __init__(self, model_checkpoint: str = "gemini-2.0-flash"):
        self.model_checkpoint = model_checkpoint
        self.model_hash = hash_text(model_checkpoint)
        self.dep_hash = get_dependency_hash()
        self.golden_dataset_path = str(Path(__file__).parent.parent / "data" / "golden_dataset_v1.json")
        self._cached_dataset_hash = hash_file(self.golden_dataset_path)

    def get_dataset_hash(self) -> str:
        return self._cached_dataset_hash

    def get_prompt_hash(self, prompt_text: str) -> str:
        return hash_text(prompt_text)

    def get_provenance_record(self, prompt_text: str = "") -> Dict[str, str]:
        """Returns provenance dictionary for inclusion in audit logs."""
        return {
            "model_checkpoint": self.model_checkpoint,
            "model_hash": self.model_hash,
            "dataset_hash": self.get_dataset_hash(),
            "dependency_hash": self.dep_hash,
            "prompt_hash": self.get_prompt_hash(prompt_text) if prompt_text else "N/A"
        }

_tracker_singleton = None

def get_provenance_tracker(model_checkpoint: str = "gemini-2.0-flash") -> ProvenanceTracker:
    global _tracker_singleton
    if _tracker_singleton is None:
        _tracker_singleton = ProvenanceTracker(model_checkpoint)
    return _tracker_singleton
