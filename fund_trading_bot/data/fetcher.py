import time
import logging
import akshare as ak
import pandas as pd
from typing import Optional, Dict
from config.settings import MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)


class DataFetcher:
    """数据获取器：所有数据在这里获取，组装后喂给 Jev"""

    # ==================== 技术指标 ====================
    def get_technical_indicators(self, code: str, is_etf: bool = True) -> Dict:
        """获取历史数据并计算技术指标"""
        from utils.indicators import calculate_technical_indicators
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if is_etf:
                    # 获取 ETF 日线历史数据 (前复权)
                    df = ak.fund_etf_hist_em(symbol=code, period="daily", adjust="qfq")
                else:
                    # 获取场外基金单位净值走势
                    df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
                    # 统一列名以适配指标计算
                    df = df.rename(columns={"单位净值": "收盘", "日期": "日期"})
                    df["最高"] = df["收盘"]
                    df["最低"] = df["收盘"]
                
                if not df.empty:
                    logger.info(f"[{code}] 历史数据获取成功，共 {len(df)} 条")
                    return calculate_technical_indicators(df)
                    
            except Exception as e:
                logger.warning(f"[{code}] 第{attempt}次获取历史数据失败: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
        
        return {"error": "获取历史数据失败"}

    # ==================== 场内 ETF ====================
    def get_etf_realtime(self, etf_code: str) -> Optional[Dict]:
        """获取 ETF 实时行情"""
        raw = self._get_etf_realtime_with_retry(etf_code)
        if raw is None:
            return None

        premium = self._get_etf_premium_discount_with_retry(etf_code)
        current_price = float(raw["最新价"])

        return {
            "code": etf_code,
            "type": "场内ETF",
            "current_price": current_price,
            "daily_change_pct": float(raw["涨跌幅"]),
            "volume": float(raw["成交量"]),
            "amount": float(raw["成交额"]),
            "premium_discount_rate": premium,
            "estimated_nav": current_price / (1 + premium) if premium != 0 else current_price,
        }

    def _get_etf_realtime_with_retry(self, etf_code: str) -> Optional[pd.Series]:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                df = ak.fund_etf_spot_em()
                row = df[df["代码"] == etf_code]
                if not row.empty:
                    logger.info(f"[ETF {etf_code}] 行情获取成功 (第{attempt}次)")
                    return row.iloc[0]
                logger.warning(f"[ETF {etf_code}] 未找到代码")
                return None
            except Exception as e:
                logger.warning(f"[ETF {etf_code}] 第{attempt}次获取失败: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
        logger.error(f"[ETF {etf_code}] {MAX_RETRIES}次重试后仍失败")
        return None

    def _get_etf_premium_discount_with_retry(self, etf_code: str) -> float:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                df = ak.fund_etf_fund_info_em()
                row = df[df["基金代码"] == etf_code]
                if not row.empty and "折价率" in row.columns:
                    val = row.iloc[0]["折价率"]
                    if pd.notna(val):
                        return float(val) / 100.0
                return 0.0
            except Exception:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
        return 0.0

    # ==================== 场外基金 ====================
    def get_fund_estimation(self, fund_code: str) -> Optional[Dict]:
        """获取场外基金实时估值"""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                df = ak.fund_value_estimation_em()
                row = df[df["基金代码"] == fund_code]
                if not row.empty:
                    d = row.iloc[0]
                    logger.info(f"[基金 {fund_code}] 估值获取成功 (第{attempt}次)")
                    return {
                        "code": fund_code,
                        "type": "场外基金",
                        "fund_name": str(d.get("基金简称", "")),
                        "estimated_nav": float(d.get("估算净值", 0)),
                        "estimated_change_pct": float(d.get("估算涨幅", 0)),
                        "last_nav": float(d.get("昨日净值", 0)),
                        "last_nav_date": str(d.get("昨日净值日期", "")),
                    }
                logger.warning(f"[基金 {fund_code}] 未找到代码")
                return None
            except Exception as e:
                logger.warning(f"[基金 {fund_code}] 第{attempt}次获取失败: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
        logger.error(f"[基金 {fund_code}] {MAX_RETRIES}次重试后仍失败")
        return None

    # ==================== 大盘环境 ====================
    def get_market_environment(self) -> Dict:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
                sh = df[df["名称"] == "上证指数"]
                cyb = df[df["名称"] == "创业板指"]
                return {
                    "sh_index_change_pct": float(sh.iloc[0]["涨跌幅"]) if not sh.empty else 0.0,
                    "cyb_index_change_pct": float(cyb.iloc[0]["涨跌幅"]) if not cyb.empty else 0.0,
                    "market_breadth": self._get_market_breadth(),
                }
            except Exception as e:
                logger.warning(f"[大盘] 第{attempt}次获取失败: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
        return {"sh_index_change_pct": 0.0, "cyb_index_change_pct": 0.0, "market_breadth": "未知"}

    def _get_market_breadth(self) -> str:
        try:
            df = ak.stock_zh_a_spot_em()
            up = len(df[df["涨跌幅"] > 0])
            down = len(df[df["涨跌幅"] < 0])
            if up > down * 1.5:
                return "涨多跌少"
            elif down > up * 1.5:
                return "跌多涨少"
            return "涨跌各半"
        except Exception:
            return "未知"

    # ==================== 资金流向 ====================
    def get_fund_flow(self, code: str) -> Dict:
        for market in ["sh", "sz"]:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    df = ak.stock_individual_fund_flow(stock=code, market=market)
                    if not df.empty:
                        latest = df.iloc[-1]
                        return {
                            "main_net_inflow": float(latest.get("主力净流入-净额", 0)),
                            "main_net_inflow_pct": float(latest.get("主力净流入-净占比", 0)),
                        }
                except Exception:
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
        return {"main_net_inflow": 0.0, "main_net_inflow_pct": 0.0}