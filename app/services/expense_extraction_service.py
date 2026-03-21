from __future__ import annotations

from datetime import date, datetime
import json
import logging
import re
from typing import Any

import google.generativeai as genai
from pydantic import ValidationError

from app.core.config import settings
from app.models.expense import ExpenseCreate

logger = logging.getLogger(__name__)

_ALLOWED_BILL_TYPES = {"grocery", "restaurant", "service", "utility", "other"}
_CODE_FENCE_PATTERN = re.compile(r"```(?:json)?|```", re.IGNORECASE)
_JSON_OBJECT_PATTERN = re.compile(r"\{[\s\S]*\}")
_MAX_OUTPUT_TOKENS = 512
_gemini_model: genai.GenerativeModel | None = None


PROMPT_TEMPLATE = """
Extract expense details and return ONLY valid JSON.

Required JSON shape:
{
  "amount": number,
  "category": string,
  "bill_type": "grocery" | "restaurant" | "service" | "utility" | "other",
    "invoice_number": string,
  "vendor": string,
  "description": string,
  "expense_date": "YYYY-MM-DD",
    "tax_details": {
        "subtotal": number,
        "tax": number,
        "cgst": number,
        "sgst": number,
        "igst": number,
        "vat": number,
        "service_tax": number,
        "cess": number,
        "tip": number,
        "discount": number,
        "total_tax": number
    },
  "line_items": [
    {
      "name": string,
      "quantity": number,
      "unit_price": number,
      "total": number
    }
  ]
}

Rules:
- Return JSON only, no markdown.
- If a field is unknown, use reasonable defaults.
- amount must reflect the final paid total.
- line_items can be an empty list.
- expense_date must be a valid date in YYYY-MM-DD.
- Keep all tax_details numeric (use 0 when missing).
""".strip()


def extract_expense_payload(
    text_input: str | None,
    image_bytes: bytes | None,
    image_mime_type: str | None,
) -> dict[str, Any]:
    """Extract and normalize expense payload from text and/or image."""
    if not text_input and not image_bytes:
        raise ValueError("Provide either text_input or an image")

    model = _get_model()

    prompt_parts: list[Any] = [PROMPT_TEMPLATE]
    if text_input:
        prompt_parts.append(f"Source text:\n{text_input.strip()}")

    if image_bytes:
        if image_mime_type and not image_mime_type.startswith("image/"):
            raise ValueError("Only image uploads are supported")
        prompt_parts.append(
            {
                "mime_type": image_mime_type or "image/jpeg",
                "data": image_bytes,
            }
        )

    logger.info("Calling Gemini model for expense extraction")
    response = model.generate_content(
        prompt_parts,
        generation_config=genai.GenerationConfig(max_output_tokens=_MAX_OUTPUT_TOKENS),
    )
    raw_text = (getattr(response, "text", "") or "").strip()

    if not raw_text:
        raise RuntimeError("Gemini returned an empty response")

    parsed = _parse_json_from_model(raw_text)
    normalized = _normalize_payload(parsed, text_input=text_input)

    logger.info("Expense extraction completed successfully")
    return normalized


def _get_model() -> genai.GenerativeModel:
    """Lazily initialize Gemini model with configured credentials."""
    global _gemini_model

    if _gemini_model is not None:
        return _gemini_model

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    genai.configure(api_key=settings.GEMINI_API_KEY)
    _gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
    return _gemini_model


def _parse_json_from_model(raw_text: str) -> dict[str, Any]:
    """Extract JSON object from model output text."""
    cleaned = _CODE_FENCE_PATTERN.sub("", raw_text).strip()

    if cleaned.startswith("{") and cleaned.endswith("}"):
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Fall through to regex search
            pass

    match = _JSON_OBJECT_PATTERN.search(cleaned)
    if not match:
        logger.error("Could not find a JSON object in model output. Raw text: %s", raw_text)
        raise RuntimeError("Could not find a JSON object in model output")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.error(
            "Found a JSON-like object, but failed to parse. Raw text: %s",
            raw_text,
            exc_info=True,
        )
        raise RuntimeError("Could not parse JSON object from model output") from exc


def _normalize_payload(
    raw: dict[str, Any],
    text_input: str | None,
) -> dict[str, Any]:
    """Normalize model output into validated ExpenseCreate payload."""
    line_items = _normalize_line_items(raw.get("line_items") or raw.get("items") or [])

    amount = _to_float(raw.get("amount"))
    if amount is None:
        amount = _to_float(raw.get("total"))
    if (amount is None or amount <= 0) and line_items:
        amount = round(sum(item["total"] for item in line_items), 2)
    if amount is None or amount <= 0:
        raise RuntimeError("Could not extract a valid expense amount")

    category = str(raw.get("category") or "other").strip().lower()
    if len(category) < 2:
        category = "other"

    bill_type = str(raw.get("bill_type") or "other").strip().lower()
    if bill_type not in _ALLOWED_BILL_TYPES:
        bill_type = "other"

    vendor = str(raw.get("vendor") or "").strip()[:128]
    description = str(raw.get("description") or "").strip()
    if not description and text_input:
        description = text_input.strip()[:255]
    description = description[:255]

    invoice_number = _normalize_invoice_number(
        raw,
        text_input=text_input,
        description=description,
    )

    expense_date = _normalize_date(raw.get("expense_date") or raw.get("date"))
    tax_details = _normalize_tax_details(raw)

    payload = {
        "amount": round(amount, 2),
        "category": category,
        "bill_type": bill_type,
        "invoice_number": invoice_number,
        "vendor": vendor,
        "description": description,
        "expense_date": expense_date.isoformat(),
        "tax_details": tax_details,
        "line_items": line_items,
    }

    try:
        # Validate final payload against API schema constraints.
        return ExpenseCreate(**payload).model_dump(mode="json")
    except ValidationError as exc:
        raise RuntimeError("Extracted data failed validation") from exc


