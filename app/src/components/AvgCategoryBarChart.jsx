import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const COLORS = [
  '#0057ff', '#00a37a', '#ff7a00', '#e040fb', '#00bcd4',
  '#ff5252', '#ffeb3b', '#8d6e63',
];

const MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const inrFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});

function formatInr(value) {
  return inrFormatter.format(Number(value || 0));
}

function pivotItems(items) {
  if (!items || items.length === 0) return { rows: [], categories: [] };

  const categoriesSet = new Set();
  const monthMap = {};

  for (const item of items) {
    const abbr = MONTH_ABBR[(item.month || 1) - 1];
    categoriesSet.add(item.category);
    if (!monthMap[abbr]) {
      monthMap[abbr] = { month: abbr };
    }
    monthMap[abbr][item.category] = (monthMap[abbr][item.category] || 0) + item.total;
  }

  const rows = MONTH_ABBR
    .filter((abbr) => monthMap[abbr])
    .map((abbr) => monthMap[abbr]);

  return { rows, categories: Array.from(categoriesSet) };
}

export default function AvgCategoryBarChart({ items, loading, error }) {
  if (error) {
    return <p className="error-text">{error}</p>;
  }

  const { rows, categories } = pivotItems(items);

  if (!loading && rows.length === 0) {
    return <p className="help-text">No data for this period.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis tickFormatter={formatInr} />
        <Tooltip formatter={(v) => formatInr(v)} />
        <Legend />
        {categories.map((cat, index) => (
          <Bar key={cat} dataKey={cat} fill={COLORS[index % COLORS.length]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
