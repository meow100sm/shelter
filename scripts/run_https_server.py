from __future__ import annotations

import os
import ssl
import sys
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


BASE_DIR = Path(__file__).resolve().parent.parent
CERT_DIR = BASE_DIR / "caddy" / "ssl"
CERT_FILE = CERT_DIR / "localhost.cert.pem"
KEY_FILE = CERT_DIR / "localhost.key.pem"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def _to_wsgi_header_name(header_name: str) -> str:
    return "HTTP_" + header_name.upper().replace("-", "_")


class DjangoHTTPSHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        sys.stdout.write("%s\n" % (format % args))

    def _dispatch(self) -> None:
        if self._serve_static_or_media():
            return

        from django.test import Client

        path = self.path
        parsed = urlsplit(path)
        full_path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        print(f"REQ {self.command} {full_path}", flush=True)
        body = b""
        content_length = int(self.headers.get("Content-Length") or 0)
        if content_length:
            body = self.rfile.read(content_length)

        client = Client()
        cookie_header = self.headers.get("Cookie")
        if cookie_header:
            client.cookies.load(cookie_header)

        extra = {
            "HTTP_HOST": self.headers.get("Host", f"localhost:{self.server.server_port}"),
            "HTTP_X_FORWARDED_PROTO": "https",
        }
        for header_name, value in self.headers.items():
            upper_name = header_name.upper().replace("-", "_")
            if upper_name in {"HOST", "CONTENT_LENGTH", "CONTENT_TYPE", "COOKIE"}:
                continue
            extra[_to_wsgi_header_name(header_name)] = value

        content_type = self.headers.get("Content-Type", "application/octet-stream")
        response = client.generic(
            self.command,
            full_path,
            data=body,
            content_type=content_type,
            secure=True,
            **extra,
        )
        print(f"RESP {response.status_code} location={response.get('Location')}", flush=True)

        self.send_response(response.status_code)
        for header_name, header_value in response.items():
            if header_name.lower() in {"content-length", "transfer-encoding", "connection"}:
                continue
            self.send_header(header_name, header_value)

        for cookie in response.cookies.values():
            self.send_header("Set-Cookie", cookie.OutputString())

        response_body = b"" if self.command == "HEAD" else response.content
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        if response_body:
            self.wfile.write(response_body)

    def _serve_static_or_media(self) -> bool:
        parsed = urlsplit(self.path)
        request_path = parsed.path

        if request_path.startswith("/static/"):
            relative_path = request_path[len("/static/"):]
            # Prefer source assets during local HTTPS dev so CSS/JS changes apply immediately
            # without needing `collectstatic`.
            candidates = [BASE_DIR / "static" / relative_path, BASE_DIR / "staticfiles" / relative_path]
        elif request_path.startswith("/media/"):
            relative_path = request_path[len("/media/"):]
            candidates = [BASE_DIR / "media" / relative_path]
        else:
            return False

        for file_path in candidates:
            if file_path.is_file():
                content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
                body = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                # Avoid stale CSS/JS on mobile browsers during local development.
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(body)
                return True

        self.send_error(404, "File not found")
        return True

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch()

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch()

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch()

    def do_PATCH(self) -> None:  # noqa: N802
        self._dispatch()

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch()

    def do_HEAD(self) -> None:  # noqa: N802
        self._dispatch()


def main() -> int:
    os.environ["DJANGO_SETTINGS_MODULE"] = "shelter.settings"
    os.environ["HTTPS_MODE"] = "direct"

    if not CERT_FILE.exists() or not KEY_FILE.exists():
        print("Missing certificate files. Run scripts/generate_local_certs.ps1 first.")
        return 1

    import django

    django.setup()

    host = os.environ.get("HTTPS_HOST", "0.0.0.0")
    port = int(os.environ.get("HTTPS_PORT", "8444"))

    server = ThreadingHTTPServer((host, port), DjangoHTTPSHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(CERT_FILE), keyfile=str(KEY_FILE))
    server.socket = context.wrap_socket(server.socket, server_side=True)

    print(f"Serving HTTPS on https://localhost:{port}/")
    print(f"Also reachable on your LAN IP at the same port, if the certificate SAN includes it.")
    print("Use Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
