import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

const COLORS = [
  '#0057ff', '#00a37a', '#ff7a00', '#e040fb', '#00bcd4',
  '#ff5252', '#ffeb3b', '#8d6e63',
];

const inrFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});

function formatInr(value) {
  return inrFormatter.format(Number(value || 0));
}

export default function VendorDonutChart({ items, loading, error }) {
  if (error) {
    return <p className="error-text">{error}</p>;
  }
  if (!loading && (!items || items.length === 0)) {
    return <p className="help-text">No data for this period.</p>;
  }

  const normalized = (items || []).map((item) => ({
    ...item,
    vendor: item.vendor === '' ? 'Unknown' : item.vendor,
  }));

  const sorted = [...normalized].sort((a, b) => b.total - a.total);
  let chartData;
  if (sorted.length <= 7) {
    chartData = sorted;
  } else {
    const top7 = sorted.slice(0, 7);
    const othersTotal = sorted.slice(7).reduce((sum, v) => sum + v.total, 0);
    chartData = [...top7, { vendor: 'Others', total: Math.round(othersTotal * 100) / 100 }];
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="total"
          nameKey="vendor"
          innerRadius={60}
          outerRadius={90}
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Legend />
        <Tooltip formatter={(v) => formatInr(v)} />
      </PieChart>
    </ResponsiveContainer>
  );
}
