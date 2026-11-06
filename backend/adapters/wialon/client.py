import asyncio
import json
from typing import Any

import httpx

from domain.errors import UpstreamError, UpstreamUnavailable

_INVALID_SESSION = 1
_TIMEOUT_SECONDS = 10.0


class WialonClient:
    """Cliente HTTP mínimo para Wialon Remote API. Sin lógica de negocio."""

    def __init__(self, host: str, token: str) -> None:
        base = host.strip().rstrip("/").removesuffix("/wialon/ajax.html")
        self._url: str = f"{base}/wialon/ajax.html"
        self._token: str = token
        self._sid: str | None = None
        self._lock: asyncio.Lock = asyncio.Lock()
        self._http: httpx.AsyncClient = httpx.AsyncClient(timeout=_TIMEOUT_SECONDS)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def login(self) -> None:
        async with self._lock:
            await self._login_locked()

    async def call(self, svc: str, params: dict[str, Any]) -> Any:
        sid = await self._ensure_sid()
        result = await self._post(svc, params, sid)
        if self._error_code(result) == _INVALID_SESSION:
            # Sesión inválida: re-login (una sola vez) y un único reintento.
            sid = await self._relogin(stale_sid=sid)
            result = await self._post(svc, params, sid)
        self._raise_if_error(result)
        return result

    # --- internos ---------------------------------------------------------

    async def _ensure_sid(self) -> str:
        async with self._lock:
            if self._sid is None:
                await self._login_locked()
            assert self._sid is not None
            return self._sid

    async def _relogin(self, stale_sid: str) -> str | None:
        async with self._lock:
            # Si otra corrutina ya renovó la sesión, reutilizarla.
            if self._sid is None or self._sid == stale_sid:
                await self._login_locked()
            assert self._sid is not None
            return self._sid

    async def _login_locked(self) -> None:
        data = await self._post(
            "token/login", {"token": self._token, "fl": 1}, sid=None
        )
        self._raise_if_error(data)
        eid = data.get("eid") if isinstance(data, dict) else None
        if not isinstance(eid, str) or not eid:
            raise UpstreamUnavailable("Respuesta de login sin 'eid'")
        self._sid = eid

    async def _post(self, svc: str, params: dict[str, Any], sid: str | None) -> Any:
        form: dict[str, str] = {"svc": svc, "params": json.dumps(params)}
        if sid is not None:
            form["sid"] = sid
        try:
            response = await self._http.post(self._url, data=form)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            # El servidor respondió, pero con un código no 2xx.
            raise UpstreamUnavailable(
                f"Wialon respondió HTTP {exc.response.status_code}"
            ) from None
        except httpx.HTTPError as exc:
            # Timeout, conexión rechazada, DNS... no hay response.
            raise UpstreamUnavailable(
                f"Wialon no disponible ({type(exc).__name__})"
            ) from None
        except ValueError:
            raise UpstreamUnavailable("Respuesta de Wialon no es JSON válido") from None

    @staticmethod
    def _error_code(data: Any) -> int:
        if isinstance(data, dict):
            code = data.get("error", 0)
            if isinstance(code, int):
                return code
        return 0

    @classmethod
    def _raise_if_error(cls, data: Any) -> None:
        code = cls._error_code(data)
        if code != 0:
            raise UpstreamError(code, f"Wialon devolvió error {code}")
