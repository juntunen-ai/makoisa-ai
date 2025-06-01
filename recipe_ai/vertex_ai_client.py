"""Vertex AI client for recipe generation."""

import logging
from typing import Dict, List, Optional, Any
import json
import random
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
        self.model = None
        self.fallback_mode = False
        
        try:
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel(self.model_name)
            logger.info(f"Initialized Vertex AI client with project: {self.project_id}, location: {self.location}")
        except Exception as e:
            logger.warning(f"Failed to initialize Vertex AI, using fallback mode: {e}")
            self.fallback_mode = True
    
    def generate_recipe(self, user_prompt: str, dietary_restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a recipe based on user prompt."""
        
        # Check if we should use fallback mode
        if self.fallback_mode or self.model is None:
            logger.info("Using fallback recipe generation")
            return self._generate_fallback_recipe(user_prompt, dietary_restrictions)
        
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
            logger.warning(f"Vertex AI failed, falling back to demo recipe: {e}")
            return self._generate_fallback_recipe(user_prompt, dietary_restrictions)
    
    def _generate_fallback_recipe(self, user_prompt: str, dietary_restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate a fallback recipe when Vertex AI is not available."""
        
        # Demo recipes to choose from
        demo_recipes = [
            {
                "name": "Helppo Kanapastavuoka",
                "description": "Kermainen kanapastavuoka joka maistuu koko perheelle",
                "servings": 4,
                "prep_time_minutes": 15,
                "cook_time_minutes": 30,
                "total_time_minutes": 45,
                "difficulty": "helppo",
                "ingredients": [
                    {"item": "kanafilee", "amount": "400", "unit": "g", "notes": "kuutioitu"},
                    {"item": "pasta", "amount": "300", "unit": "g", "notes": "esim. penne"},
                    {"item": "ruokakerma", "amount": "2", "unit": "dl", "notes": ""},
                    {"item": "sipuli", "amount": "1", "unit": "kpl", "notes": "hienoksi silppu"},
                    {"item": "valkosipuli", "amount": "2", "unit": "kynttä", "notes": "hienoksi silppu"},
                    {"item": "tomaattipyree", "amount": "2", "unit": "rkl", "notes": ""},
                    {"item": "ranskankermajuusto", "amount": "150", "unit": "g", "notes": ""},
                    {"item": "basilika", "amount": "1", "unit": "tl", "notes": "kuivattua"},
                    {"item": "suola", "amount": "", "unit": "", "notes": "maun mukaan"},
                    {"item": "pippuri", "amount": "", "unit": "", "notes": "maun mukaan"}
                ],
                "instructions": [
                    "Keitä pasta ohjeen mukaan suolassa vedessä. Valuta.",
                    "Kuumenna öljy pannulla ja paista kanakuutiot kypsiksi. Mausta suolalla ja pippurilla.",
                    "Lisää sipuli ja valkosipuli. Paista hetki.",
                    "Lisää tomaattipyree ja sekoita. Anna kiehua hetki.",
                    "Kaada kerma ja anna kiehua muutama minuutti.",
                    "Lisää ranskankermajuusto ja basilika. Sekoita kunnes juusto sulaa.",
                    "Lisää pasta kastikkeeseen ja sekoita hyvin.",
                    "Tarjoile heti lämpimänä."
                ],
                "tags": ["helppo", "arkiruoka", "pasta", "kana"],
                "nutrition_notes": "Runsaasti proteiinia kanasta, hiilihydraatteja pastasta"
            },
            {
                "name": "Suomalainen Hernekeitto",
                "description": "Perinteinen suomalainen hernekeitto pannukakun kanssa",
                "servings": 6,
                "prep_time_minutes": 20,
                "cook_time_minutes": 120,
                "total_time_minutes": 140,
                "difficulty": "helppo",
                "ingredients": [
                    {"item": "kuivatut herneet", "amount": "500", "unit": "g", "notes": "liotu yön yli"},
                    {"item": "sianliha", "amount": "300", "unit": "g", "notes": "esim. kylkiluu"},
                    {"item": "sipuli", "amount": "1", "unit": "kpl", "notes": "kuutioitu"},
                    {"item": "porkkana", "amount": "2", "unit": "kpl", "notes": "kuutioitu"},
                    {"item": "vesi", "amount": "2", "unit": "l", "notes": ""},
                    {"item": "suola", "amount": "1", "unit": "tl", "notes": ""},
                    {"item": "sinappi", "amount": "", "unit": "", "notes": "tarjoiluun"}
                ],
                "instructions": [
                    "Liota herneet yön yli kylmässä vedessä.",
                    "Valuta ja huuhtele herneet.",
                    "Laita herneet, liha ja vesi kattilaan. Keitä.",
                    "Poista vaahto pinnalta. Anna hautua 1,5 tuntia.",
                    "Lisää sipuli ja porkkana. Keitä 30 min lisää.",
                    "Mausta suolalla.",
                    "Tarjoile sinapin kanssa ja pannukakun kera."
                ],
                "tags": ["perinteinen", "suomalainen", "talviruoka"],
                "nutrition_notes": "Paljon proteiinia ja kuitua, täyttävä ateria"
            },
            {
                "name": "Lohikiusaus",
                "description": "Suomalainen klassikko uuniruoka lohesta ja perunoista",
                "servings": 4,
                "prep_time_minutes": 30,
                "cook_time_minutes": 45,
                "total_time_minutes": 75,
                "difficulty": "keskivaikea",
                "ingredients": [
                    {"item": "lohi", "amount": "400", "unit": "g", "notes": "fileenä, kuutioitu"},
                    {"item": "peruna", "amount": "800", "unit": "g", "notes": "ohut viipaleet"},
                    {"item": "sipuli", "amount": "1", "unit": "kpl", "notes": "viipaleet"},
                    {"item": "ruokakerma", "amount": "3", "unit": "dl", "notes": ""},
                    {"item": "juustoraaste", "amount": "100", "unit": "g", "notes": ""},
                    {"item": "kapris", "amount": "2", "unit": "rkl", "notes": ""},
                    {"item": "tilli", "amount": "2", "unit": "rkl", "notes": "tuoretta"},
                    {"item": "suola", "amount": "", "unit": "", "notes": "maun mukaan"},
                    {"item": "pippuri", "amount": "", "unit": "", "notes": "maun mukaan"}
                ],
                "instructions": [
                    "Kuori ja viipaloi perunat ohuiksi.",
                    "Viipaloi sipuli.",
                    "Voitele uunivuoka.",
                    "Asettele keroksittain perunat, sipuli ja lohikuutiot.",
                    "Kaada kerma päälle.",
                    "Ripottele kaprikset ja tilli.",
                    "Peitä foliolla ja paista 200°C 30 min.",
                    "Poista folio, lisää juusto ja paista 15 min lisää.",
                    "Anna vetäytyä 10 min ennen tarjoilua."
                ],
                "tags": ["uuniruoka", "lohi", "perinteinen", "juhla-ateria"],
                "nutrition_notes": "Omega-3 rasvahappoja lohesta, C-vitamiinia perunoista"
            }
        ]
        
        # Try to pick a relevant recipe based on prompt keywords
        prompt_lower = user_prompt.lower()
        
        if any(word in prompt_lower for word in ['kana', 'chicken', 'pasta']):
            chosen_recipe = demo_recipes[0]  # Kanapastavuoka
        elif any(word in prompt_lower for word in ['herne', 'soup', 'keitto', 'lämmitä']):
            chosen_recipe = demo_recipes[1]  # Hernekeitto
        elif any(word in prompt_lower for word in ['lohi', 'salmon', 'fish', 'kala', 'juhla']):
            chosen_recipe = demo_recipes[2]  # Lohikiusaus
        else:
            # Random selection
            chosen_recipe = random.choice(demo_recipes)
        
        # Apply dietary restrictions if any
        if dietary_restrictions:
            chosen_recipe = self._apply_dietary_restrictions(chosen_recipe, dietary_restrictions)
        
        # Add a note that this is a demo recipe
        chosen_recipe["demo_mode"] = True
        chosen_recipe["ai_note"] = f"Tämä on esimerkkiresepti (AI ei käytettävissä). Alkuperäinen pyyntö: '{user_prompt}'"
        
        logger.info(f"Generated fallback recipe: {chosen_recipe['name']}")
        return chosen_recipe
    
    def _apply_dietary_restrictions(self, recipe: Dict[str, Any], restrictions: List[str]) -> Dict[str, Any]:
        """Apply dietary restrictions to a recipe."""
        # This is a simple implementation - in practice, you'd want more sophisticated logic
        
        if "kasvis" in restrictions or "vegetarian" in restrictions:
            # Remove meat ingredients and suggest alternatives
            recipe["ingredients"] = [
                ing for ing in recipe["ingredients"] 
                if not any(meat in ing["item"].lower() for meat in ['kana', 'sian', 'nauta', 'liha'])
            ]
            recipe["name"] = f"Kasvis-{recipe['name']}"
            recipe["ai_note"] += " (mukautettu kasvisruokavalioon)"
        
        return recipe
    
    def _build_system_prompt(self, dietary_restrictions: Optional[List[str]] = None) -> str:
        """Build the system prompt for recipe generation."""
        
        restrictions_text = ""
        if dietary_restrictions:
            restrictions_text = f"\nRuokavaliorajoitukset: {', '.join(dietary_restrictions)}"
        
        return f"""
Olet kokenut keittiömestari ja reseptisuunnittelija. Tehtäväsi on luoda herkullisia, käytännöllisiä reseptejä suomalaisten ruokakauppojen ainesosilla.

OHJE:
1. Luo resepti käyttäjän pyynnön perusteella
2. Käytä ainesosia, joita löytyy todennäköisesti suomalaisista ruokakaupoista
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
        
        # If in fallback mode or model not available, add simple tips
        if self.fallback_mode or self.model is None:
            return self._add_fallback_tips(recipe_data)
        
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
            logger.warning(f"Failed to enhance recipe with AI, using fallback tips: {e}")
            return self._add_fallback_tips(recipe_data)
    
    def _add_fallback_tips(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add basic cooking tips when AI is not available."""
        
        recipe_data.update({
            "cooking_tips": [
                "Lue resepti kokonaan läpi ennen aloittamista",
                "Mittaa ainekset valmiiksi ennen valmistuksen aloittamista",
                "Maista ruokaa valmistuksen aikana ja säädä mausteita tarpeen mukaan"
            ],
            "ingredient_substitutions": {
                "ruokakerma": "kasvikerma tai maito + voi",
                "tuore basilika": "kuivattu basilika (puolet määrästä)"
            },
            "storage_instructions": "Säilytä jääkaapissa 2-3 päivää. Lämmitä varovasti uudelleen.",
            "serving_suggestions": [
                "Tarjoile tuoreen leivän kanssa",
                "Koristele tuoreilla yrteillä"
            ]
        })
        
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
