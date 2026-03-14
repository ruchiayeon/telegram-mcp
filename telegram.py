import json
import httpx
from pathlib import Path
from mcp.server.fastmcp import FastMCP

CONFIG_PATH = Path(__file__).parent / "telegram_config.json"

def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_default_user() -> str:
    config = load_config()
    return config.get("default_user", list(config.keys())[0])

DEFAULT_USER = get_default_user()

def get_user_config(user: str) -> dict:
    config = load_config()
    if user not in config:
        available = ", ".join(k for k in config.keys() if k != "default_user")
        raise ValueError(f"알 수 없는 사용자: {user}. 가능한 사용자: {available}")
    cfg = config[user]
    if not cfg.get("bot_token") or not cfg.get("chat_id"):
        raise ValueError(f"'{user}' 사용자의 bot_token 또는 chat_id가 설정되지 않았습니다.")
    return cfg

mcp = FastMCP("telegram_mcp")


async def _tg(method: str, payload: dict, user: str | None = None) -> dict:
    user = user or DEFAULT_USER
    cfg = get_user_config(user)
    api_url = f"https://api.telegram.org/bot{cfg['bot_token']}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{api_url}/{method}", json=payload)
        r.raise_for_status()
        return r.json()

def get_chat_id(user: str | None = None) -> int:
    user = user or DEFAULT_USER
    cfg = get_user_config(user)
    return int(cfg["chat_id"])

def _err(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        return f"Error: 텔레그램 API 오류 ({e.response.status_code}): {e.response.text}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: 요청 시간 초과."
    return f"Error: {type(e).__name__}: {str(e)}"


import tg_messages
import tg_chat
import tg_interactive
import tg_media

if __name__ == "__main__":
    mcp.run()
