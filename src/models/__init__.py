"""Объекты данных FinTrack."""

from dataclasses import dataclass, field


@dataclass
class Role:
    role_id: int
    role_name: str
    description: str | None = None


@dataclass
class User:
    user_id: int
    username: str
    password_hash: str = field(repr=False)
    full_name: str
    is_active: int
    role_id: int
    role_name: str | None = None


@dataclass
class Category:
    category_id: int
    category_name: str
    operation_type: str


@dataclass
class Operation:
    operation_id: int
    user_id: int
    category_id: int
    amount: float
    operation_date: str
    description: str | None = None
    category_name: str | None = None
    operation_type: str | None = None
    author_name: str | None = None


@dataclass
class Report:
    report_id: int
    user_id: int
    report_name: str
    period_start: str
    period_end: str
    created_at: str
    total_income: float
    total_expense: float
    profit: float
    author_name: str | None = None


@dataclass
class FinancialSummary:
    period_start: str
    period_end: str
    total_income: float
    total_expense: float
    profit: float
