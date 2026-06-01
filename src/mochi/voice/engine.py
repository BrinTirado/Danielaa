from mochi.conversation.engine import ConversationEngine
from mochi.voice.base import SpeechRecognizer, SpeechSynthesizer
from mochi.voice.models import VoiceTurnResult


class VoiceEngine:
    def __init__(
        self,
        *,
        conversation_engine: ConversationEngine,
        recognizer: SpeechRecognizer,
        synthesizer: SpeechSynthesizer,
    ) -> None:
        self.conversation_engine = conversation_engine
        self.recognizer = recognizer
        self.synthesizer = synthesizer

    def handle_turn(self, person_id: str | None = None) -> VoiceTurnResult:
        speech_input = self.recognizer.listen()
        response = self.conversation_engine.respond(speech_input.text, person_id=person_id)
        speech_output = self.synthesizer.speak(response.text)
        return VoiceTurnResult(
            input=speech_input,
            response_text=response.text,
            output=speech_output,
            actions=response.actions,
        )