def _normalize_line_items(raw_items: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []

    normalized: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name") or "item").strip()[:128]
        quantity = _to_float(item.get("quantity")) or 1.0
        unit_price = _to_float(item.get("unit_price"))
        if unit_price is None:
            unit_price = _to_float(item.get("price"))

        total = _to_float(item.get("total"))
        if total is None and unit_price is not None:
            total = quantity * unit_price

        invalid_row = (
            quantity <= 0
            or (unit_price is not None and unit_price <= 0)
            or total is None
            or total <= 0
        )
        if invalid_row:
            continue

        if unit_price is None:
            unit_price = total / quantity

        normalized.append(
            {
                "name": name or "item",
                "quantity": round(quantity, 3),
                "unit_price": round(unit_price, 2),
                "total": round(total, 2),
            }
        )

    return normalized


def _normalize_date(value: Any) -> date:
    if not value:
        return date.today()

    raw = str(value).strip()
    if not raw:
        return date.today()

    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        try:
            return datetime.fromisoformat(raw).date()
        except ValueError:
            return date.today()


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    text = re.sub(r"[^0-9.\-]", "", text)
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _normalize_tax_details(raw: dict[str, Any]) -> dict[str, float]:
    tax_raw = raw.get("tax_details") if isinstance(raw.get("tax_details"), dict) else {}

    normalized = {
        "subtotal": _to_float(tax_raw.get("subtotal") or raw.get("subtotal")) or 0.0,
        "tax": _to_float(tax_raw.get("tax") or raw.get("tax")) or 0.0,
        "cgst": _to_float(tax_raw.get("cgst") or raw.get("cgst")) or 0.0,
        "sgst": _to_float(tax_raw.get("sgst") or raw.get("sgst")) or 0.0,
        "igst": _to_float(tax_raw.get("igst") or raw.get("igst")) or 0.0,
        "vat": _to_float(tax_raw.get("vat") or raw.get("vat")) or 0.0,
        "service_tax": _to_float(
            tax_raw.get("service_tax")
            or raw.get("service_tax")
            or raw.get("serviceCharge")
        )
        or 0.0,
        "cess": _to_float(tax_raw.get("cess") or raw.get("cess")) or 0.0,
        "tip": _to_float(tax_raw.get("tip") or raw.get("tip")) or 0.0,
        "discount": _to_float(tax_raw.get("discount") or raw.get("discount")) or 0.0,
        "total_tax": _to_float(tax_raw.get("total_tax") or raw.get("total_tax")) or 0.0,
    }

    if normalized["total_tax"] <= 0:
        normalized["total_tax"] = (
            normalized["cgst"]
            + normalized["sgst"]
            + normalized["igst"]
            + normalized["vat"]
            + normalized["service_tax"]
            + normalized["cess"]
        )

    if normalized["tax"] <= 0 and normalized["total_tax"] > 0:
        normalized["tax"] = normalized["total_tax"]

    return {key: round(max(0.0, value), 2) for key, value in normalized.items()}


def _normalize_invoice_number(
    raw: dict[str, Any],
    text_input: str | None,
    description: str,
) -> str:
    invoice_keys = [
        "invoice_number",
        "invoice_no",
        "invoice",
        "bill_number",
        "bill_no",
        "receipt_number",
        "receipt_no",
    ]

    value = ""
    for key in invoice_keys:
        candidate = raw.get(key)
        if candidate:
            value = str(candidate)
            break

    cleaned = re.sub(r"\s+", " ", value).strip()
    cleaned = re.sub(r"[^A-Za-z0-9\-/]", "", cleaned)

    if cleaned:
        return cleaned[:64]

    fallback_text = " ".join(part for part in [text_input or "", description] if part)
    if not fallback_text:
        return ""

    patterns = [
        (
            r"(?:invoice|inv|bill|receipt)\s*(?:no|number|#|:)?\s*"
            r"([A-Za-z0-9\-/]{3,64})"
        ),
        r"\b([A-Za-z]{2,6}[-/][A-Za-z0-9\-/]{2,58})\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, fallback_text, flags=re.IGNORECASE)
        if not match:
            continue

        candidate = re.sub(r"[^A-Za-z0-9\-/]", "", match.group(1)).strip()
        if candidate:
            return candidate[:64]

    return ""
