"""tg_media.py — 미디어 전송 도구 (9개)"""

from telegram import mcp, _tg, _err

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ── Input 모델 ────────────────────────────────────────────

class SendPhotoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    photo:      str           = Field(..., description="이미지 URL 또는 file_id")
    caption:    Optional[str] = Field(default=None, description="이미지 설명 (최대 1024자)", max_length=1024)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")


class SendDocumentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    document:   str           = Field(..., description="파일 URL 또는 file_id")
    caption:    Optional[str] = Field(default=None, description="파일 설명 (최대 1024자)", max_length=1024)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")


class SendVideoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    video:      str           = Field(..., description="동영상 URL 또는 file_id")
    caption:    Optional[str] = Field(default=None, description="동영상 설명 (최대 1024자)", max_length=1024)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")
    duration:   Optional[int] = Field(default=None, description="동영상 길이(초)")
    width:      Optional[int] = Field(default=None, description="동영상 너비")
    height:     Optional[int] = Field(default=None, description="동영상 높이")


class SendAudioInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    audio:      str           = Field(..., description="오디오 URL 또는 file_id")
    caption:    Optional[str] = Field(default=None, description="오디오 설명 (최대 1024자)", max_length=1024)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")
    duration:   Optional[int] = Field(default=None, description="오디오 길이(초)")
    performer:  Optional[str] = Field(default=None, description="연주자/아티스트")
    title:      Optional[str] = Field(default=None, description="트랙 제목")


class SendVoiceInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    voice:      str           = Field(..., description="음성 파일 URL 또는 file_id (.ogg OPUS)")
    caption:    Optional[str] = Field(default=None, description="음성 설명 (최대 1024자)", max_length=1024)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")
    duration:   Optional[int] = Field(default=None, description="음성 길이(초)")


class SendAnimationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    animation:  str           = Field(..., description="GIF/MP4 URL 또는 file_id")
    caption:    Optional[str] = Field(default=None, description="설명 (최대 1024자)", max_length=1024)
    parse_mode: Optional[str] = Field(default="Markdown", description="'Markdown' 또는 'HTML'")
    duration:   Optional[int] = Field(default=None, description="애니메이션 길이(초)")
    width:      Optional[int] = Field(default=None, description="너비")
    height:     Optional[int] = Field(default=None, description="높이")


class SendVideoNoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id:    int           = Field(..., description="채팅 ID")
    video_note: str           = Field(..., description="둥근 비디오 file_id 또는 URL")
    duration:   Optional[int] = Field(default=None, description="비디오 길이(초)")
    length:     Optional[int] = Field(default=None, description="비디오 지름(px)")


class MediaItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type:       str           = Field(..., description="'photo' 또는 'video'")
    media:      str           = Field(..., description="URL 또는 file_id")
    caption:    Optional[str] = Field(default=None, description="개별 캡션")
    parse_mode: Optional[str] = Field(default=None, description="'Markdown' 또는 'HTML'")


class SendMediaGroupInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id: int             = Field(..., description="채팅 ID")
    media:   list[MediaItem] = Field(..., description="미디어 배열 (2~10개)", min_length=2, max_length=10)


class SendStickerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chat_id: int = Field(..., description="채팅 ID")
    sticker: str = Field(..., description="스티커 file_id 또는 URL (.webp/.tgs/.webm)")


# ── 도구 등록 ─────────────────────────────────────────────

