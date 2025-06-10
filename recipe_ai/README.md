# AI Recipe Generator

> **🎉 STATUS: FULLY OPERATIONAL** ✅  
> The AI Recipe Generator is now complete and working! All core features are implemented and tested.

An AI-powered recipe generator that uses Google Vertex AI to create recipes based on user prompts and integrates with grocery store product data to provide ingredient pricing and shopping lists.

## ✅ What's Working

- **✅ Vertex AI Integration**: Using Gemini 2.5 Flash Preview model (gemini-2.5-flash-preview-05-20) in us-central1
- **✅ BigQuery Integration**: Successfully searching the `products` table for ingredient pricing  
- **✅ Web UI**: Streamlit application running at http://localhost:8501
- **✅ Environment Configuration**: Proper .env setup with project ID `ruokahinta-scraper-1748695687`
- **✅ Recipe Generation**: Generating authentic Finnish recipes with local ingredient names
- **✅ Price Discovery**: Finding ingredient prices from grocery store product data
- **✅ Error Handling**: Graceful fallbacks when services are unavailable

## 🚀 Quick Start

1. **Start the application**:
   ```bash
   cd /Users/harrijuntunen/s-kaupat-scraper
   streamlit run recipe_ai/ui/app.py
   ```

2. **Open your browser**: http://localhost:8501

3. **Generate recipes**: Enter prompts like "helppo pasta tomaattikastike" or "terveellinen kanaa ja riisiä"

## Features

- 🤖 **AI Recipe Generation**: Uses Google's Gemini Pro model to generate recipes in Finnish
- 💰 **Real-time Pricing**: Searches BigQuery for ingredient prices from grocery store data  
- 🛒 **Shopping Lists**: Creates organized shopping lists with pricing
- 📊 **Cost Analysis**: Provides cost breakdowns and price comparisons
- 🌐 **Web Interface**: Beautiful Streamlit UI for easy interaction
- 📱 **Mobile Friendly**: Responsive design works on all devices
- 📺 **Non-intrusive Ads**: Optional Google AdSense integration for cooking-related advertising

## Architecture

```
recipe_ai/
├── __init__.py              # Module exports
├── config.py                # Configuration management
├── vertex_ai_client.py      # Google Vertex AI integration
├── ingredient_matcher.py    # BigQuery product matching
├── recipe_generator.py      # Main orchestrator
└── ui/
    └── app.py              # Streamlit web application
```

## Setup

### Prerequisites

1. **Google Cloud SDK**: Install and authenticate
   ```bash
   brew install google-cloud-sdk
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Active Product Data**: Ensure your BigQuery table is populated with product data

3. **Python Dependencies**: Installed via Poetry (already configured)

### Quick Setup

Run the automated setup script:

```bash
./setup_recipe_ai.sh
```

### Manual Setup

1. **Enable Google Cloud APIs**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable bigquery.googleapis.com
   ```

2. **Configure Environment**:
   Create `recipe_ai/.env` with your settings:
   ```bash
   GOOGLE_CLOUD_PROJECT=your-project-id
   BIGQUERY_TABLE=your-project-id.s_kaupat.products
   VERTEX_AI_LOCATION=europe-west4
   VERTEX_AI_MODEL=gemini-1.5-pro
   
   # Optional: Google AdSense Configuration
   GOOGLE_ADSENSE_ENABLED=true
   GOOGLE_ADSENSE_CLIENT_ID=ca-pub-YOUR_PUBLISHER_ID
   GOOGLE_ADSENSE_SIDEBAR_SLOT=1234567890
   GOOGLE_ADSENSE_MAIN_SLOT=0987654321
   ```

### Google Ads Setup (Optional)

The application includes optional Google AdSense integration for non-intrusive, cooking-related advertising:

1. **Apply for Google AdSense**: Get approved and obtain your Publisher ID
2. **Create Ad Units**: Set up display ads for sidebar and main content areas
3. **Configure Environment**: Add your AdSense details to `.env` file
4. **Deploy**: Ads will automatically appear when enabled

