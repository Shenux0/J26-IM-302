"""The ONE Figma REST client. Nobody else calls Figma directly."""
from __future__ import annotations

import os
import re
from typing import Any

import requests
from dotenv import load_dotenv

FIGMA_API = "https://api.figma.com/v1"
TIMEOUT_S = 60

_URL_KEY = re.compile(r"figma\.com/(?:file|design|proto|board)/([A-Za-z0-9]+)")
_URL_BRANCH = re.compile(r"/branch/([A-Za-z0-9]+)")


class FigmaError(RuntimeError):
    """The token is missing or the Figma API returned an error."""


def parse_file_key(url_or_key: str) -> str:
    """Accept a bare file key or any Figma file URL and return the file key."""
    text = url_or_key.strip()
    if branch := _URL_BRANCH.search(text):
        return branch.group(1)
    if match := _URL_KEY.search(text):
        return match.group(1)
    return text


def get_file(file_key: str) -> dict[str, Any]:
    """Return the full file JSON from ``GET /v1/files/:key``."""
    load_dotenv()
    token = os.getenv("FIGMA_TOKEN", "")
    if not token or token == "your_figma_token_here":
        raise FigmaError("FIGMA_TOKEN is not set. Copy .env.example to .env and add your token.")

    resp = requests.get(
        f"{FIGMA_API}/files/{file_key}",
        headers={"X-Figma-Token": token},
        timeout=TIMEOUT_S,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("err") or resp.json().get("message") or resp.text
        except ValueError:
            detail = resp.text
        raise FigmaError(f"Figma API returned {resp.status_code} for '{file_key}': {detail}")
    return resp.json()
