"""Session tracking and revocation."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from cobra_core.security.audit import SECURITY_AUDIT
from cobra_core.security.config import SecurityConfig, load_security_config
from cobra_core.security.errors import SecurityError, SecurityErrorCode
from cobra_core.security.metrics import SECURITY_METRICS
from cobra_core.security.schemas import AuthMethod
from cobra_core.security.tokens import issue_opaque_token, token_fingerprint


@dataclass
class Session:
    session_id: str
    principal_id: str
    roles: list[str]
    permissions: list[str]
    authentication_method: AuthMethod
    issued_at: float
    expires_at: float
    revoked: bool = False
    token_fingerprint: str = ""
    _token: str = field(default="", repr=False)

    def public_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "principal_id": self.principal_id,
            "roles": list(self.roles),
            "permissions": list(self.permissions),
            "authentication_method": self.authentication_method.value,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "token_fingerprint": self.token_fingerprint,
            # Never expose raw token
        }

    def is_active(self, *, now: float | None = None) -> bool:
        ts = time.time() if now is None else now
        return not self.revoked and ts < self.expires_at


class SessionStore:
    def __init__(self, *, config: SecurityConfig | None = None) -> None:
        self.config = config or load_security_config()
        self._lock = threading.Lock()
        self._sessions: dict[str, Session] = {}
        self._by_token_fp: dict[str, str] = {}

    def reset_for_tests(self) -> None:
        with self._lock:
            self._sessions.clear()
            self._by_token_fp.clear()
        SECURITY_METRICS.set_active_sessions(0)

    def _sync_metric(self) -> None:
        now = time.time()
        active = sum(1 for s in self._sessions.values() if s.is_active(now=now))
        SECURITY_METRICS.set_active_sessions(active)

    def create(
        self,
        *,
        principal_id: str,
        roles: list[str],
        permissions: list[str],
        authentication_method: AuthMethod = AuthMethod.SESSION,
        ttl_seconds: int | None = None,
    ) -> tuple[Session, str]:
        ttl = ttl_seconds if ttl_seconds is not None else self.config.session_ttl_seconds
        now = time.time()
        token = issue_opaque_token()
        fp = token_fingerprint(token)
        sid = f"sess_{uuid.uuid4().hex[:16]}"
        session = Session(
            session_id=sid,
            principal_id=principal_id,
            roles=list(roles),
            permissions=sorted(set(permissions)),
            authentication_method=authentication_method,
            issued_at=now,
            expires_at=now + max(60, int(ttl)),
            token_fingerprint=fp,
            _token=token,
        )
        with self._lock:
            self._sessions[sid] = session
            self._by_token_fp[fp] = sid
            self._sync_metric()
        SECURITY_AUDIT.record(
            "session_created",
            principal_id=principal_id,
            result="ok",
            session_id=sid,
            authentication_method=authentication_method.value,
        )
        return session, token

    def get(self, session_id: str) -> Session:
        with self._lock:
            try:
                return self._sessions[session_id]
            except KeyError as exc:
                raise SecurityError(
                    SecurityErrorCode.SESSION_NOT_FOUND, f"session not found: {session_id}"
                ) from exc

    def resolve_token(self, token: str) -> Session:
        fp = token_fingerprint(token)
        with self._lock:
            sid = self._by_token_fp.get(fp)
            if not sid:
                raise SecurityError(SecurityErrorCode.SESSION_NOT_FOUND, "session not found")
            session = self._sessions[sid]
        if session.revoked:
            raise SecurityError(SecurityErrorCode.SESSION_REVOKED, "session revoked")
        if not session.is_active():
            raise SecurityError(SecurityErrorCode.SESSION_EXPIRED, "session expired")
        if session._token != token:
            raise SecurityError(SecurityErrorCode.SESSION_NOT_FOUND, "session not found")
        return session

    def revoke(self, session_id: str, *, actor: str = "admin") -> Session:
        with self._lock:
            try:
                session = self._sessions[session_id]
            except KeyError as exc:
                raise SecurityError(
                    SecurityErrorCode.SESSION_NOT_FOUND, f"session not found: {session_id}"
                ) from exc
            session.revoked = True
            self._sync_metric()
        SECURITY_AUDIT.record(
            "session_revoked",
            principal_id=session.principal_id,
            result="revoked",
            session_id=session_id,
            actor=actor,
        )
        return session

    def list_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._sessions[k].public_dict() for k in sorted(self._sessions)]


SESSION_STORE = SessionStore()
