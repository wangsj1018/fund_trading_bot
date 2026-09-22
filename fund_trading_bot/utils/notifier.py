import requests
import hashlib
import hmac
import base64
import time
import urllib.parse
import logging
from config.settings import DINGTALK_WEBHOOK, DINGTALK_SECRET

logger = logging.getLogger(__name__)


def send_notification(title: str, text: str):
    if not DINGTALK_WEBHOOK:
        logger.warning("未配置钉钉通知，仅输出日志")
        return

    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{DINGTALK_SECRET}"
    hmac_code = hmac.new(
        DINGTALK_SECRET.encode(), string_to_sign.encode(), digestmod=hashlib.sha256
    ).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    try:
        requests.post(
            f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}",
            json={"msgtype": "markdown", "markdown": {"title": title, "text": text}},
            timeout=10,
        )
    except Exception as e:
        logger.error(f"通知发送失败: {e}")