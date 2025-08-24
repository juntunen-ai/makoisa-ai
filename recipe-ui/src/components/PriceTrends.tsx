import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PriceData {
  date: string;
  price: number;
  store: string;
}

interface PriceTrendsProps {
  productName: string;
  data: PriceData[];
}

const PriceTrends = ({ productName, data }: PriceTrendsProps) => {
  // Group data by store for multiple lines
  const stores = [...new Set(data.map(item => item.store))];
  const colors = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed'];

  // Transform data for Recharts
  const chartData = data.reduce((acc, item) => {
    const existingDate = acc.find(d => d.date === item.date);
    if (existingDate) {
      existingDate[item.store] = item.price;
    } else {
      acc.push({
        date: item.date,
        [item.store]: item.price
      });
    }
    return acc;
  }, [] as any[]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg">Price Trends for {productName}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              <YAxis 
                fontSize={12}
                tickFormatter={(value) => `$${value.toFixed(2)}`}
              />
              <Tooltip 
                formatter={(value, name) => [`$${Number(value).toFixed(2)}`, name]}
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
              />
              {stores.map((store, index) => (
                <Line
                  key={store}
                  type="monotone"
                  dataKey={store}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  connectNulls={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        <div className="flex flex-wrap gap-4 mt-4">
          {stores.map((store, index) => (
            <div key={store} className="flex items-center space-x-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: colors[index % colors.length] }}
              />
              <span className="text-sm font-medium">{store}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default PriceTrends;
