# Makoisa AI

An intelligent Finnish grocery shopping and AI-powered recipe generation platform.

## 🎯 Overview

This project provides:
- **Store Data Scraping**: Extract store information from S-kaupat.fi
- **Product Discovery**: Scrape product data and pricing information
- **AI Recipe Generator**: Generate recipes with ingredient matching and pricing
- **BigQuery Integration**: Store and analyze scraped data
- **Google Ads Integration**: Monetization through targeted advertising

## 🏗️ Architecture

### Core Components
- **Scraper Module**: Intelligent web scraping with API-first approach
- **Recipe AI**: Vertex AI-powered recipe generation with ingredient matching
- **Data Pipeline**: BigQuery integration for data storage and analytics
- **Web Interface**: Modern React + TypeScript UI with shadcn/ui components
- **API Server**: FastAPI REST endpoints

### Services
- **Makoisa AI API**: `https://makoisa-ai-api-dfahwqncla-lz.a.run.app`
- **AI Recipe Generator**: `https://ai-recipe-generator-dfahwqncla-uc.a.run.app`

## 🚀 Features

### Web Scraping
- Multi-strategy scraping (API discovery + browser fallback)
- Store chain detection (Prisma, S-market, Alepa, Sale, etc.)
- Product data extraction with pricing
- Rate limiting and anti-detection
- Error handling and retry mechanisms

### AI Recipe Generation
- Ingredient matching with local pricing
- Recipe generation using Vertex AI
- Nutritional information and cooking instructions
- Cost optimization and budget-friendly suggestions
- Dietary preference support

### Data Management
- BigQuery integration for scalable storage
- Data normalization and validation
- Query interface for store and product data
- Export capabilities (JSON, CSV)

### Monetization
- Google AdSense integration (commercial module)
- Non-intrusive ad placement
- Cooking and food-focused targeting
- Revenue optimization

## 📦 Installation

### Prerequisites
- Python 3.11+
- Google Cloud credentials (for BigQuery and Vertex AI)
- Poetry for dependency management

### Setup
```bash
# Clone repository
git clone https://github.com/juntunen-ai/makoisa-ai.git
cd makoisa-ai

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run scraper
poetry run python -m scraper.main

# Start web interface
cd recipe-ui
npm install
npm run dev
```

## 🔧 Usage

### Command Line Interface
```bash
# Scrape stores
poetry run python -m scraper.cli scrape-stores

# Load data to BigQuery
poetry run python -m loader.cli upload stores.json

# Generate recipes
poetry run python -m recipe_ai.main
```

### API Usage
```bash
# Get stores
curl https://makoisa-ai-api-dfahwqncla-lz.a.run.app/stores

# Generate recipe
curl -X POST https://ai-recipe-generator-dfahwqncla-uc.a.run.app/generate-recipe \
  -H "Content-Type: application/json" \
  -d '{"ingredients": ["chicken", "rice", "vegetables"]}'
```

## 📄 Licensing

### Open Source License
This project is licensed under the **PolyForm Noncommercial License 1.0.0**, which allows:
- ✅ Personal use, research, and experimentation
- ✅ Educational and academic use
- ✅ Use by nonprofits and government organizations
- ✅ Modification and distribution (with license notices)
- ❌ Commercial use by third parties

### Commercial Exception
The original author (Harri Juntunen/juntunen-ai) retains full commercial rights and may use this software for any commercial purpose without restriction.

### Commercial Licensing
Commercial licenses are available for businesses wanting to:
- Deploy the solution commercially
- Integrate with proprietary systems
- Remove attribution requirements
- Access premium support and features

**Contact**: For commercial licensing inquiries, please reach out to harri@juntunen.ai

### Dual Licensing Strategy
- **Open Source**: Full source code available under noncommercial license
- **Commercial**: Separate licensing for business use cases
- **Contributions**: Contributors grant rights for dual licensing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contributor License Agreement
By contributing, you grant the project maintainers the right to license your contributions under both the open source and commercial licenses.

## 📊 Project Status

- ✅ **Core Scraping**: Production ready
- ✅ **BigQuery Integration**: Production ready
- ✅ **Recipe AI**: Production ready with Google Ads
- ✅ **API Server**: Deployed and operational
- ✅ **Web Interface**: Live and accessible
- 🚧 **Commercial Module**: Separated for optional integration

## 🔗 Links

- [Live Recipe Generator](https://ai-recipe-generator-dfahwqncla-uc.a.run.app)
- [API Documentation](https://makoisa-ai-api-dfahwqncla-lz.a.run.app/docs)
- [Google Ads Implementation Guide](GOOGLE_ADS_IMPLEMENTATION.md)
- [Commercial Licensing](mailto:harri@juntunen.ai)

## 📧 Contact

**Author**: Harri Juntunen  
**Email**: harri@juntunen.ai  
**Organization**: juntunen-ai  
**Commercial Inquiries**: harri@juntunen.ai

---

*This project demonstrates advanced web scraping, AI integration, and modern web application architecture while maintaining clear licensing boundaries for both open source and commercial use.*
