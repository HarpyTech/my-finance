import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useAuth } from '../auth/AuthContext';
import { apiRequest } from '../lib/api';

const CATEGORIES = ['Food', 'Travel', 'Utilities', 'Shopping', 'Health', 'Other'];

export default function DashboardPage() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();

  const [expenseForm, setExpenseForm] = useState({
    amount: '',
    category: CATEGORIES[0],
    description: '',
    expense_date: new Date().toISOString().slice(0, 10),
  });
  const [expenses, setExpenses] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [yearly, setYearly] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [error, setError] = useState('');

  const currentYear = new Date().getFullYear();

  async function loadData() {
    try {
      const [allRes, monthRes, yearRes, categoryRes] = await Promise.all([
        apiRequest('/expenses'),
        apiRequest(`/expenses/summary/monthly?year=${currentYear}`),
        apiRequest('/expenses/summary/yearly'),
        apiRequest(`/expenses/summary/categories?year=${currentYear}`),
      ]);
      setExpenses(allRes.items || []);
      setMonthly(monthRes.items || []);
      setYearly(yearRes.items || []);
      setCategoryData(categoryRes.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function addExpense(event) {
    event.preventDefault();
    setError('');

    try {
      await apiRequest('/expenses', {
        method: 'POST',
        body: JSON.stringify({
          amount: Number(expenseForm.amount),
          category: expenseForm.category,
          description: expenseForm.description,
          expense_date: expenseForm.expense_date,
        }),
      });

      setExpenseForm((prev) => ({
        ...prev,
        amount: '',
        description: '',
      }));
      await loadData();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  const totalSpend = useMemo(
    () => expenses.reduce((sum, item) => sum + Number(item.amount || 0), 0),
    [expenses]
  );

  return (
    <main className="dashboard-layout">
      <header className="dashboard-header">
        <div>
          <h1>My Finance Dashboard</h1>
          <p>
            Logged in as <strong>{session.user}</strong> ({session.role})
          </p>
        </div>
        <button onClick={handleLogout}>Logout</button>
      </header>

      <section className="stats-grid">
        <article className="stat-card">
          <h3>Total Expenses</h3>
          <p>${totalSpend.toFixed(2)}</p>
        </article>
        <article className="stat-card">
          <h3>Entries</h3>
          <p>{expenses.length}</p>
        </article>
        <article className="stat-card">
          <h3>Tracking Year</h3>
          <p>{currentYear}</p>
        </article>
      </section>

      <section className="panel-grid">
        <article className="panel">
          <h2>Add Daily Expense</h2>
          <form onSubmit={addExpense} className="stack-form">
            <label>
              Amount
              <input
                type="number"
                min="0.01"
                step="0.01"
                required
                value={expenseForm.amount}
                onChange={(e) => setExpenseForm((prev) => ({ ...prev, amount: e.target.value }))}
              />
            </label>
            <label>
              Category
              <select
                value={expenseForm.category}
                onChange={(e) => setExpenseForm((prev) => ({ ...prev, category: e.target.value }))}
              >
                {CATEGORIES.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Date
              <input
                type="date"
                required
                value={expenseForm.expense_date}
                onChange={(e) => setExpenseForm((prev) => ({ ...prev, expense_date: e.target.value }))}
              />
            </label>
            <label>
              Note
              <input
                type="text"
                value={expenseForm.description}
                onChange={(e) => setExpenseForm((prev) => ({ ...prev, description: e.target.value }))}
              />
            </label>
            <button type="submit">Save Expense</button>
          </form>
          {error ? <p className="error-text">{error}</p> : null}
        </article>

        <article className="panel">
          <h2>Monthly Trend ({currentYear})</h2>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={monthly}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total" fill="#0057ff" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="panel">
          <h2>Yearly Trend</h2>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={yearly}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="total" fill="#00a37a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="panel">
          <h2>Category Split</h2>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={categoryData} dataKey="total" nameKey="category" outerRadius={90} fill="#ff7a00" />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

      <section className="panel">
        <h2>Recent Expenses</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Date</th>
                <th>Category</th>
                <th>Description</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {expenses.slice().reverse().map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.expense_date}</td>
                  <td>{item.category}</td>
                  <td>{item.description || '-'}</td>
                  <td>${Number(item.amount).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
