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
import AvgCategoryBarChart from '../components/AvgCategoryBarChart';
import CategoryDonutChart from '../components/CategoryDonutChart';
import DailyExpenseChart from '../components/DailyExpenseChart';
import MonthYearFilter from '../components/MonthYearFilter';
import TopNavigation from '../components/TopNavigation';
import VendorDonutChart from '../components/VendorDonutChart';
import { apiRequest } from '../lib/api';

const MONTH_NAMES = ['January','February','March','April','May','June','July','August','September','October','November','December'];

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
  const [extracting, setExtracting] = useState(false);
  const [lastExtracted, setLastExtracted] = useState(null);
  const [successToast, setSuccessToast] = useState('');

  const [filterYear, setFilterYear] = useState(new Date().getFullYear());
  const [filterMonth, setFilterMonth] = useState(new Date().getMonth() + 1);
  const [dailyItems, setDailyItems] = useState([]);
  const [categoryMonthlyItems, setCategoryMonthlyItems] = useState([]);
  const [vendorMonthlyItems, setVendorMonthlyItems] = useState([]);
  const [categoryYearlyItems, setCategoryYearlyItems] = useState([]);
  const [dailyError, setDailyError] = useState('');
  const [categoryMonthlyError, setCategoryMonthlyError] = useState('');
  const [vendorMonthlyError, setVendorMonthlyError] = useState('');
  const [categoryYearlyError, setCategoryYearlyError] = useState('');
  const [dailyLoading, setDailyLoading] = useState(false);
  const [categoryMonthlyLoading, setCategoryMonthlyLoading] = useState(false);
  const [vendorMonthlyLoading, setVendorMonthlyLoading] = useState(false);
  const [categoryYearlyLoading, setCategoryYearlyLoading] = useState(false);

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

  async function loadChartData(year, month) {
    setDailyLoading(true);
    setCategoryMonthlyLoading(true);
    setVendorMonthlyLoading(true);
    setCategoryYearlyLoading(true);
    setDailyError('');
    setCategoryMonthlyError('');
    setVendorMonthlyError('');
    setCategoryYearlyError('');

    const [dailyResult, categoryMonthlyResult, vendorMonthlyResult, categoryYearlyResult] =
      await Promise.allSettled([
        apiRequest(`/expenses/summary/daily?year=${year}&month=${month}`),
        apiRequest(`/expenses/summary/categories-monthly?year=${year}&month=${month}`),
        apiRequest(`/expenses/summary/vendors-monthly?year=${year}&month=${month}`),
        apiRequest(`/expenses/summary/categories?year=${year}`),
      ]);

    if (dailyResult.status === 'fulfilled') {
      setDailyItems(dailyResult.value.items || []);
    } else {
      setDailyError(dailyResult.reason?.message || 'Failed to load daily data.');
    }
    setDailyLoading(false);

    if (categoryMonthlyResult.status === 'fulfilled') {
      setCategoryMonthlyItems(categoryMonthlyResult.value.items || []);
    } else {
      setCategoryMonthlyError(categoryMonthlyResult.reason?.message || 'Failed to load category data.');
    }
    setCategoryMonthlyLoading(false);

    if (vendorMonthlyResult.status === 'fulfilled') {
      setVendorMonthlyItems(vendorMonthlyResult.value.items || []);
    } else {
      setVendorMonthlyError(vendorMonthlyResult.reason?.message || 'Failed to load vendor data.');
    }
    setVendorMonthlyLoading(false);

    if (categoryYearlyResult.status === 'fulfilled') {
      setCategoryYearlyItems(categoryYearlyResult.value.items || []);
    } else {
      setCategoryYearlyError(categoryYearlyResult.reason?.message || 'Failed to load yearly category data.');
    }
    setCategoryYearlyLoading(false);
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadChartData(filterYear, filterMonth);
  }, [filterYear, filterMonth]);

  useEffect(() => {
    function handleExpenseCreated() {
      loadData();
      loadChartData(filterYear, filterMonth);
    }

    window.addEventListener('expense:created', handleExpenseCreated);
    return () => {
      window.removeEventListener('expense:created', handleExpenseCreated);
    };
  }, [filterYear, filterMonth]);

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

      const response = await apiRequest('/expenses/extract-and-create', {
        method: 'POST',
        body: formData,
      });

      setLastExtracted(response.extracted || null);
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

      <section className="panel-grid">
        <article className="panel" style={{ gridColumn: 'span 2' }}>
          <h2>Daily Expenses — {MONTH_NAMES[filterMonth - 1]} {filterYear}</h2>
          <MonthYearFilter
            year={filterYear} month={filterMonth}
            onYearChange={setFilterYear} onMonthChange={setFilterMonth}
          />
          <DailyExpenseChart items={dailyItems} loading={dailyLoading} error={dailyError} />
        </article>

        <article className="panel">
          <h2>Expenses by Category — {MONTH_NAMES[filterMonth - 1]} {filterYear}</h2>
          <CategoryDonutChart items={categoryMonthlyItems} loading={categoryMonthlyLoading} error={categoryMonthlyError} />
        </article>

        <article className="panel">
          <h2>Expenses by Vendor — {MONTH_NAMES[filterMonth - 1]} {filterYear}</h2>
          <VendorDonutChart items={vendorMonthlyItems} loading={vendorMonthlyLoading} error={vendorMonthlyError} />
        </article>

        <article className="panel" style={{ gridColumn: 'span 2' }}>
          <h2>Avg Expense by Category — {filterYear}</h2>
          <AvgCategoryBarChart items={categoryYearlyItems} loading={categoryYearlyLoading} error={categoryYearlyError} />
        </article>
      </section>

    </main>
  );
}
