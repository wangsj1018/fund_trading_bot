import json
import logging
from typing import Dict, Optional
from typesafe_sdk import TypeSafeClient
from config.settings import JEV_MODE

logger = logging.getLogger(__name__)

class JevEngine:
    def __init__(self):
        # 官方 SDK 会自动读取 TYPESAFE_API_KEY 环境变量
        self.client = TypeSafeClient(model="jev-latest") 
        self.mode = JEV_MODE

    def decide_etf(self, context_data: Dict) -> Optional[Dict]:
        if self.mode == "mock":
            return self._mock_decide_etf(context_data)
        return self._call_system_one(context_data, is_etf=True)

    def decide_fund(self, context_data: Dict) -> Optional[Dict]:
        if self.mode == "mock":
            return self._mock_decide_fund(context_data)
        return self._call_system_one(context_data, is_etf=False)

    def _call_system_one(self, context_data: Dict, is_etf: bool) -> Optional[Dict]:
        """调用官方 System One API"""
        from core.schema import ETF_QUESTIONS, FUND_QUESTIONS
        
        # 1. 将字典序列化为 JSON 字符串作为 State
        state = json.dumps(context_data, ensure_ascii=False, indent=2)
        questions = ETF_QUESTIONS if is_etf else FUND_QUESTIONS

        try:
            # 2. 调用 system_one
            result = self.client.system_one(state, questions)
            
            # 3. 解析结构化结果并映射为业务数值
            if is_etf:
                return self._parse_etf_result(result)
            else:
                return self._parse_fund_result(result)
                
        except Exception as e:
            logger.error(f"System One API 调用失败: {e}")
            return None

    def _parse_etf_result(self, result) -> Dict:
        """解析 ETF 决策结果并映射数值"""
        action = result.choices["action"].choice
        pos_action = result.choices["position_adjustment"].choice
        conf_level = result.choices["confidence"].choice
        is_stop_loss = result.nouls["is_stop_loss_triggered"].noul # 返回 True/False 或 0-1 概率

        pos_map = {"clear": -1.0, "heavy_sell": -0.5, "light_sell": -0.15, "hold": 0.0, 
                   "light_buy": 0.15, "medium_buy": 0.3, "heavy_buy": 0.5}
        conf_map = {"low": 0.4, "medium": 0.7, "high": 0.95}

        return {
            "action": action,
            "position_adjustment_pct": pos_map.get(pos_action, 0.0),
            "confidence": conf_map.get(conf_level, 0.5),
            "tail_trend": result.choices["tail_trend"].choice,
            "is_stop_loss": bool(is_stop_loss) if isinstance(is_stop_loss, bool) else (is_stop_loss > 0.5),
        }

    def _parse_fund_result(self, result) -> Dict:
        """解析场外基金决策结果"""
        action = result.choices["action"].choice
        ratio_action = result.choices["amount_ratio"].choice
        conf_level = result.choices["confidence"].choice
        is_high_risk = result.nouls["is_high_risk_environment"].noul

        ratio_map = {"none": 0.0, "light": 0.1, "medium": 0.3, "half": 0.5, "full": 1.0}
        conf_map = {"low": 0.4, "medium": 0.7, "high": 0.95}

        return {
            "action": action,
            "amount_ratio": ratio_map.get(ratio_action, 0.0),
            "confidence": conf_map.get(conf_level, 0.5),
            "is_high_risk": bool(is_high_risk) if isinstance(is_high_risk, bool) else (is_high_risk > 0.5),
        }

    # Mock 模式保留用于本地无 API Key 测试
    def _mock_decide_etf(self, context: Dict) -> Dict:
        change = context.get("market_data", {}).get("daily_change_pct", 0)
        flow = context.get("fund_flow", {}).get("main_net_inflow", 0)
        if change > 1.5 and flow > 0:
            return {"action": "BUY", "position_adjustment_pct": 0.15, "confidence": 0.95, "tail_trend": "mild_rebound", "is_stop_loss": False}
        elif change < -1.5 and flow < 0:
            return {"action": "SELL", "position_adjustment_pct": -0.15, "confidence": 0.7, "tail_trend": "mild_pullback", "is_stop_loss": False}
        return {"action": "HOLD", "position_adjustment_pct": 0.0, "confidence": 0.7, "tail_trend": "flat_consolidation", "is_stop_loss": False}

    def _mock_decide_fund(self, context: Dict) -> Dict:
        change = context.get("estimation_data", {}).get("estimated_change_pct", 0)
        if change > 2.0:
            return {"action": "REDEEM", "amount_ratio": 0.3, "confidence": 0.7, "is_high_risk": False}
        elif change < -2.0:
            return {"action": "SUBSCRIBE", "amount_ratio": 0.3, "confidence": 0.7, "is_high_risk": False}
        return {"action": "HOLD", "amount_ratio": 0.0, "confidence": 0.7, "is_high_risk": False}