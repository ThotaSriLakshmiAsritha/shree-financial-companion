from enum import StrEnum


class KnowledgeState(StrEnum):
    NOT_INTRODUCED = "NOT_INTRODUCED"
    INTRODUCED = "INTRODUCED"
    BASIC_UNDERSTANDING = "BASIC_UNDERSTANDING"
    STRONG_UNDERSTANDING = "STRONG_UNDERSTANDING"
    SUCCESSFULLY_APPLIED = "SUCCESSFULLY_APPLIED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    MISUNDERSTOOD = "MISUNDERSTOOD"


class ApplicationState(StrEnum):
    NOT_OBSERVED = "NOT_OBSERVED"
    ATTEMPTED = "ATTEMPTED"
    SUCCESSFULLY_APPLIED = "SUCCESSFULLY_APPLIED"


class LearningEvidenceType(StrEnum):
    INTRODUCED = "introduced"
    UNDERSTOOD = "understood"
    APPLIED = "applied"
    NEEDS_CLARIFICATION = "needs_clarification"
    MISUNDERSTOOD = "misunderstood"


# Evidence can move forward, repeat a state, or move to a corrective state.
# A strong, explicit application signal can promote a learner to strong
# understanding while recording the separate application state.
ALLOWED_KNOWLEDGE_TRANSITIONS: dict[KnowledgeState, frozenset[KnowledgeState]] = {
    KnowledgeState.NOT_INTRODUCED: frozenset(
        {
            KnowledgeState.NOT_INTRODUCED,
            KnowledgeState.INTRODUCED,
            KnowledgeState.BASIC_UNDERSTANDING,
            KnowledgeState.STRONG_UNDERSTANDING,
            KnowledgeState.SUCCESSFULLY_APPLIED,
            KnowledgeState.NEEDS_CLARIFICATION,
            KnowledgeState.MISUNDERSTOOD,
        }
    ),
    KnowledgeState.INTRODUCED: frozenset(
        {
            KnowledgeState.INTRODUCED,
            KnowledgeState.BASIC_UNDERSTANDING,
            KnowledgeState.STRONG_UNDERSTANDING,
            KnowledgeState.SUCCESSFULLY_APPLIED,
            KnowledgeState.NEEDS_CLARIFICATION,
            KnowledgeState.MISUNDERSTOOD,
        }
    ),
    KnowledgeState.BASIC_UNDERSTANDING: frozenset(
        {
            KnowledgeState.BASIC_UNDERSTANDING,
            KnowledgeState.STRONG_UNDERSTANDING,
            KnowledgeState.SUCCESSFULLY_APPLIED,
            KnowledgeState.NEEDS_CLARIFICATION,
            KnowledgeState.MISUNDERSTOOD,
        }
    ),
    KnowledgeState.STRONG_UNDERSTANDING: frozenset(
        {
            KnowledgeState.STRONG_UNDERSTANDING,
            KnowledgeState.SUCCESSFULLY_APPLIED,
            KnowledgeState.NEEDS_CLARIFICATION,
            KnowledgeState.MISUNDERSTOOD,
        }
    ),
    KnowledgeState.SUCCESSFULLY_APPLIED: frozenset(
        {
            KnowledgeState.SUCCESSFULLY_APPLIED,
            KnowledgeState.NEEDS_CLARIFICATION,
            KnowledgeState.MISUNDERSTOOD,
        }
    ),
    KnowledgeState.NEEDS_CLARIFICATION: frozenset(
        {
            KnowledgeState.NEEDS_CLARIFICATION,
            KnowledgeState.INTRODUCED,
            KnowledgeState.BASIC_UNDERSTANDING,
            KnowledgeState.STRONG_UNDERSTANDING,
            KnowledgeState.SUCCESSFULLY_APPLIED,
            KnowledgeState.MISUNDERSTOOD,
        }
    ),
    KnowledgeState.MISUNDERSTOOD: frozenset(
        {
            KnowledgeState.MISUNDERSTOOD,
            KnowledgeState.NEEDS_CLARIFICATION,
            KnowledgeState.INTRODUCED,
            KnowledgeState.BASIC_UNDERSTANDING,
            KnowledgeState.STRONG_UNDERSTANDING,
            KnowledgeState.SUCCESSFULLY_APPLIED,
        }
    ),
}


def can_transition(current: KnowledgeState | str, target: KnowledgeState | str) -> bool:
    current_state = KnowledgeState(current)
    target_state = KnowledgeState(target)
    return target_state in ALLOWED_KNOWLEDGE_TRANSITIONS[current_state]


def assert_transition(current: KnowledgeState | str, target: KnowledgeState | str) -> None:
    current_state = KnowledgeState(current)
    target_state = KnowledgeState(target)
    if not can_transition(current_state, target_state):
        raise ValueError(f"Invalid educational transition: {current_state} -> {target_state}.")


def target_state_for_evidence(
    current: KnowledgeState | str,
    evidence_type: LearningEvidenceType | str,
) -> KnowledgeState:
    current_state = KnowledgeState(current)
    evidence = LearningEvidenceType(evidence_type)

    if evidence is LearningEvidenceType.INTRODUCED:
        target = KnowledgeState.INTRODUCED if current_state is KnowledgeState.NOT_INTRODUCED else current_state
    elif evidence is LearningEvidenceType.UNDERSTOOD:
        target = (
            KnowledgeState.BASIC_UNDERSTANDING
            if current_state
            in {
                KnowledgeState.NOT_INTRODUCED,
                KnowledgeState.INTRODUCED,
                KnowledgeState.NEEDS_CLARIFICATION,
                KnowledgeState.MISUNDERSTOOD,
            }
            else current_state
        )
    elif evidence is LearningEvidenceType.APPLIED:
        target = (
            KnowledgeState.STRONG_UNDERSTANDING
            if current_state
            in {
                KnowledgeState.NOT_INTRODUCED,
                KnowledgeState.INTRODUCED,
                KnowledgeState.BASIC_UNDERSTANDING,
                KnowledgeState.NEEDS_CLARIFICATION,
                KnowledgeState.MISUNDERSTOOD,
            }
            else current_state
        )
    elif evidence is LearningEvidenceType.NEEDS_CLARIFICATION:
        target = KnowledgeState.NEEDS_CLARIFICATION
    else:
        target = KnowledgeState.MISUNDERSTOOD

    assert_transition(current_state, target)
    return target
