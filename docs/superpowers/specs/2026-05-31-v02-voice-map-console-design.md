# Mochi v0.2 Voice And Map Console Design

## Purpose

v0.2 prepares Mochi for voice interaction and gives the owner a visual way to
inspect fake robot movement. The milestone stays software-only: no live
microphone input, no real speaker output, no cameras, no motors, no ROS, and no
robot hardware dependencies.

The goal is to make Mochi easier to validate before real-world integrations
exist. The owner should be able to see where Mochi thinks it is, which rooms are
connected, which destinations are blocked, what command was processed, and what
Mochi would have said through a future voice system.

## Scope

In scope:

- Fake voice input and output interfaces.
- A fake voice turn that routes spoken text through the existing conversation
  engine.
- A local browser map console for the fake house map and fake navigation state.
- Movement history for attempted moves, including blocked no-go zones.
- A CLI path for simulated voice turns.
- Tests for voice adapters, voice engine behavior, map snapshots, movement
  history, and local UI/API behavior.

Out of scope:

- Real microphone capture.
- Real audio playback.
- Speech-to-text or text-to-speech provider integrations.
- Robot hardware, motors, ROS, cameras, and Home Assistant.
- Autonomous background loops.

## User Experience

The main new owner-facing surface is a local map console launched from the CLI,
for example:

```bash
mochi map-ui
```

The command starts a local-only web server, prints the URL, and keeps one
runtime alive for that browser session. The first view shows:

- the configured rooms and connections from `config/house_map.yaml`;
- Mochi's current fake location;
- no-go zones;
- fake battery, mood, and privacy mode;
- the last command and result;
- a movement log;
- controls to run fake movement commands.

The same UI also includes a fake voice input field. Submitting text through that
field simulates speech recognition, routes the text into `ConversationEngine`,
passes Mochi's response to a fake speech synthesizer, updates state, and appends
a turn to the visible log.

The CLI also exposes a smaller voice simulation command, for example:

```bash
mochi voice "go to kitchen"
```

It prints the recognized text, Mochi's response, action results, and fake spoken
output.

## Architecture

### Voice Package

Add `mochi.voice` with small, replaceable interfaces:

- `SpeechRecognizer`: returns a structured `SpeechInput`.
- `SpeechSynthesizer`: accepts response text and returns a structured
  `SpeechOutput`.
- `FakeSpeechRecognizer`: returns queued or provided text.
- `FakeSpeechSynthesizer`: records the text Mochi would have spoken.
- `VoiceEngine`: coordinates one voice turn.

`VoiceEngine` depends on `ConversationEngine`, a recognizer, and a synthesizer.
It does not know about hardware, microphones, speakers, or providers.

### Map And Movement Tracking

Add a small map/debug layer that reads the existing `HouseMap` and `RobotState`
and produces a serializable map snapshot. The snapshot includes rooms,
connections, no-go zones, current location, and recent movement events.

Movement tracking should be attached around navigation/action execution, not
inside real hardware concepts. v0.2 can keep this simple with a runtime-local
history object that records:

- requested destination;
- starting location;
- ending location;
- success/failure;
- message;
- command source, such as `chat`, `voice`, or `map-ui`.

The tracker remains session-local in v0.2. Persisted robot state and persisted
movement history can be considered later.

### Map Layout

The browser UI needs stable room positions. Extend the config model with
optional room coordinates, for example:

```yaml
rooms:
  living_room:
    display_name: Living Room
    map_position:
      x: 160
      y: 160
```

If a room does not define `map_position`, the UI uses a deterministic fallback
layout so the map still renders.

### Local Web UI

Add a lightweight local web server using the Python standard library. Avoid
adding a frontend framework or heavy web dependency in v0.2.

Recommended command:

```bash
mochi map-ui --host 127.0.0.1 --port 8765
```

Recommended endpoints:

- `GET /`: serves the static console HTML.
- `GET /api/snapshot`: returns map, robot state, history, and last voice turn.
- `POST /api/command`: routes a text command through `ConversationEngine`.
- `POST /api/voice-turn`: routes text through `VoiceEngine`.

The browser console can use plain HTML, CSS, and small vanilla JavaScript. It
should render an SVG map, keep text readable, and update the snapshot after each
command.

## Data Flow

Fake voice turn:

```text
UI/CLI text
  -> FakeSpeechRecognizer
  -> VoiceEngine
  -> ConversationEngine
  -> ActionRouter
  -> FakeNavigator / MemoryStore / RobotState
  -> FakeSpeechSynthesizer
  -> VoiceTurnResult
  -> UI/CLI display
```

Map command:

```text
UI command
  -> local server
  -> ConversationEngine
  -> ActionRouter
  -> FakeNavigator
  -> movement history
  -> map snapshot
  -> UI refresh
```

## Privacy And Safety

- Voice simulation must not auto-save memories.
- Unknown people must not be enrolled or remembered automatically.
- Privacy mode remains explicit and visible in the UI.
- Privacy mode continues to suppress proactive behavior, but explicit owner
  commands still work.
- The web server binds to `127.0.0.1` by default.
- No secrets are stored or displayed.

## Error Handling

- Empty voice input returns a clear validation message.
- Unknown rooms show a failed movement event and leave location unchanged.
- No-go zones show a failed movement event and leave location unchanged.
- Malformed JSON requests return a structured error response.
- Server startup reports the selected URL and fails clearly if the port is in
  use.

## Testing

Add focused tests for:

- fake recognizer and synthesizer behavior;
- `VoiceEngine` routing a command through `ConversationEngine`;
- voice turns updating fake navigation state;
- voice turns not auto-saving memories;
- no-go zones producing failed movement history;
- map snapshot shape and room connection data;
- optional room position parsing;
- local server JSON endpoints;
- CLI `voice` command output;
- CLI `map-ui` command startup behavior where practical without blocking tests.

Before claiming completion, run:

```bash
pytest
ruff check .
```

For the browser UI, also do a manual/browser verification pass that confirms the
map renders, movement updates the displayed current location, and blocked moves
are visibly logged.

## Acceptance Criteria

- `mochi voice "where are you?"` produces a fake recognized input and fake
  spoken output.
- `mochi voice "go to kitchen"` moves the fake robot to `kitchen`.
- `mochi map-ui` starts a local browser console.
- The map console displays the fake house map, current location, no-go zones,
  and movement history.
- Submitting `go to kitchen` in the UI updates Mochi's location.
- Submitting `go to bedroom` in the UI records a blocked no-go-zone result and
  does not move Mochi.
- No real audio, hardware, ROS, camera, or motor dependency is added.
