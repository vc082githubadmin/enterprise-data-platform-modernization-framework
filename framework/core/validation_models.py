from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"


@dataclass(frozen=True)
class Issue:
    code: str
    severity: Severity
    path: str
    message: str
    hint: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "code": self.code.value if hasattr(self.code, "value") else self.code,
            "severity": self.severity.value,
            "path": self.path,
            "message": self.message,
        }
        if self.hint:
            d["hint"] = self.hint
        if self.context:
            d["context"] = self.context
        return d


@dataclass
class ValidationResult:
    issues: List[Issue] = field(default_factory=list)

    @property
    def errors(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARN]

    def is_valid(self, strict: bool = False) -> bool:
        # strict=True can treat WARN as blocking
        if self.errors:
            return False
        if strict and self.warnings:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"issues": [i.to_dict() for i in self.issues]}
    
    def raise_if_invalid(self, strict: bool = False) -> None:
        if not self.is_valid(strict=strict):
            formatted = "\n".join(
                [f"- [{i.severity.value}:{i.code}] {i.path}: {i.message}" for i in self.issues]
            )
            raise ValueError(f"Contract validation failed:\n{formatted}")