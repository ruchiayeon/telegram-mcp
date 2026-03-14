"""tg_interactive.py — 인터랙티브/유틸 도구 (9개)"""

from telegram import mcp, _tg, _err

import json
import os
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ── Input 모델 ────────────────────────────────────────────

class SendPollInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:      int       = Field(..., description="채팅 ID")
    question:     str       = Field(..., description="투표 질문 (최대 300자)", min_length=1, max_length=300)
    options:      list[str] = Field(..., description="선택지 목록 (2~10개)", min_length=2, max_length=10)
    is_anonymous: bool      = Field(default=True, description="익명 투표 여부")
    allows_multiple_answers: bool = Field(default=False, description="복수 선택 허용 여부")


class SendInlineKeyboardInput(BaseModel):
    """인라인 버튼이 붙은 메시지 전송"""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int                   = Field(..., description="채팅 ID")
    text:       str                   = Field(..., description="메시지 내용", min_length=1, max_length=4096)
    buttons:    list[list[dict]]      = Field(
        ...,
        description=(
            "버튼 행(row) 의 2차원 배열. 각 버튼 dict는 "
            "{'text': '표시 텍스트', 'url': 'https://...'}  또는 "
            "{'text': '표시 텍스트', 'callback_data': '데이터'} 형태."
        ),
    )
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")


class AnswerCallbackQueryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    callback_query_id: str           = Field(..., description="콜백 쿼리 ID")
    text:              Optional[str] = Field(default=None, description="사용자에게 보여줄 알림 텍스트")
    show_alert:        bool          = Field(default=False, description="True이면 팝업 알림, False이면 토스트")
    url:               Optional[str] = Field(default=None, description="열릴 URL (Game 봇 전용)")
    cache_time:        Optional[int] = Field(default=None, description="클라이언트 캐시 시간(초)")


class SendLocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id:   int   = Field(..., description="채팅 ID")
    latitude:  float = Field(..., description="위도 (예: 37.5665)", ge=-90.0, le=90.0)
    longitude: float = Field(..., description="경도 (예: 126.9780)", ge=-180.0, le=180.0)


class SendVenueInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:        int           = Field(..., description="채팅 ID")
    latitude:       float         = Field(..., description="위도", ge=-90.0, le=90.0)
    longitude:      float         = Field(..., description="경도", ge=-180.0, le=180.0)
    title:          str           = Field(..., description="장소 이름")
    address:        str           = Field(..., description="장소 주소")
    foursquare_id:  Optional[str] = Field(default=None, description="Foursquare 장소 ID")


class SendContactInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:      int           = Field(..., description="채팅 ID")
    phone_number: str           = Field(..., description="연락처 전화번호")
    first_name:   str           = Field(..., description="연락처 이름")
    last_name:    Optional[str] = Field(default=None, description="연락처 성")
    vcard:        Optional[str] = Field(default=None, description="vCard 형식 추가 정보")


class SendDiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id: int           = Field(..., description="채팅 ID")
    emoji:   Optional[str] = Field(default="🎲", description="이모지: 🎲🎯🏀⚽🎳🎰")


class SetMessageReactionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id:    int       = Field(..., description="채팅 ID")
    message_id: int       = Field(..., description="리액션 대상 메시지 ID")
    reaction:   list[str] = Field(default_factory=list, description="이모지 리스트 (빈 배열이면 리액션 제거)")
    is_big:     bool      = Field(default=False, description="큰 리액션 애니메이션 여부")


class GetFileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_id: str = Field(..., description="Telegram 파일 ID")


# ── 도구 등록 ─────────────────────────────────────────────

