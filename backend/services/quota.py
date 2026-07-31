import datetime

from backend.logger import get_logger

logger = get_logger(__name__)

_quota_count = 0
_quota_date = datetime.date.today()


def check_quota(limit: int = 50) -> bool:
    global _quota_count, _quota_date
    today = datetime.date.today()
    if today != _quota_date:
        logger.info("Quota reset: new day %s (was %s)", today, _quota_date)
        _quota_count = 0
        _quota_date = today
    ok = _quota_count < limit
    if not ok:
        logger.warning("Daily quota reached: %d/%d", _quota_count, limit)
    return ok


def increment_quota():
    global _quota_count
    _quota_count += 1
    logger.info("Quota incremented: %d/50", _quota_count)


def get_remaining_quota(limit: int = 50) -> int:
    check_quota(limit)
    return max(0, limit - _quota_count)
