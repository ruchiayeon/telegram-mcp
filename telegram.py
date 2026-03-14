import os
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
mcp          = FastMCP("telegram_mcp")


async def _tg(method: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{TELEGRAM_API}/{method}", json=payload)
        r.raise_for_status()
        return r.json()

def _err(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        return f"Error: 텔레그램 API 오류 ({e.response.status_code}): {e.response.text}"
    if isinstance(e, httpx.TimeoutException):
        return "Error: 요청 시간 초과."
    return f"Error: {type(e).__name__}: {str(e)}"


if __name__ == "__main__":
    mcp.run()
