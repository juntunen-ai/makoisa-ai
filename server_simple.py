"""
Simple FastAPI server for Makoisa AI - Development Version
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="Makoisa AI API",
    description="API for Finnish grocery shopping and recipe platform",
    version="1.3.0-dev"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Makoisa AI API",
        "version": "1.3.0-dev",
        "status": "running",
        "frontend_url": "http://localhost:5173"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2025-08-24T19:45:00Z",
        "services": {
            "api": "running",
            "frontend": "http://localhost:5173"
        }
    }

@app.get("/api/products")
async def get_products():
    # Mock data for development
    return {
        "products": [
            {
                "id": 1,
                "name": "Myllyn Paras Vehnäjauho",
                "category": "Baking",
                "image": "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=400",
                "stores": [
                    {"name": "K-Kauppa", "price": 2.49, "rating": 4.5, "inStock": True},
                    {"name": "S-Market", "price": 2.65, "rating": 4.3, "inStock": True},
                    {"name": "Prisma", "price": 2.39, "rating": 4.7, "inStock": True}
                ],
                "bestPrice": 2.39,
                "averagePrice": 2.51
            },
            {
                "id": 2,
                "name": "Valio Rasvaton Maito",
                "category": "Dairy",
                "image": "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400",
                "stores": [
                    {"name": "K-Kauppa", "price": 1.89, "rating": 4.6, "inStock": True},
                    {"name": "S-Market", "price": 1.95, "rating": 4.4, "inStock": True},
                    {"name": "Prisma", "price": 1.79, "rating": 4.8, "inStock": True}
                ],
                "bestPrice": 1.79,
                "averagePrice": 1.88
            }
        ]
    }

@app.get("/api/stores")
async def get_stores():
    return {
        "stores": [
            {"name": "K-Kauppa", "count": 156},
            {"name": "S-Market", "count": 203},
            {"name": "Prisma", "count": 89}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000, reload=True)
