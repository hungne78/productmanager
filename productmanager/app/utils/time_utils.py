# app/utils/time_utils.py
from datetime import datetime
from pytz import timezone

def convert_utc_to_kst(utc_time):
    """ UTC 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")

    # 만약 객체가 이미 KST로 변환된 경우, 재귀 호출을 방지
    if isinstance(utc_time, datetime) and utc_time.tzinfo is not None:
        # 이미 timezone 정보가 있다면 변환할 필요 없음
        return utc_time

    # 문자열을 datetime으로 변환
    if isinstance(utc_time, str):
        try:
            utc_time = datetime.fromisoformat(utc_time)
        except ValueError:
            return utc_time  # 변환 실패 시 원래 문자열 반환

    # datetime 객체라면 KST로 변환
    if isinstance(utc_time, datetime):
        return utc_time.astimezone(kst)

    return utc_time  # 변환이 불가능한 경우 원래 값 반환
def convert_utc_str_to_kst(utc_time_str: str):
    """ 문자열(예: '2025-03-04 18:01:24')을 KST로 변환 """
    try:
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%d %H:%M:%S")
        kst = timezone("Asia/Seoul")
        return utc_time.replace(tzinfo=timezone("UTC")).astimezone(kst).strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"시간 변환 실패: {e}")
        return utc_time_str  # 변환 실패 시 원래 문자열 반환
def get_kst_today():
    """ UTC 시간을 KST로 변환한 날짜 반환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst).date()

def get_kst_now():
    """ 현재 시간을 한국 시간(KST)으로 변환 """
    kst = timezone("Asia/Seoul")
    return datetime.utcnow().astimezone(kst)