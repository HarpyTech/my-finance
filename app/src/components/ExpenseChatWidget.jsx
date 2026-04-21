import { useEffect, useRef, useState } from 'react';
import { apiRequest } from '../lib/api';

const STARTER_MESSAGE =
  'Describe an expense in one sentence. Include the merchant, amount, date, and what it was for.';
const EXAMPLE_MESSAGE =
  'Example: Paid 320 at Starbucks on 2026-04-20 for coffee with client.';

function createEntry(role, text, tone = 'default') {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    role,
    text,
    tone,
  };
}

function parseMissingFields(message) {
  if (!message) {
    return [];
  }

  const lower = String(message).toLowerCase();
  const startToken = 'extract the ';
  const endToken = '. please include';
  const startIndex = lower.indexOf(startToken);
  const endIndex = lower.indexOf(endToken);

  if (startIndex === -1 || endIndex === -1 || endIndex <= startIndex) {
    return [];
  }

  const missingSegment = lower
    .slice(startIndex + startToken.length, endIndex)
    .replace(/\./g, '')
    .trim();

  if (!missingSegment) {
    return [];
  }

  return missingSegment
    .replace(/\sand\s/g, ',')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

export default function ExpenseChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [messages, setMessages] = useState([
    createEntry('assistant', STARTER_MESSAGE),
    createEntry('assistant', EXAMPLE_MESSAGE),
  ]);
  const [pendingExpenseContext, setPendingExpenseContext] = useState('');
  const [pendingMissingFields, setPendingMissingFields] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [isOpen, messages]);

  async function handleSubmit(event) {
    event.preventDefault();
    const latestUserMessage = draft.trim();
    if (!latestUserMessage || submitting) {
      return;
    }

    const composedMessage = pendingExpenseContext
      ? `${pendingExpenseContext}\n${latestUserMessage}`
      : latestUserMessage;

    setMessages((prev) => [...prev, createEntry('user', latestUserMessage)]);
    setDraft('');
    setSubmitting(true);

    try {
      const response = await apiRequest('/expenses/chat-create', {
        method: 'POST',
        body: JSON.stringify({ message: composedMessage }),
      });

      setMessages((prev) => [
        ...prev,
        createEntry('assistant', response.message || 'Expense saved successfully.', 'success'),
      ]);
      setPendingExpenseContext('');
      setPendingMissingFields([]);

      window.dispatchEvent(
        new CustomEvent('expense:created', {
          detail: response.expense,
        })
      );
    } catch (err) {
      const missingFields = parseMissingFields(err.message || '');
      if (missingFields.length > 0) {
        setPendingExpenseContext(composedMessage);
        setPendingMissingFields(missingFields);
        setMessages((prev) => [
          ...prev,
          createEntry(
            'assistant',
            `Need only these missing details: ${missingFields.join(', ')}.`,
            'missing'
          ),
        ]);
      } else {
        setPendingExpenseContext('');
        setPendingMissingFields([]);
        setMessages((prev) => [
          ...prev,
          createEntry('assistant', err.message || 'Unable to save that expense right now.', 'error'),
        ]);
      }
    } finally {
      setSubmitting(false);
    }
  }

  function handleStartNewExpense() {
    setPendingExpenseContext('');
    setPendingMissingFields([]);
    setDraft('');
    setMessages((prev) => [
      ...prev,
      createEntry('assistant', 'Ready for a new expense. Share the next one in one sentence.'),
    ]);
  }

  return (
    <div className="expense-chat-widget">
      {isOpen ? (
        <section id="expense-chat-panel" className="expense-chat-panel" aria-label="Expense chat assistant">
          <header className="expense-chat-header">
            <div>
              <h2>Expense Chat</h2>
              <p>Log an expense from plain text.</p>
            </div>
            <button
              type="button"
              className="expense-chat-close"
              onClick={() => setIsOpen(false)}
              aria-label="Close expense chat"
            >
              Close
            </button>
          </header>

          <div className="expense-chat-body" ref={scrollRef}>
            {messages.map((entry) => (
              <div
                key={entry.id}
                className={
                  entry.role === 'user'
                    ? 'expense-chat-message user'
                    : `expense-chat-message assistant ${entry.tone}`
                }
              >
                <p>{entry.text}</p>
              </div>
            ))}
          </div>

          <form className="expense-chat-form" onSubmit={handleSubmit}>
            <label className="expense-chat-label">
              {pendingMissingFields.length > 0
                ? `Reply with only: ${pendingMissingFields.join(', ')}`
                : 'Describe the expense'}
              <textarea
                rows={3}
                placeholder={
                  pendingMissingFields.length > 0
                    ? `Provide only ${pendingMissingFields.join(', ')}.`
                    : 'Paid 320 at Starbucks on 2026-04-20 for coffee with client.'
                }
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
              />
            </label>
            <div className="expense-chat-actions">
              <button
                type="button"
                className="expense-chat-reset"
                onClick={handleStartNewExpense}
                disabled={submitting}
              >
                Start new expense
              </button>
            <button type="submit" disabled={submitting || !draft.trim()}>
              {submitting ? 'Saving...' : 'Send'}
            </button>
            </div>
          </form>
        </section>
      ) : null}

      <button
        type="button"
        className="expense-chat-launcher"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-expanded={isOpen}
        aria-controls="expense-chat-panel"
      >
        Chat Expense
      </button>
    </div>
  );
}