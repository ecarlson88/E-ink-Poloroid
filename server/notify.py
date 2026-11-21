import logging
import os

import httpx

log = logging.getLogger(__name__)


def notify_low_battery(battery_mv: int) -> None:
    """POST {"battery_mv": n} to LOW_BATTERY_WEBHOOK_URL; never raise."""
    url = os.environ.get("LOW_BATTERY_WEBHOOK_URL")
    if not url:
        log.warning("low battery (%s mV) but LOW_BATTERY_WEBHOOK_URL is unset", battery_mv)
        return
    try:
        httpx.post(url, json={"battery_mv": battery_mv}, timeout=10)
    except httpx.HTTPError:
        log.exception("low battery webhook failed")
