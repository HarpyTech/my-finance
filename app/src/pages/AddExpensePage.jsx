import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import TopNavigation from '../components/TopNavigation';
import { apiRequest } from '../lib/api';

const CATEGORIES = ['Food', 'Travel', 'Utilities', 'Shopping', 'Health', 'Other'];
const SUPPORT_EMAIL = 'support@harpytechco.in';
const SUPPORT_SUBJECT = 'Request to increase expense limit';
const SUPPORT_BODY_TEMPLATE = [
  'Hi Customer Support Team,',
  '',
  'I have reached the 10 expense limit on my account and request a limit increase.',
  '',
  'Account email: ',
  'Requested new limit: ',
  'Reason: ',
  '',
  'Thank you,',
].join('\n');
const SUPPORT_MAILTO_LINK =
  `mailto:${SUPPORT_EMAIL}` +
  `?subject=${encodeURIComponent(SUPPORT_SUBJECT)}` +
  `&body=${encodeURIComponent(SUPPORT_BODY_TEMPLATE)}`;

export default function AddExpensePage() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const isMobileDevice = /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);

  const [expenseForm, setExpenseForm] = useState({
    amount: '',
    category: CATEGORIES[0],
    description: '',
    expense_date: new Date().toISOString().slice(0, 10),
  });
  const [aiInputText, setAiInputText] = useState('');
  const [aiImageFile, setAiImageFile] = useState(null);
  const [cameraImageFile, setCameraImageFile] = useState(null);
  const [extracting, setExtracting] = useState(false);
  const [lastExtracted, setLastExtracted] = useState(null);
  const [lastUsedLlmModel, setLastUsedLlmModel] = useState('');
  const [error, setError] = useState('');
  const [sessionLimitReached, setSessionLimitReached] = useState(false);

  useEffect(() => {
    syncExpenseLimitState();
  }, []);

  async function syncExpenseLimitState() {
    try {
      const response = await apiRequest('/expenses/limit-status');
      setSessionLimitReached(Boolean(response.reached));
    } catch {
      // Keep this non-blocking: user can still try submit and backend enforces limit.
    }
  }

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

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
      await syncExpenseLimitState();
    } catch (err) {
      if (err.status === 429) {
        setSessionLimitReached(true);
      } else {
        setError(err.message);
      }
    }
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
      setLastUsedLlmModel(response.llm_model || 'gemini-2.5-flash');
      setAiInputText('');
      setAiImageFile(null);
      setCameraImageFile(null);
      await syncExpenseLimitState();
    } catch (err) {
      if (err.status === 429) {
        setSessionLimitReached(true);
      } else {
        setError(err.message);
      }
    } finally {
      setExtracting(false);
    }
  }

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
          <h1>Add Expense</h1>
        </div>
        <div className="header-actions">
          <TopNavigation />
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>

      {sessionLimitReached && (
        <div className="session-limit-banner" role="alert">
          <strong>Expense limit reached.</strong> You have added the maximum of{' '}
          10 expenses allowed on your plan.{' '}
          <a href={SUPPORT_MAILTO_LINK}>Contact our customer team</a> to
          upgrade your plan or get help.
        </div>
      )}

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
            <button type="submit" disabled={sessionLimitReached}>Save Expense</button>
          </form>
        </article>

        <article className="panel">
          <h2>Add Expense From Text or Image</h2>
          <form onSubmit={addExpenseFromAi} className="stack-form">
            {/* <p className="help-text">AI model: gemini-2.5-flash</p> */}
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
            <button type="submit" disabled={extracting || sessionLimitReached}>
              {extracting ? 'Extracting...' : 'Extract + Save Expense'}
            </button>
          </form>
          {lastExtracted ? (
            <div className="extract-output">
              <h3>Last Extracted JSON</h3>
              {/* {lastUsedLlmModel ? <p>Model Used: {lastUsedLlmModel}</p> : null} */}
              <pre>{JSON.stringify(lastExtracted, null, 2)}</pre>
            </div>
          ) : null}
          {error ? <p className="error-text">{error}</p> : null}
        </article>
      </section>
    </main>
  );
}
