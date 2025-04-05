from datetime import datetime, timezone as dt_timezone
import pytz
from pytz import timezone

KST = timezone("Asia/Seoul")
UTC = dt_timezone.utc

def convert_utc_to_kst(utc_time):
    """ UTC 시간을 한국 시간(KST)으로 변환 (중복 변환 방지) """
    if isinstance(utc_time, datetime):
        if utc_time.tzinfo is None:
            return utc_time.replace(tzinfo=UTC).astimezone(KST)  # ✅ UTC라면 변환
        if utc_time.tzinfo == KST:
            return utc_time  # ✅ 이미 KST이면 변환하지 않음
        return utc_time.astimezone(KST)  # ✅ UTC 등 다른 타임존이면 변환

    if isinstance(utc_time, str):
        try:
            dt_obj = datetime.fromisoformat(utc_time)
            return convert_utc_to_kst(dt_obj)
        except ValueError:
            return utc_time

    return utc_time

def get_kst_today():
    """ 현재 KST 날짜 반환 (UTC 기준 변환) """
    return datetime.now(UTC).astimezone(KST).date()  # ✅ UTC → KST 변환 후 반환

def get_kst_now():
    """ 현재 시간을 KST로 반환 (UTC에서 변환) """
    return datetime.now(UTC).astimezone(KST)  # ✅ UTC → KST 변환

