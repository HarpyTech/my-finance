
# Skip the Form: Building a Multi-Turn AI Expense Chatbot with FastAPI, React, and Gemini 2.5 Flash

Most expense trackers share the same UX story: open a drawer, fill out a form, click Save. It works, but the friction is real — especially on mobile, or when you just want to say *"spent 320 at Starbucks for a client meeting"* and move on.

This post walks through the complete, production-ready implementation I shipped for **FinTrackr** — a personal finance app — adding a floating AI chat widget that lets authenticated users log expenses in plain English. It covers the FastAPI backend, the React widget, multi-turn context design, and the error-recovery UX that makes it actually usable.

---

## The Goal

A fixed-position chat panel, available on every authenticated page, that:

- Accepts a single sentence like *"Paid ₹1,450 at Zomato on April 18 for team lunch"*
- Calls Google Gemini 2.5 Flash to extract structured fields
- Persists the expense in MongoDB with the same pipeline used by manual entry
- Recovers gracefully when the model can't find all required fields, asking only for what is missing
- Keeps conversation history across expenses without losing context

No third-party chat library. No WebSockets. Just React state, a new FastAPI endpoint, and a carefully designed error contract between the two.

---

## Architecture Overview

```
Browser (React 18 + Vite)
  └─ ExpenseChatWidget.jsx
       └─ POST /api/v1/expenses/chat-create
            └─ FastAPI route (expenses.py)
                 └─ extract_text_chat_expense_payload()   ← Gemini 2.5 Flash
                 └─ add_expense()                         ← MongoDB write
```

The new endpoint slots directly into the existing `expenses` router. No new service or database collection was needed — the chat path reuses the same `add_expense()` business logic and the same Gemini extraction pipeline, with a stricter validation layer on top.

---

## Backend: The Strict Chat Extraction Path

### A Custom Validation Error with Field Names

The existing image/text extraction path uses `_normalize_payload()`, which fills in sensible defaults when fields are missing. For chat that is the wrong behaviour — if the model couldn't figure out the vendor or the date, the user needs to supply it, not the system.

The solution was a dedicated exception class that carries the *list* of missing field names:

```python
class ExpenseExtractionValidationError(ValueError):
    """Raised when chat extraction is missing required fields."""

    def __init__(self, missing_fields: list[str]):
        self.missing_fields = missing_fields
        fields_text = ", ".join(missing_fields)
        super().__init__(
            "I couldn't confidently extract the "
            f"{fields_text}. Please include the merchant, amount, "
            "date, and what the expense was for."
        )
```

The human-readable message is designed to be forwarded directly to the frontend and then parsed back into individual field names — more on that below.

### `_normalize_text_chat_payload()` — Strict Mode

A new private normalizer validates all four required fields and raises `ExpenseExtractionValidationError` listing only those that failed:

```python
def _normalize_text_chat_payload(
    raw: dict[str, Any],
    text_input: str,
) -> dict[str, Any]:
    missing: list[str] = []

    amount = _to_float(raw.get("amount"))
    if not amount or amount <= 0:
        missing.append("amount")

    vendor = str(raw.get("vendor") or "").strip()[:128]
    if not vendor:
        missing.append("vendor")

    expense_date = _normalize_date(
        raw.get("expense_date") or raw.get("date"),
        default_to_today=False,   # key difference from the lenient path
    )
    if not expense_date:
        missing.append("expense_date")

    description = str(raw.get("description") or "").strip()[:255]
    if not description:
        missing.append("description")

    if missing:
        raise ExpenseExtractionValidationError(missing)

    # ... build and validate the final ExpenseCreate payload
```

Notice `default_to_today=False`. In the existing manual-entry path, a missing date silently becomes today. For the chat path that would silently log expenses on the wrong date — so `_normalize_date` gained an optional parameter that returns `None` instead, which the chat normalizer then treats as a missing field.

### The Endpoint

The FastAPI endpoint runs Gemini off the async event loop via `run_in_threadpool` (the SDK is synchronous), then re-uses the existing `add_expense()` service call:

```python
@router.post("/chat-create", status_code=201)
async def create_expense_from_chat(
    payload: ExpenseChatCreateRequest,
    user: str = Depends(get_current_user),
):
    check_session_expense_limit(user)

    extracted, used_llm_model = await run_in_threadpool(
        extract_text_chat_expense_payload,
        payload.message,
    )

    result = await run_in_threadpool(
        add_expense,
        username=user,
        amount=extracted["amount"],
        # ... other fields
        input_type="text",
        llm_model=used_llm_model,
        line_items=[],
    )

    return {
        "expense": result,
        "extracted": extracted,
        "llm_model": used_llm_model,
        "message": (
            f"Saved {result['vendor']} for {result['amount']:.2f} "
            f"on {result['expense_date']}."
        ),
    }
```

`ExpenseExtractionValidationError` maps to HTTP 422. All other `ValueError` → 400. `SessionExpenseLimitError` → 429. `RuntimeError` (Gemini config issues) → 503.

The input model enforces length bounds at the Pydantic layer:

```python
class ExpenseChatCreateRequest(BaseModel):
    message: str = Field(min_length=5, max_length=1000)
```

---

## Frontend: The `ExpenseChatWidget`

The widget is a single self-contained React component mounted once inside `ProtectedRoute` in `App.jsx`. It does not depend on any chat library — all state is plain `useState`.

### The Multi-Turn Context Problem

The most interesting design challenge: the first message from a user might only contain partial information. The follow-up provides the rest. But the API endpoint accepts a single `message` string — it doesn't maintain session state.

The solution is to accumulate the prior message text in a React state variable `pendingExpenseContext` and compose both parts client-side before the next API call:

