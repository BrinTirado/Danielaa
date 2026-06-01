from typing import Protocol

from mochi.voice.models import SpeechInput, SpeechOutput


class SpeechRecognizer(Protocol):
    def listen(self) -> SpeechInput:
        """Return one recognized speech input."""
        ...


class SpeechSynthesizer(Protocol):
    def speak(self, text: str) -> SpeechOutput:
        """Return one synthesized speech output."""
        ...
