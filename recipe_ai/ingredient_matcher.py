"""Ingredient matcher for finding products in BigQuery data."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
import re
from google.cloud import bigquery
from .config import RecipeAIConfig

logger = logging.getLogger(__name__)


class IngredientMatcher:
    """Matches recipe ingredients to products in BigQuery."""
    
    def __init__(self, project_id: Optional[str] = None):
        """Initialize ingredient matcher."""
        self.project_id = project_id or RecipeAIConfig.get_project_id()
        self.client = bigquery.Client(project=self.project_id)
        self.table_id = RecipeAIConfig.get_bigquery_table()
        
        # Common ingredient mappings for better matching
        self.ingredient_mappings = {
            # Meats
            "kana": ["kana", "broileri", "chicken"],
            "nauta": ["nauta", "beef", "härkä"],
            "sika": ["sika", "pork", "possu"],
            "kala": ["kala", "fish", "lohi", "salmon", "turska"],
            
            # Vegetables
            "sipuli": ["sipuli", "onion"],
            "valkosipuli": ["valkosipuli", "garlic"],
            "tomaatti": ["tomaatti", "tomato"],
            "peruna": ["peruna", "potato", "pottu"],
            "porkkana": ["porkkana", "carrot"],
            
            # Dairy
            "maito": ["maito", "milk"],
            "kerma": ["kerma", "cream"],
            "juusto": ["juusto", "cheese"],
            "voi": ["voi", "butter"],
            
            # Grains
            "riisi": ["riisi", "rice"],
            "pasta": ["pasta", "makaroni", "spagetti"],
            "leipä": ["leipä", "bread"],
            "jauhot": ["jauhot", "flour"],
            
            # Common seasonings
            "suola": ["suola", "salt"],
            "pippuri": ["pippuri", "pepper"],
            "sokeri": ["sokeri", "sugar"],
            "öljy": ["öljy", "oil", "rypsiöljy", "oliiviöljy"]
        }
        
        logger.info(f"Initialized IngredientMatcher for project: {self.project_id}")
    
    def find_ingredient_products(self, ingredient: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find products matching an ingredient."""
        ingredient_name = ingredient.get('item', '').lower()
        amount = ingredient.get('amount', '')
        unit = ingredient.get('unit', '')
        
        logger.info(f"Searching for ingredient: {ingredient_name}")
        
        # Get search terms for this ingredient
        search_terms = self._get_search_terms(ingredient_name)
        
        # Search BigQuery for matching products
        products = []
        for term in search_terms:
            matching_products = self._search_products(term)
            products.extend(matching_products)
        
        # Remove duplicates and sort by relevance
        unique_products = self._deduplicate_and_rank(products, ingredient_name)
        
        # Add ingredient info to results
        for product in unique_products:
            product['requested_amount'] = amount
            product['requested_unit'] = unit
            product['match_score'] = self._calculate_match_score(ingredient_name, product['name'])
        
        return unique_products[:RecipeAIConfig.MAX_PRICE_RESULTS]
    
    def find_all_ingredients(self, recipe_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Find products for all ingredients in a recipe."""
        ingredients = recipe_data.get('ingredients', [])
        results = {}
        total_price = 0.0
        
        logger.info(f"Searching for {len(ingredients)} ingredients")
        
        for ingredient in ingredients:
            ingredient_name = ingredient.get('item', '')
            products = self.find_ingredient_products(ingredient)
            results[ingredient_name] = products
            
            # Calculate estimated price (use cheapest option)
            if products:
                cheapest = min(products, key=lambda p: self._extract_price(p.get('price', '0')))
                price = self._extract_price(cheapest.get('price', '0'))
                total_price += price
                logger.info(f"Found {len(products)} products for {ingredient_name}, cheapest: {cheapest.get('price', 'N/A')}")
            else:
                logger.warning(f"No products found for ingredient: {ingredient_name}")
        
        # Add summary information
        results['_summary'] = {
            'total_ingredients': len(ingredients),
            'found_ingredients': len([k for k, v in results.items() if k != '_summary' and v]),
            'estimated_total_price': f"{total_price:.2f} €",
            'average_price_per_serving': f"{total_price / recipe_data.get('servings', 4):.2f} €"
        }
        
        return results
    
    def _get_search_terms(self, ingredient_name: str) -> List[str]:
        """Get search terms for an ingredient."""
        terms = [ingredient_name]
        
        # Check mappings
        for key, values in self.ingredient_mappings.items():
            if any(term in ingredient_name for term in values):
                terms.extend(values)
        
        # Add variations
        terms.extend(self._generate_variations(ingredient_name))
        
        # Remove duplicates and empty terms
        return list(set([term.strip() for term in terms if term.strip()]))
    
    def _generate_variations(self, ingredient_name: str) -> List[str]:
        """Generate variations of ingredient name."""
        variations = []
        
        # Remove common modifiers
        clean_name = re.sub(r'\b(tuore|pakastettu|kuivattu|suolattu|makeutettu)\b', '', ingredient_name).strip()
        if clean_name != ingredient_name:
            variations.append(clean_name)
        
        # Singular/plural variations
        if ingredient_name.endswith('t'):
            variations.append(ingredient_name[:-1])  # Remove 't' for singular
        elif ingredient_name.endswith('a') or ingredient_name.endswith('ä'):
            variations.append(ingredient_name + 't')  # Add 't' for plural
        
        # Common brand variations
        if 'juusto' in ingredient_name:
            variations.extend(['cheddar', 'gouda', 'edam'])
        
        return variations
    
    def _search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """Search products in BigQuery."""
        query = f"""
        SELECT 
            name,
            price,
            description,
            url,
            scraped_at
        FROM `{self.table_id}`
        WHERE LOWER(name) LIKE @search_term
           OR LOWER(description) LIKE @search_term
        ORDER BY 
            CASE 
                WHEN LOWER(name) LIKE @exact_term THEN 1
                WHEN LOWER(name) LIKE @search_term THEN 2
                ELSE 3
            END,
            price
        LIMIT 20
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("search_term", "STRING", f"%{search_term.lower()}%"),
                bigquery.ScalarQueryParameter("exact_term", "STRING", f"%{search_term.lower()}%")
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            products = []
            for row in results:
                products.append({
                    'name': row.name,
                    'price': row.price,
                    'description': row.description or '',
                    'url': row.url,
                    'scraped_at': row.scraped_at.isoformat() if row.scraped_at else None,
                    'search_term': search_term
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching products for term '{search_term}': {e}")
            return []
    
    def _deduplicate_and_rank(self, products: List[Dict[str, Any]], ingredient_name: str) -> List[Dict[str, Any]]:
        """Remove duplicates and rank products by relevance."""
        seen_urls = set()
        unique_products = []
        
        for product in products:
            url = product.get('url')
            if url not in seen_urls:
                seen_urls.add(url)
                unique_products.append(product)
        
        # Sort by match score
        unique_products.sort(
            key=lambda p: self._calculate_match_score(ingredient_name, p['name']),
            reverse=True
        )
        
        return unique_products
    
    def _calculate_match_score(self, ingredient_name: str, product_name: str) -> float:
        """Calculate match score between ingredient and product name."""
        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, ingredient_name.lower(), product_name.lower()).ratio()
        
        # Boost score for exact word matches
        ingredient_words = set(ingredient_name.lower().split())
        product_words = set(product_name.lower().split())
        word_overlap = len(ingredient_words.intersection(product_words))
        
        # Combine similarity and word overlap
        score = similarity * 0.7 + (word_overlap / max(len(ingredient_words), 1)) * 0.3
        
        return score
    
    def _extract_price(self, price_str: str) -> float:
        """Extract numeric price from price string."""
        if not price_str:
            return 0.0
        
        # Remove currency symbols and extract number
        clean_price = re.sub(r'[^\d,.]', '', str(price_str))
        clean_price = clean_price.replace(',', '.')
        
        try:
            return float(clean_price)
        except (ValueError, TypeError):
            return 0.0
    
    def get_price_comparison(self, ingredient_name: str) -> Dict[str, Any]:
        """Get price comparison for a specific ingredient."""
        search_terms = self._get_search_terms(ingredient_name)
        all_products = []
        
        for term in search_terms:
            products = self._search_products(term)
            all_products.extend(products)
        
        unique_products = self._deduplicate_and_rank(all_products, ingredient_name)
        
        if not unique_products:
            return {'ingredient': ingredient_name, 'products': [], 'price_range': 'No products found'}
        
        prices = [self._extract_price(p['price']) for p in unique_products]
        prices = [p for p in prices if p > 0]
        
        price_analysis = {
            'ingredient': ingredient_name,
            'products': unique_products,
            'price_range': {
                'min': f"{min(prices):.2f} €" if prices else "N/A",
                'max': f"{max(prices):.2f} €" if prices else "N/A",
                'average': f"{sum(prices) / len(prices):.2f} €" if prices else "N/A",
                'count': len(prices)
            }
        }
        
        return price_analysis
