import anthropic

from config import settings

VALID_EMOTIONS = [
    "Happy", "Productive", "Good", "Tired", "Lazy", "SAD",
    "Stress/Anxiety", "Angry/Annoyed", "Depressed", "Hopeless", "Suicidal",
]

SYSTEM_PROMPT = """You are a mood categorizer for a personal daily tracking app.
Given a user's natural language message about their day, return ONLY one of these exact labels:
Happy, Productive, Good, Tired, Lazy, SAD, Stress/Anxiety, Angry/Annoyed, Depressed, Hopeless, Suicidal

Rules:
- Return ONLY the emotion label, nothing else, no punctuation, no explanation
- Pick the single best-matching emotion
- Examples: "stressful" → Stress/Anxiety  |  "exhausted" → Tired  |  "got a lot done" → Productive  |  "pretty good" → Good"""


def categorize_emotion(text: str) -> str:
    api_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    msg = api_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=20,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    result = msg.content[0].text.strip()
    # Validate — fall back to Good if Claude returns something unexpected
    return result if result in VALID_EMOTIONS else "Good"
