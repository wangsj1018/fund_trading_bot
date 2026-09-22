from typesafe_sdk import Choice, Noul

# ==================== 场内 ETF 决策问题 ====================
ETF_QUESTIONS = {
    "action": Choice(
        instructions=(
            "根据尾盘行情、资金流向、大盘环境，以及提供的【技术指标】(MA均线、MACD、RSI、60日相对位置)，"
            "给出明确的交易动作。"
            "注意：如果 RSI > 70 且价格处于 60日高位，警惕回调；如果 MACD 金叉且均线多头排列，可积极买入。"
        ),
        criteria={
            "BUY": "尾盘强势，主力流入，且技术指标支持 (如均线多头、MACD金叉)",
            "SELL": "尾盘弱势，主力流出，或技术指标超买 (如RSI过高、跌破关键均线)",
            "HOLD": "波动极小，指标无明显方向，持有不动",
            "WAIT_AND_SEE": "信号冲突或风险较高，建议继续观望"
        }
    ),
    "tail_trend": Choice(
        instructions="对 14:30-14:50 尾盘趋势的判断",
        criteria={
            "strong_surge": "强势拉升",
            "mild_rebound": "温和反弹",
            "flat_consolidation": "横盘震荡",
            "mild_pullback": "温和回调",
            "sharp_dump": "急速跳水"
        }
    ),
    "position_adjustment": Choice(
        instructions="建议的仓位调整动作（正数加仓，负数减仓）",
        criteria={
            "clear": "清仓 (-100%)",
            "heavy_sell": "大幅减仓 (-50%)",
            "light_sell": "小幅减仓 (-15%)",
            "hold": "不动 (0%)",
            "light_buy": "小幅加仓 (+15%)",
            "medium_buy": "中幅加仓 (+30%)",
            "heavy_buy": "大幅加仓 (+50%)"
        }
    ),
    "confidence": Choice(
        instructions="对该决策的置信度评估",
        criteria={
            "low": "低 (信号模糊，风险高)",
            "medium": "中 (有一定逻辑支撑，但存在分歧)",
            "high": "高 (行情、资金、指标多维度共振)"
        }
    ),
    "is_stop_loss_triggered": Noul(
        instructions="当前价格是否已经跌破关键技术支撑位 (如 20日/60日均线)，需要立即无条件止损？"
    )
}

# ==================== 场外基金决策问题 ====================
FUND_QUESTIONS = {
    "action": Choice(
        instructions="根据基金实时估值和大盘环境，判断今天是否应该申购或赎回该场外基金",
        criteria={
            "SUBSCRIBE": "估值大跌且处于低位，适合申购摊低成本",
            "REDEEM": "估值大涨且近期连续上涨，适合赎回锁定收益",
            "HOLD": "估值波动极小或处于震荡期，持有不动",
            "WAIT_AND_SEE": "趋势不明，建议观望"
        }
    ),
    "amount_ratio": Choice(
        instructions="建议操作金额占可用资金的比例",
        criteria={
            "none": "不操作 (0%)",
            "light": "小试牛刀 (10%)",
            "medium": "部分操作 (30%)",
            "half": "半仓操作 (50%)",
            "full": "全仓/清仓 (100%)"
        }
    ),
    "confidence": Choice(
        instructions="对该决策的置信度评估",
        criteria={
            "low": "低", "medium": "中", "high": "高"
        }
    ),
    "is_high_risk_environment": Noul(
        instructions="当前大盘环境是否处于高风险状态（如暴跌、流动性危机）？"
    )
}