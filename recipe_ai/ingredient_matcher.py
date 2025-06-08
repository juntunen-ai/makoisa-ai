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
            "jauheliha": ["jauheliha", "nauta", "sika", "nauta-sika", "sika-nauta"],
            "kala": ["kala", "fish", "lohi", "salmon", "turska"],
            
            # Vegetables
            "sipuli": ["sipuli", "onion"],
            "valkosipuli": ["valkosipuli", "garlic"],
            "tomaatti": ["tomaatti", "tomato"],
            "peruna": ["peruna", "potato", "pottu"],
            "porkkana": ["porkkana", "carrot"],
            
            # Dairy
            "maito": ["maito", "milk"],
            "kerma": ["kerma", "cream", "ruokakerma"],
            "juusto": ["juusto", "cheese"],
            "parmesaanijuusto": ["parmesaani", "parmesan", "grana padano"],
            "mozzarella": ["mozzarella", "pizza juusto"],
            "voi": ["voi 500g", "voi 250g", "butter", "margariini"],
            "kananmuna": ["kananmuna", "muna", "egg"],
            
            # Grains and Baking
            "riisi": ["riisi 1kg", "riisi 500g", "basmati", "jasmiini riisi", "riisin"],
            "pasta": ["pasta", "makaroni", "spagetti"],
            "leipä": ["leipä", "bread"],
            "jauhot": ["jauhot", "flour", "vehnäjauho"],
            "korppujauho": ["korppujauho", "strö", "breadcrumb"],
            
            # Seasonings and Condiments
            "suola": ["suola 1kg", "keittosuola", "merisuola", "salt"],
            "pippuri": ["mustapippuri", "pippuri", "pepper", "black pepper"],
            "mustapippuri": ["mustapippuri", "pippuri", "pepper", "black pepper"],
            "sokeri": ["sokeri", "sugar"],
            "öljy": ["rypsiöljy", "öljy", "oil"],
            "oliiviöljy": ["oliiviöljy", "olive oil", "extra virgin"],
            "soijakastike": ["soijakastike", "soja", "soy sauce"],
            "lihaliemikuutio": ["liemikuutio", "lihaliemi", "kasviliemi", "fond"],
            "tomaattimurska": ["tomaattimurska", "crushed tomato", "tomaattisäilyke"],
            "tomaattipyree": ["tomaattipyree", "tomato paste", "tomato puree"],
            
            # Herbs and Spices
            "persilja": ["persilja", "parsley"],
            "ruohosipuli": ["ruohosipuli", "chive"],
            "basilika": ["basilika", "basil"],
            "oregano": ["oregano"],
            "timjami": ["timjami", "thyme"]
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
        terms = []
        
        # Clean the ingredient name - remove parenthetical descriptions
        clean_name = re.sub(r'\s*\([^)]*\)', '', ingredient_name).strip()
        terms.append(clean_name)
        
        # Also add the original if different
        if clean_name != ingredient_name:
            terms.append(ingredient_name)
        
        # Extract main ingredient words (remove modifiers)
        main_words = self._extract_main_ingredient_words(clean_name)
        terms.extend(main_words)
        
        # Check mappings for each main word
        for word in main_words:
            for key, values in self.ingredient_mappings.items():
                if word.lower() in key or any(term in word.lower() for term in values):
                    terms.extend(values)
        
        # Add variations
        terms.extend(self._generate_variations(clean_name))
        
        # Remove duplicates and empty terms
        unique_terms = list(set([term.strip().lower() for term in terms if term.strip()]))
        
        # Sort by relevance (exact matches first, then shorter terms)
        def term_priority(term):
            if term == clean_name.lower():
                return 0  # Exact match highest priority
            elif len(term.split()) == 1:
                return 1  # Single words second priority
            else:
                return 2  # Multi-word terms last
        
        unique_terms.sort(key=term_priority)
        return unique_terms[:10]  # Limit to top 10 most relevant terms
    
    def _extract_main_ingredient_words(self, ingredient_name: str) -> List[str]:
        """Extract main ingredient words, removing modifiers and descriptions."""
        # Common modifiers to remove
        modifiers = [
            'tuore', 'kuivattu', 'pakastettu', 'suolattu', 'makeutettu',
            'kiinteä', 'jauhoinen', 'yleisperuna', 'tai', 'esim', 'vähälaktoosinen',
            'laktoositon', 'luomu', 'pieni', 'iso', 'kova', 'pehmeä'
        ]
        
        words = ingredient_name.lower().split()
        main_words = []
        
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            
            # Skip modifiers, percentages, and very short words
            if (clean_word not in modifiers and 
                not re.match(r'\d+%?', clean_word) and 
                len(clean_word) > 2):
                main_words.append(clean_word)
        
        return main_words
    
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
        WHERE (LOWER(name) LIKE @search_term
           OR LOWER(description) LIKE @search_term)
        AND LENGTH(name) < 200  -- Filter out overly long product names
        ORDER BY 
            CASE 
                WHEN LOWER(name) = @exact_term THEN 1
                WHEN LOWER(name) LIKE CONCAT(@exact_term, '%') THEN 2
                WHEN LOWER(name) LIKE CONCAT('%', @exact_term, '%') THEN 3
                WHEN LOWER(description) LIKE @search_term THEN 4
                ELSE 5
            END,
            SAFE_CAST(REPLACE(REGEXP_REPLACE(price, r'[^0-9,.]', ''), ',', '.') AS FLOAT64) ASC
        LIMIT 25
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("search_term", "STRING", f"%{search_term.lower()}%"),
                bigquery.ScalarQueryParameter("exact_term", "STRING", search_term.lower())
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            products = []
            for row in results:
                # Basic relevance filtering
                if self._is_relevant_product(search_term, row.name, row.description or ''):
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
    
    def _is_relevant_product(self, search_term: str, product_name: str, description: str) -> bool:
        """Filter out obviously irrelevant products."""
        search_lower = search_term.lower()
        name_lower = product_name.lower()
        desc_lower = description.lower()
        
        # Skip baby food unless specifically searching for it
        if 'piltti' in name_lower and 'baby' not in search_lower and 'vauva' not in search_lower:
            return False
        
        # Skip pet food unless specifically searching for it
        if any(term in name_lower for term in ['koira', 'kissa', 'pet']) and 'pet' not in search_lower:
            return False
        
        # For specific ingredients, apply category filters
        if search_lower in ['jauheliha', 'nauta', 'sika']:
            # Skip processed/prepared products for raw meat searches
            if any(term in name_lower for term in ['makkara', 'pihvi', 'leikkele', 'pyörykkä']):
                return False
        
        if search_lower in ['peruna', 'potato']:
            # Skip highly processed potato products for basic potato searches
            if any(term in name_lower for term in ['chips', 'fries', 'lasagne', 'salaatti']):
                return False
        
        if search_lower in ['riisi', 'rice']:
            # Skip rice snacks, rice cakes, and ready meals for basic rice searches
            if any(term in name_lower for term in ['välipala', 'keksi', 'murokeksi', 'vadelma', 'hedelmä', 'kakku', 'kebab', 'ateria']):
                return False
        
        if search_lower in ['voi', 'butter']:
            # Skip products that just contain 'vo' but aren't butter
            if any(term in name_lower for term in ['voima', 'papu', 'muro', 'kuohuviini', 'avokaado']):
                return False
            # Must actually contain butter-related terms
            if not any(term in name_lower for term in ['voi', 'butter', 'margariini']):
                return False
        
        if search_lower in ['suola', 'salt']:
            # Skip products that aren't actually salt
            if any(term in name_lower for term in ['margariini', 'pakaste', 'papu', 'peruna']):
                return False
        
        if search_lower in ['mustapippuri', 'pippuri', 'pepper']:
            # Skip products that contain pepper but aren't pepper spice
            if any(term in name_lower for term in ['peruna', 'pakaste', 'einekset', 'ateria']):
                return False
        
        if search_lower in ['oliiviöljy', 'olive oil']:
            # Skip products that contain olive oil but aren't olive oil
            if any(term in name_lower for term in ['peruna', 'pakaste', 'einekset', 'ateria']):
                return False
        
        return True
    
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
        ingredient_lower = ingredient_name.lower()
        product_lower = product_name.lower()
        
        # Extract main words from ingredient
        ingredient_words = set(self._extract_main_ingredient_words(ingredient_lower))
        product_words = set(product_lower.split())
        
        # Exact name match (highest score)
        if ingredient_lower == product_lower:
            return 1.0
        
        # Check for exact word matches
        exact_matches = ingredient_words.intersection(product_words)
        word_match_ratio = len(exact_matches) / max(len(ingredient_words), 1)
        
        # Sequence similarity
        similarity = SequenceMatcher(None, ingredient_lower, product_lower).ratio()
        
        # Substring matches (ingredient words contained in product name)
        substring_matches = 0
        for ing_word in ingredient_words:
            if any(ing_word in prod_word for prod_word in product_words):
                substring_matches += 1
        
        substring_ratio = substring_matches / max(len(ingredient_words), 1)
        
        # Combined score with weights
        # Prioritize exact word matches, then substring matches, then similarity
        score = (
            word_match_ratio * 0.5 +      # Exact word matches (50%)
            substring_ratio * 0.3 +       # Substring matches (30%)
            similarity * 0.2              # Overall similarity (20%)
        )
        
        # Boost score for category-specific matches
        score = self._apply_category_boost(ingredient_lower, product_lower, score)
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _apply_category_boost(self, ingredient: str, product: str, base_score: float) -> float:
        """Apply category-specific boosts to improve relevance."""
        # Meat products
        meat_terms = ['jauheliha', 'nauta', 'sika', 'kana', 'broileri']
        if any(term in ingredient for term in meat_terms):
            if any(term in product for term in meat_terms):
                base_score += 0.1
        
        # Dairy products
        dairy_terms = ['maito', 'kerma', 'juusto', 'voi', 'jogurtti']
        if any(term in ingredient for term in dairy_terms):
            if any(term in product for term in dairy_terms):
                base_score += 0.1
        
        # Vegetables
        veg_terms = ['sipuli', 'peruna', 'tomaatti', 'porkkana']
        if any(term in ingredient for term in veg_terms):
            if any(term in product for term in veg_terms):
                base_score += 0.1
        
        # Grains and flour
        grain_terms = ['jauhot', 'riisi', 'pasta', 'makaroni']
        if any(term in ingredient for term in grain_terms):
            if any(term in product for term in grain_terms):
                base_score += 0.1
        
        return base_score
    
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
