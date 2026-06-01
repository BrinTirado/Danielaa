APP_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mochi Map Console</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fa;
      --ink: #17202a;
      --muted: #637083;
      --line: #d8dee8;
      --panel: #ffffff;
      --accent: #1668dc;
      --accent-soft: #e7f0ff;
      --danger: #b42318;
      --danger-soft: #fff0ed;
      --ok: #15803d;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family:
        Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
        sans-serif;
      line-height: 1.45;
    }

    main {
      width: min(1180px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 24px 0;
    }

    h1,
    h2 {
      margin: 0;
      letter-spacing: 0;
    }

    h1 {
      font-size: 2rem;
    }

    h2 {
      font-size: 1rem;
    }

    .topbar {
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      margin-bottom: 18px;
    }

    .status-pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--panel);
      padding: 7px 12px;
      color: var(--muted);
      font-size: 0.9rem;
      white-space: nowrap;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
      gap: 16px;
      align-items: start;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }

    .map-wrap {
      min-height: 460px;
    }

    #map {
      width: 100%;
      min-height: 420px;
      display: block;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfe;
    }

    .controls {
      display: grid;
      gap: 12px;
      margin-bottom: 16px;
    }

    .control-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: center;
    }

    label {
      display: block;
      margin-bottom: 6px;
      font-size: 0.85rem;
      color: var(--muted);
    }

    input {
      width: 100%;
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      color: var(--ink);
      font: inherit;
    }

    button {
      border: 1px solid var(--accent);
      border-radius: 6px;
      background: var(--accent);
      color: #ffffff;
      padding: 9px 12px;
      font: inherit;
      cursor: pointer;
    }

    button:hover {
      filter: brightness(0.96);
    }

    .stack {
      display: grid;
      gap: 12px;
    }

    .section {
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }

    .state-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 10px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 8px;
      min-height: 56px;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 0.78rem;
    }

    .metric strong {
      display: block;
      overflow-wrap: anywhere;
      margin-top: 2px;
    }

    .turn,
    .movement,
    .zone-list {
      margin-top: 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      background: #fbfcfe;
    }

    .empty {
      color: var(--muted);
      margin: 10px 0 0;
    }

    .error {
      display: none;
      margin: 0 0 12px;
      border: 1px solid #ffc9c2;
      border-radius: 6px;
      background: var(--danger-soft);
      color: var(--danger);
      padding: 9px 10px;
    }

    .zone-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      list-style: none;
      margin-bottom: 0;
    }

    .zone-list li {
      border: 1px solid #ffc9c2;
      border-radius: 999px;
      background: var(--danger-soft);
      color: var(--danger);
      padding: 5px 9px;
      overflow-wrap: anywhere;
    }

    .room {
      fill: #ffffff;
      stroke: var(--accent);
      stroke-width: 2;
    }

    .room.current {
      fill: var(--accent-soft);
      stroke-width: 4;
    }

    .room.no-go {
      fill: var(--danger-soft);
      stroke: var(--danger);
      stroke-dasharray: 5 4;
    }

    .connection {
      stroke: #aab5c5;
      stroke-width: 3;
    }

    .robot-dot {
      fill: var(--ok);
      stroke: #ffffff;
      stroke-width: 3;
    }

    .map-label {
      fill: var(--ink);
      font-size: 14px;
      font-weight: 700;
      text-anchor: middle;
      dominant-baseline: middle;
    }

    .map-sub {
      fill: var(--muted);
      font-size: 11px;
      text-anchor: middle;
      dominant-baseline: middle;
    }

    @media (max-width: 860px) {
      main {
        width: min(100vw - 20px, 680px);
        padding: 16px 0;
      }

      .topbar,
      .layout {
        display: grid;
      }

      .status-pill {
        justify-self: start;
      }

      .layout {
        grid-template-columns: 1fr;
      }

      .control-row {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main>
    <header class="topbar">
      <div>
        <h1>Mochi Map Console</h1>
        <p>Local software-only console for fake navigation and text turns.</p>
      </div>
      <div class="status-pill" id="connection-status">Loading snapshot...</div>
    </header>

    <div class="layout">
      <section class="panel map-wrap" aria-label="House map">
        <svg id="map" viewBox="0 0 640 440" role="img" aria-label="Mochi house map"></svg>
      </section>

      <aside class="panel stack">
        <p class="error" id="error"></p>

        <section class="controls" aria-label="Console commands">
          <div>
            <label for="command-input">Fake command</label>
            <div class="control-row">
              <input id="command-input" value="go to kitchen">
              <button id="command-button" type="button">Send</button>
            </div>
          </div>

          <div>
            <label for="voice-input">Fake voice input</label>
            <div class="control-row">
              <input id="voice-input" value="where are you?">
              <button id="voice-button" type="button">Voice turn</button>
            </div>
          </div>
        </section>

        <section class="section" aria-labelledby="state-title">
          <h2 id="state-title">State</h2>
          <div class="state-grid" id="state"></div>
        </section>

        <section class="section" aria-labelledby="last-turn-title">
          <h2 id="last-turn-title">Last Turn</h2>
          <div id="last-turn"></div>
        </section>

        <section class="section" aria-labelledby="no-go-zones-title">
          <h2 id="no-go-zones-title">No-Go Zones</h2>
          <div id="no-go-zones"></div>
        </section>

        <section class="section" aria-labelledby="movement-history-title">
          <h2 id="movement-history-title">Movement History</h2>
          <div id="movement-history"></div>
        </section>
      </aside>
    </div>
  </main>

  <script>
    const map = document.querySelector("#map");
    const stateEl = document.querySelector("#state");
    const lastTurnEl = document.querySelector("#last-turn");
    const noGoZonesEl = document.querySelector("#no-go-zones");
    const movementHistoryEl = document.querySelector("#movement-history");
    const errorEl = document.querySelector("#error");
    const statusEl = document.querySelector("#connection-status");
    const commandInput = document.querySelector("#command-input");
    const voiceInput = document.querySelector("#voice-input");

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function setError(message) {
      errorEl.textContent = message || "";
      errorEl.style.display = message ? "block" : "none";
    }

    async function fetchJson(path, options = {}) {
      const response = await fetch(path, options);
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Request failed.");
      }
      return payload;
    }

    async function refreshSnapshot() {
      setError("");
      const snapshot = await fetchJson("/api/snapshot");
      render(snapshot);
    }

    async function postText(path, text) {
      setError("");
      const snapshot = await fetchJson(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      render(snapshot);
    }

    function render(snapshot) {
      statusEl.textContent = "Current location: " + snapshot.current_location;
      renderState(snapshot);
      renderLastTurn(snapshot.last_turn);
      renderNoGoZones(snapshot.no_go_zones || []);
      renderMovements(snapshot.movements || []);
      renderMap(snapshot);
    }

    function renderState(snapshot) {
      const metrics = [
        ["Robot", snapshot.robot_name],
        ["Location", snapshot.current_location],
        ["Battery", snapshot.battery_percent + "%"],
        ["Mood", snapshot.mood],
        ["Privacy", snapshot.privacy_mode ? "On" : "Off"],
      ];
      stateEl.innerHTML = metrics
        .map(([label, value]) => `
          <div class="metric">
            <span>${escapeHtml(label)}</span>
            <strong>${escapeHtml(value)}</strong>
          </div>
        `)
        .join("");
    }

    function renderLastTurn(turn) {
      if (!turn) {
        lastTurnEl.innerHTML = '<p class="empty">No turns yet.</p>';
        return;
      }
      lastTurnEl.innerHTML = `
        <div class="turn">
          <strong>${escapeHtml(turn.source)}</strong>
          <div>${escapeHtml(turn.input_text)}</div>
          <div>${escapeHtml(turn.response_text)}</div>
        </div>
      `;
    }

    function renderNoGoZones(noGoZones) {
      if (!noGoZones.length) {
        noGoZonesEl.innerHTML = '<p class="empty">No blocked zones.</p>';
        return;
      }
      noGoZonesEl.innerHTML = `
        <ul class="zone-list">
          ${noGoZones.map((zone) => `<li>${escapeHtml(zone)}</li>`).join("")}
        </ul>
      `;
    }

    function renderMovements(movements) {
      if (!movements.length) {
        movementHistoryEl.innerHTML = '<p class="empty">No movements yet.</p>';
        return;
      }
      movementHistoryEl.innerHTML = movements
        .map((movement) => `
          <div class="movement">
            <strong>${escapeHtml(movement.requested_destination)}</strong>
            <div>
              ${escapeHtml(movement.start_location)} -> ${escapeHtml(movement.end_location)}
            </div>
            <div>${escapeHtml(movement.succeeded ? "Succeeded" : "Blocked")}</div>
            <div>${escapeHtml(movement.message)}</div>
          </div>
        `)
        .join("");
    }

    function renderMap(snapshot) {
      const rooms = snapshot.rooms || [];
      const roomById = Object.fromEntries(rooms.map((room) => [room.id, room]));
      const seenConnections = new Set();
      const connectionMarkup = [];

      for (const room of rooms) {
        for (const targetId of room.connected_to || []) {
          const target = roomById[targetId];
          if (!target) continue;
          const key = [room.id, targetId].sort().join(":");
          if (seenConnections.has(key)) continue;
          seenConnections.add(key);
          connectionMarkup.push(`
            <line class="connection" x1="${room.x}" y1="${room.y}"
              x2="${target.x}" y2="${target.y}"></line>
          `);
        }
      }

      const roomMarkup = rooms.map((room) => {
        const classes = [
          "room",
          room.id === snapshot.current_location ? "current" : "",
          room.no_go_zone ? "no-go" : "",
        ].filter(Boolean).join(" ");
        const subLabel = room.no_go_zone ? "no-go zone" : room.id;
        return `
          <g>
            <rect class="${classes}" x="${room.x - 70}" y="${room.y - 38}"
              width="140" height="76" rx="8"></rect>
            <text class="map-label" x="${room.x}" y="${room.y - 6}">
              ${escapeHtml(room.display_name)}
            </text>
            <text class="map-sub" x="${room.x}" y="${room.y + 18}">
              ${escapeHtml(subLabel)}
            </text>
          </g>
        `;
      });

      const current = roomById[snapshot.current_location];
      const robotMarkup = current
        ? `<circle class="robot-dot" cx="${current.x + 48}" cy="${current.y - 28}" r="10"></circle>`
        : "";

      map.innerHTML = [...connectionMarkup, ...roomMarkup, robotMarkup].join("");
    }

    document.querySelector("#command-button").addEventListener("click", () => {
      postText("/api/command", commandInput.value).catch((error) => setError(error.message));
    });

    document.querySelector("#voice-button").addEventListener("click", () => {
      postText("/api/voice-turn", voiceInput.value).catch((error) => setError(error.message));
    });

    refreshSnapshot().catch((error) => {
      statusEl.textContent = "Snapshot unavailable";
      setError(error.message);
    });
  </script>
</body>
</html>
"""
