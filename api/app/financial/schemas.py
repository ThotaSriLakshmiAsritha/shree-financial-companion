from datetime import date as Date
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionProposalCreate(BaseModel):
    transaction_type: str
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    category: str | None = Field(default=None, max_length=80)
    description: str | None = Field(default=None, max_length=500)
    date: Date
    source: str = Field(min_length=2, max_length=30)
    confidence: Decimal = Field(ge=0, le=1)
    raw_statement: str | None = Field(default=None, max_length=2000)
    goal_id: UUID | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("transaction_type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value not in {"income", "expense", "saving"}:
            raise ValueError("transaction_type must be income, expense, or saving")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        return value.lower()


class TransactionProposalResponse(BaseModel):
    id: UUID
    user_id: UUID
    transaction_type: str
    amount: Decimal
    currency: str
    category: str | None
    description: str | None
    date: Date = Field(validation_alias="transaction_date", serialization_alias="date")
    source: str
    confidence: Decimal
    raw_statement: str | None
    goal_id: UUID | None
    status: str
    created_at: datetime
    confirmed_at: datetime | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    proposal_id: UUID
    transaction_type: str
    amount: Decimal
    currency: str
    category: str | None
    description: str | None
    date: Date = Field(validation_alias="transaction_date", serialization_alias="date")
    source: str
    confidence: Decimal
    confirmation_status: str
    created_at: datetime
    confirmed_at: datetime
    goal_id: UUID | None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class IncomeSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    income_type: str = Field(min_length=1, max_length=40)
    typical_amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    frequency: str | None = Field(default=None, max_length=30)
    seasonal: bool = False
    notes: str | None = Field(default=None, max_length=1000)


class IncomeSourceResponse(IncomeSourceCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ObligationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    frequency: str = Field(min_length=1, max_length=30)
    due_day: int | None = Field(default=None, ge=1, le=31)
    priority: str = Field(default="normal", max_length=20)
    status: str = Field(default="active", max_length=20)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class ObligationResponse(ObligationCreate):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    category: str = Field(default="general", min_length=1, max_length=40)
    icon: str = Field(default="✦", min_length=1, max_length=20)
    target_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    target_date: Date | None = None
    status: str = Field(default="active", max_length=20)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class GoalResponse(GoalCreate):
    id: UUID
    user_id: UUID
    current_amount: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalMilestoneResponse(BaseModel):
    id: UUID
    goal_id: UUID
    amount: Decimal
    title: str
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalContributionResponse(BaseModel):
    id: UUID
    goal_id: UUID
    user_id: UUID
    amount: Decimal
    transaction_id: UUID | None
    contributed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalDetailsResponse(GoalResponse):
    milestones: list[GoalMilestoneResponse]
    contributions: list[GoalContributionResponse]


class GoalAllocationCreate(BaseModel):
    goal_id: UUID
    amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)


class SavingsDistributionCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    allocations: list[GoalAllocationCreate] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid")


class FinancialContextResponse(BaseModel):
    user_id: UUID
    income_pattern: str | None
    monthly_income_estimate: Decimal | None
    current_savings: Decimal
    total_income: Decimal
    total_expenses: Decimal
    total_savings: Decimal
    currency: str
    last_financial_update: datetime | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
