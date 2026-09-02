"""Generic outbound webhook notifications.

There is no portable way for a container to reach into the Unraid host and call
its native notify script -- that lives outside the container's namespace. The
practical, documented pattern instead: point this at ntfy.sh (free, has an
Unraid Community Apps plugin/app you can install to see pushes), a Discord/Slack
incoming webhook, or Unraid's own "webhook" User Script trigger.
"""
import logging
import httpx
from sqlmodel import Session

from app.settings_store import get_setting

logger = logging.getLogger("modelhub.notify")


def notify(session: Session, title: str, message: str):
    url = get_setting(session, "notify_webhook_url")
    if not url:
        return
    try:
        # A generic JSON body covers Discord/Slack-style webhooks (which accept
        # "content"/"text") and ntfy (which reads the raw body as the message,
        # with title carried in a header) in one shot.
        httpx.post(
            url,
            json={"title": title, "message": message, "content": f"**{title}**\n{message}", "text": f"{title}: {message}"},
            headers={"Title": title[:200]},
            timeout=10,
        )
    except Exception as e:
        logger.warning("Notification webhook failed: %s", e)
