"""tg_messages.py — 메시지 CRUD 도구 (9개)"""

from telegram import mcp, _tg, _err

import json
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ── Input 모델 ────────────────────────────────────────────

class SendMessageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="메시지를 보낼 채팅 ID")
    text:       str           = Field(..., description="보낼 메시지 내용 (최대 4096자)", min_length=1, max_length=4096)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")


class GetUpdatesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    offset: Optional[int] = Field(default=None, description="이 update_id 이후 메시지만 가져오기 (중복 방지)")
    limit:  Optional[int] = Field(default=20, description="가져올 메시지 수 (최대 100)", ge=1, le=100)


class EditMessageInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    message_id: int           = Field(..., description="수정할 메시지 ID")
    text:       str           = Field(..., description="새 메시지 내용", min_length=1, max_length=4096)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")


class DeleteMessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id:    int = Field(..., description="채팅 ID")
    message_id: int = Field(..., description="삭제할 메시지 ID")


class DeleteMessagesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id:     int       = Field(..., description="채팅 ID")
    message_ids: list[int] = Field(..., description="삭제할 메시지 ID 목록", min_length=1, max_length=100)


class ForwardMessageInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_chat_id: int = Field(..., description="원본 채팅 ID")
    to_chat_id:   int = Field(..., description="전달 대상 채팅 ID")
    message_id:   int = Field(..., description="전달할 메시지 ID")


class ForwardMessagesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_chat_id: int       = Field(..., description="원본 채팅 ID")
    to_chat_id:   int       = Field(..., description="전달 대상 채팅 ID")
    message_ids:  list[int] = Field(..., description="전달할 메시지 ID 목록", min_length=1, max_length=100)


class CopyMessageInput(BaseModel):
    """포워드 마크 없이 메시지 내용만 복사"""
    model_config = ConfigDict(extra="forbid")
    from_chat_id: int           = Field(..., description="원본 채팅 ID")
    to_chat_id:   int           = Field(..., description="복사 대상 채팅 ID")
    message_id:   int           = Field(..., description="복사할 메시지 ID")
    caption:      Optional[str] = Field(default=None, description="미디어 메시지에 추가할 캡션")


class CopyMessagesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_chat_id: int       = Field(..., description="원본 채팅 ID")
    to_chat_id:   int       = Field(..., description="복사 대상 채팅 ID")
    message_ids:  list[int] = Field(..., description="복사할 메시지 ID 목록", min_length=1, max_length=100)


# ── 도구 등록 ─────────────────────────────────────────────

