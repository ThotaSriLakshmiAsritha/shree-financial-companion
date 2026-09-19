import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.models import Profile
from app.context.context_builder import build_context_package
from app.context.conversation_context_service import (
    append_message,
    create_conversation,
    get_owned_conversation,
)
from app.context.schemas import ConversationCreate, ConversationMessageCreate
from app.core.time import local_today
from app.conversation.educational_extraction import extract_educational_concept
from app.conversation.extraction_service import extract_transaction
from app.conversation.gemini_client import GeminiClient, GeminiUnavailable
from app.conversation.intent_service import detect_intent
from app.conversation.language_service import detect_language
from app.conversation.personalization_service import build_personalization_instructions
from app.conversation.response_validation import validate_response
from app.conversation.safety_service import evaluate_safety
from app.conversation.schemas import (
    ConversationMessageRequest,
    ConversationMessageResponse,
    ExtractedTransaction,
    GeminiResponsePayload,
    LanguageCode,
    LanguageDetectionResult,
    SafetyAssessment,
    TransactionProposalSummary,
)
from app.education.intelligence_service import record_learning_evidence
from app.education.schemas import EducationalEvidenceCreate
from app.financial.schemas import TransactionProposalCreate
from app.financial.service import create_transaction_proposal
from app.privacy.service import record_audit_event

logger = logging.getLogger(__name__)


def _fallback_response(
    language: LanguageCode,
    safety: SafetyAssessment,
    transaction: ExtractedTransaction | None,
) -> GeminiResponsePayload:
    if safety.guidance and not safety.allow_llm:
        return GeminiResponsePayload(response=safety.guidance)
    if transaction is not None:
        messages = {
            LanguageCode.ENGLISH: (
                f"I understood {transaction.transaction_type} of {transaction.currency} {transaction.amount} "
                "from your message. Please confirm before I record it."
            ),
            LanguageCode.HINDI: (
                f"मैंने आपके संदेश में {transaction.currency} {transaction.amount} की जानकारी समझी है। "
                "इसे दर्ज करने से पहले कृपया पुष्टि करें।"
            ),
            LanguageCode.TELUGU: (
                f"మీ సందేశంలో {transaction.currency} {transaction.amount} సమాచారం అర్థమైంది. "
                "దీన్ని నమోదు చేయడానికి ముందు దయచేసి నిర్ధారించండి."
            ),
        }
        return GeminiResponsePayload(response=messages[language], asks_confirmation=True)
    messages = {
        LanguageCode.ENGLISH: "I’m here with you. Tell me what you would like help with.",
        LanguageCode.HINDI: "मैं आपके साथ हूँ। बताइए, मैं किस बात में मदद करूँ?",
        LanguageCode.TELUGU: "నేను మీతో ఉన్నాను. మీకు ఏ విషయంలో సహాయం కావాలో చెప్పండి.",
    }
    return GeminiResponsePayload(response=messages[language])


def _entity_text(transaction: ExtractedTransaction | None) -> str:
    return transaction.model_dump_json() if transaction else "none"


def _known_financial_values(context, transaction: ExtractedTransaction | None) -> set[str]:
    values = {str(context.financial.current_savings)}
    if context.financial.active_goal:
        values.update(
            {
                str(context.financial.active_goal.current_amount),
                str(context.financial.active_goal.target_amount),
            }
        )
    if transaction:
        values.add(str(transaction.amount))
    return {value.replace(",", "") for value in values}


def _persist_educational_evidence(db: Session, user_id: UUID, message: str) -> None:
    concept = extract_educational_concept(message)
    if concept is None:
        return
    try:
        record_learning_evidence(
            db,
            user_id,
            EducationalEvidenceCreate(concept=concept, statement=message),
        )
    except ValueError:
        logger.info("No actionable educational evidence detected for user=%s", user_id)