@mcp.tool(
    name="telegram_send_poll",
    annotations={"title": "텔레그램 투표 생성", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_poll(params: SendPollInput) -> str:
    """텔레그램 채팅에 투표를 생성합니다.

    Args:
        params (SendPollInput):
            - chat_id (int): 채팅 ID
            - question (str): 투표 질문 (최대 300자)
            - options (list[str]): 선택지 목록 (2~10개)
            - is_anonymous (bool): 익명 투표 여부 (기본 True)
            - allows_multiple_answers (bool): 복수 선택 허용 (기본 False)

    Returns:
        str: 투표 생성 성공 메시지 또는 에러
    """
    try:
        result = await _tg("sendPoll", {
            "chat_id":                 params.chat_id,
            "question":                params.question,
            "options":                 params.options,
            "is_anonymous":            params.is_anonymous,
            "allows_multiple_answers": params.allows_multiple_answers,
        })
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"📊 투표 생성 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_with_buttons",
    annotations={"title": "인라인 버튼이 포함된 텔레그램 메시지 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_with_buttons(params: SendInlineKeyboardInput) -> str:
    """URL 링크 또는 콜백 버튼이 붙은 텔레그램 메시지를 전송합니다.

    버튼 예시 (buttons 파라미터):
      [[{"text": "공식 사이트", "url": "https://example.com"}],
       [{"text": "확인", "callback_data": "ok"}, {"text": "취소", "callback_data": "cancel"}]]

    Args:
        params (SendInlineKeyboardInput):
            - chat_id (int): 채팅 ID
            - text (str): 메시지 내용
            - buttons (list[list[dict]]): 버튼 2차원 배열
            - parse_mode (str): 'Markdown' 또는 'HTML' (기본값: Markdown)

    Returns:
        str: 전송 성공 메시지 또는 에러
    """
    try:
        result = await _tg("sendMessage", {
            "chat_id":    params.chat_id,
            "text":       params.text,
            "parse_mode": params.parse_mode,
            "reply_markup": {"inline_keyboard": params.buttons},
        })
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"⌨️ 버튼 메시지 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_answer_callback_query",
    annotations={"title": "텔레그램 콜백 쿼리 응답", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_answer_callback_query(params: AnswerCallbackQueryInput) -> str:
    """인라인 버튼 클릭(콜백 쿼리)에 대한 응답을 보냅니다."""
    try:
        payload: dict = {"callback_query_id": params.callback_query_id}
        if params.text is not None:
            payload["text"] = params.text
        payload["show_alert"] = params.show_alert
        if params.url is not None:
            payload["url"] = params.url
        if params.cache_time is not None:
            payload["cache_time"] = params.cache_time
        await _tg("answerCallbackQuery", payload)
        return f"✅ 콜백 쿼리 응답 완료 (id: {params.callback_query_id[:8]}…)"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_location",
    annotations={"title": "텔레그램 위치 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_location(params: SendLocationInput) -> str:
    """텔레그램 채팅에 지도 핀(위치 정보)을 전송합니다.

    Args:
        params (SendLocationInput):
            - chat_id (int): 채팅 ID
            - latitude (float): 위도 (예: 37.5665)
            - longitude (float): 경도 (예: 126.9780)

    Returns:
        str: 전송 성공 메시지 또는 에러
    """
    try:
        result = await _tg("sendLocation", {
            "chat_id":   params.chat_id,
            "latitude":  params.latitude,
            "longitude": params.longitude,
        })
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"📍 위치 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_venue",
    annotations={"title": "텔레그램 장소 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_venue(params: SendVenueInput) -> str:
    """텔레그램 채팅에 장소(위치+이름+주소)를 전송합니다."""
    try:
        payload: dict = {
            "chat_id":   params.chat_id,
            "latitude":  params.latitude,
            "longitude": params.longitude,
            "title":     params.title,
            "address":   params.address,
        }
        if params.foursquare_id is not None:
            payload["foursquare_id"] = params.foursquare_id
        result = await _tg("sendVenue", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"📍 장소 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_contact",
    annotations={"title": "텔레그램 연락처 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_contact(params: SendContactInput) -> str:
    """텔레그램 채팅에 연락처(전화번호+이름)를 전송합니다."""
    try:
        payload: dict = {
            "chat_id":      params.chat_id,
            "phone_number": params.phone_number,
            "first_name":   params.first_name,
        }
        if params.last_name is not None:
            payload["last_name"] = params.last_name
        if params.vcard is not None:
            payload["vcard"] = params.vcard
        result = await _tg("sendContact", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"📇 연락처 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_dice",
    annotations={"title": "텔레그램 주사위/랜덤 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_dice(params: SendDiceInput) -> str:
    """텔레그램 채팅에 주사위/슬롯 등 랜덤 애니메이션을 전송합니다."""
    try:
        payload: dict = {"chat_id": params.chat_id}
        if params.emoji:
            payload["emoji"] = params.emoji
        result = await _tg("sendDice", payload)
        dice   = result.get("result", {}).get("dice", {})
        value  = dice.get("value", "?")
        return f"🎲 주사위 전송 완료 (결과: {value})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_set_message_reaction",
    annotations={"title": "텔레그램 메시지 리액션", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_set_message_reaction(params: SetMessageReactionInput) -> str:
    """메시지에 이모지 리액션을 설정하거나 제거합니다."""
    try:
        reaction_objs = [{"type": "emoji", "emoji": e} for e in params.reaction]
        await _tg("setMessageReaction", {
            "chat_id":    params.chat_id,
            "message_id": params.message_id,
            "reaction":   reaction_objs,
            "is_big":     params.is_big,
        })
        if params.reaction:
            return f"👍 리액션 설정 완료 ({', '.join(params.reaction)})"
        return "👍 리액션 제거 완료"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_get_file",
    annotations={"title": "텔레그램 파일 정보 조회", "readOnlyHint": True, "destructiveHint": False},
)
async def telegram_get_file(params: GetFileInput) -> str:
    """file_id로 파일 정보와 다운로드 URL을 조회합니다."""
    try:
        result    = await _tg("getFile", {"file_id": params.file_id})
        file_info = result.get("result", {})
        file_path = file_info.get("file_path", "")
        token     = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        download  = f"https://api.telegram.org/file/bot{token}/{file_path}" if file_path else None
        info = {
            "file_id":        file_info.get("file_id"),
            "file_unique_id": file_info.get("file_unique_id"),
            "file_size":      file_info.get("file_size"),
            "file_path":      file_path,
            "download_url":   download,
        }
        return json.dumps(info, ensure_ascii=False, indent=2)
    except Exception as e:
        return _err(e)
