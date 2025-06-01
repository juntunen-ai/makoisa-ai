"""Main recipe generator orchestrating AI and ingredient matching."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from .vertex_ai_client import VertexAIClient
from .ingredient_matcher import IngredientMatcher
from .config import RecipeAIConfig

logger = logging.getLogger(__name__)


class RecipeGenerator:
    """Main class for generating recipes with ingredient pricing."""
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize recipe generator."""
        self.project_id = project_id or RecipeAIConfig.get_project_id()
        self.ai_client = VertexAIClient(project_id=self.project_id)
        self.ingredient_matcher = IngredientMatcher(project_id=self.project_id)
        
        logger.info("Initialized RecipeGenerator with AI and ingredient matching capabilities")
    
    def generate_complete_recipe(
        self, 
        user_prompt: str, 
        dietary_restrictions: Optional[List[str]] = None,
        enhance_with_tips: bool = True,
        find_ingredients: bool = True
    ) -> Dict[str, Any]:
        """Generate a complete recipe with AI and find ingredient prices."""
        
        logger.info(f"Generating recipe for prompt: '{user_prompt[:50]}...'")
        
        try:
            # Step 1: Generate recipe with AI
            recipe_data = self.ai_client.generate_recipe(user_prompt, dietary_restrictions)
            
            # Step 2: Enhance with tips if requested
            if enhance_with_tips:
                recipe_data = self.ai_client.enhance_recipe_with_tips(recipe_data)
            
            # Step 3: Find ingredient prices if requested
            if find_ingredients:
                ingredient_data = self.ingredient_matcher.find_all_ingredients(recipe_data)
                recipe_data['ingredient_pricing'] = ingredient_data
            
            # Step 4: Add metadata
            recipe_data['generated_at'] = datetime.now().isoformat()
            recipe_data['user_prompt'] = user_prompt
            recipe_data['dietary_restrictions'] = dietary_restrictions or []
            recipe_data['generator_version'] = "1.0.0"
            
            logger.info(f"Successfully generated complete recipe: {recipe_data['name']}")
            return recipe_data
            
        except Exception as e:
            logger.error(f"Error generating complete recipe: {e}")
            raise
    
    def quick_recipe(self, user_prompt: str) -> Dict[str, Any]:
        """Generate a quick recipe without ingredient pricing (faster)."""
        return self.generate_complete_recipe(
            user_prompt=user_prompt,
            enhance_with_tips=False,
            find_ingredients=False
        )
    
    def recipe_with_pricing(self, user_prompt: str, dietary_restrictions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate recipe with full ingredient pricing analysis."""
        return self.generate_complete_recipe(
            user_prompt=user_prompt,
            dietary_restrictions=dietary_restrictions,
            enhance_with_tips=True,
            find_ingredients=True
        )
    
    def analyze_recipe_cost(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the cost of an existing recipe."""
        if 'ingredients' not in recipe_data:
            raise ValueError("Recipe must have 'ingredients' field")
        
        ingredient_data = self.ingredient_matcher.find_all_ingredients(recipe_data)
        
        cost_analysis = {
            'recipe_name': recipe_data.get('name', 'Unknown Recipe'),
            'servings': recipe_data.get('servings', 4),
            'ingredient_analysis': ingredient_data,
            'cost_breakdown': self._create_cost_breakdown(ingredient_data),
            'analyzed_at': datetime.now().isoformat()
        }
        
        return cost_analysis
    
    def suggest_cheaper_alternatives(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest cheaper alternatives for expensive ingredients."""
        if 'ingredient_pricing' not in recipe_data:
            # Analyze costs first
            ingredient_data = self.ingredient_matcher.find_all_ingredients(recipe_data)
        else:
            ingredient_data = recipe_data['ingredient_pricing']
        
        alternatives = {}
        expensive_threshold = 5.0  # €5 per ingredient
        
        for ingredient_name, products in ingredient_data.items():
            if ingredient_name == '_summary' or not products:
                continue
            
            # Find expensive ingredients
            min_price = min([self._extract_price(p.get('price', '0')) for p in products])
            
            if min_price > expensive_threshold:
                # Get alternative suggestions from AI
                alternatives[ingredient_name] = self._get_ai_alternatives(ingredient_name, min_price)
        
        return {
            'recipe_name': recipe_data.get('name', 'Unknown'),
            'expensive_ingredients': alternatives,
            'savings_potential': self._calculate_savings_potential(alternatives),
            'analyzed_at': datetime.now().isoformat()
        }
    
    def create_shopping_list(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shopping list with prices and store information."""
        if 'ingredient_pricing' not in recipe_data:
            ingredient_data = self.ingredient_matcher.find_all_ingredients(recipe_data)
        else:
            ingredient_data = recipe_data['ingredient_pricing']
        
        shopping_list = []
        total_cost = 0.0
        
        for ingredient in recipe_data.get('ingredients', []):
            ingredient_name = ingredient.get('item', '')
            amount = ingredient.get('amount', '')
            unit = ingredient.get('unit', '')
            
            products = ingredient_data.get(ingredient_name, [])
            
            if products:
                # Choose the best value product (balance of price and relevance)
                best_product = self._choose_best_product(products)
                price = self._extract_price(best_product.get('price', '0'))
                total_cost += price
                
                shopping_list.append({
                    'ingredient': ingredient_name,
                    'amount': amount,
                    'unit': unit,
                    'selected_product': best_product,
                    'price': best_product.get('price', 'N/A'),
                    'store_url': best_product.get('url', ''),
                    'notes': ingredient.get('notes', '')
                })
            else:
                shopping_list.append({
                    'ingredient': ingredient_name,
                    'amount': amount,
                    'unit': unit,
                    'selected_product': None,
                    'price': 'Ei löytynyt',
                    'store_url': '',
                    'notes': f"{ingredient.get('notes', '')} - Tuotetta ei löytynyt"
                })
        
        return {
            'recipe_name': recipe_data.get('name', 'Unknown'),
            'servings': recipe_data.get('servings', 4),
            'shopping_list': shopping_list,
            'total_cost': f"{total_cost:.2f} €",
            'cost_per_serving': f"{total_cost / recipe_data.get('servings', 4):.2f} €",
            'created_at': datetime.now().isoformat()
        }
    
    def _create_cost_breakdown(self, ingredient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed cost breakdown."""
        breakdown = {
            'by_ingredient': {},
            'total_cost': 0.0,
            'most_expensive': None,
            'cheapest': None
        }
        
        ingredient_costs = []
        
        for ingredient_name, products in ingredient_data.items():
            if ingredient_name == '_summary' or not products:
                continue
            
            cheapest_product = min(products, key=lambda p: self._extract_price(p.get('price', '0')))
            cost = self._extract_price(cheapest_product.get('price', '0'))
            
            breakdown['by_ingredient'][ingredient_name] = {
                'cost': f"{cost:.2f} €",
                'product': cheapest_product.get('name', 'Unknown'),
                'options_count': len(products)
            }
            
            ingredient_costs.append((ingredient_name, cost))
            breakdown['total_cost'] += cost
        
        if ingredient_costs:
            ingredient_costs.sort(key=lambda x: x[1], reverse=True)
            breakdown['most_expensive'] = ingredient_costs[0]
            breakdown['cheapest'] = ingredient_costs[-1]
        
        breakdown['total_cost'] = f"{breakdown['total_cost']:.2f} €"
        
        return breakdown
    
    def _get_ai_alternatives(self, ingredient_name: str, current_price: float) -> Dict[str, Any]:
        """Get AI suggestions for cheaper alternatives."""
        prompt = f"""
        Ainesosa: {ingredient_name}
        Nykyinen hinta: {current_price:.2f} €
        
        Ehdota 3-5 halvempaa vaihtoehtoa tälle ainesosalle ruoanlaitossa.
        Vastaa JSON-muodossa:
        {{
            "alternatives": [
                {{"name": "vaihtoehto", "reason": "miksi se toimii", "estimated_savings": "säästö euroina"}}
            ]
        }}
        """
        
        try:
            response = self.ai_client.model.generate_content(prompt)
            # Parse JSON response
            start_idx = response.text.find('{')
            end_idx = response.text.rfind('}') + 1
            json_str = response.text[start_idx:end_idx]
            return json.loads(json_str)
        except:
            return {"alternatives": []}
    
    def _calculate_savings_potential(self, alternatives: Dict[str, Any]) -> str:
        """Calculate potential savings from alternatives."""
        # This is a simplified calculation
        return "Arvioitu säästö: 2-5 € per resepti"
    
    def _choose_best_product(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Choose the best product balancing price and relevance."""
        if not products:
            return {}
        
        # Score products (combination of price and match score)
        scored_products = []
        for product in products:
            price = self._extract_price(product.get('price', '0'))
            match_score = product.get('match_score', 0.0)
            
            # Lower price is better, higher match score is better
            # Normalize and combine (price weight 0.6, match weight 0.4)
            if price > 0:
                price_score = 1.0 / price  # Invert so lower price = higher score
                combined_score = price_score * 0.6 + match_score * 0.4
                scored_products.append((combined_score, product))
        
        if scored_products:
            # Return product with highest combined score
            return max(scored_products, key=lambda x: x[0])[1]
        else:
            return products[0]  # Fallback to first product
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numeric price from price string."""
        import re
        if not price_str:
            return 0.0
        
        clean_price = re.sub(r'[^\d,.]', '', str(price_str))
        clean_price = clean_price.replace(',', '.')
        
        try:
            return float(clean_price)
        except (ValueError, TypeError):
            return 0.0
    
    def save_recipe(self, recipe_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save recipe to JSON file."""
        if not filename:
            recipe_name = recipe_data.get('name', 'recipe').lower().replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recipe_{recipe_name}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(recipe_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved recipe to {filename}")
        return filename
