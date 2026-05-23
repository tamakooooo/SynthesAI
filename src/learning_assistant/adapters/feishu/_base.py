"""Shared base for Feishu API clients."""

from __future__ import annotations

import os
import threading
import time
from typing import Any

import requests
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from learning_assistant.adapters.feishu.models import FeishuKnowledgeBaseConfig


FEISHU_API_BASE = "https://open.feishu.cn/open-apis"
_TOKEN_REFRESH_BUFFER_SECONDS = 300


class FeishuBaseClient:
    """Common HTTP session, token caching, and error handling."""

    _token_cache: dict[tuple[str, str], tuple[str, float]] = {}
    _token_lock = threading.Lock()

    def __init__(self, config: FeishuKnowledgeBaseConfig) -> None:
        self.config = config
        self.base_url = FEISHU_API_BASE
        self.session = self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST", "PATCH", "PUT", "DELETE"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _raise_for_business_error(self, payload: dict[str, Any]) -> None:
        code = payload.get("code")
        if code not in (None, 0):
            raise RuntimeError(
                f"Feishu API error {code}: {payload.get('msg', 'unknown error')}"
            )

    def _get_tenant_access_token(self) -> str:
        app_id = self.config.app_id or os.environ.get(self.config.app_id_env)
        app_secret = self.config.app_secret or os.environ.get(self.config.app_secret_env)
        if not app_id or not app_secret:
            raise RuntimeError(
                "Missing Feishu credentials. "
                f"Set app_id/app_secret in config or set "
                f"{self.config.app_id_env}/{self.config.app_secret_env} env vars."
            )

        cache_key = (app_id, app_secret)
        now = time.time()

        with FeishuBaseClient._token_lock:
            cached = FeishuBaseClient._token_cache.get(cache_key)
            if cached and cached[1] - _TOKEN_REFRESH_BUFFER_SECONDS > now:
                return cached[0]

        response = self.session.post(
            f"{self.base_url}/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_business_error(payload)
        token = payload.get("tenant_access_token")
        if not token:
            raise RuntimeError(f"Failed to obtain Feishu tenant access token: {payload}")

        expire_seconds = int(payload.get("expire", 7200))
        expires_at = now + expire_seconds
        with FeishuBaseClient._token_lock:
            FeishuBaseClient._token_cache[cache_key] = (token, expires_at)
        logger.debug(f"Feishu token cached for {expire_seconds}s")
        return token

    @classmethod
    def clear_token_cache(cls) -> None:
        with cls._token_lock:
            cls._token_cache.clear()

    def _auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
