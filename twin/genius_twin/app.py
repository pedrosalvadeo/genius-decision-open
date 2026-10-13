"""Loopback-only host for the shared declared-model product API."""
from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlsplit

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

from .service import TwinService, ServiceError
from .store import Store
from .http_api import make_blueprint


def create_app(database_path=None, testing=False, evaluator=None):
    """Create an application; the runner must bind exclusively to 127.0.0.1.

    ``evaluator`` injection is for service conformance tests. The default uses
    the real FP1 compiler and received kernel, without an external provider.
    """
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.update(TESTING=testing, MAX_CONTENT_LENGTH=262144)
    database_path = database_path or Path(__file__).resolve().parents[2] / "local-data" / "twin.sqlite3"
    service = TwinService(Store(database_path), evaluator=evaluator)
    app.extensions["twin_service"] = service

    @app.before_request
    def local_boundary():
        host = request.host.lower()
        if not re.fullmatch(r"(?:127\.0\.0\.1|localhost|\[::1\])(?::[0-9]{1,5})?", host):
            raise ServiceError("host_not_allowed", "Esta aplicación solo admite el host local.", 403)
        origin = request.headers.get("Origin")
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != host or parsed.path or parsed.query or parsed.fragment:
                raise ServiceError("origin_not_allowed", "El origen no corresponde a esta aplicación local.", 403)
        if request.headers.get("Sec-Fetch-Site") == "cross-site":
            raise ServiceError("cross_site_not_allowed", "Solicitud entre sitios no admitida.", 403)
        if request.method in {"POST", "PATCH", "PUT", "DELETE"} and request.mimetype != "application/json":
            raise ServiceError("json_required", "Las operaciones requieren JSON explícito.", 415)

    @app.after_request
    def security_headers(response):
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

    @app.errorhandler(ServiceError)
    def service_error(exc):
        return jsonify(error={"code": exc.code, "message": exc.message, "details": exc.details}), exc.status

    @app.errorhandler(HTTPException)
    def http_error(exc):
        return jsonify(error={"code": "http_error", "message": exc.name, "details": None}), exc.code

    @app.errorhandler(Exception)
    def unexpected(exc):
        app.logger.error("Local request failed class=%s", type(exc).__name__)
        return jsonify(error={"code": "internal_error", "message": "La operación no pudo completarse.", "details": None}), 500

    @app.get("/")
    def home():
        return app.send_static_file("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="local_ready", empirical_validation="NOT_ASSESSED")

    app.register_blueprint(make_blueprint(lambda: service), url_prefix="/api")
    return app
