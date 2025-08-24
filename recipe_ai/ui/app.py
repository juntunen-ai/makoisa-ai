"""
Recipe AI Streamlit Application

Main interface for the AI-powered recipe generator with optional commercial features.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Core imports (always available)
from recipe_ai.vertex_ai_client import VertexAIClient
from recipe_ai.ingredient_matcher import IngredientMatcher

# Optional commercial module import
try:
    from commercial.google_ads import (
        render_sidebar_ad, 
        render_main_ad, 
        inject_adsense_script,
        is_ads_enabled
    )
    COMMERCIAL_FEATURES = True
except ImportError:
    COMMERCIAL_FEATURES = False

# Page configuration
st.set_page_config(
    page_title="AI Recipe Generator",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject AdSense script if commercial features are available
if COMMERCIAL_FEATURES:
    inject_adsense_script()

def main():
    """Main application function."""
    
    # Header
    st.title("🍳 AI Recipe Generator")
    st.markdown("Generate delicious recipes with local Finnish grocery pricing!")
    
    # Show commercial features status (only in development)
    if st.sidebar.checkbox("Debug Info", value=False):
        st.sidebar.markdown("---")
        st.sidebar.markdown("**System Status**")
        st.sidebar.write(f"Commercial Features: {'✅ Enabled' if COMMERCIAL_FEATURES else '❌ Disabled'}")
        if COMMERCIAL_FEATURES:
            st.sidebar.write(f"Ads Enabled: {'✅ Yes' if is_ads_enabled() else '❌ No'}")
    
    # Sidebar with optional ads
    st.sidebar.markdown("## Recipe Options")
    
    # Ingredient input
    ingredients = st.sidebar.text_area(
        "Enter ingredients (one per line):",
        value="chicken breast\nrice\nvegetables\ngarlic",
        height=100
    )
    
    # Recipe preferences
    cuisine_type = st.sidebar.selectbox(
        "Cuisine Type:",
        ["Any", "Finnish", "Italian", "Asian", "Mediterranean", "Mexican"]
    )
    
    difficulty = st.sidebar.selectbox(
        "Difficulty Level:",
        ["Any", "Easy", "Medium", "Hard"]
    )
    
    cooking_time = st.sidebar.selectbox(
        "Cooking Time:",
        ["Any", "15 min", "30 min", "1 hour", "2+ hours"]
    )
    
    # Render sidebar ad if commercial features are enabled
    if COMMERCIAL_FEATURES and is_ads_enabled():
        render_sidebar_ad()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Top advertisement (commercial)
        if COMMERCIAL_FEATURES and is_ads_enabled():
            render_main_ad("top")
        
        # Generate button
        if st.button("🚀 Generate Recipe", type="primary"):
            generate_recipe(ingredients, cuisine_type, difficulty, cooking_time)
        
        # Sample recipes section
        st.markdown("### 📖 Sample Recipes")
        
        sample_recipes = [
            {"name": "Finnish Salmon Soup", "time": "30 min", "difficulty": "Easy"},
            {"name": "Chicken Rice Bowl", "time": "25 min", "difficulty": "Easy"},
            {"name": "Vegetable Pasta", "time": "20 min", "difficulty": "Easy"},
        ]
        
        for recipe in sample_recipes:
            with st.expander(f"{recipe['name']} - {recipe['time']} - {recipe['difficulty']}"):
                st.write("Click 'Generate Recipe' with your ingredients to get detailed instructions!")
        
        # Middle advertisement (commercial)
        if COMMERCIAL_FEATURES and is_ads_enabled():
            render_main_ad("middle")
    
    with col2:
        # Pricing info
        st.markdown("### 💰 Local Pricing")
        st.info("Prices from Finnish grocery stores (S-market, Prisma, Alepa)")
        
        # Recent ingredients with pricing
        st.markdown("**Recent Ingredient Prices:**")
        sample_prices = [
            {"item": "Chicken breast", "price": "12.95 €/kg", "store": "Prisma"},
            {"item": "Basmati rice", "price": "3.45 €/kg", "store": "S-market"},
            {"item": "Fresh vegetables", "price": "2.99 €/kg", "store": "Alepa"},
        ]
        
        for item in sample_prices:
            st.write(f"• **{item['item']}**: {item['price']} ({item['store']})")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style='text-align: center'>
                <p>Powered by Google Vertex AI & Finnish grocery data</p>
                <p><small>Data from S-kaupat.fi | Prices updated daily</small></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Bottom advertisement (commercial)
    if COMMERCIAL_FEATURES and is_ads_enabled():
        render_main_ad("bottom")


def generate_recipe(ingredients: str, cuisine: str, difficulty: str, cooking_time: str):
    """Generate a recipe based on user inputs."""
    
    with st.spinner("🔍 Finding ingredients and generating recipe..."):
        try:
            # Parse ingredients
            ingredient_list = [ing.strip() for ing in ingredients.split('\n') if ing.strip()]
            
            if not ingredient_list:
                st.error("Please enter at least one ingredient!")
                return
            
            # Mock recipe generation (replace with actual Vertex AI integration)
            st.success("✅ Recipe generated successfully!")
            
            # Display recipe
            st.markdown("### 🍽️ Your Recipe")
            
            # Recipe title
            recipe_name = f"{cuisine} Style Recipe" if cuisine != "Any" else "Custom Recipe"
            st.markdown(f"## {recipe_name}")
            
            # Ingredients with pricing
            st.markdown("#### 🛒 Ingredients & Pricing")
            total_cost = 0
            
            for ingredient in ingredient_list:
                # Mock pricing (replace with actual price lookup)
                mock_price = f"{2.50 + len(ingredient) * 0.3:.2f}"
                total_cost += float(mock_price)
                st.write(f"• **{ingredient.title()}**: {mock_price} € (estimated)")
            
            st.markdown(f"**Total estimated cost: {total_cost:.2f} €**")
            
            # Instructions
            st.markdown("#### 👩‍🍳 Instructions")
            instructions = [
                "Prepare all ingredients by washing and chopping as needed",
                "Heat oil in a large pan over medium heat",
                "Add ingredients in order of cooking time required",
                "Season with salt, pepper, and preferred spices",
                "Cook until ingredients are tender and well combined",
                "Serve hot and enjoy your meal!"
            ]
            
            for i, instruction in enumerate(instructions, 1):
                st.write(f"{i}. {instruction}")
            
            # Nutritional info
            st.markdown("#### 📊 Nutritional Information")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Calories", "450")
            with col2:
                st.metric("Protein", "25g")
            with col3:
                st.metric("Carbs", "35g")
            with col4:
                st.metric("Fat", "18g")
            
        except Exception as e:
            st.error(f"Error generating recipe: {str(e)}")
            st.info("This is a demo version. Full integration with Vertex AI coming soon!")


if __name__ == "__main__":
    main()
