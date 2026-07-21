import datetime

_quota_count = 0
_quota_date = datetime.date.today()


def check_quota(limit: int = 50) -> bool:
    global _quota_count, _quota_date
    today = datetime.date.today()
    if today != _quota_date:
        _quota_count = 0
        _quota_date = today
    return _quota_count < limit


def increment_quota():
    global _quota_count
    _quota_count += 1


def get_remaining_quota(limit: int = 50) -> int:
    check_quota(limit)
    return max(0, limit - _quota_count)
