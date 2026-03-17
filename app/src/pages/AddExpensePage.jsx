import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import TopNavigation from '../components/TopNavigation';
import { apiRequest } from '../lib/api';

const CATEGORIES = ['Food', 'Travel', 'Utilities', 'Shopping', 'Health', 'Other'];

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
  const [error, setError] = useState('');

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
    } catch (err) {
      setError(err.message);
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
      setAiInputText('');
      setAiImageFile(null);
      setCameraImageFile(null);
    } catch (err) {
      setError(err.message);
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
          {error ? <p className="error-text">{error}</p> : null}
        </article>
      </section>
    </main>
  );
}
