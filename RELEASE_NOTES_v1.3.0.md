# 🚀 Makoisa AI v1.3.0 - Complete Rebranding Release

## 🎨 Major Changes

### Project Rebranding
- **Complete transformation** from "s-kaupat-scraper" to "Makoisa AI"
- Updated project identity, documentation, and service URLs
- Modernized BigQuery configuration (`s_kaupat` → `makoisa_ai`)
- Enhanced commercial licensing framework

## ✨ New Features

### Development Environment
- **Comprehensive v1.3.0-dev environment** with automated setup
- Enhanced development tooling and VS Code integration
- Automated BigQuery dataset creation and configuration

### Google Ads Integration
- **Google AdSense integration** in Recipe AI interface
- Optional commercial module with proper separation
- Revenue generation capabilities for recipe suggestions

### Licensing Strategy
- **Dual licensing framework** with PolyForm Noncommercial base
- Commercial exception for original author
- Modular commercial features with separate licensing

## 🔧 Technical Improvements

### Configuration Updates
- **Updated CLI tools** and loader configurations
- Modernized cloud deployment configurations
- Enhanced project documentation and branding
- **All functionality preserved** during rebranding

### Service URLs
- **API**: `https://makoisa-ai-api-dfahwqncla-lz.a.run.app`
- **Recipe AI**: `https://makoisa-ai-recipes-dfahwqncla-lz.a.run.app`

## 📦 What's Included

### Core Components
- **FastAPI backend** for grocery store data processing
- **Streamlit Recipe AI frontend** with Google Ads integration
- **BigQuery integration** with updated dataset naming
- **Commercial module** separation for optional features

### Development Tools
- Automated development environment setup
- VS Code debugging configurations
- Comprehensive testing framework
- Development-specific configurations

## 🎯 Use Cases

### For Developers
- Finnish grocery data analysis and processing
- AI-powered recipe generation and suggestions
- Commercial recipe app development
- Food technology research and development

### For End Users
- Smart recipe suggestions based on available ingredients
- Price-aware meal planning with Finnish grocery data
- Ingredient-based recipe discovery
- Cost-effective meal preparation

## 🚀 Getting Started

```bash
# Clone the repository
git clone https://github.com/juntunen-ai/makoisa-ai.git
cd makoisa-ai

# Set up development environment
./setup_dev_env.sh

# Install dependencies
poetry install --with dev,commercial

# Start the API server
poetry run uvicorn server:app --reload

# Start Recipe AI interface
cd recipe_ai && streamlit run ui/app.py
```

## 📋 Migration Notes

### For Existing Users
- BigQuery dataset references updated from `s_kaupat` to `makoisa_ai`
- Service URLs updated to new Makoisa AI domains
- All functionality preserved with new branding

### Breaking Changes
- **Dataset naming**: Update any external references to use `makoisa_ai`
- **Service URLs**: Update API endpoint references
- **Repository URL**: Use `https://github.com/juntunen-ai/makoisa-ai.git`

## 🔗 Links

- **Documentation**: [README.md](https://github.com/juntunen-ai/makoisa-ai/blob/main/README.md)
- **API Documentation**: [https://makoisa-ai-api-dfahwqncla-lz.a.run.app/docs](https://makoisa-ai-api-dfahwqncla-lz.a.run.app/docs)
- **Commercial Licensing**: [LICENSE_COMMERCIAL.md](https://github.com/juntunen-ai/makoisa-ai/blob/main/LICENSE_COMMERCIAL.md)
- **Development Guide**: [DEVELOPMENT_ROADMAP.md](https://github.com/juntunen-ai/makoisa-ai/blob/main/DEVELOPMENT_ROADMAP.md)

## 🙏 Acknowledgments

This release represents a significant milestone in the project's evolution, establishing a cohesive brand identity while maintaining all the powerful functionality for Finnish grocery data analysis and AI-powered recipe generation.

---

**Full Changelog**: [v1.2.0...v1.3.0](https://github.com/juntunen-ai/makoisa-ai/compare/v1.2.0...v1.3.0)
