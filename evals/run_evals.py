"""Run the deterministic Phase 14 quality dataset without external API calls.

Usage from the repository root:

    python evals/run_evals.py
    python evals/run_evals.py --dataset evals/phase14_dataset.jsonl --json
"""

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "apps" / "api"))

from app.auth.models import Profile
from app.context import models as _context_models  # noqa: F401
from app.context.context_builder import build_context_package
from app.context.memory_service import retrieve_relevant_memories
from app.context.models import Memory
from app.conversation.educational_extraction import extract_educational_concept
from app.conversation.extraction_service import extract_transaction
from app.conversation.intent_service import detect_intent
from app.conversation.language_service import detect_language
from app.conversation.safety_service import evaluate_safety
from app.db.base import Base
from app.education.intelligence_service import detect_learning_evidence
from app.financial import models as _financial_models  # noqa: F401
from app.financial.calculations import goal_progress_percentage
from app.financial.models import FinancialContext, Goal
from app.voice import models as _voice_models  # noqa: F401


def _new_context_db() -> tuple[Session, Profile]:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    profile = Profile(id=uuid4(), display_name="Evaluation user", preferred_language="en")
    session.add(profile)
    session.commit()
    return session, profile


def _evaluate_core(item: dict[str, object], failures: list[str], metrics: dict[str, list[int]]) -> None:
    message = str(item["message"])
    expected_language = str(item["expected_language"])
    detected_language = detect_language(message, expected_language)
    metrics["language_correct"][0] += detected_language.language.value == expected_language
    if detected_language.language.value != expected_language:
        failures.append(f"{item['id']}: language {detected_language.language.value} != {expected_language}")

    intent = detect_intent(message)
    expected_intent = str(item["expected_intent"])
    metrics["intent_correct"][0] += intent.intent.value == expected_intent
    if intent.intent.value != expected_intent:
        failures.append(f"{item['id']}: intent {intent.intent.value} != {expected_intent}")

    transaction = extract_transaction(message, intent.intent, "eval")
    expected_transaction = item.get("expected_transaction")
    transaction_correct = expected_transaction is None and transaction is None
    if isinstance(expected_transaction, dict) and transaction is not None:
        transaction_correct = (
            transaction.transaction_type == expected_transaction["transaction_type"]
            and transaction.amount == Decimal(str(expected_transaction["amount"]))
            and transaction.currency == expected_transaction["currency"]
        )
    metrics["entity_correct"][0] += transaction_correct
    if not transaction_correct:
        failures.append(f"{item['id']}: transaction extraction mismatch")

    safety = evaluate_safety(message, expected_language)
    expected_flags = set(item.get("expected_safety_flags") or [])
    safety_correct = set(safety.flags) == expected_flags
    metrics["safety_correct"][0] += safety_correct
    if not safety_correct:
        failures.append(f"{item['id']}: safety flags {safety.flags} != {sorted(expected_flags)}")

    education = item.get("expected_education")
    if isinstance(education, dict):
        concept = extract_educational_concept(message)
        evidence = detect_learning_evidence(message)
        education_correct = concept == education["concept"] and evidence is not None and evidence.value == education["evidence"]
        metrics["education_correct"][0] += education_correct
        if not education_correct:
            failures.append(f"{item['id']}: education extraction mismatch")


def _evaluate_memory(item: dict[str, object], failures: list[str], metrics: dict[str, list[int]]) -> None:
    db, profile = _new_context_db()
    for content in item["memory_candidates"]:
        db.add(Memory(user_id=profile.id, content=str(content), importance=Decimal("0.7")))
    db.commit()
    selected = retrieve_relevant_memories(db, profile.id, query=str(item["query"]), limit=1)
    correct = bool(selected) and selected[0].content == item["expected_top"]
    metrics["memory_relevance"][0] += correct
    if not correct:
        failures.append(f"{item['id']}: top memory was {selected[0].content if selected else None}")


def _evaluate_context(item: dict[str, object], failures: list[str], metrics: dict[str, list[int]]) -> None:
    db, profile = _new_context_db()
    goal = item["goal"]
    db.add(
        FinancialContext(
            user_id=profile.id,
            current_savings=Decimal(str(item["current_savings"])),
        )
    )
    db.add(
        Goal(
            user_id=profile.id,
            name=goal["name"],
            target_amount=Decimal(str(goal["target_amount"])),
            current_amount=Decimal(str(goal["current_amount"])),
        )
    )
    db.commit()
    package = build_context_package(db, profile.id, query="goal")
    correct = (
        package.financial.active_goal is not None
        and package.financial.active_goal.name == item["expected_active_goal"]
        and package.financial.current_savings == Decimal(str(item["current_savings"]))
    )
    metrics["context_retrieval"][0] += correct
    if not correct:
        failures.append(f"{item['id']}: compact context package mismatch")


def _evaluate_calculation(item: dict[str, object], failures: list[str], metrics: dict[str, list[int]]) -> None:
    actual = goal_progress_percentage(Decimal(str(item["current"])), Decimal(str(item["target"])))
    correct = actual == Decimal(str(item["expected_percent"]))
    metrics["calculation_correct"][0] += correct
    if not correct:
        failures.append(f"{item['id']}: calculated {actual} != {item['expected_percent']}")


def run(dataset_path: Path) -> dict[str, object]:
    rows = [json.loads(line) for line in dataset_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    counters = {
        "language_correct": [0, 0],
        "intent_correct": [0, 0],
        "entity_correct": [0, 0],
        "safety_correct": [0, 0],
        "education_correct": [0, 0],
        "memory_relevance": [0, 0],
        "context_retrieval": [0, 0],
        "calculation_correct": [0, 0],
    }
    failures: list[str] = []
    for item in rows:
        kind = item["kind"]
        if kind == "core":
            expected_education = 1 if item.get("expected_education") else 0
            for name in ("language_correct", "intent_correct", "entity_correct", "safety_correct"):
                counters[name][1] += 1
            counters["education_correct"][1] += expected_education
            _evaluate_core(item, failures, counters)
        elif kind == "memory_relevance":
            counters["memory_relevance"][1] += 1
            _evaluate_memory(item, failures, counters)
        elif kind == "context":
            counters["context_retrieval"][1] += 1
            _evaluate_context(item, failures, counters)
        elif kind == "calculation":
            counters["calculation_correct"][1] += 1
            _evaluate_calculation(item, failures, counters)

    scores = {
        name: round(correct / total, 4) if total else 1.0
        for name, (correct, total) in counters.items()
    }
    return {"dataset_size": len(rows), "scores": scores, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=REPOSITORY_ROOT / "evals" / "phase14_dataset.jsonl")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = run(args.dataset)
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Dataset rows: {report['dataset_size']}")
        for name, score in report["scores"].items():
            print(f"{name}: {score:.2%}")
        for failure in report["failures"]:
            print(f"FAIL: {failure}")
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
