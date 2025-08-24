import { ShoppingCart, Twitter, Facebook, Instagram, Mail } from "lucide-react";

const Footer = () => {
  return (
    <footer className="bg-card border-t border-border">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <ShoppingCart className="h-6 w-6 text-primary" />
              <span className="text-xl font-bold text-foreground">FoodCompare</span>
            </div>
            <p className="text-muted-foreground text-sm">
              Your trusted partner for finding the best food prices across all stores. 
              Save money, eat better.
            </p>
            <div className="flex space-x-4">
              <Twitter className="h-5 w-5 text-muted-foreground hover:text-primary cursor-pointer transition-colors" />
              <Facebook className="h-5 w-5 text-muted-foreground hover:text-primary cursor-pointer transition-colors" />
              <Instagram className="h-5 w-5 text-muted-foreground hover:text-primary cursor-pointer transition-colors" />
              <Mail className="h-5 w-5 text-muted-foreground hover:text-primary cursor-pointer transition-colors" />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold text-foreground">Categories</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="hover:text-primary cursor-pointer">Fruits & Vegetables</li>
              <li className="hover:text-primary cursor-pointer">Meat & Seafood</li>
              <li className="hover:text-primary cursor-pointer">Dairy & Eggs</li>
              <li className="hover:text-primary cursor-pointer">Pantry Staples</li>
            </ul>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold text-foreground">Company</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="hover:text-primary cursor-pointer">About Us</li>
              <li className="hover:text-primary cursor-pointer">How It Works</li>
              <li className="hover:text-primary cursor-pointer">Careers</li>
              <li className="hover:text-primary cursor-pointer">Contact</li>
            </ul>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold text-foreground">Support</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="hover:text-primary cursor-pointer">Help Center</li>
              <li className="hover:text-primary cursor-pointer">Privacy Policy</li>
              <li className="hover:text-primary cursor-pointer">Terms of Service</li>
              <li className="hover:text-primary cursor-pointer">Cookie Policy</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-border mt-12 pt-8 text-center">
          <p className="text-muted-foreground text-sm">
            © 2024 FoodCompare. All rights reserved. | Made with ❤️ for smart shoppers.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
