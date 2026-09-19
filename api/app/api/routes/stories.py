import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_profile
from app.auth.models import Profile
from app.db.session import get_db
from app.privacy.service import record_audit_event
from app.stories.schemas import StoryFullNarrationResponse, StoryNarrationRequest, StoryNarrationResponse, StoryResponse
from app.stories.service import get_story, get_story_scene, story_text
from app.voice.sarvam_client import SarvamClient, SarvamUnavailable, sarvam_language_code

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("/current", response_model=StoryResponse)
def read_current_story(
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
    language: str | None = Query(default=None, pattern="^(en|hi|te)$"),
) -> StoryResponse:
    try:
        return get_story(db, profile, language=language)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{slug}", response_model=StoryResponse)
def read_story(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
    language: str | None = Query(default=None, pattern="^(en|hi|te)$"),
) -> StoryResponse:
    try:
        return get_story(db, profile, slug=slug, language=language)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{slug}/narrate", response_model=StoryNarrationResponse)
def narrate_story_scene(
    slug: str,
    payload: StoryNarrationRequest,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
) -> StoryNarrationResponse:
    try:
        story, scene_index, scene = get_story_scene(
            db,
            profile,
            slug=slug,
            scene_index=payload.scene_index,
            language=payload.language,
        )
        audio = SarvamClient().synthesize(scene.text, sarvam_language_code(story.language_code))
    except IndexError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SarvamUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    record_audit_event(
        db,
        profile.id,
        "story.scene_narrated",
        resource_type="story",
        resource_id=story.id,
        channel="web",
        metadata={"slug": story.slug, "scene_index": scene_index, "language": story.language_code},
    )
    return StoryNarrationResponse(
        story_slug=story.slug,
        scene_index=scene_index,
        total_scenes=len(story.scenes),
        language_code=story.language_code,
        text=scene.text,
        pause_after_ms=scene.pause_after_ms,
        audio_base64=base64.b64encode(audio.audio).decode("ascii"),
        audio_mime_type=audio.mime_type,
        request_id=audio.request_id,
    )


@router.post("/{slug}/narrate-full", response_model=StoryFullNarrationResponse)
def narrate_full_story(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    profile: Annotated[Profile, Depends(get_current_profile)],
    language: str | None = Query(default=None, pattern="^(en|hi|te)$"),
) -> StoryFullNarrationResponse:
    try:
        story = get_story(db, profile, slug=slug, language=language)
        text = story_text(story)
        audio = SarvamClient().synthesize(text, sarvam_language_code(story.language_code))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SarvamUnavailable as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    record_audit_event(
        db,
        profile.id,
        "story.narrated",
        resource_type="story",
        resource_id=story.id,
        channel="web",
        metadata={"slug": story.slug, "language": story.language_code, "scene_count": len(story.scenes)},
    )
    return StoryFullNarrationResponse(
        story_slug=story.slug,
        language_code=story.language_code,
        text=text,
        audio_base64=base64.b64encode(audio.audio).decode("ascii"),
        audio_mime_type=audio.mime_type,
        request_id=audio.request_id,
    )
