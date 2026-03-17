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
  const isMobileDevice = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);

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
  const [aiInputText, setAiInputText] = useState('');
  const [aiImageFile, setAiImageFile] = useState(null);
  const [cameraImageFile, setCameraImageFile] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [lastExtracted, setLastExtracted] = useState(null);

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
          input_type: 'manual',
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

  async function addExpenseFromAi(event) {
    event.preventDefault();
    setError('');

    const selectedImageFile = cameraImageFile || aiImageFile;

    if (!aiInputText.trim() && !selectedImageFile) {
      setError('Provide text input or upload an image for extraction.');
      return;
    }

    try {
      setExtracting(true);
      const formData = new FormData();
      const derivedInputType = getDerivedInputType({
        textInput: aiInputText,
        imageFile: aiImageFile,
        cameraFile: cameraImageFile,
      });

      if (aiInputText.trim()) {
        formData.append('text_input', aiInputText.trim());
      }
      if (selectedImageFile) {
        formData.append('image', selectedImageFile);
      }
      formData.append('input_type', derivedInputType);

      const response = await apiRequest('/expenses/extract-and-create', {
        method: 'POST',
        body: formData,
      });

      setLastExtracted(response.extracted || null);
      setAiInputText('');
      setAiImageFile(null);
      setCameraImageFile(null);
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setExtracting(false);
    }
  }

  const totalSpend = useMemo(
    () => expenses.reduce((sum, item) => sum + Number(item.amount || 0), 0),
    [expenses]
  );

  function getDerivedInputType({ textInput, imageFile, cameraFile }) {
    const hasText = Boolean(textInput.trim());
    const hasImage = Boolean(imageFile);
    const hasCamera = Boolean(cameraFile);

    if (hasText && (hasImage || hasCamera)) {
      return 'mixed';
    }
    if (hasCamera) {
      return 'camera';
    }
    if (hasImage) {
      return 'image';
    }
    return 'text';
  }

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
          <h2>Add Expense From Text or Image</h2>
          <form onSubmit={addExpenseFromAi} className="stack-form">
            <label>
              Text Input
              <textarea
                rows={4}
                placeholder="Paste receipt text or describe the expense"
                value={aiInputText}
                onChange={(e) => setAiInputText(e.target.value)}
              />
            </label>
            <label>
              Receipt Image
              <input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  setAiImageFile(e.target.files?.[0] || null);
                  setCameraImageFile(null);
                }}
              />
            </label>
            {isMobileDevice ? (
              <label>
                Capture With Camera
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={(e) => {
                    setCameraImageFile(e.target.files?.[0] || null);
                    setAiImageFile(null);
                  }}
                />
              </label>
            ) : null}
            <p className="help-text">
              {isMobileDevice
                ? 'On mobile you can either upload an image or open the camera directly.'
                : 'Upload a receipt image or paste text for AI extraction.'}
            </p>
            <button type="submit" disabled={extracting}>
              {extracting ? 'Extracting...' : 'Extract + Save Expense'}
            </button>
          </form>
          {lastExtracted ? (
            <div className="extract-output">
              <h3>Last Extracted JSON</h3>
              <pre>{JSON.stringify(lastExtracted, null, 2)}</pre>
            </div>
          ) : null}
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
                <th>Input Type</th>
                <th>Vendor</th>
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
                  <td>{item.input_type || 'manual'}</td>
                  <td>{item.vendor || '-'}</td>
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
