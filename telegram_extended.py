"""
telegram_extended.py
4개 도구 모듈을 import하여 mcp에 도구를 등록하고 서버를 실행하는 진입점.

실행 방법:
    python telegram_extended.py
    uv run telegram_extended.py
"""

from telegram import mcp  # noqa: F401

import tg_messages     # noqa: F401
import tg_media        # noqa: F401
import tg_chat         # noqa: F401
import tg_interactive  # noqa: F401

if __name__ == "__main__":
    mcp.run()