```javascript
const composedMessage = pendingExpenseContext
  ? `${pendingExpenseContext}\n${latestUserMessage}`
  : latestUserMessage;
```

When the server returns a 422:

```javascript
const missingFields = parseMissingFields(err.message || '');
if (missingFields.length > 0) {
  setPendingExpenseContext(composedMessage);   // accumulate
  setPendingMissingFields(missingFields);
  setMessages((prev) => [
    ...prev,
    createEntry(
      'assistant',
      `Need only these missing details: ${missingFields.join(', ')}.`,
      'missing'
    ),
  ]);
}
```

On the next user turn the composed message carries both turns together. Gemini sees all the context at once and can extract a complete record. This avoids any server-side session state while still giving the user a conversational feel.

### Parsing Missing Fields from the Error String

The error message from the server has a predictable shape:

> *"I couldn't confidently extract the **amount, vendor**. Please include…"*

`parseMissingFields()` extracts the field names using simple string slicing — no regex, no external parser:

```javascript
function parseMissingFields(message) {
  const lower = String(message).toLowerCase();
  const startToken = 'extract the ';
  const endToken = '. please include';
  const startIndex = lower.indexOf(startToken);
  const endIndex = lower.indexOf(endToken);

  if (startIndex === -1 || endIndex === -1) return [];

  return lower
    .slice(startIndex + startToken.length, endIndex)
    .replace(/\sand\s/g, ',')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}
```

Those field names then drive both the textarea label and the placeholder text, so the user sees exactly what is still needed — not a generic error.

### Cross-Page Refresh Without a Global Store

After a successful save the widget fires a browser custom event:

```javascript
window.dispatchEvent(
  new CustomEvent('expense:created', { detail: response.expense })
);
```

Each page (`DashboardPage`, `ReportPage`, `AddExpensePage`) listens for it and calls its own data-reload function:

```javascript
useEffect(() => {
  function handleCreated() { loadData(); }
  window.addEventListener('expense:created', handleCreated);
  return () => window.removeEventListener('expense:created', handleCreated);
}, []);
```

No context, no Redux, no prop drilling. A 5-line pattern that keeps every page in sync.

### The Launcher FAB

The trigger button is a 58×58 circular FAB with an inline SVG bot icon — no icon font, no external dependency, no network request:

```jsx
<svg className="expense-chat-launcher-icon" viewBox="0 0 24 24" aria-hidden="true">
  <rect x="5" y="7" width="14" height="10" rx="3" />
  <circle cx="9.5" cy="12" r="1.2" />
  <circle cx="14.5" cy="12" r="1.2" />
  <path d="M9 15.3c1 .7 2 .9 3 .9s2-.2 3-.9" />
  <path d="M12 7V4" />
  <circle cx="12" cy="3" r="1" />
</svg>
```

The button carries `aria-expanded` and `aria-controls` pointing at the panel, so screen readers announce the toggle state correctly.

---

## Tricky Parts Worth Calling Out

**`run_in_threadpool` for synchronous SDK calls.** FastAPI's async routes should never block the event loop. The Google Generative AI SDK is synchronous, so every Gemini call goes through `await run_in_threadpool(...)`. This is the correct pattern — not `asyncio.to_thread`, not a background task.

**Gemini JSON repair loop.** The extraction service already had a built-in retry: if the model returns malformed JSON the service sends it back to Gemini with an explicit repair prompt and retries up to `_MAX_JSON_RETRIES = 2` times. The chat path inherits this for free because it goes through the same `_generate_and_parse_json_with_retries()` function.

**`default_to_today` on `_normalize_date`.** Adding a single optional boolean parameter to an existing utility function was enough to split lenient from strict behaviour without duplicating logic. Small change, meaningful consequence.

**Panel min-height.** When the chat body has zero messages it previously collapsed to nothing, which made the panel look broken. A single CSS rule fixed it: `min-height: 170px` on `.expense-chat-body`.

---

## What the Full Flow Looks Like

```
User:       "Zomato, team lunch"
Bot (422):  "Need only these missing details: amount, expense_date."

User:       "1200, April 19"
Bot (201):  "Saved Zomato for 1200.00 on 2026-04-19."
Dashboard auto-refreshes via expense:created event.
```

Two turns. No form. The composed message on the second call is:

```
Zomato, team lunch
1200, April 19
```

Gemini sees the full context and extracts a complete, valid record.

---

## What Was Not Done (and Why)

- **No server-side session.** Accumulating context client-side is simpler and stateless. A server-side conversation store would add latency and a new persistence concern for no user-visible benefit.
- **No streaming response.** Gemini output for a structured JSON extraction is short. Streaming would add complexity without improving perceived speed.
- **No dedicated chat database collection.** All saved expenses land in the same `expenses` collection with `input_type="text"`, making reporting and queries uniform.

---

## Key Takeaways

1. **Reuse extraction infrastructure.** The chat endpoint shares the Gemini model, the JSON repair loop, and the `add_expense()` service. The only new code is the stricter normalizer and the custom exception.
2. **Encode field names in the error message.** Making the validation error message machine-parseable (while still being human-readable) lets the frontend give targeted follow-up prompts without a dedicated field-status API.
3. **Compose context client-side for multi-turn on a stateless API.** Concatenating prior turns in the request body is simple, debuggable, and adds no server state.
4. **Custom DOM events decouple the widget from page logic.** The widget has no knowledge of which page is currently visible. Each page owns its own refresh handler.

---

## Suggested Tags

`fastapi` · `react` · `gemini` · `ai` · `llm` · `expense-tracker` · `python` · `full-stack` · `chatbot` · `google-generativeai` · `vite` · `mongodb` · `ux` · `javascript`
