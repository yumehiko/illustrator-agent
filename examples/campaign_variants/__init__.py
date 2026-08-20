"""Data-driven campaign variant production."""

from .document import build_document
from .input import CampaignInput, VariantSpec, load_campaign_input

__all__ = ["CampaignInput", "VariantSpec", "build_document", "load_campaign_input"]
