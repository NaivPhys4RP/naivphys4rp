"""
Gestalt Perception Package
Implementing Algorithm 1: Gestalt Distance (Kenfack, 2026)
"""

# 1. Promote main classes to the package level for cleaner imports
from .core import GestaltEngine
from .mtsf import MTSFExtractor
from .matching import vector_distance, optimal_fit
from .vision_utils import BildVerarbeitung, BildEntrauschung

# 2. Define what is available when someone imports *
__all__ = [
    'GestaltEngine',
    'MTSFExtractor',
    'vector_distance',
    'optimal_fit',
    'BildVerarbeitung',
    'BildEntrauschung'
]

__version__ = "0.1.0"
__author__ = "Franklin Kenghagho Kenfack"
