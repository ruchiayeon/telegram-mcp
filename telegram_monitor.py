"""
telegram_monitor.py
Telethon User API 기반 텔레그램 채널 실시간 모니터링 (메시지 로깅)
"""

import asyncio
import logging
import os
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import Message

# ─────────────────────────────────────────────
# 환경변수 로드
# ─────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("telegram_monitor")


# ─────────────────────────────────────────────
# 설정 (여기서 커스터마이징)
# ─────────────────────────────────────────────
class Config:
    # Telegram 인증
    API_ID: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    API_HASH: str = os.getenv("TELEGRAM_API_HASH", "")
    PHONE: str = os.getenv("TELEGRAM_PHONE", "")

    # 세션 파일명 (telegram_session.session 파일로 저장됨)
    SESSION_NAME: str = os.getenv("SESSION_NAME", "telegram_session")

    # ── 모니터링할 채널 목록 ──
    # username 문자열("@channelname" 또는 "channelname") 또는 채널 ID(음수 정수) 모두 지원
    MONITOR_CHANNELS: list = [
        # 예시 — 사용 전에 본인 채널로 교체하세요
        # "some_channel_username",
        # -1001234567890,
    ]


# ─────────────────────────────────────────────
# 메인 모니터 클래스
# ─────────────────────────────────────────────
class TelegramMonitor:
    def __init__(self):
        self.client = TelegramClient(
            Config.SESSION_NAME,
            Config.API_ID,
            Config.API_HASH,
        )

    # ── 채널 식별자 정규화 ──
    @staticmethod
    def _channel_key(chat) -> str:
        """채널 객체에서 일관된 문자열 키를 추출"""
        if hasattr(chat, "username") and chat.username:
            return f"@{chat.username}"
        return str(chat.id)

    # ── 이벤트 핸들러 ──
    async def _on_new_message(self, event: events.NewMessage.Event):
        msg: Message = event.message
        if not msg.text:
            return  # 텍스트 없는 미디어 등 스킵

        chat = await event.get_chat()
        key = self._channel_key(chat)

        # sender 이름 추출
        try:
            sender = await event.get_sender()
            sender_name = (
                getattr(sender, "username", None)
                or getattr(sender, "first_name", None)
                or "Unknown"
            )
        except Exception:
            sender_name = "Unknown"

        logger.info("[%s] %s: %s", key, sender_name, msg.text[:80])

    # ── 메인 실행 ──
    async def run(self):
        if not Config.API_ID or not Config.API_HASH or not Config.PHONE:
            raise ValueError(
                "TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_PHONE 환경변수를 설정하세요."
            )
        if not Config.MONITOR_CHANNELS:
            raise ValueError(
                "Config.MONITOR_CHANNELS 목록이 비어 있습니다. "
                "telegram_monitor.py 상단의 MONITOR_CHANNELS에 채널을 추가하세요."
            )

        await self.client.start(phone=Config.PHONE)
        logger.info("텔레그램 로그인 완료")

        # 채널 등록 — username 문자열은 앞의 @ 제거
        resolved_channels = []
        for ch in Config.MONITOR_CHANNELS:
            if isinstance(ch, str):
                resolved_channels.append(ch.lstrip("@"))
            else:
                resolved_channels.append(ch)

        # 이벤트 핸들러 등록
        self.client.add_event_handler(
            self._on_new_message,
            events.NewMessage(chats=resolved_channels),
        )
        logger.info("모니터링 시작 | 채널: %s", resolved_channels)

        # 연결 유지
        await self.client.run_until_disconnected()


# ─────────────────────────────────────────────
# 진입점
# ─────────────────────────────────────────────
if __name__ == "__main__":
    monitor = TelegramMonitor()
    asyncio.run(monitor.run())
