"""tg_chat.py — 채팅 정보/관리 도구 (8개)"""

from telegram import mcp, _tg, _err, get_chat_id, DEFAULT_USER

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ── Input 모델 ────────────────────────────────────────────

class GetChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[str] = Field(default=None, description="사용자 (telegram_config.json에 정의된 사용자 이름)")


class PinMessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[str] = Field(default=None, description="사용자 (telegram_config.json에 정의된 사용자 이름)")
    message_id:           int  = Field(..., description="고정할 메시지 ID")
    disable_notification: bool = Field(default=False, description="알림 없이 고정")


class UnpinMessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[str] = Field(default=None, description="사용자 (telegram_config.json에 정의된 사용자 이름)")
    message_id: Optional[int] = Field(default=None, description="고정 해제할 메시지 ID (None이면 최신 고정 메시지)")


class BanUserInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[str] = Field(default=None, description="사용자 (telegram_config.json에 정의된 사용자 이름)")
    user_id:    int           = Field(..., description="차단할 사용자 ID")
    until_date: Optional[int] = Field(default=None, description="차단 해제 Unix 타임스탬프 (None=영구)")


class UnbanUserInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[str] = Field(default=None, description="사용자 (telegram_config.json에 정의된 사용자 이름)")
    user_id:        int  = Field(..., description="차단 해제할 사용자 ID")
    only_if_banned: bool = Field(default=True, description="차단된 경우에만 해제")


class SendChatActionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user: Optional[str] = Field(default=None, description="사용자 (telegram_config.json에 정의된 사용자 이름)")
    action: str = Field(..., description="액션: typing, upload_photo, upload_video, upload_document, record_voice 등")


# ── 도구 등록 ─────────────────────────────────────────────

