"""Supervised learning strategy module"""

from .features import prepare_data
from .selection import select_feature
from .model import train_model

__all__ = ["prepare_data", "select_feature", "train_model"]
