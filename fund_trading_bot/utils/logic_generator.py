from typing import Dict

def generate_decision_logic(decision: Dict, context: Dict) -> str:
    """
    根据 Jev 的结构化决策和原始数据，生成人类可读的决策逻辑
    """
    action = decision.get("action", "HOLD")
    market = context.get("market_data", {})
    flow = context.get("fund_flow", {})
    daily = context.get("daily_indicators", {})
    intraday = context.get("intraday_indicators", {})
    
    change = market.get("daily_change_pct", 0)
    main_flow = flow.get("main_net_inflow", 0) / 10000  # 转为万
    rs = context.get("relative_strength_pct", 0)
    pos_60d = daily.get("price_position_60d", 0)
    tail_slope = intraday.get("tail_slope_pct", 0)
    tail_vol = intraday.get("tail_vol_ratio", 0)
    vwap_dev = intraday.get("vwap_deviation_pct", 0)
    atr = daily.get("atr_14", 0)
    
    # 1. 核心结论
    if action == "BUY":
        conclusion = "🟢 建议买入/加仓。多维度数据共振，尾盘出现积极信号。"
    elif action == "SELL":
        conclusion = "🔴 建议卖出/减仓。风险信号显现，建议锁定利润或规避回调。"
    elif action == "WAIT_AND_SEE":
        conclusion = "🟡 建议观望。信号冲突或环境不佳，盈亏比不划算。"
    else:
        conclusion = "⚪ 建议持有。多空博弈均衡，方向不明。"

    # 2. 行情与资金面
    flow_desc = "净流入" if main_flow > 0 else "净流出"
    rs_desc = "逆势走强" if rs > 0 else "弱于大盘"
    
    # 3. 技术面描述
    pos_desc = "高位危险区" if pos_60d > 0.8 else ("低位安全区" if pos_60d < 0.3 else "中位震荡区")
    bias = daily.get("bias_20", 0)
    bias_desc = "严重超买" if bias > 5 else ("超卖" if bias < -5 else "正常")

    # 4. 日内微观描述
    if tail_slope > 0.5 and tail_vol > 1.2:
        tail_desc = "主力尾盘抢筹"
    elif tail_slope < -0.5 and tail_vol > 1.2:
        tail_desc = "主力尾盘出货"
    elif tail_slope > 0.3:
        tail_desc = "尾盘温和拉升"
    elif tail_slope < -0.3:
        tail_desc = "尾盘承压回落"
    else:
        tail_desc = "尾盘横盘整理"
        
    vwap_desc = "站上" if vwap_dev > 0 else "跌破"

    # 5. 拼装逻辑
    logic = f"""
【核心结论】{conclusion}
【行情资金】当前涨跌幅 {change:+.2f}%，主力资金{flow_desc} {abs(main_flow):.0f} 万，相对大盘超额收益 {rs:+.2f}% ({rs_desc})。
【技术位置】价格处于近60日 {pos_60d*100:.0f}% 分位 ({pos_desc})，20日乖离率 {bias:.1f}% ({bias_desc})。
【日内微观】尾盘20分钟斜率 {tail_slope:+.2f}%，量比 {tail_vol:.1f}，判定为 {tail_desc}；当前价格{vwap_desc}日内均价 {abs(vwap_dev):.2f}%。
【风险波动】近期平均真实波幅(ATR)为 {atr:.3f}，波动风险{'较高' if atr > change else '可控'}。
""".strip()
    
    return logic