import Header from "@/components/Header";
import GoogleAds from "@/components/GoogleAds";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import FoodGrid from "@/components/FoodGrid";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <GoogleAds />
      <Hero />
      <Features />
      <FoodGrid />
      <Footer />
    </div>
  );
};

export default Index;