@mcp.tool(
    name="telegram_get_updates",
    annotations={"title": "새 텔레그램 메시지 조회", "readOnlyHint": True, "destructiveHint": False}
)
async def telegram_get_updates(params: GetUpdatesInput) -> str:
    """텔레그램 봇으로 수신된 새 메시지를 가져옵니다.

    스케줄 태스크에서 주기적으로 호출하여 새 메시지를 확인합니다.
    offset을 사용하면 이미 처리한 메시지를 다시 가져오지 않습니다.

    Args:
        params (GetUpdatesInput):
            - offset (int): 마지막으로 처리한 update_id + 1 (선택사항)
            - limit (int): 가져올 메시지 수 (기본 20)

    Returns:
        str: 메시지 목록 JSON. 각 항목에 update_id, chat_id, sender, text 포함.
             메시지 없으면 "새 메시지 없음" 반환.
    """
    try:
        payload: dict = {"limit": params.limit}
        if params.offset is not None:
            payload["offset"] = params.offset

        result  = await _tg("getUpdates", payload)
        updates = result.get("result", [])

        if not updates:
            return "📭 새 메시지 없음"

        messages = []
        for u in updates:
            msg = u.get("message", {})
            if not msg:
                continue
            messages.append({
                "update_id": u.get("update_id"),
                "chat_id":   msg.get("chat", {}).get("id"),
                "sender":    msg.get("from", {}).get("username", "unknown"),
                "text":      msg.get("text", ""),
            })

        return json.dumps(messages, ensure_ascii=False, indent=2)
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_message",
    annotations={"title": "텔레그램 메시지 전송", "readOnlyHint": False, "destructiveHint": False}
)
async def telegram_send_message(params: SendMessageInput) -> str:
    """텔레그램 채팅에 메시지를 전송합니다.

    Args:
        params (SendMessageInput):
            - chat_id (int): 대상 채팅 ID
            - text (str): 전송할 메시지 (Markdown 지원)
            - parse_mode (str): 'Markdown' 또는 'HTML' (기본값: Markdown)

    Returns:
        str: 전송 성공 메시지 또는 에러
    """
    try:
        result = await _tg("sendMessage", {
            "chat_id":    params.chat_id,
            "text":       params.text,
            "parse_mode": params.parse_mode
        })
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"✅ 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_edit_message",
    annotations={"title": "텔레그램 메시지 수정", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_edit_message(params: EditMessageInput) -> str:
    """이미 전송된 텔레그램 메시지의 내용을 수정합니다.

    Args:
        params (EditMessageInput):
            - chat_id (int): 채팅 ID
            - message_id (int): 수정할 메시지 ID
            - text (str): 새 메시지 내용
            - parse_mode (str): 'Markdown' 또는 'HTML' (기본값: Markdown)

    Returns:
        str: 수정 성공 메시지 또는 에러
    """
    try:
        result = await _tg("editMessageText", {
            "chat_id":    params.chat_id,
            "message_id": params.message_id,
            "text":       params.text,
            "parse_mode": params.parse_mode,
        })
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"✏️ 메시지 수정 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_delete_message",
    annotations={"title": "텔레그램 메시지 삭제", "readOnlyHint": False, "destructiveHint": True},
)
async def telegram_delete_message(params: DeleteMessageInput) -> str:
    """텔레그램 채팅에서 특정 메시지를 삭제합니다.

    Args:
        params (DeleteMessageInput):
            - chat_id (int): 채팅 ID
            - message_id (int): 삭제할 메시지 ID

    Returns:
        str: 삭제 성공 메시지 또는 에러
    """
    try:
        await _tg("deleteMessage", {
            "chat_id":    params.chat_id,
            "message_id": params.message_id,
        })
        return f"🗑️ 메시지 삭제 완료 (message_id: {params.message_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_delete_messages",
    annotations={"title": "텔레그램 메시지 복수 삭제", "readOnlyHint": False, "destructiveHint": True},
)
async def telegram_delete_messages(params: DeleteMessagesInput) -> str:
    """텔레그램 채팅에서 여러 메시지를 한 번에 삭제합니다."""
    try:
        await _tg("deleteMessages", {
            "chat_id":     params.chat_id,
            "message_ids": params.message_ids,
        })
        return f"🗑️ 메시지 {len(params.message_ids)}개 삭제 완료"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_forward_message",
    annotations={"title": "텔레그램 메시지 포워드", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_forward_message(params: ForwardMessageInput) -> str:
    """한 채팅에서 다른 채팅으로 메시지를 포워드(전달)합니다. 출처 표시 포함.

    Args:
        params (ForwardMessageInput):
            - from_chat_id (int): 원본 채팅 ID
            - to_chat_id (int): 전달 대상 채팅 ID
            - message_id (int): 전달할 메시지 ID

    Returns:
        str: 포워드 성공 메시지 또는 에러
    """
    try:
        result = await _tg("forwardMessage", {
            "chat_id":      params.to_chat_id,
            "from_chat_id": params.from_chat_id,
            "message_id":   params.message_id,
        })
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"↪️ 메시지 포워드 완료 (새 message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_forward_messages",
    annotations={"title": "텔레그램 메시지 복수 포워드", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_forward_messages(params: ForwardMessagesInput) -> str:
    """한 채팅에서 다른 채팅으로 여러 메시지를 한 번에 포워드합니다."""
    try:
        result = await _tg("forwardMessages", {
            "chat_id":      params.to_chat_id,
            "from_chat_id": params.from_chat_id,
            "message_ids":  params.message_ids,
        })
        msg_ids = result.get("result", [])
        ids_str = ", ".join(str(m.get("message_id", "?")) for m in msg_ids) if isinstance(msg_ids, list) else "?"
        return f"↪️ 메시지 {len(params.message_ids)}개 포워드 완료 (새 message_ids: {ids_str})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_copy_message",
    annotations={"title": "텔레그램 메시지 복사 (출처 표시 없음)", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_copy_message(params: CopyMessageInput) -> str:
    """메시지 내용을 포워드 마크 없이 복사하여 다른 채팅에 전송합니다.

    Args:
        params (CopyMessageInput):
            - from_chat_id (int): 원본 채팅 ID
            - to_chat_id (int): 복사 대상 채팅 ID
            - message_id (int): 복사할 메시지 ID
            - caption (str): 미디어 메시지에 추가할 캡션 (선택)

    Returns:
        str: 복사 성공 메시지 또는 에러
    """
    try:
        payload: dict = {
            "chat_id":      params.to_chat_id,
            "from_chat_id": params.from_chat_id,
            "message_id":   params.message_id,
        }
        if params.caption:
            payload["caption"] = params.caption
        result = await _tg("copyMessage", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"📋 메시지 복사 완료 (새 message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_copy_messages",
    annotations={"title": "텔레그램 메시지 복수 복사", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_copy_messages(params: CopyMessagesInput) -> str:
    """여러 메시지를 포워드 마크 없이 복사하여 다른 채팅에 전송합니다."""
    try:
        result = await _tg("copyMessages", {
            "chat_id":      params.to_chat_id,
            "from_chat_id": params.from_chat_id,
            "message_ids":  params.message_ids,
        })
        msg_ids = result.get("result", [])
        ids_str = ", ".join(str(m.get("message_id", "?")) for m in msg_ids) if isinstance(msg_ids, list) else "?"
        return f"📋 메시지 {len(params.message_ids)}개 복사 완료 (새 message_ids: {ids_str})"
    except Exception as e:
        return _err(e)
