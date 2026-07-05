"""MSME Financial Health Card — scoring engine.

Public API:
    from scoring import score_entity
    card = score_entity(row_dict)
"""
from .engine import score_entity

__all__ = ["score_entity"]
