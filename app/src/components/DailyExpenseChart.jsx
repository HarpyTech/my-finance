import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const inrFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});

function formatInr(value) {
  return inrFormatter.format(Number(value || 0));
}

export default function DailyExpenseChart({ items, loading, error }) {
  if (error) {
    return <p className="error-text">{error}</p>;
  }
  if (!loading && (!items || items.length === 0)) {
    return <p className="help-text">No data for this period.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={items}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="day" label={{ value: 'Day', position: 'insideBottom', offset: -2 }} />
        <YAxis tickFormatter={formatInr} />
        <Tooltip formatter={(value) => formatInr(value)} />
        <Bar dataKey="total" fill="#0057ff" />
      </BarChart>
    </ResponsiveContainer>
  );
}
