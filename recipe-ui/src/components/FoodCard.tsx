import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Star, TrendingDown, ShoppingCart } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Store {
  name: string;
  price: number;
  originalPrice?: number;
  rating: number;
  inStock: boolean;
}

interface FoodCardProps {
  name: string;
  image: string;
  category: string;
  stores: Store[];
  bestPrice: number;
  averagePrice: number;
}

const FoodCard = ({ name, image, category, stores, bestPrice, averagePrice }: FoodCardProps) => {
  const bestStore = stores.find(store => store.price === bestPrice);
  const savings = averagePrice - bestPrice;

  return (
    <Card className="overflow-hidden hover:shadow-hover transition-all duration-300">
      <div className="relative">
        <img 
          src={image} 
          alt={name}
          className="w-full h-48 object-cover"
        />
        <Badge className="absolute top-2 right-2" variant="secondary">
          {category}
        </Badge>
      </div>
      
      <CardHeader className="pb-3">
        <CardTitle className="text-lg line-clamp-2">{name}</CardTitle>
        <div className="flex items-center justify-between">
          <div className="text-2xl font-bold text-primary">
            ${bestPrice.toFixed(2)}
          </div>
          {savings > 0 && (
            <div className="flex items-center text-success text-sm">
              <TrendingDown className="h-3 w-3 mr-1" />
              Save ${savings.toFixed(2)}
            </div>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        <div className="text-sm text-muted-foreground">
          Best at <span className="font-medium">{bestStore?.name}</span>
        </div>
        
        <div className="space-y-2">
          {stores.slice(0, 3).map((store, index) => (
            <div key={index} className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <span className={store.inStock ? "text-foreground" : "text-muted-foreground line-through"}>
                  {store.name}
                </span>
                <div className="flex items-center">
                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                  <span className="text-xs ml-1">{store.rating}</span>
                </div>
              </div>
              <div className="text-right">
                {store.originalPrice && (
                  <span className="text-xs text-muted-foreground line-through mr-1">
                    ${store.originalPrice.toFixed(2)}
                  </span>
                )}
                <span className={store.price === bestPrice ? "font-bold text-primary" : ""}>
                  ${store.price.toFixed(2)}
                </span>
              </div>
            </div>
          ))}
        </div>
        
        <Button className="w-full mt-4" variant="outline">
          <ShoppingCart className="h-4 w-4 mr-2" />
          Compare All Stores
        </Button>
      </CardContent>
    </Card>
  );
};

export default FoodCard;
