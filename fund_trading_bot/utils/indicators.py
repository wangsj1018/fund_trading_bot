import pandas as pd
from typing import Dict

def calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    """计算常用技术指标，返回结构化字典"""
    if df.empty or len(df) < 60:
        return {"error": "历史数据不足60天，无法计算指标"}
    
    close = df["收盘"].astype(float)
    
    # 1. 均线 (MA)
    ma5 = close.rolling(window=5).mean().iloc[-1]
    ma20 = close.rolling(window=20).mean().iloc[-1]
    ma60 = close.rolling(window=60).mean().iloc[-1]
    
    # 2. RSI (14日)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_14 = rsi.iloc[-1]
    
    # 3. MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd_hist = 2 * (dif - dea)
    
    # 4. 相对位置 (当前价格在近60日高低点之间的位置)
    high_60 = df["最高"].astype(float).tail(60).max()
    low_60 = df["最低"].astype(float).tail(60).min()
    current_price = close.iloc[-1]
    position_pct = (current_price - low_60) / (high_60 - low_60) if high_60 != low_60 else 0.5
    
    # 5. 趋势总结 (供 Jev 参考)
    trend_summary = _summarize_trend(close)
    
    return {
        "ma5": round(float(ma5), 3),
        "ma20": round(float(ma20), 3),
        "ma60": round(float(ma60), 3),
        "rsi_14": round(float(rsi_14), 2),
        "macd_dif": round(float(dif.iloc[-1]), 3),
        "macd_dea": round(float(dea.iloc[-1]), 3),
        "macd_hist": round(float(macd_hist.iloc[-1]), 3),
        "price_position_60d": round(float(position_pct), 2), # 0=近60日最低点, 1=最高点
        "trend_summary": trend_summary
    }

def _summarize_trend(close: pd.Series) -> str:
    """总结近期趋势"""
    if len(close) < 20:
        return "数据不足"
    ma5 = close.rolling(5).mean().iloc[-1]
    ma20 = close.rolling(20).mean().iloc[-1]
    current = close.iloc[-1]
    
    if ma5 > ma20 and current > ma5:
        return "多头排列，短期趋势向上"
    elif ma5 < ma20 and current < ma5:
        return "空头排列，短期趋势向下"
    else:
        return "均线缠绕，处于震荡整理期"