from collections.abc import Iterable

from mochi.voice.models import SpeechInput, SpeechOutput


class FakeSpeechRecognizer:
    def __init__(self, queued_text: Iterable[str]) -> None:
        self._queued_text = list(queued_text)

    def listen(self) -> SpeechInput:
        if not self._queued_text:
            msg = "No fake speech input queued."
            raise ValueError(msg)
        text = self._queued_text.pop(0).strip()
        if not text:
            msg = "Fake speech input cannot be empty."
            raise ValueError(msg)
        return SpeechInput(text=text, source="fake", confidence=1.0)


class FakeSpeechSynthesizer:
    def __init__(self) -> None:
        self.spoken_texts: list[str] = []

    def speak(self, text: str) -> SpeechOutput:
        stripped_text = text.strip()
        if not stripped_text:
            msg = "Speech output cannot be empty."
            raise ValueError(msg)
        self.spoken_texts.append(stripped_text)
        return SpeechOutput(text=stripped_text, voice_id="fake")
