"""Test kontrak routing: versi v1 wajib ada, alias lama tetap hidup.

Test ini tidak membuka koneksi database (endpoint yang diuji hanya membaca
data statis dan lifespan aplikasi tidak dijalankan), sehingga aman dipakai
di CI tanpa Supabase.
"""

import asyncio

import httpx
from fastapi import FastAPI

from app.api.router import API_LEGACY_PREFIX, API_V1_PREFIX, api_legacy_router, api_v1_router


def _build_test_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_v1_router)
    app.include_router(api_legacy_router)
    return app


APP = _build_test_app()
SCHEMA_PATHS = set(APP.openapi()["paths"].keys())


def _get(path: str) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=APP)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(path)

    return asyncio.run(run())


def test_prefixes_are_explicit():
    assert API_V1_PREFIX == "/api/v1"
    assert API_LEGACY_PREFIX == "/api"


def test_public_endpoints_available_in_v1():
    assert "/api/v1/education/content" in SCHEMA_PATHS
    assert "/api/v1/schedules" in SCHEMA_PATHS


def test_auth_endpoints_available_in_v1():
    for path in ("/register", "/login", "/forgot-password/request", "/forgot-password/reset"):
        assert f"/api/v1/auth{path}" in SCHEMA_PATHS


def test_user_endpoints_available_in_v1():
    for path in ("/profile", "/toggle-alarm", "/test-notification", "/change-password"):
        assert f"/api/v1/user{path}" in SCHEMA_PATHS


def test_admin_endpoints_available_in_v1():
    for path in ("/create", "/list", "/update/{user_id}", "/delete/{user_id}"):
        assert f"/api/v1/admin{path}" in SCHEMA_PATHS


def test_legacy_paths_hidden_from_docs():
    legacy_in_schema = [p for p in SCHEMA_PATHS if p.startswith("/api/") and not p.startswith("/api/v1/")]
    assert legacy_in_schema == []


def test_v1_endpoint_responds():
    response = _get("/api/v1/schedules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_legacy_endpoint_still_responds():
    response = _get("/api/schedules")
    assert response.status_code == 200
    assert response.json() == _get("/api/v1/schedules").json()
