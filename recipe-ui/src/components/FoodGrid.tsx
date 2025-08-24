import FoodCard from "./FoodCard";

// Mock data for demonstration
const mockFoodData = [
  {
    id: 1,
    name: "Organic Bananas (1 lb)",
    image: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400&h=300&fit=crop",
    category: "Fruits",
    stores: [
      { name: "Whole Foods", price: 2.49, originalPrice: 2.99, rating: 4.5, inStock: true },
      { name: "Trader Joe's", price: 2.79, rating: 4.3, inStock: true },
      { name: "Safeway", price: 3.19, rating: 4.0, inStock: true },
      { name: "Target", price: 2.89, rating: 4.2, inStock: false }
    ],
    bestPrice: 2.49,
    averagePrice: 2.84
  },
  {
    id: 2,
    name: "Organic Whole Milk (1 gallon)",
    image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=300&fit=crop",
    category: "Dairy",
    stores: [
      { name: "Costco", price: 4.29, rating: 4.6, inStock: true },
      { name: "Whole Foods", price: 5.99, rating: 4.5, inStock: true },
      { name: "Kroger", price: 4.89, rating: 4.1, inStock: true },
      { name: "Walmart", price: 4.67, rating: 3.9, inStock: true }
    ],
    bestPrice: 4.29,
    averagePrice: 4.96
  },
  {
    id: 3,
    name: "Atlantic Salmon Fillet",
    image: "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=400&h=300&fit=crop",
    category: "Seafood",
    stores: [
      { name: "Costco", price: 12.99, rating: 4.6, inStock: true },
      { name: "Whole Foods", price: 16.99, rating: 4.7, inStock: true },
      { name: "Safeway", price: 15.49, rating: 4.2, inStock: true },
      { name: "Fresh Market", price: 18.99, rating: 4.8, inStock: true }
    ],
    bestPrice: 12.99,
    averagePrice: 16.12
  }
];

const FoodGrid = () => {
  return (
    <section className="py-16 bg-background">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-foreground mb-4">
            Popular Food Items
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Compare prices across multiple stores and find the best deals on your favorite food items.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {mockFoodData.map((food) => (
            <FoodCard
              key={food.id}
              name={food.name}
              image={food.image}
              category={food.category}
              stores={food.stores}
              bestPrice={food.bestPrice}
              averagePrice={food.averagePrice}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default FoodGrid;
