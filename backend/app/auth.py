from __future__ import annotations

import base64
import json
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse

from .db import (
    delete_auth_session_async,
    get_auth_session_async,
    upsert_auth_session_async,
)

logger = logging.getLogger("app.auth")

AUTH_BASE_URL = "https://login.eveonline.com"
AUTHORIZE_URL = f"{AUTH_BASE_URL}/v2/oauth/authorize"
TOKEN_URL = f"{AUTH_BASE_URL}/v2/oauth/token"
VERIFY_URL = f"{AUTH_BASE_URL}/oauth/verify"
ESI_LOCATION_URL = "https://esi.evetech.net/latest/characters/{character_id}/location/"
ESI_NAMES_URL = "https://esi.evetech.net/latest/universe/names/"
REQUIRED_SCOPE = "esi-location.read_location.v1 esi-location.read_ship_type.v1 esi-location.read_online.v1 esi-wallet.read_character_wallet.v1 esi-skills.read_skills.v1 esi-skills.read_skillqueue.v1 esi-assets.read_assets.v1"
STATE_COOKIE = "eve_oauth_state"
RETURN_PATH_COOKIE = "eve_return_path"
SESSION_COOKIE = "session_id"
SESSION_COOKIE_MAX_AGE = 7 * 24 * 60 * 60
LOGIN_STATE_MAX_AGE = 10 * 60
RETURN_PATH_MAX_AGE = 10 * 60
TOKEN_REFRESH_WINDOW = timedelta(seconds=60)

router = APIRouter()


def _get_required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing environment variable {name}")
    return value


def _get_client_id() -> str:
    return _get_required_env("EVE_CLIENT_ID")


def _get_client_secret() -> str:
    return _get_required_env("EVE_CLIENT_SECRET")


def _get_callback_url() -> str:
    return _get_required_env("EVE_CALLBACK_URL")


def _is_safe_redirect_path(path: str) -> bool:
    return bool(path and path.startswith("/") and not path.startswith("//"))


def _encode_state(csrf_token: str, return_path: str) -> str:
    data = json.dumps({"csrf": csrf_token, "next": return_path})
    return base64.urlsafe_b64encode(data.encode("utf-8")).decode("utf-8")


def _decode_state(state: str) -> dict[str, str] | None:
    try:
        payload = base64.urlsafe_b64decode(state.encode("utf-8"))
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return None


def _build_login_url(state: str, prompt: str | None = None) -> str:
    params = {
        "response_type": "code",
        "redirect_uri": _get_callback_url(),
        "client_id": _get_client_id(),
        "scope": REQUIRED_SCOPE,
        "state": state,
    }
    if prompt == "consent":
        params["prompt"] = "consent"
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def _extract_scope(data: dict[str, Any] | None) -> str | None:
    if not data:
        return None

    for key in ("scope", "scopes", "Scopes", "Scope"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list) and value:
            return " ".join(str(item) for item in value if item)

    return None


def _get_session_id_from_request(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def _create_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        path="/",
        httponly=True,
        samesite="lax",
        max_age=SESSION_COOKIE_MAX_AGE,
    )


def _create_return_path_cookie(response: Response, path: str) -> None:
    response.set_cookie(
        RETURN_PATH_COOKIE,
        path,
        path="/",
        httponly=True,
        samesite="lax",
        max_age=RETURN_PATH_MAX_AGE,
    )


def _get_return_path_from_request(request: Request) -> str | None:
    return request.query_params.get("next") or request.cookies.get(RETURN_PATH_COOKIE)


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.delete_cookie(STATE_COOKIE, path="/")
    response.delete_cookie(RETURN_PATH_COOKIE, path="/")