@mcp.tool(
    name="telegram_send_photo",
    annotations={"title": "텔레그램 사진 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_photo(params: SendPhotoInput) -> str:
    """텔레그램 채팅에 사진을 전송합니다. URL 또는 file_id 사용 가능.

    Args:
        params (SendPhotoInput):
            - chat_id (int): 채팅 ID
            - photo (str): 이미지 URL 또는 Telegram file_id
            - caption (str): 이미지 설명 (선택, 최대 1024자)
            - parse_mode (str): 'Markdown' 또는 'HTML' (기본값: Markdown)

    Returns:
        str: 전송 성공 메시지 또는 에러
    """
    try:
        payload: dict = {"chat_id": params.chat_id, "photo": params.photo}
        if params.caption:
            payload["caption"]    = params.caption
            payload["parse_mode"] = params.parse_mode
        result = await _tg("sendPhoto", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"🖼️ 사진 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_document",
    annotations={"title": "텔레그램 파일/문서 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_document(params: SendDocumentInput) -> str:
    """텔레그램 채팅에 파일(문서)을 전송합니다. URL 또는 file_id 사용 가능.

    Args:
        params (SendDocumentInput):
            - chat_id (int): 채팅 ID
            - document (str): 파일 URL 또는 Telegram file_id
            - caption (str): 파일 설명 (선택, 최대 1024자)
            - parse_mode (str): 'Markdown' 또는 'HTML' (기본값: Markdown)

    Returns:
        str: 전송 성공 메시지 또는 에러
    """
    try:
        payload: dict = {"chat_id": params.chat_id, "document": params.document}
        if params.caption:
            payload["caption"]    = params.caption
            payload["parse_mode"] = params.parse_mode
        result = await _tg("sendDocument", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"📎 파일 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_video",
    annotations={"title": "텔레그램 동영상 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_video(params: SendVideoInput) -> str:
    """텔레그램 채팅에 동영상을 전송합니다. URL 또는 file_id 사용 가능."""
    try:
        payload: dict = {"chat_id": params.chat_id, "video": params.video}
        if params.caption:
            payload["caption"]    = params.caption
            payload["parse_mode"] = params.parse_mode
        if params.duration is not None:
            payload["duration"] = params.duration
        if params.width is not None:
            payload["width"] = params.width
        if params.height is not None:
            payload["height"] = params.height
        result = await _tg("sendVideo", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"🎬 동영상 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_audio",
    annotations={"title": "텔레그램 오디오 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_audio(params: SendAudioInput) -> str:
    """텔레그램 채팅에 오디오 파일을 전송합니다. URL 또는 file_id 사용 가능."""
    try:
        payload: dict = {"chat_id": params.chat_id, "audio": params.audio}
        if params.caption:
            payload["caption"]    = params.caption
            payload["parse_mode"] = params.parse_mode
        if params.duration is not None:
            payload["duration"] = params.duration
        if params.performer is not None:
            payload["performer"] = params.performer
        if params.title is not None:
            payload["title"] = params.title
        result = await _tg("sendAudio", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"🎵 오디오 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_voice",
    annotations={"title": "텔레그램 음성 메시지 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_voice(params: SendVoiceInput) -> str:
    """텔레그램 채팅에 음성 메시지를 전송합니다. .ogg OPUS 형식."""
    try:
        payload: dict = {"chat_id": params.chat_id, "voice": params.voice}
        if params.caption:
            payload["caption"]    = params.caption
            payload["parse_mode"] = params.parse_mode
        if params.duration is not None:
            payload["duration"] = params.duration
        result = await _tg("sendVoice", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"🎤 음성 메시지 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_animation",
    annotations={"title": "텔레그램 GIF/애니메이션 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_animation(params: SendAnimationInput) -> str:
    """텔레그램 채팅에 GIF 또는 무음 MP4 애니메이션을 전송합니다."""
    try:
        payload: dict = {"chat_id": params.chat_id, "animation": params.animation}
        if params.caption:
            payload["caption"]    = params.caption
            payload["parse_mode"] = params.parse_mode
        if params.duration is not None:
            payload["duration"] = params.duration
        if params.width is not None:
            payload["width"] = params.width
        if params.height is not None:
            payload["height"] = params.height
        result = await _tg("sendAnimation", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"🎞️ 애니메이션 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_video_note",
    annotations={"title": "텔레그램 둥근 비디오 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_video_note(params: SendVideoNoteInput) -> str:
    """텔레그램 채팅에 둥근 비디오 메시지를 전송합니다."""
    try:
        payload: dict = {"chat_id": params.chat_id, "video_note": params.video_note}
        if params.duration is not None:
            payload["duration"] = params.duration
        if params.length is not None:
            payload["length"] = params.length
        result = await _tg("sendVideoNote", payload)
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"⏺️ 둥근 비디오 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_media_group",
    annotations={"title": "텔레그램 미디어 그룹(앨범) 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_media_group(params: SendMediaGroupInput) -> str:
    """텔레그램 채팅에 사진/동영상 앨범(미디어 그룹)을 전송합니다. 2~10개."""
    try:
        media_list = []
        for item in params.media:
            m: dict = {"type": item.type, "media": item.media}
            if item.caption:
                m["caption"] = item.caption
            if item.parse_mode:
                m["parse_mode"] = item.parse_mode
            media_list.append(m)
        result = await _tg("sendMediaGroup", {
            "chat_id": params.chat_id,
            "media":   media_list,
        })
        msgs = result.get("result", [])
        ids  = [str(m.get("message_id", "?")) for m in msgs]
        return f"🖼️ 미디어 그룹 전송 완료 ({len(ids)}개, message_ids: {', '.join(ids)})"
    except Exception as e:
        return _err(e)


@mcp.tool(
    name="telegram_send_sticker",
    annotations={"title": "텔레그램 스티커 전송", "readOnlyHint": False, "destructiveHint": False},
)
async def telegram_send_sticker(params: SendStickerInput) -> str:
    """텔레그램 채팅에 스티커를 전송합니다. file_id 또는 URL 사용 가능."""
    try:
        result = await _tg("sendSticker", {
            "chat_id": params.chat_id,
            "sticker": params.sticker,
        })
        msg_id = result.get("result", {}).get("message_id", "?")
        return f"😀 스티커 전송 완료 (message_id: {msg_id})"
    except Exception as e:
        return _err(e)