class ConversationOrchestrator:
    def __init__(self, gemini_client: GeminiClient | None = None, use_llm: bool = True) -> None:
        self.gemini_client = gemini_client or GeminiClient()
        self.use_llm = use_llm

    def handle(
        self,
        db: Session,
        profile: Profile,
        request: ConversationMessageRequest,
    ) -> ConversationMessageResponse:
        detected_language = (
            detect_language(request.message, profile.preferred_language)
            if request.language is None
            else LanguageDetectionResult(language=request.language, confidence=1, method="provided")
        )
        language = detected_language.language
        intent_result = detect_intent(request.message)
        safety = evaluate_safety(request.message, profile.preferred_language)

        if request.conversation_id is None:
            conversation = create_conversation(
                db,
                profile.id,
                ConversationCreate(channel=request.channel, language=language.value),
            )
        else:
            conversation = get_owned_conversation(db, profile.id, request.conversation_id)
            if conversation is None:
                raise LookupError("Conversation not found for this user.")

        user_message = append_message(
            db,
            profile.id,
            conversation.id,
            ConversationMessageCreate(
                role="user",
                message=request.message,
                language=language.value,
            ),
        )

        context = build_context_package(db, profile.id, query=request.message)
        transaction = extract_transaction(
            request.message,
            intent_result.intent,
            request.channel,
            today=local_today(),
        )
        proposal = None
        # Scam-related text must never create even a pending financial proposal.
        if transaction is not None and not safety.flags:
            proposal = create_transaction_proposal(
                db,
                profile.id,
                TransactionProposalCreate(
                    transaction_type=transaction.transaction_type,
                    amount=transaction.amount,
                    currency=transaction.currency,
                    category=transaction.category,
                    description=transaction.description,
                    date=transaction.date,
                    source=transaction.source,
                    confidence=transaction.confidence,
                    raw_statement=transaction.raw_statement,
                    goal_id=transaction.goal_id,
                ),
            )

        if self.use_llm and safety.allow_llm:
            try:
                generated = self.gemini_client.generate_response(
                    user_message=request.message,
                    intent=intent_result.intent.value,
                    extracted_entities=_entity_text(transaction),
                    personalization=build_personalization_instructions(context, language, safety),
                )
            except GeminiUnavailable:
                logger.info("Using deterministic conversation fallback for user=%s", profile.id)
                generated = _fallback_response(language, safety, transaction)
        else:
            generated = _fallback_response(language, safety, transaction)

        if proposal is not None:
            generated = generated.model_copy(update={"asks_confirmation": True})
        generated = validate_response(
            generated,
            safety,
            requires_confirmation=proposal is not None,
            language=language.value,
            known_financial_values=_known_financial_values(context, transaction),
        )
        assistant_message = append_message(
            db,
            profile.id,
            conversation.id,
            ConversationMessageCreate(
                role="assistant",
                message=generated.response,
                language=language.value,
                intent=intent_result.intent.value,
                metadata={
                    "safety_risk": safety.risk_level,
                    "proposal_id": str(proposal.id) if proposal else None,
                },
            ),
        )
        _persist_educational_evidence(db, profile.id, request.message)
        record_audit_event(
            db,
            profile.id,
            "conversation.message_handled",
            resource_type="conversation",
            resource_id=conversation.id,
            channel=request.channel,
            metadata={
                "intent": intent_result.intent.value,
                "safety_risk": safety.risk_level,
                "safety_flags": safety.flags,
                "proposal_id": str(proposal.id) if proposal else None,
            },
        )

        logger.info(
            "Conversation handled user=%s language=%s intent=%s safety=%s proposal=%s",
            profile.id,
            language.value,
            intent_result.intent.value,
            safety.risk_level,
            bool(proposal),
        )
        return ConversationMessageResponse(
            conversation_id=conversation.id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            language=language,
            intent=intent_result.intent,
            response=generated.response,
            suggested_next_step=generated.suggested_next_step,
            safety=safety,
            transaction_proposal=(
                TransactionProposalSummary(
                    id=proposal.id,
                    transaction_type=proposal.transaction_type,
                    amount=proposal.amount,
                    currency=proposal.currency,
                    category=proposal.category,
                    description=proposal.description,
                    date=proposal.transaction_date,
                    status=proposal.status,
                )
                if proposal
                else None
            ),
        )
