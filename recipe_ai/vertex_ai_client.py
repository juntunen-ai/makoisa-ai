"""
Vertex AI Client for Recipe Generation
Now with Local LLM fallback support
"""

class VertexAIClient:
    """Vertex AI client with local LLM fallback for recipe generation"""
    
    def __init__(self):
        self.initialized = False
        self._local_client = None
    
    def _get_local_client(self):
        """Get local LLM client as fallback"""
        if self._local_client is None:
            try:
                # Import here to avoid circular imports
                import sys
                from pathlib import Path
                project_root = Path(__file__).parent.parent
                sys.path.insert(0, str(project_root))
                
                from local_llm_client import LocalLLMClient
                self._local_client = LocalLLMClient()
                print("🤖 Using local LLM for recipe generation")
            except ImportError:
                print("⚠️ Local LLM not available")
                self._local_client = False
        return self._local_client
    
    def generate_recipe(self, ingredients, preferences=None):
        """Generate a recipe based on ingredients and preferences"""
        
        # Try local LLM first
        local_client = self._get_local_client()
        if local_client and hasattr(local_client, 'generate_recipe'):
            try:
                preferences_str = preferences or "healthy and delicious"
                return self._format_local_response(
                    local_client.generate_recipe(ingredients, preferences_str)
                )
            except Exception as e:
                print(f"Local LLM error: {e}")
        
        # Fallback to placeholder
        return {
            "title": "Sample Recipe",
            "ingredients": ingredients,
            "instructions": [
                "This is a placeholder recipe generator.",
                "Local LLM integration is available!",
                f"Using ingredients: {', '.join(ingredients)}",
                f"Preferences: {preferences or 'None specified'}"
            ],
            "prep_time": "30 minutes",
            "cooking_time": "45 minutes"
        }
    
    def _format_local_response(self, response: str) -> dict:
        """Format local LLM response to match expected structure"""
        lines = response.split('\n')
        
        # Extract title
        title = "AI Generated Recipe"
        for line in lines:
            if "recipe name" in line.lower() or line.startswith('**') and 'recipe' in line.lower():
                title = line.replace('*', '').replace('Recipe Name:', '').strip()
                break
        
        # Extract times
        prep_time = "30 minutes"
        cooking_time = "30 minutes"
        for line in lines:
            if "prep time" in line.lower():
                prep_time = line.split(':')[-1].strip() if ':' in line else prep_time
            elif "cooking time" in line.lower() or "cook time" in line.lower():
                cooking_time = line.split(':')[-1].strip() if ':' in line else cooking_time
        
        # Extract instructions (everything after ingredients list)
        instructions = []
        in_instructions = False
        for line in lines:
            line = line.strip()
            if line and (
                "instructions" in line.lower() or 
                "steps" in line.lower() or
                "method" in line.lower() or
                line.startswith(('1.', '2.', '3.'))
            ):
                in_instructions = True
                if not line.lower().startswith(('instructions', 'steps', 'method')):
                    instructions.append(line)
            elif in_instructions and line:
                if line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '-', '*')):
                    instructions.append(line)
                elif line and not line.startswith('**'):
                    instructions.append(line)
        
        # If no numbered instructions found, use the full response
        if not instructions:
            instructions = [response]
        
        return {
            "title": title,
            "ingredients": [],  # Local LLM handles this in the response
            "instructions": instructions,
            "prep_time": prep_time,
            "cooking_time": cooking_time,
            "generated_by": "Local LLM"
        }