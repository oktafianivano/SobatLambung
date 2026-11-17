"""Kumpulan router API dengan versi eksplisit.

Struktur:
- ``/api/v1/...``  -> versi resmi (tampil di dokumentasi /docs)
- ``/api/...``     -> alias lama untuk kompatibilitas klien/browser yang
  masih menyimpan URL versi sebelumnya (tidak ditampilkan di /docs).

Dengan cara ini perubahan versi berikutnya bisa rilis di ``/api/v2`` tanpa
merusak integrasi yang sudah berjalan.
"""

from fastapi import APIRouter

from app.api.endpoints import admin, auth, public, users

API_V1_PREFIX = "/api/v1"
API_LEGACY_PREFIX = "/api"


def _build_router(prefix: str, include_in_schema: bool) -> APIRouter:
    router = APIRouter(prefix=prefix, include_in_schema=include_in_schema)
    router.include_router(public.router, tags=["Public"])
    router.include_router(auth.router, prefix="/auth", tags=["Auth"])
    router.include_router(users.router, prefix="/user", tags=["User Dashboard"])
    router.include_router(admin.router, prefix="/admin", tags=["Admin Tools"])
    return router


api_v1_router = _build_router(API_V1_PREFIX, include_in_schema=True)
api_legacy_router = _build_router(API_LEGACY_PREFIX, include_in_schema=False)
