import os
from dotenv import load_dotenv

load_dotenv()

# ==================== Jev ====================
JEV_API_URL = os.getenv("JEV_API_URL", "https://api.typesafe.ai/v1/jev/decision")
JEV_API_KEY = os.getenv("JEV_API_KEY", "")
JEV_MODE = os.getenv("JEV_MODE", "mock")

# ==================== 默认标的 ====================
DEFAULT_ETF_TARGETS = [
    {"code": "588000", "name": "科创50ETF"},
    {"code": "512880", "name": "证券ETF"},
]

DEFAULT_FUND_TARGETS = [
    {"code": "110011", "name": "易方达中小盘混合"},
]

# ==================== 策略 ====================
CONFIDENCE_THRESHOLD = 0.6
MAX_POSITION_PCT = 0.2

# ==================== 通知 ====================
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")

# ==================== 重试 ====================
MAX_RETRIES = 3
RETRY_DELAY = 2