async def _get_auth_session_or_401(request: Request) -> dict[str, Any]:
    session_id = _get_session_id_from_request(request)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session = await get_auth_session_async(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return session


async def get_optional_auth_session(request: Request) -> dict[str, Any] | None:
    session_id = _get_session_id_from_request(request)
    if not session_id:
        return None
    return await get_auth_session_async(session_id)


async def _refresh_token(session: dict[str, Any]) -> dict[str, Any]:
    client_id = _get_client_id()
    client_secret = _get_client_secret()
    refresh_token = session["refresh_token"]

    headers = {"Accept": "application/json"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(TOKEN_URL, auth=(client_id, client_secret), data=data, headers=headers)

    if response.status_code != 200:
        logger.warning("Failed to refresh EVE token for session %s: %s", session["session_id"], response.text)
        await delete_auth_session_async(session["session_id"])
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication expired")

    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = int(token_data.get("expires_in", 0))
    token_type = token_data.get("token_type")
    scope = _extract_scope(token_data) or session.get("scope")

    if not access_token or not refresh_token or expires_in <= 0:
        logger.error("Invalid refresh token response: %s", token_data)
        await delete_auth_session_async(session["session_id"])
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication expired")

    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
    await upsert_auth_session_async(
        session_id=session["session_id"],
        character_id=session["character_id"],
        character_name=session["character_name"],
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        token_type=token_type,
        scope=scope,
    )
    return await get_auth_session_async(session["session_id"])


async def _ensure_fresh_token(session: dict[str, Any]) -> dict[str, Any]:
    expires_at = datetime.fromisoformat(session["expires_at"])
    if datetime.utcnow() + TOKEN_REFRESH_WINDOW >= expires_at:
        return await _refresh_token(session)
    return session


async def _fetch_location(access_token: str, character_id: int) -> dict[str, Any]:
    url = ESI_LOCATION_URL.format(character_id=character_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = {"datasource": "tranquility"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers, params=params)

    if response.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid EVE token")
    if response.status_code != 200:
        logger.warning("Unexpected ESI location response %s for character %s", response.status_code, character_id)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to load location")

    return response.json()


async def _resolve_system_name(system_id: int) -> str | None:
    params = {"datasource": "tranquility"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(ESI_NAMES_URL, params=params, json=[system_id])

    if response.status_code != 200:
        logger.warning("Failed to resolve system name for %s: %s", system_id, response.text)
        return None

    data = response.json()
    if isinstance(data, list) and data:
        entry = data[0]
        return entry.get("name")
    return None


async def _verify_access_token(access_token: str) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(VERIFY_URL, headers=headers)

    if response.status_code != 200:
        logger.error("EVE verify failed: %s", response.text)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to verify EVE identity")

    return response.json()


@router.get("/auth/login")
async def login(request: Request, response: Response) -> Response:
    csrf_token = secrets.token_urlsafe(24)
    session_id = secrets.token_urlsafe(32)
    next_path = request.query_params.get("next", "/nearby")
    if not _is_safe_redirect_path(next_path):
        next_path = "/nearby"

    prompt = request.query_params.get("prompt")
    if prompt != "consent":
        prompt = None

    state = _encode_state(csrf_token, next_path)
    auth_url = _build_login_url(state, prompt)

    response = RedirectResponse(url=auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        STATE_COOKIE,
        csrf_token,
        path="/",
        httponly=True,
        samesite="lax",
        max_age=LOGIN_STATE_MAX_AGE,
    )
    _create_session_cookie(response, session_id)
    _create_return_path_cookie(response, next_path)
    return response


@router.get("/auth/callback")
async def callback(request: Request) -> Response:
    error = request.query_params.get("error")
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"EVE authorization failed: {error}")

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    stored_csrf = request.cookies.get(STATE_COOKIE)
    state_data = _decode_state(state) if state else None
    if not code or not state or not state_data or state_data.get("csrf") != stored_csrf:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or missing authorization state")

    client_id = _get_client_id()
    client_secret = _get_client_secret()
    callback_url = _get_callback_url()

    headers = {"Accept": "application/json"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": callback_url,
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(TOKEN_URL, auth=(client_id, client_secret), data=data, headers=headers)

    if response.status_code != 200:
        logger.error("EVE token exchange failed: %s", response.text)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to exchange authorization code")

    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = int(token_data.get("expires_in", 0))
    token_type = token_data.get("token_type")
    scope = _extract_scope(token_data)

    if not access_token or not refresh_token or expires_in <= 0:
        logger.error("Invalid token response from EVE: %s", token_data)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid authorization response")

    verify_data = await _verify_access_token(access_token)
    if not scope:
        scope = _extract_scope(verify_data)
    if not scope:
        scope = REQUIRED_SCOPE
    character_id = int(
        token_data.get("CharacterID")
        or token_data.get("character_id")
        or verify_data.get("CharacterID")
        or verify_data.get("character_id")
        or 0
    )
    character_name = (
        token_data.get("CharacterName")
        or token_data.get("character_name")
        or verify_data.get("CharacterName")
        or verify_data.get("character_name")
        or ""
    )

    if character_id <= 0 or not character_name:
        logger.error("Invalid token or verify response from EVE: %s / %s", token_data, verify_data)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Invalid authorization response")

    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
    session_id = _get_session_id_from_request(request) or secrets.token_urlsafe(32)

    await upsert_auth_session_async(
        session_id=session_id,
        character_id=character_id,
        character_name=character_name,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        token_type=token_type,
        scope=scope,
    )

    return_path = None
    if state_data and isinstance(state_data, dict):
        return_path = state_data.get("next")
    if not _is_safe_redirect_path(return_path):
        return_path = request.cookies.get(RETURN_PATH_COOKIE)
    if not _is_safe_redirect_path(return_path):
        return_path = "/nearby"

    response = RedirectResponse(url=return_path, status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(STATE_COOKIE, path="/")
    response.delete_cookie(RETURN_PATH_COOKIE, path="/")
    _create_session_cookie(response, session_id)
    return response


@router.get("/auth/me")
async def me(request: Request) -> JSONResponse:
    session = await _get_auth_session_or_401(request)
    return JSONResponse(
        {
            "character_id": session["character_id"],
            "character_name": session["character_name"],
            "scope": session["scope"],
            "expires_at": session["expires_at"],
        }
    )


@router.get("/auth/location")
async def location(request: Request) -> JSONResponse:
    session = await _get_auth_session_or_401(request)
    session = await _ensure_fresh_token(session)
    access_token = session["access_token"]
    character_id = session["character_id"]
    location_data = await _fetch_location(access_token, character_id)
    system_id = location_data.get("solar_system_id") or location_data.get("system_id")
    if system_id:
        system_name = await _resolve_system_name(system_id)
        if system_name:
            location_data["system_name"] = system_name
    return JSONResponse(location_data)


@router.post("/auth/logout")
async def logout(request: Request) -> JSONResponse:
    session_id = _get_session_id_from_request(request)
    if session_id:
        await delete_auth_session_async(session_id)

    response = JSONResponse({"status": "logged_out"})
    _clear_session_cookie(response)
    return response
