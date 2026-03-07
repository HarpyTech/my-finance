from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


BillType = Literal["grocery", "restaurant", "service", "utility", "other"]


class ExpenseLineItem(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    quantity: float = Field(default=1, gt=0)
    unit_price: float = Field(gt=0)
    total: float = Field(gt=0)


class ExpenseCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str = Field(default="other", min_length=2, max_length=64)
    bill_type: BillType = "other"
    vendor: str = Field(default="", max_length=128)
    description: str = Field(default="", max_length=255)
    expense_date: date
    line_items: list[ExpenseLineItem] = Field(default_factory=list)


class ExpenseItem(BaseModel):
    id: str
    amount: float
    category: str
    bill_type: BillType
    vendor: str
    description: str
    expense_date: date
    line_items: list[ExpenseLineItem] = Field(default_factory=list)
