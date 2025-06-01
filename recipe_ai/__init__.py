"""
AI-powered recipe generator with ingredient pricing.
Generates recipes using Vertex AI and finds ingredient prices from BigQuery data.
"""

__version__ = "0.1.0"
__author__ = "Harri Juntunen"
__email__ = "vihreamies.juntunen@gmail.com"

from .recipe_generator import RecipeGenerator
from .ingredient_matcher import IngredientMatcher
from .vertex_ai_client import VertexAIClient

__all__ = [
    "RecipeGenerator",
    "IngredientMatcher", 
    "VertexAIClient"
]
