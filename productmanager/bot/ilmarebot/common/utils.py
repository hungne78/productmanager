"""
순수(pure) 함수 모음. 상태가 없어서 어디서나 import 해도 안전.
"""
import re

__all__ = ["remove_emoji", "remove_non_bmp"]

_EMOJI = re.compile(
    "["                               # Emoji / pictograph ranges
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF"
    u"\U00002500-\U00002BEF"
    u"\U00002702-\U000027B0"
    u"\U0001F900-\U0001F9FF"
    u"\U0001FA70-\U0001FAFF"
    "]+",
    flags=re.UNICODE,
)

def remove_emoji(text: str) -> str:
    "문자열에서 emoji 제거"
    return _EMOJI.sub("", text or "")

def remove_non_bmp(text: str) -> str:
    "BMP(기본 다국어 평면) 바깥 글자 제거 – 일부 DB·폰트 호환용"
    return re.sub(r"[^\u0000-\uFFFF]", "", text or "")
