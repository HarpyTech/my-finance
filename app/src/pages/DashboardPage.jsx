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
import TopNavigation from '../components/TopNavigation';
import { apiRequest } from '../lib/api';

const LLM_OPTIONS = [
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'gemini-3-flash-preview',
  'gemini-3.1-pro-preview',
];

const inrCurrencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});

function formatInr(value) {
  return inrCurrencyFormatter.format(Number(value || 0));
}

export default function DashboardPage() {
  const { session, logout } = useAuth();
  const navigate = useNavigate();
  const isMobileDevice = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);

  const [expenses, setExpenses] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [yearly, setYearly] = useState([]);
  const [categoryData, setCategoryData] = useState([]);
  const [error, setError] = useState('');
  const [cameraImageFile, setCameraImageFile] = useState(null);
  const [cameraPreviewUrl, setCameraPreviewUrl] = useState('');
  const [selectedLlmModel, setSelectedLlmModel] = useState('gemini-3-flash-preview');
  const [extracting, setExtracting] = useState(false);
  const [lastExtracted, setLastExtracted] = useState(null);
  const [lastUsedLlmModel, setLastUsedLlmModel] = useState('');
  const [successToast, setSuccessToast] = useState('');

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

  useEffect(() => {
    if (!cameraImageFile) {
      setCameraPreviewUrl('');
      return undefined;
    }

    const nextPreviewUrl = URL.createObjectURL(cameraImageFile);
    setCameraPreviewUrl(nextPreviewUrl);

    return () => {
      URL.revokeObjectURL(nextPreviewUrl);
    };
  }, [cameraImageFile]);

  useEffect(() => {
    if (!successToast) {
      return undefined;
    }

    const timeoutId = window.setTimeout(() => {
      setSuccessToast('');
    }, 2600);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [successToast]);

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  async function addExpenseFromCamera(event) {
    event.preventDefault();
    setError('');

    if (!cameraImageFile) {
      setError('Capture a receipt image to add an expense from the dashboard.');
      return;
    }

    try {
      setExtracting(true);
      const formData = new FormData();
      formData.append('image', cameraImageFile);
      formData.append('input_type', 'camera');
      formData.append('llm_model', selectedLlmModel);

      const response = await apiRequest('/expenses/extract-and-create', {
        method: 'POST',
        body: formData,
      });

      setLastExtracted(response.extracted || null);
      setLastUsedLlmModel(response.llm_model || selectedLlmModel);
      setCameraImageFile(null);
      setSuccessToast('Expense captured and saved successfully.');
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

  return (
    <main className="dashboard-layout">
      {successToast ? (
        <div className="success-toast" role="status" aria-live="polite">
          {successToast}
        </div>
      ) : null}

      <header className="dashboard-header">
        <div className="dashboard-header-title">
          <img src="/assets/name_logo.svg" alt="FinTrackr" className="dashboard-logo" />
          <h1>Dashboard</h1>
        </div>
        <div className="header-actions">
          <TopNavigation />
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <section className="stats-grid">
        <article className="stat-card">
          <h3>Total Expenses</h3>
          <p>{formatInr(totalSpend)}</p>
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
          <h2>Quick Add Expense</h2>
          <p className="help-text dashboard-card-copy">
            Use fast receipt capture here, or open the full Add Expense page for manual and text-based entry.
          </p>
          {isMobileDevice ? (
            <form onSubmit={addExpenseFromCamera} className="stack-form quick-capture-form">
              <label>
                AI Model
                <select
                  value={selectedLlmModel}
                  onChange={(e) => setSelectedLlmModel(e.target.value)}
                >
                  {LLM_OPTIONS.map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Capture Receipt With Camera
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={(e) => setCameraImageFile(e.target.files?.[0] || null)}
                />
              </label>
              {cameraPreviewUrl ? (
                <div className="camera-preview-card">
                  <img
                    src={cameraPreviewUrl}
                    alt="Captured receipt preview"
                    className="camera-preview-image"
                  />
                  <div className="camera-preview-actions">
                    <span className="help-text">Receipt preview ready for submission.</span>
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => setCameraImageFile(null)}
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ) : null}
              <button type="submit" disabled={extracting}>
                {extracting ? 'Extracting...' : 'Capture + Save Expense'}
              </button>
            </form>
          ) : (
            <div className="dashboard-cta-block">
              <p className="help-text">
                Camera capture opens directly on mobile. Use the Add Expense page on desktop for full entry options.
              </p>
              <button type="button" onClick={() => navigate('/add-expense')}>
                Open Add Expense
              </button>
            </div>
          )}

          {lastExtracted ? (
            <div className="extract-output">
              <h3>Last Extracted JSON</h3>
              {lastUsedLlmModel ? <p>Model Used: {lastUsedLlmModel}</p> : null}
              <pre>{JSON.stringify(lastExtracted, null, 2)}</pre>
            </div>
          ) : null}
          {error ? <p className="error-text">{error}</p> : null}
        </article>

        <article className="panel">
          <h2>Monthly Trend ({currentYear})</h2>
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={monthly}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={formatInr} />
                <Tooltip formatter={(value) => formatInr(value)} />
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
                <YAxis tickFormatter={formatInr} />
                <Tooltip formatter={(value) => formatInr(value)} />
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
                <Tooltip formatter={(value) => formatInr(value)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </article>
      </section>

    </main>
  );
}
