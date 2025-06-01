"""Streamlit web application for AI Recipe Generator."""

import streamlit as st
import json
import logging
from typing import Dict, Any, List
import sys
import os
from pathlib import Path

# Load environment variables from recipe_ai/.env file before importing modules
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Force override environment variables from .env file
                os.environ[key.strip()] = value.strip()

# Add the parent directory to the path so we can import recipe_ai
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recipe_ai.recipe_generator import RecipeGenerator
from recipe_ai.config import RecipeAIConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Reseptigeneraattori",
    page_icon="👨‍🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .recipe-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 5px solid #2e7d32;
    }
    .ingredient-item {
        background-color: #e8f5e8;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .price-tag {
        background-color: #1976d2;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    .total-cost {
        font-size: 1.2em;
        font-weight: bold;
        color: #2e7d32;
        text-align: center;
        padding: 15px;
        background-color: #e8f5e8;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


class RecipeApp:
    """Streamlit application for recipe generation."""
    
    def __init__(self):
        """Initialize the recipe application."""
        self.generator = None
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables."""
        if 'current_recipe' not in st.session_state:
            st.session_state.current_recipe = None
        if 'recipe_history' not in st.session_state:
            st.session_state.recipe_history = []
        if 'generator_initialized' not in st.session_state:
            st.session_state.generator_initialized = False
    
    def _initialize_generator(self):
        """Initialize the recipe generator with error handling."""
        if st.session_state.generator_initialized and self.generator is not None:
            return True
            
        try:
            with st.spinner("Alustetan AI-reseptigeneraattoria..."):
                self.generator = RecipeGenerator()
                st.session_state.generator_initialized = True
                st.success("AI-reseptigeneraattori valmis käyttöön! 🎉")
                return True
        except Exception as e:
            st.error(f"Virhe alustettaessa generaattoria: {e}")
            st.error("Tarkista Google Cloud -asetukset ja yritä uudelleen.")
            
            # Add retry button
            if st.button("🔄 Yritä uudelleen"):
                st.session_state.generator_initialized = False
                st.rerun()
                
            return False
    
    def run(self):
        """Run the main application."""
        st.title("🍳 AI Reseptigeneraattori")
        st.markdown("**Luo herkullisia reseptejä tekoälyn avulla ja löydä ainesosat suomalaisista ruokakaupoista!**")
        
        # Sidebar for settings and navigation
        self._render_sidebar()
        
        # Main content area
        if not self._initialize_generator():
            st.stop()
        
        # Tab navigation
        tab1, tab2, tab3, tab4 = st.tabs([
            "🆕 Luo Resepti", 
            "📋 Nykyinen Resepti", 
            "🛒 Ostoslista", 
            "📚 Historia"
        ])
        
        with tab1:
            self._render_recipe_generator()
        
        with tab2:
            self._render_current_recipe()
        
        with tab3:
            self._render_shopping_list()
        
        with tab4:
            self._render_recipe_history()
    
    def _render_sidebar(self):
        """Render the sidebar with settings."""
        st.sidebar.title("⚙️ Asetukset")
        
        # Dietary restrictions
        st.sidebar.subheader("Ruokavaliorajoitukset")
        restrictions = []
        
        if st.sidebar.checkbox("Kasvisruoka"):
            restrictions.append("kasvisruoka")
        if st.sidebar.checkbox("Vegaani"):
            restrictions.append("vegaani")
        if st.sidebar.checkbox("Gluteeniton"):
            restrictions.append("gluteeniton")
        if st.sidebar.checkbox("Laktoositon"):
            restrictions.append("laktoositon")
        if st.sidebar.checkbox("Vähäsuolainen"):
            restrictions.append("vähäsuolainen")
        
        # Custom restrictions
        custom_restriction = st.sidebar.text_input("Muut rajoitukset:")
        if custom_restriction:
            restrictions.append(custom_restriction)
        
        st.session_state.dietary_restrictions = restrictions
        
        # Recipe settings
        st.sidebar.subheader("Reseptiasetukset")
        st.session_state.include_tips = st.sidebar.checkbox("Sisällytä vinkkit", value=True)
        st.session_state.find_prices = st.sidebar.checkbox("Etsi hintatiedot", value=True)
        
        # About section
        st.sidebar.subheader("ℹ️ Tietoa")
        st.sidebar.markdown("""
        Tämä sovellus käyttää:
        - **Vertex AI** reseptien luomiseen
        - **BigQuery** hintatietojen hakuun
        - **Tuotetietokantaa** ainesosien löytämiseen
        
        Kehittäjä: Harri Juntunen
        """)
    
    def _render_recipe_generator(self):
        """Render the recipe generation interface."""
        st.header("Luo uusi resepti")
        
        # Recipe prompt input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_prompt = st.text_area(
                "Kerro mitä haluat syödä:",
                placeholder="Esim: 'Haluan tehdä broileria tänään' tai 'Jotain helppoa ja terveellistä'",
                height=100
            )
        
        with col2:
            st.markdown("**💡 Vinkkejä:**")
            st.markdown("""
            - Mainitse ruoka-aine
            - Kerro vaikeustaso
            - Ehdota ruokailuaika
            - Kerro erityistoiveet
            """)
        
        # Generation options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            quick_mode = st.checkbox("Pikamodi (ei hintatietoja)", value=False)
        
        with col2:
            servings = st.number_input("Annoksia:", min_value=1, max_value=12, value=4)
        
        with col3:
            if st.button("🎲 Satunnainen resepti"):
                user_prompt = self._get_random_prompt()
                st.rerun()
        
        # Generate button
        if st.button("🚀 Luo resepti", type="primary", disabled=not user_prompt.strip()):
            self._generate_recipe(user_prompt, quick_mode, servings)
    
    def _generate_recipe(self, user_prompt: str, quick_mode: bool, servings: int):
        """Generate a recipe based on user input."""
        # Check if generator is properly initialized
        if self.generator is None:
            st.error("AI-reseptigeneraattori ei ole käytettävissä. Tarkista asetukset ja lataa sivu uudelleen.")
            return
            
        try:
            with st.spinner("Luon reseptiä... ⏳"):
                
                # Add servings to prompt if specified
                enhanced_prompt = f"{user_prompt}. Tee resepti {servings} hengelle."
                
                if quick_mode:
                    recipe_data = self.generator.quick_recipe(enhanced_prompt)
                else:
                    recipe_data = self.generator.recipe_with_pricing(
                        enhanced_prompt, 
                        st.session_state.get('dietary_restrictions', [])
                    )
                
                # Update servings in recipe data
                recipe_data['servings'] = servings
                
                # Store in session state
                st.session_state.current_recipe = recipe_data
                st.session_state.recipe_history.append(recipe_data)
                
                st.success(f"✅ Resepti '{recipe_data['name']}' luotu onnistuneesti!")
                st.balloons()
                
        except Exception as e:
            st.error(f"Virhe luotaessa reseptiä: {e}")
            logger.error(f"Recipe generation error: {e}")
    
    def _render_current_recipe(self):
        """Render the current recipe."""
        if not st.session_state.current_recipe:
            st.info("👨‍🍳 Ei aktiivista reseptiä. Luo uusi resepti ensimmäisessä välilehdessä!")
            return
        
        recipe = st.session_state.current_recipe
        
        # Recipe header
        st.markdown(f"""
        <div class="recipe-card">
            <h1>{recipe['name']}</h1>
            <p><strong>Kuvaus:</strong> {recipe.get('description', 'Ei kuvausta')}</p>
            <div style="display: flex; gap: 20px; margin: 10px 0;">
                <span>👥 <strong>{recipe.get('servings', 4)} annosta</strong></span>
                <span>⏱️ <strong>{recipe.get('total_time_minutes', 'N/A')} min</strong></span>
                <span>📊 <strong>{recipe.get('difficulty', 'Keskivaikea')}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tabs for recipe details
        tab1, tab2, tab3 = st.tabs(["📝 Ainesosat", "👩‍🍳 Ohjeet", "💰 Hintatiedot"])
        
        with tab1:
            self._render_ingredients(recipe)
        
        with tab2:
            self._render_instructions(recipe)
        
        with tab3:
            self._render_pricing_info(recipe)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Tallenna resepti"):
                self._save_recipe(recipe)
        
        with col2:
            if st.button("🛒 Luo ostoslista"):
                self._create_shopping_list(recipe)
        
        with col3:
            if st.button("💡 Ehdota vaihtoehtoja"):
                self._suggest_alternatives(recipe)
        
        with col4:
            if st.button("📋 Kopioi resepti"):
                self._copy_recipe_to_clipboard(recipe)
    
    def _render_ingredients(self, recipe: Dict[str, Any]):
        """Render ingredients section."""
        ingredients = recipe.get('ingredients', [])
        
        if not ingredients:
            st.warning("Ei ainesosia saatavilla.")
            return
        
        st.subheader("🥘 Ainesosat")
        
        for i, ingredient in enumerate(ingredients):
            amount = ingredient.get('amount', '')
            unit = ingredient.get('unit', '')
            item = ingredient.get('item', '')
            notes = ingredient.get('notes', '')
            
            ingredient_text = f"**{amount} {unit} {item}**"
            if notes:
                ingredient_text += f" _{notes}_"
            
            st.markdown(f"""
            <div class="ingredient-item">
                {ingredient_text}
            </div>
            """, unsafe_allow_html=True)
    
    def _render_instructions(self, recipe: Dict[str, Any]):
        """Render cooking instructions."""
        instructions = recipe.get('instructions', [])
        
        if not instructions:
            st.warning("Ei ohjeita saatavilla.")
            return
        
        st.subheader("👩‍🍳 Valmistusohje")
        
        for i, instruction in enumerate(instructions, 1):
            st.markdown(f"**{i}.** {instruction}")
        
        # Additional tips if available
        if 'cooking_tips' in recipe:
            st.subheader("💡 Vinkkejä")
            for tip in recipe['cooking_tips']:
                st.markdown(f"• {tip}")
    
    def _render_pricing_info(self, recipe: Dict[str, Any]):
        """Render pricing information."""
        if 'ingredient_pricing' not in recipe:
            st.info("💰 Hintatietoja ei ole saatavilla. Valitse 'Etsi hintatiedot' luodessasi reseptiä.")
            return
        
        pricing = recipe['ingredient_pricing']
        summary = pricing.get('_summary', {})
        
        # Summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Löydetyt ainesosat", f"{summary.get('found_ingredients', 0)}/{summary.get('total_ingredients', 0)}")
        
        with col2:
            st.metric("Kokonaishinta", summary.get('estimated_total_price', 'N/A'))
        
        with col3:
            st.metric("Hinta/annos", summary.get('average_price_per_serving', 'N/A'))
        
        # Detailed pricing
        st.subheader("📊 Yksityiskohtaiset hintatiedot")
        
        for ingredient_name, products in pricing.items():
            if ingredient_name == '_summary' or not products:
                continue
            
            with st.expander(f"🛍️ {ingredient_name} ({len(products)} vaihtoehtoa)"):
                for product in products[:3]:  # Show top 3 options
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{product['name'][:60]}...**" if len(product['name']) > 60 else f"**{product['name']}**")
                        if product.get('description'):
                            st.caption(product['description'][:100] + "..." if len(product['description']) > 100 else product['description'])
                    
                    with col2:
                        st.markdown(f"<div class='price-tag'>{product['price']}</div>", unsafe_allow_html=True)
                    
                    with col3:
                        if product.get('url'):
                            st.markdown(f"[Katso tuote]({product['url']})")
    
    def _render_shopping_list(self):
        """Render shopping list."""
        if not st.session_state.current_recipe:
            st.info("🛒 Valitse ensin resepti ostoslistan luomiseksi.")
            return
            
        if self.generator is None:
            st.error("AI-reseptigeneraattori ei ole käytettävissä.")
            return
        
        st.header("🛒 Ostoslista")
        
        try:
            with st.spinner("Luon ostoslistaa..."):
                shopping_list = self.generator.create_shopping_list(st.session_state.current_recipe)
            
            # Shopping list header
            recipe_name = shopping_list.get('recipe_name', 'Unknown')
            total_cost = shopping_list.get('total_cost', 'N/A')
            
            st.markdown(f"""
            <div class="total-cost">
                <h3>📋 {recipe_name}</h3>
                <p>Kokonaishinta: {total_cost}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Shopping items
            for item in shopping_list.get('shopping_list', []):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{item['ingredient']}**")
                    st.caption(f"{item['amount']} {item['unit']}")
                
                with col2:
                    if item['selected_product']:
                        st.markdown(item['selected_product']['name'][:30] + "..." if len(item['selected_product']['name']) > 30 else item['selected_product']['name'])
                    else:
                        st.markdown("_Ei löytynyt_")
                
                with col3:
                    st.markdown(f"**{item['price']}**")
                
                with col4:
                    if item.get('store_url'):
                        st.markdown(f"[Osta]({item['store_url']})")
            
            # Download options
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Lataa JSON"):
                    self._download_shopping_list(shopping_list, 'json')
            
            with col2:
                if st.button("📄 Lataa tekstitiedosto"):
                    self._download_shopping_list(shopping_list, 'txt')
                    
        except Exception as e:
            st.error(f"Virhe luotaessa ostoslistaa: {e}")
    
    def _render_recipe_history(self):
        """Render recipe history."""
        st.header("📚 Reseptihistoria")
        
        if not st.session_state.recipe_history:
            st.info("📝 Ei tallennettuja reseptejä.")
            return
        
        for i, recipe in enumerate(reversed(st.session_state.recipe_history)):
            with st.expander(f"🍽️ {recipe['name']} - {recipe.get('generated_at', 'Unknown time')[:10]}"):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**Kuvaus:** {recipe.get('description', 'Ei kuvausta')}")
                    st.markdown(f"**Annoksia:** {recipe.get('servings', 4)}")
                    st.markdown(f"**Vaikeustaso:** {recipe.get('difficulty', 'Keskivaikea')}")
                
                with col2:
                    if 'ingredient_pricing' in recipe:
                        summary = recipe['ingredient_pricing'].get('_summary', {})
                        st.markdown(f"**Hinta:** {summary.get('estimated_total_price', 'N/A')}")
                
                with col3:
                    if st.button(f"🔄 Lataa resepti", key=f"load_{i}"):
                        st.session_state.current_recipe = recipe
                        st.success("Resepti ladattu!")
                        st.rerun()
    
    def _get_random_prompt(self) -> str:
        """Get a random recipe prompt."""
        prompts = [
            "Tee jotain nopeaa ja helppoa arkiaterialle",
            "Haluan terveellistä salaattia lounaaksi",
            "Tee jotain makeaa jälkiruoaksi",
            "Haluan tehdä jotain erikoista broilerista",
            "Tee kasvisruokaa illalliseksi",
            "Jotain lämmintä ja mukavaa talvi-iltaan",
            "Haluan kokeilla jotain uutta kalasta",
            "Tee helppo pasta-annos",
            "Jotain gluteenitonta",
            "Haluan tehdä jotain grillaukseen"
        ]
        import random
        return random.choice(prompts)
    
    def _save_recipe(self, recipe: Dict[str, Any]):
        """Save recipe to file."""
        if self.generator is None:
            st.error("AI-reseptigeneraattori ei ole käytettävissä.")
            return
            
        try:
            filename = self.generator.save_recipe(recipe)
            st.success(f"✅ Resepti tallennettu tiedostoon: {filename}")
        except Exception as e:
            st.error(f"Virhe tallentaessa reseptiä: {e}")
    
    def _create_shopping_list(self, recipe: Dict[str, Any]):
        """Create and switch to shopping list tab."""
        st.info("🛒 Siirry 'Ostoslista'-välilehteen nähdäksesi ostoslistan!")
    
    def _suggest_alternatives(self, recipe: Dict[str, Any]):
        """Suggest cheaper alternatives."""
        if self.generator is None:
            st.error("AI-reseptigeneraattori ei ole käytettävissä.")
            return
            
        try:
            with st.spinner("Etsin halvempia vaihtoehtoja..."):
                alternatives = self.generator.suggest_cheaper_alternatives(recipe)
            
            if alternatives.get('expensive_ingredients'):
                st.subheader("💡 Halvemmat vaihtoehdot")
                for ingredient, suggestion in alternatives['expensive_ingredients'].items():
                    st.markdown(f"**{ingredient}:** {suggestion}")
            else:
                st.info("✅ Resepti on jo budjettitietoisesti suunniteltu!")
                
        except Exception as e:
            st.error(f"Virhe etsittäessä vaihtoehtoja: {e}")
    
    def _copy_recipe_to_clipboard(self, recipe: Dict[str, Any]):
        """Copy recipe text to clipboard."""
        recipe_text = self._format_recipe_as_text(recipe)
        st.code(recipe_text, language='text')
        st.info("📋 Kopioi yllä oleva teksti leikepöydälle!")
    
    def _format_recipe_as_text(self, recipe: Dict[str, Any]) -> str:
        """Format recipe as plain text."""
        text = f"""
{recipe['name']}
{'='*len(recipe['name'])}

Kuvaus: {recipe.get('description', '')}
Annoksia: {recipe.get('servings', 4)}
Aika: {recipe.get('total_time_minutes', 'N/A')} min
Vaikeustaso: {recipe.get('difficulty', 'Keskivaikea')}

AINESOSAT:
"""
        for ingredient in recipe.get('ingredients', []):
            text += f"- {ingredient.get('amount', '')} {ingredient.get('unit', '')} {ingredient.get('item', '')}\n"
        
        text += "\nVALMISTUSOHJE:\n"
        for i, instruction in enumerate(recipe.get('instructions', []), 1):
            text += f"{i}. {instruction}\n"
        
        return text
    
    def _download_shopping_list(self, shopping_list: Dict[str, Any], format_type: str):
        """Download shopping list in specified format."""
        if format_type == 'json':
            st.download_button(
                label="📥 Lataa JSON",
                data=json.dumps(shopping_list, indent=2, ensure_ascii=False),
                file_name=f"ostoslista_{shopping_list.get('recipe_name', 'resepti')}.json",
                mime="application/json"
            )
        elif format_type == 'txt':
            text_content = self._format_shopping_list_as_text(shopping_list)
            st.download_button(
                label="📄 Lataa teksti",
                data=text_content,
                file_name=f"ostoslista_{shopping_list.get('recipe_name', 'resepti')}.txt",
                mime="text/plain"
            )
    
    def _format_shopping_list_as_text(self, shopping_list: Dict[str, Any]) -> str:
        """Format shopping list as plain text."""
        text = f"""
OSTOSLISTA - {shopping_list.get('recipe_name', 'Resepti')}
{'='*50}

Annoksia: {shopping_list.get('servings', 4)}
Kokonaishinta: {shopping_list.get('total_cost', 'N/A')}
Hinta per annos: {shopping_list.get('cost_per_serving', 'N/A')}

TUOTTEET:
"""
        for item in shopping_list.get('shopping_list', []):
            text += f"☐ {item['ingredient']} - {item['amount']} {item['unit']}\n"
            if item['selected_product']:
                text += f"   → {item['selected_product']['name']} - {item['price']}\n"
            if item.get('store_url'):
                text += f"   🔗 {item['store_url']}\n"
            text += "\n"
        
        return text


def main():
    """Main application entry point."""
    app = RecipeApp()
    app.run()


if __name__ == "__main__":
    main()
