from app.context.schemas import ContextPackage
from app.conversation.schemas import LanguageCode, SafetyAssessment


def build_personalization_instructions(
    context: ContextPackage,
    language: LanguageCode,
    safety: SafetyAssessment,
) -> str:
    safety_note = safety.guidance or "Use calm, practical, uncertainty-aware financial language."
    return (
        f"Respond in language code {language.value}. Address the user by name only when present. "
        "Use the supplied context as personalization, never invent facts, and do not claim that an action "
        "was persisted unless the structured result says so. Financial records require explicit confirmation. "
        "Never guarantee returns or outcomes. If a figure is not present in the supplied context or extracted "
        "entities, say that it is unverified instead of guessing. Disclose uncertainty when advice depends on "
        "missing information. "
        f"Safety guidance: {safety_note}\n\n"
        f"USER CONTEXT:\n{context.to_prompt_text()}"
    )
