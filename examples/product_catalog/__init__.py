"""Public entry points for the product catalog production."""

from .cli import DEFAULT_OUTPUT, PRODUCTION_CONTRACT, main
from .document import DOCUMENT_SOURCE, LINK, build_document

__all__ = [
    "DEFAULT_OUTPUT",
    "DOCUMENT_SOURCE",
    "LINK",
    "PRODUCTION_CONTRACT",
    "build_document",
    "main",
]