**Features:**
- Maximum 2 ads per page (sidebar + main content)
- Cooking and food-related content only
- Clearly labeled as advertisements
- Can be disabled by setting `GOOGLE_ADSENSE_ENABLED=false`

For detailed setup instructions, see [Google Ads Implementation Guide](GOOGLE_ADS_IMPLEMENTATION.md).

## Usage

### Web Interface

Start the Streamlit application:

```bash
poetry run streamlit run recipe_ai/ui/app.py
```

Navigate to `http://localhost:8501` and:
1. Enter a recipe prompt (e.g., "I want chicken pasta for 4 people")
2. Get AI-generated recipe with ingredient pricing
3. View shopping list and cost analysis
4. Browse recipe history

### Python API

Use the recipe generator programmatically:

```python
from recipe_ai import RecipeGenerator

# Initialize generator
rg = RecipeGenerator()

# Generate a recipe
result = rg.generate_recipe(
    prompt="I want a healthy vegetarian dinner",
    servings=4
)

print(f"Recipe: {result['recipe']['title']}")
print(f"Total cost: {result['ingredients']['_summary']['estimated_total_price']}")
```

### Advanced Usage

```python
from recipe_ai import VertexAIClient, IngredientMatcher

# Direct AI client usage
ai_client = VertexAIClient()
recipe = ai_client.generate_recipe("Comfort food for winter")

# Direct ingredient matching
matcher = IngredientMatcher()
products = matcher.find_ingredient_products({
    'item': 'chicken breast',
    'amount': '500',
    'unit': 'g'
})
```

## API Reference

### RecipeGenerator

Main orchestrator class that combines AI generation with ingredient matching.

**Methods:**
- `generate_recipe(prompt, servings=4)`: Generate complete recipe with pricing
- `get_recipe_suggestions(cuisine_type)`: Get recipe ideas by cuisine
- `analyze_recipe_cost(recipe_data)`: Analyze cost of existing recipe

### VertexAIClient

Handles communication with Google Vertex AI.

**Methods:**
- `generate_recipe(prompt, servings=4)`: Generate recipe using Gemini Pro
- `get_recipe_variations(base_recipe)`: Get variations of existing recipe
- `extract_ingredients(recipe_text)`: Extract structured ingredients from text

### IngredientMatcher

Matches recipe ingredients to grocery store products.

**Methods:**
- `find_ingredient_products(ingredient)`: Find products for single ingredient
- `find_all_ingredients(recipe_data)`: Find products for all recipe ingredients
- `get_price_comparison(ingredient_name)`: Compare prices across products

## Configuration

The system uses `RecipeAIConfig` for centralized configuration:

```python
from recipe_ai.config import RecipeAIConfig

# Override default settings
RecipeAIConfig.MAX_PRICE_RESULTS = 15
RecipeAIConfig.VERTEX_AI_LOCATION = "us-central1"
```

## Error Handling

The system includes comprehensive error handling:

- **API Failures**: Graceful fallbacks for Vertex AI timeouts
- **Missing Data**: Helpful messages when products aren't found
- **Authentication**: Clear instructions for auth issues
- **Rate Limits**: Automatic retry with exponential backoff

## Troubleshooting

### Common Issues

1. **"No module named 'vertexai'"**
   ```bash
   poetry install  # Reinstall dependencies
   ```

2. **"BigQuery table not found"**
   - Ensure product scraper has run and populated data
   - Check your project ID and table name in config

3. **"Authentication failed"**
   ```bash
   gcloud auth application-default login
   ```

4. **"Vertex AI quota exceeded"**
   - Wait for quota reset or request increase in Google Cloud Console

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance

- **Recipe Generation**: ~2-5 seconds via Vertex AI
- **Ingredient Matching**: ~1-3 seconds per recipe via BigQuery
- **UI Response**: Real-time updates with progress indicators
- **Caching**: Results cached for improved performance

## Contributing

1. Create feature branch from `main`
2. Make changes in `recipe_ai/` module
3. Add tests in `recipe_ai/tests/`
4. Update documentation
5. Submit pull request

## License

This project is a standalone AI recipe generator with grocery store integration.
