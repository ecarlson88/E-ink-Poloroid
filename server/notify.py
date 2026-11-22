import logging
import os

import httpx

log = logging.getLogger(__name__)


def notify_low_battery(battery_mv: int, magnet: str | None = None) -> None:
    """POST {"battery_mv": n, "magnet": name} to LOW_BATTERY_WEBHOOK_URL; never raise."""
    url = os.environ.get("LOW_BATTERY_WEBHOOK_URL")
    if not url:
        log.warning("low battery on %s (%s mV) but LOW_BATTERY_WEBHOOK_URL is unset", magnet, battery_mv)
        return
    try:
        httpx.post(url, json={"battery_mv": battery_mv, "magnet": magnet}, timeout=10)
    except httpx.HTTPError:
        log.exception("low battery webhook failed")
