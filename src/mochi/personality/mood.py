MOOD_DESCRIPTIONS = {
    "curious": "curious and attentive",
    "playful": "playful and lightly mischievous",
    "calm": "calm and steady",
}


def describe_mood(mood: str) -> str:
    return MOOD_DESCRIPTIONS.get(mood, mood)
