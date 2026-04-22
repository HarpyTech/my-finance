import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import TopNavigation from '../components/TopNavigation';
import { apiRequest } from '../lib/api';

const inrCurrencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});

function formatInr(value) {
  return inrCurrencyFormatter.format(Number(value || 0));
}

export default function ReportPage() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const [expenses, setExpenses] = useState([]);
  const [historyView, setHistoryView] = useState('expense');
  const [historyFilters, setHistoryFilters] = useState({
    startDate: '',
    endDate: '',
    category: 'all',
  });
  const [error, setError] = useState('');

  useEffect(() => {
    loadExpenses();
  }, []);

  useEffect(() => {
    function handleExpenseCreated() {
      loadExpenses();
    }

    window.addEventListener('expense:created', handleExpenseCreated);
    return () => {
      window.removeEventListener('expense:created', handleExpenseCreated);
    };
  }, []);

  async function loadExpenses() {
    try {
      const response = await apiRequest('/expenses');
      setExpenses(response.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  const historyCategories = useMemo(() => {
    const values = new Set(
      expenses
        .map((item) => String(item.category || '').trim().toLowerCase())
        .filter(Boolean)
    );

    return ['all', ...Array.from(values).sort()];
  }, [expenses]);

  const filteredExpenses = useMemo(() => {
    return expenses.filter((item) => {
      const rawDate = String(item.expense_date || '');
      const dateOnly = rawDate.slice(0, 10);
      const category = String(item.category || '').trim().toLowerCase();

      if (historyFilters.startDate && dateOnly < historyFilters.startDate) {
        return false;
      }

      if (historyFilters.endDate && dateOnly > historyFilters.endDate) {
        return false;
      }

      if (
        historyFilters.category !== 'all' &&
        category !== historyFilters.category
      ) {
        return false;
      }

      return true;
    });
  }, [expenses, historyFilters]);

  const filteredLineItems = useMemo(() => {
    return filteredExpenses.flatMap((expense) => {
      const items = Array.isArray(expense.line_items) ? expense.line_items : [];

      if (items.length === 0) {
        return [];
      }

      return items.map((lineItem, index) => ({
        id: `${expense.id}-${index}`,
        expenseId: expense.id,
        expenseDate: String(expense.expense_date || '').slice(0, 10),
        category: expense.category,
        vendor: expense.vendor,
        inputType: expense.input_type || 'manual',
        itemName: lineItem.name,
        quantity: Number(lineItem.quantity || 0),
        unitPrice: Number(lineItem.unit_price || 0),
        total: Number(lineItem.total || 0),
      }));
    });
  }, [filteredExpenses]);

  const filteredSpend = useMemo(
    () => filteredExpenses.reduce((sum, item) => sum + Number(item.amount || 0), 0),
    [filteredExpenses]
  );

  function toTitleCase(value) {
    return String(value || '')
      .split(/[_\s-]+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  return (
    <main className="dashboard-layout">
      <header className="dashboard-header">
        <div>
          <h1>Expense Reports</h1>
        </div>
        <div className="header-actions">
          <TopNavigation />
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <section className="panel">
        <div className="report-header">
          <div>
            <h2>Historical Expense Report</h2>
            <p className="help-text">
              Filter by date and category, then switch between expense-level and line-item views.
            </p>
          </div>
          <div
            className="report-toggle"
            role="tablist"
            aria-label="Historical report view selector"
          >
            <button
              type="button"
              className={historyView === 'expense' ? 'toggle-button active' : 'toggle-button'}
              onClick={() => setHistoryView('expense')}
            >
              View By Expense
            </button>
            <button
              type="button"
              className={historyView === 'line_items' ? 'toggle-button active' : 'toggle-button'}
              onClick={() => setHistoryView('line_items')}
            >
              View By Line Items
            </button>
          </div>
        </div>

        <div className="report-filters">
          <label>
            Start Date
            <input
              type="date"
              value={historyFilters.startDate}
              onChange={(e) => setHistoryFilters((prev) => ({ ...prev, startDate: e.target.value }))}
            />
          </label>
          <label>
            End Date
            <input
              type="date"
              value={historyFilters.endDate}
              onChange={(e) => setHistoryFilters((prev) => ({ ...prev, endDate: e.target.value }))}
            />
          </label>
          <label>
            Category
            <select
              value={historyFilters.category}
              onChange={(e) => setHistoryFilters((prev) => ({ ...prev, category: e.target.value }))}
            >
              {historyCategories.map((category) => (
                <option key={category} value={category}>
                  {category === 'all' ? 'All Categories' : toTitleCase(category)}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="report-summary">
          <span>{filteredExpenses.length} expenses</span>
          <span>{filteredLineItems.length} line items</span>
          <span>{formatInr(filteredSpend)} filtered spend</span>
        </div>

        {error ? <p className="error-text">{error}</p> : null}

        <div className="table-wrap">
          {historyView === 'expense' ? (
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Input Type</th>
                  <th>Invoice No.</th>
                  <th>Vendor</th>
                  <th>Description</th>
                  <th>Line Items</th>
                  <th>Amount</th>
                </tr>
              </thead>
              <tbody>
                {filteredExpenses.length > 0 ? (
                  filteredExpenses.map((item) => (
                    <tr key={item.id}>
                      <td>{item.id}</td>
                      <td>{String(item.expense_date || '').slice(0, 10)}</td>
                      <td>{toTitleCase(item.category)}</td>
                      <td>{toTitleCase(item.input_type || 'manual')}</td>
                      <td>{item.invoice_number || '-'}</td>
                      <td>{item.vendor || '-'}</td>
                      <td>{item.description || '-'}</td>
                      <td>{item.line_items?.length || 0}</td>
                      <td>{formatInr(item.amount)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="empty-state-cell">
                      No historical expenses matched the selected filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Expense ID</th>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Vendor</th>
                  <th>Input Type</th>
                  <th>Item</th>
                  <th>Qty</th>
                  <th>Unit Price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {filteredLineItems.length > 0 ? (
                  filteredLineItems.map((item) => (
                    <tr key={item.id}>
                      <td>{item.expenseId}</td>
                      <td>{item.expenseDate}</td>
                      <td>{toTitleCase(item.category)}</td>
                      <td>{item.vendor || '-'}</td>
                      <td>{toTitleCase(item.inputType)}</td>
                      <td>{item.itemName || '-'}</td>
                      <td>{item.quantity}</td>
                      <td>{formatInr(item.unitPrice)}</td>
                      <td>{formatInr(item.total)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="empty-state-cell">
                      No line items matched the selected filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </main>
  );
}
