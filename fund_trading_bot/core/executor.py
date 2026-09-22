import logging
from typing import Dict
from config.settings import MAX_POSITION_PCT, CONFIDENCE_THRESHOLD
from utils.notifier import send_notification
from utils.logic_generator import generate_decision_logic  # 引入逻辑生成器

logger = logging.getLogger(__name__)


class TradeExecutor:
    def __init__(self, notify_enabled: bool = True):
        self.notify_enabled = notify_enabled

    def _notify(self, title: str, text: str):
        if not self.notify_enabled:
            logger.info(f"[通知已关闭]\n{title}\n{text}")
            return
        send_notification(title, text)

    def execute_etf(self, fund_info: Dict, decision: Dict, context: Dict):
        action = decision.get("action")
        confidence = decision.get("confidence", 0)
        adj = decision.get("position_adjustment_pct", 0)
        
        # 【新增】生成完整的决策逻辑
        logic_text = generate_decision_logic(decision, context)
        
        # 止损优先级最高
        if decision.get("is_stop_loss"):
            self._notify(f"⚠️ 止损触发: {fund_info['name']}", "跌破关键技术支撑位，无条件清仓！")
            return

        if confidence < CONFIDENCE_THRESHOLD:
            logger.info(f"[{fund_info['name']}] 置信度 {confidence} 不足，跳过")
            return

        adj = max(-MAX_POSITION_PCT, min(MAX_POSITION_PCT, adj))

        if action == "BUY" and adj > 0:
            title = f"🟢 买入: {fund_info['name']} (置信度:{confidence:.0%})"
            text = f"代码: {fund_info['code']}\n建议仓位: +{adj*100:.0f}%\n\n{logic_text}"
            self._notify(title, text)
            
        elif action == "SELL" and adj < 0:
            title = f"🔴 卖出: {fund_info['name']} (置信度:{confidence:.0%})"
            text = f"代码: {fund_info['code']}\n建议仓位: {adj*100:.0f}%\n\n{logic_text}"
            self._notify(title, text)
            
        else:
            logger.info(f"[{fund_info['name']}] {action}\n{logic_text}")