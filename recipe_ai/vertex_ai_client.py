"""Vertex AI client for recipe generation."""

import logging
from typing import Dict, List, Optional, Any
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from .config import RecipeAIConfig

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Client for interacting with Vertex AI for recipe generation."""
    
    def __init__(self, project_id: Optional[str] = None, location: Optional[str] = None):
        """Initialize Vertex AI client."""
        self.project_id = project_id or RecipeAIConfig.get_project_id()
        self.location = location or RecipeAIConfig.get_vertex_location()
        self.model_name = RecipeAIConfig.get_vertex_model()
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        self.model = GenerativeModel(self.model_name)
        
        logger.info(f"Initialized Vertex AI client with project: {self.project_id}, location: {self.location}")
    
    def generate_recipe(self, user_prompt: str, dietary_restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a recipe based on user prompt."""
        
        # Build the system prompt
        system_prompt = self._build_system_prompt(dietary_restrictions)
        
        # Build the user prompt
        full_prompt = f"""
{system_prompt}

Käyttäjän pyyntö: "{user_prompt}"

Luo resepti JSON-muodossa:
"""
        
        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "max_output_tokens": RecipeAIConfig.MAX_RECIPE_TOKENS,
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40
                }
            )
            
            # Parse the response
            recipe_data = self._parse_recipe_response(response.text)
            
            logger.info(f"Successfully generated recipe: {recipe_data.get('name', 'Unknown')}")
            return recipe_data
            
        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            raise
    
    def _build_system_prompt(self, dietary_restrictions: Optional[List[str]] = None) -> str:
        """Build the system prompt for recipe generation."""
        
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text = f"\nRuokavaliorajoitukset: {', '.join(dietary_restrictions)}"
        
        return f"""
Olet kokenut keittiömestari ja reseptisuunnittelija. Tehtäväsi on luoda herkullisia, käytännöllisiä reseptejä suomalaisten ruokakauppojen ainesosilla.

OHJE:
1. Luo resepti käyttäjän pyynnön perusteella
2. Käytä ainesosia, joita löytyy todennäköisesti suomalaisista ruokakaupoista (S-kaupat)
3. Anna tarkat määrät ja selkeät ohjeet
4. Sisällytä valmistusaika ja annosmäärä
5. Voit ehdottaa vaihtoehtoja ainesosille{restrictions_text}

VASTAA AINA TÄSSÄ JSON-MUODOSSA:
{{
    "name": "Reseptin nimi",
    "description": "Lyhyt kuvaus ruoasta",
    "servings": 4,
    "prep_time_minutes": 30,
    "cook_time_minutes": 45,
    "total_time_minutes": 75,
    "difficulty": "helppo|keskivaikea|vaikea",
    "ingredients": [
        {{
            "item": "ainesosan nimi",
            "amount": "määrä",
            "unit": "yksikkö",
            "notes": "mahdolliset lisätiedot"
        }}
    ],
    "instructions": [
        "Vaihe 1: Selkeä ohje",
        "Vaihe 2: Seuraava ohje",
        "..."
    ],
    "tags": ["suomalainen", "helppo", "arkiruoka"],
    "nutrition_notes": "Ravitsemustietoja tai terveysvinkkejä"
}}

Pidä ainesosat yksinkertaisina ja käytä nimiä, joita käytetään suomalaisissa ruokakaupoissa.
"""
    
    def _parse_recipe_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response to extract recipe JSON."""
        try:
            # Find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            recipe_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['name', 'ingredients', 'instructions']
            for field in required_fields:
                if field not in recipe_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set defaults for optional fields
            recipe_data.setdefault('servings', 4)
            recipe_data.setdefault('prep_time_minutes', 30)
            recipe_data.setdefault('cook_time_minutes', 30)
            recipe_data.setdefault('total_time_minutes', 60)
            recipe_data.setdefault('difficulty', 'keskivaikea')
            recipe_data.setdefault('tags', [])
            recipe_data.setdefault('description', '')
            recipe_data.setdefault('nutrition_notes', '')
            
            return recipe_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            logger.error(f"Response text: {response_text}")
            raise ValueError("Invalid JSON in AI response")
        except Exception as e:
            logger.error(f"Error parsing recipe response: {e}")
            raise
    
    def enhance_recipe_with_tips(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance recipe with cooking tips and variations."""
        
        prompt = f"""
Annettu resepti: {json.dumps(recipe_data, ensure_ascii=False, indent=2)}

Lisää tähän reseptiin:
1. Käytännöllisiä vinklejä valmistukseen
2. Mahdollisia ainesosavaihtoehtoja
3. Säilytysohjeita
4. Tarjoiluvinkkejä

Vastaa JSON-muodossa:
{{
    "cooking_tips": ["vinkki 1", "vinkki 2"],
    "ingredient_substitutions": {{"alkuperäinen": "vaihtoehto"}},
    "storage_instructions": "säilytysohje",
    "serving_suggestions": ["tarjoiluvinkki 1", "tarjoiluvinkki 2"]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            enhancement_data = self._parse_enhancement_response(response.text)
            
            # Merge with original recipe
            recipe_data.update(enhancement_data)
            
            logger.info("Successfully enhanced recipe with tips")
            return recipe_data
            
        except Exception as e:
            logger.warning(f"Failed to enhance recipe: {e}")
            # Return original recipe if enhancement fails
            return recipe_data
    
    def _parse_enhancement_response(self, response_text: str) -> Dict[str, Any]:
        """Parse enhancement response."""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        except:
            return {}  # Return empty dict if parsing fails
