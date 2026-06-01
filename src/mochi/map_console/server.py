import json
import socketserver
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from mochi.map_console.runtime import MapConsoleRuntime
from mochi.map_console.static import APP_HTML


class LocalMapConsoleServer(ThreadingHTTPServer):
    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = str(host)
        self.server_port = int(port)


def create_server(
    runtime: MapConsoleRuntime,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self._send_html(APP_HTML)
                return
            if path == "/api/snapshot":
                self._send_json(runtime.snapshot().model_dump(mode="json"))
                return
            self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            try:
                payload = self._read_json()
                text = payload.get("text", "")
                if not isinstance(text, str):
                    raise ValueError("text must be a string.")
                if path == "/api/command":
                    snapshot = runtime.handle_command(text)
                    self._send_json(snapshot.model_dump(mode="json"))
                    return
                if path == "/api/voice-turn":
                    snapshot = runtime.handle_voice_text(text)
                    self._send_json(snapshot.model_dump(mode="json"))
                    return
                self._send_json({"error": "Not found."}, status=HTTPStatus.NOT_FOUND)
            except (json.JSONDecodeError, ValueError) as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            if not raw_body:
                return {}
            payload = json.loads(raw_body)
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object.")
            return payload

        def _send_html(self, html: str) -> None:
            encoded = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(
            self,
            payload: dict[str, Any],
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return LocalMapConsoleServer((host, port), Handler)
