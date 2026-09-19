from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

TRANSACTION_TYPES = ("income", "expense", "saving")
CONFIRMATION_STATUSES = ("pending", "confirmed", "rejected")
PROPOSAL_STATUSES = ("pending", "confirmed", "rejected")
GOAL_STATUSES = ("active", "completed", "paused")


class FinancialContext(Base):
    __tablename__ = "financial_context"

    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    income_pattern: Mapped[str | None] = mapped_column(String(40), nullable=True)
    monthly_income_estimate: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    current_savings: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total_income: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total_expenses: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    total_savings: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    last_financial_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profile = relationship("Profile")


class IncomeSource(Base):
    __tablename__ = "income_sources"
    __table_args__ = (
        CheckConstraint("typical_amount >= 0", name="ck_income_sources_typical_amount"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    income_type: Mapped[str] = mapped_column(String(40), nullable=False)
    typical_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(30), nullable=True)
    seasonal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profile = relationship("Profile")


class FinancialObligation(Base):
    __tablename__ = "financial_obligations"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_financial_obligations_amount"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    frequency: Mapped[str] = mapped_column(String(30), nullable=False)
    due_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal", server_default="normal")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profile = relationship("Profile")


class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint("target_amount > 0", name="ck_goals_target_amount"),
        CheckConstraint("current_amount >= 0", name="ck_goals_current_amount"),
        CheckConstraint("status IN ('active', 'completed', 'paused')", name="ck_goals_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, default="general", server_default="general")
    icon: Mapped[str] = mapped_column(String(20), nullable=False, default="✦", server_default="✦")
    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    profile = relationship("Profile")
    milestones = relationship("GoalMilestone", back_populates="goal", cascade="all, delete-orphan", order_by="GoalMilestone.amount")
    contributions = relationship("GoalContribution", back_populates="goal", cascade="all, delete-orphan", order_by="GoalContribution.contributed_at.desc()")


class GoalMilestone(Base):
    __tablename__ = "goal_milestones"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_goal_milestones_amount"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    goal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    goal = relationship("Goal", back_populates="milestones")


class GoalContribution(Base):
    __tablename__ = "goal_contributions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_goal_contributions_amount"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    goal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    transaction_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    contributed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    goal = relationship("Goal", back_populates="contributions")
    profile = relationship("Profile")
    transaction = relationship("Transaction", foreign_keys=[transaction_id])


class TransactionProposal(Base):
    __tablename__ = "transaction_proposals"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transaction_proposals_amount"),
        CheckConstraint("transaction_type IN ('income', 'expense', 'saving')", name="ck_transaction_proposals_type"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_transaction_proposals_confidence"),
        CheckConstraint("status IN ('pending', 'confirmed', 'rejected')", name="ck_transaction_proposals_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=0, server_default="0")
    raw_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile = relationship("Profile")
    goal = relationship("Goal")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount"),
        CheckConstraint("transaction_type IN ('income', 'expense', 'saving')", name="ck_transactions_type"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_transactions_confidence"),
        CheckConstraint(
            "confirmation_status IN ('pending', 'confirmed', 'rejected')",
            name="ck_transactions_confirmation_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proposal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("transaction_proposals.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR", server_default="INR")
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confirmation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="confirmed", server_default="confirmed"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    goal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("goals.id", ondelete="SET NULL"), nullable=True, index=True
    )

    profile = relationship("Profile")
    proposal = relationship("TransactionProposal", foreign_keys=[proposal_id])
    goal = relationship("Goal", foreign_keys=[goal_id])
