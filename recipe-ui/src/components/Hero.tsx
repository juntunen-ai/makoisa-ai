import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, TrendingDown, MapPin, Clock } from "lucide-react";

const Hero = () => {
  const heroImage = "https://images.unsplash.com/photo-1542838132-92c53300491e?w=600&h=400&fit=crop";

  return (
    <section className="py-16 bg-gradient-hero text-primary-foreground">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h1 className="text-4xl md:text-6xl font-bold leading-tight">
              Find the Best Food Prices 
              <span className="text-accent"> Instantly</span>
            </h1>
            <p className="text-xl text-primary-foreground/90 max-w-lg">
              Compare prices across 50+ stores and never overpay for groceries again. 
              Save money, save time, eat better.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-5 w-5" />
                <Input
                  placeholder="Search any food item..."
                  className="pl-10 h-12 text-base bg-background text-foreground"
                />
              </div>
              <Button size="lg" className="h-12 px-8 bg-accent hover:bg-accent/90 text-accent-foreground">
                Search Deals
              </Button>
            </div>

            <div className="flex flex-wrap gap-6 pt-4">
              <div className="flex items-center space-x-2">
                <TrendingDown className="h-5 w-5 text-accent" />
                <span>Best Prices</span>
              </div>
              <div className="flex items-center space-x-2">
                <MapPin className="h-5 w-5 text-accent" />
                <span>Local Stores</span>
              </div>
              <div className="flex items-center space-x-2">
                <Clock className="h-5 w-5 text-accent" />
                <span>Save 20% Average</span>
              </div>
            </div>
          </div>
          
          <div className="relative">
            <img
              src={heroImage}
              alt="Fresh groceries and food items"
              className="rounded-lg shadow-hover w-full h-auto"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