@mcp.tool(
    name="telegram_get_chat",
    annotations={"title": "텔레그램 채팅 정보 조회", "readOnlyHint": True, "destructiveHint": False},
)
async def telegram_get_chat(params: GetChatInput) -> str:
    """채팅 ID로 채팅/그룹/채널의 상세 정보를 조회합니다.

    Args:
        params (GetChatInput):
            - chat_id (int): 조회할 채팅 ID

    Returns:
        str: 채팅 이름, 타입, 멤버 수, 설명 등의 JSON 정보
    """
    try:
        chat_id = get_chat_id(params.user)
        result = await _tg("getChat", {"chat_id": chat_id}, user=params.user)
        chat   = result.get("result", {})
        info   = {
            "id":          chat.get("id"),
            "type":        chat.get("type"),
            "title":       chat.get("title") or chat.get("first_name"),
            "username":    chat.get("username"),
            "description": chat.get("description"),
            "member_count": chat.get("member_count"),
        }
        return json.dumps(info, ensure_ascii=False, indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_get_chat_members_count",
    annotations={"title": "텔레그램 채팅 멤버 수 조회", "readOnlyHint": True, "destructiveHint": False},
)
async def telegram_get_chat_members_count(params: GetChatInput) -> str:
    """채팅/그룹/채널의 총 멤버(구독자) 수를 조회합니다.

    Args:
        params (GetChatInput):
            - chat_id (int): 조회할 채팅 ID

    Returns:
        str: 멤버 수 또는 에러
    """
    try:
        chat_id = get_chat_id(params.user)
        result = await _tg("getChatMemberCount", {"chat_id": chat_id}, user=params.user)
        count  = result.get("result", 0)
        return f"👥 멤버 수: {count:,}명"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_get_me",
    annotations={"title": "봇 정보 조회", "readOnlyHint": True, "destructiveHint": False},
)
async def telegram_get_me(user: str | None = None) -> str:
    """현재 봇의 기본 정보(이름, username, id 등)를 조회합니다.

    Args:
        user (str): 사용자 (telegram_config.json에 정의된 사용자 이름)

    Returns:
        str: 봇 정보 JSON 또는 에러
    """
    try:
        result = await _tg("getMe", {}, user=user)
        bot    = result.get("result", {})
        info   = {
            "id":         bot.get("id"),
            "first_name": bot.get("first_name"),
            "username":   bot.get("username"),
            "is_bot":     bot.get("is_bot"),
            "can_join_groups":          bot.get("can_join_groups"),
            "can_read_all_group_messages": bot.get("can_read_all_group_messages"),
        }
        return json.dumps(info, ensure_ascii=False, indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_pin_message",
    annotations={"title": "텔레그램 메시지 고정", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_pin_message(params: PinMessageInput) -> str:
    """채팅에서 특정 메시지를 고정합니다. (봇이 관리자 권한 필요)

    Args:
        params (PinMessageInput):
            - chat_id (int): 채팅 ID
            - message_id (int): 고정할 메시지 ID
            - disable_notification (bool): 알림 없이 고정 여부 (기본 False)

    Returns:
        str: 고정 성공 메시지 또는 에러
    """
    try:
        chat_id = get_chat_id(params.user)
        await _tg("pinChatMessage", {
            "chat_id":              chat_id,
            "message_id":           params.message_id,
            "disable_notification": params.disable_notification,
        }, user=params.user)
        return f"📌 메시지 고정 완료 (message_id: {params.message_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_unpin_message",
    annotations={"title": "텔레그램 메시지 고정 해제", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_unpin_message(params: UnpinMessageInput) -> str:
    """채팅에서 고정된 메시지를 해제합니다. (봇이 관리자 권한 필요)

    Args:
        params (UnpinMessageInput):
            - chat_id (int): 채팅 ID
            - message_id (int): 고정 해제할 메시지 ID (None이면 가장 최근 고정 메시지)

    Returns:
        str: 고정 해제 성공 메시지 또는 에러
    """
    try:
        chat_id = get_chat_id(params.user)
        payload: dict = {"chat_id": chat_id}
        if params.message_id is not None:
            payload["message_id"] = params.message_id
        await _tg("unpinChatMessage", payload, user=params.user)
        return "📌 메시지 고정 해제 완료"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_ban_user",
    annotations={"title": "텔레그램 사용자 차단", "readOnlyHint": False, "destructiveHint": True},
)
async def telegram_ban_user(params: BanUserInput) -> str:
    """그룹/채널에서 특정 사용자를 차단합니다. (봇이 관리자 권한 필요)

    Args:
        params (BanUserInput):
            - chat_id (int): 그룹/채널 ID
            - user_id (int): 차단할 사용자 ID
            - until_date (int): 차단 해제 Unix 타임스탬프 (None=영구 차단)

    Returns:
        str: 차단 성공 메시지 또는 에러
    """
    try:
        chat_id = get_chat_id(params.user)
        payload: dict = {"chat_id": chat_id, "user_id": params.user_id}
        if params.until_date is not None:
            payload["until_date"] = params.until_date
        await _tg("banChatMember", payload, user=params.user)
        return f"🚫 사용자 차단 완료 (user_id: {params.user_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_unban_user",
    annotations={"title": "텔레그램 사용자 차단 해제", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_unban_user(params: UnbanUserInput) -> str:
    """그룹/채널에서 차단된 사용자를 해제합니다. (봇이 관리자 권한 필요)

    Args:
        params (UnbanUserInput):
            - chat_id (int): 그룹/채널 ID
            - user_id (int): 차단 해제할 사용자 ID
            - only_if_banned (bool): 차단된 경우에만 해제 (기본 True)

    Returns:
        str: 차단 해제 성공 메시지 또는 에러
    """
    try:
        chat_id = get_chat_id(params.user)
        await _tg("unbanChatMember", {
            "chat_id":        chat_id,
            "user_id":        params.user_id,
            "only_if_banned": params.only_if_banned,
        }, user=params.user)
        return f"✅ 사용자 차단 해제 완료 (user_id: {params.user_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_chat_action",
    annotations={"title": "텔레그램 채팅 액션 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_chat_action(params: SendChatActionInput) -> str:
    """채팅에 '입력 중...', '파일 업로드 중...' 등 상태 표시를 전송합니다."""
    try:
        chat_id = get_chat_id(params.user)
        await _tg("sendChatAction", {
            "chat_id": chat_id,
            "action":  params.action,
        }, user=params.user)
        return f"⏳ 채팅 액션 전송 완료 (action: {params.action})"
    except Exception as e:
        return _err(e)
