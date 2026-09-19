from uuid import uuid4
from sqlalchemy.orm import Session

from app.auth.models import Profile
from app.stories.schemas import StoryResponse, StorySceneResponse


SAMPLE_STORIES = {
    "te": {
        "title": "పొదుపుతో సాధించిన విజయం",
        "slug": "savings-success",
        "story_key": "story-savings-1",
        "scenes": [
            "ఒకసారి ఒక గ్రామంలో లక్ష్మి అనే మహిళ కుట్టు మిషన్ కొనాలనుకుంది.",
            "ఆమె ప్రతి రోజూ ₹20 చొప్పున స్వయం సహాయక సంఘంలో దాచడం మొదలుపెట్టింది.",
            "ఆరు నెలల తర్వాత ఆమె తన కలల కుట్టు మిషన్‌ను సొంతం చేసుకుంది.",
        ],
        "moral": "చిన్న పొదుపులే పెద్ద మార్పులకు పునాది.",
    },
    "hi": {
        "title": "बचत से मिली सफलता",
        "slug": "savings-success",
        "story_key": "story-savings-1",
        "scenes": [
            "एक गाँव में सुनीता नाम की महिला सिलाई मशीन खरीदना चाहती थी।",
            "उसने रोज़ ₹20 स्वयं सहायता समूह में बचाना शुरू किया।",
            "छह महीने बाद उसने अपनी पसंद की सिलाई मशीन खरीद ली।",
        ],
        "moral": "छोटी बचत ही बड़े सपनों को सच करती है।",
    },
    "en": {
        "title": "The Power of Regular Savings",
        "slug": "savings-success",
        "story_key": "story-savings-1",
        "scenes": [
            "Once in a village, a woman named Lakshmi wanted to buy a sewing machine.",
            "She began saving ₹20 every day in her self-help group.",
            "Within six months, she had saved enough to buy her dream machine.",
        ],
        "moral": "Small consistent savings pave the way to financial independence.",
    },
}


def get_story(
    db: Session,
    profile: Profile,
    slug: str | None = None,
    language: str | None = None,
) -> StoryResponse:
    lang = language or (profile.preferred_language if profile else None) or "te"
    if lang not in SAMPLE_STORIES:
        lang = "en"

    data = SAMPLE_STORIES[lang]
    scenes = [
        StorySceneResponse(scene_index=i, text=txt, pause_after_ms=500)
        for i, txt in enumerate(data["scenes"])
    ]
    return StoryResponse(
        id=uuid4(),
        slug=data["slug"],
        story_key=data["story_key"],
        title=data["title"],
        language_code=lang,
        scenes=scenes,
        moral=data["moral"],
    )


def get_story_scene(
    db: Session,
    profile: Profile,
    slug: str,
    scene_index: int,
    language: str | None = None,
) -> tuple[StoryResponse, int, StorySceneResponse]:
    story = get_story(db, profile, slug=slug, language=language)
    if scene_index < 0 or scene_index >= len(story.scenes):
        raise IndexError(f"Scene index {scene_index} is out of bounds.")
    return story, scene_index, story.scenes[scene_index]


def story_text(story: StoryResponse) -> str:
    return " ".join(scene.text for scene in story.scenes)
