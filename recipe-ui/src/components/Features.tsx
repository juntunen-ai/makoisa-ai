import { TrendingDown, MapPin, Clock, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    icon: TrendingDown,
    title: "Best Price Guarantee",
    description: "We track prices across 50+ stores to ensure you always get the lowest price available.",
    color: "text-success"
  },
  {
    icon: MapPin,
    title: "Location-Based Results",
    description: "Find deals at stores near you with real-time inventory and availability updates.",
    color: "text-info"
  },
  {
    icon: Clock,
    title: "Real-Time Updates",
    description: "Prices are updated every hour to give you the most current information for smart shopping.",
    color: "text-warning"
  },
  {
    icon: Shield,
    title: "Trusted & Secure",
    description: "Your data is protected and we partner only with verified retailers and trusted brands.",
    color: "text-primary"
  }
];

const Features = () => {
  return (
    <section className="py-16 bg-muted/30">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-foreground mb-4">
            Why Choose FoodCompare?
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Save time and money with our comprehensive food price comparison platform.
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="text-center hover:shadow-hover transition-all duration-300">
              <CardHeader>
                <div className="mx-auto mb-4 p-3 rounded-full bg-gradient-hero w-fit">
                  <feature.icon className={`h-8 w-8 ${feature.color}`} />
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
