from pydantic import Field

from mochi.core.models import ActionResult, MochiBaseModel


class SpeechInput(MochiBaseModel):
    text: str
    source: str = "fake"
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class SpeechOutput(MochiBaseModel):
    text: str
    voice_id: str = "fake"
    audio_path: str | None = None


class VoiceTurnResult(MochiBaseModel):
    input: SpeechInput
    response_text: str
    output: SpeechOutput
    actions: list[ActionResult] = Field(default_factory=list)
