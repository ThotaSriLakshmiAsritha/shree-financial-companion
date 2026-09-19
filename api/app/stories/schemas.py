from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class StorySceneResponse(BaseModel):
    scene_index: int
    text: str
    pause_after_ms: int = 500


class StoryResponse(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    slug: str
    story_key: str
    title: str
    language_code: str
    scenes: list[StorySceneResponse] = []
    moral: str | None = None


class StoryNarrationRequest(BaseModel):
    scene_index: int
    language: str | None = None


class StoryNarrationResponse(BaseModel):
    story_slug: str
    scene_index: int
    total_scenes: int
    language_code: str
    text: str
    pause_after_ms: int = 500
    audio_base64: str
    audio_mime_type: str = "audio/wav"
    request_id: str | None = None


class StoryFullNarrationResponse(BaseModel):
    story_slug: str
    language_code: str
    text: str
    audio_base64: str
    audio_mime_type: str = "audio/wav"
    request_id: str | None = None
