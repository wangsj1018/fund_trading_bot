import argparse
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

# 注意：这里不再需要导入 ETF_SCHEMA 和 FUND_SCHEMA，因为 engine 内部已经处理了
from data.fetcher import DataFetcher
from core.engine import JevEngine
from core.executor import TradeExecutor
from config.settings import DEFAULT_ETF_TARGETS, DEFAULT_FUND_TARGETS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Bot")

fetcher = DataFetcher()
engine = JevEngine()


def process_etf(code: str, name: str, executor: TradeExecutor):
    """场内 ETF 处理流程"""
    logger.info(f"📊 处理场内 ETF: {name} ({code})")

    # 1. 获取数据
    market_data = fetcher.get_etf_realtime(code)
    if not market_data:
        logger.error(f"[{name}] 行情数据获取失败，跳过")
        return

    fund_flow = fetcher.get_fund_flow(code)
    market_env = fetcher.get_market_environment()

        # 【新增】获取技术指标
    tech_indicators = fetcher.get_technical_indicators(code, is_etf=True)

    # 2. 组装 context_data
    context_data = {
        "time": datetime.now().strftime("%H:%M"),
        "fund_info": {"code": code, "name": name, "type": "场内ETF"},
        "market_data": market_data,
        "fund_flow": fund_flow,
        "index_environment": market_env,
        "technical_indicators": tech_indicators,  # 【新增】喂给 Jev 的技术指标

    }

    logger.info(f"  数据已组装，准备调用 System One...")
    logger.info(f"  当前价格: {market_data['current_price']}, 涨跌: {market_data['daily_change_pct']}%")
    logger.info(f"  主力净流入: {fund_flow['main_net_inflow']}")

    # 3. 调用 Jev 做判断 (修复点：改为 decide_etf)
    decision = engine.decide_etf(context_data)

    if decision:
        logger.info(f"  Jev 决策: {decision.get('action')} | 置信度: {decision.get('confidence')}")
        executor.execute_etf({"code": code, "name": name}, decision, context_data)
    else:
        logger.error(f"  Jev 决策失败")


def process_fund(code: str, name: str, executor: TradeExecutor):
    """场外基金处理流程"""
    logger.info(f"📊 处理场外基金: {name} ({code})")

    # 1. 获取数据
    estimation = fetcher.get_fund_estimation(code)
    if not estimation:
        logger.error(f"[{name}] 估值数据获取失败，跳过")
        return

    market_env = fetcher.get_market_environment()

    # 2. 组装 context_data
    context_data = {
        "time": datetime.now().strftime("%H:%M"),
        "fund_info": {"code": code, "name": name, "type": "场外基金"},
        "estimation_data": estimation,
        "index_environment": market_env,
    }

    logger.info(f"  数据已组装，准备调用 System One...")
    logger.info(f"  估算净值: {estimation['estimated_nav']}, 估算涨幅: {estimation['estimated_change_pct']}%")

    # 3. 调用 Jev 做判断 (修复点：改为 decide_fund)
    decision = engine.decide_fund(context_data)

    if decision:
        logger.info(f"  Jev 决策: {decision.get('action')} | 置信度: {decision.get('confidence')}")
        executor.execute_fund({"code": code, "name": name}, decision)
    else:
        logger.error(f"  Jev 决策失败")


def run(codes: list[str] | None = None, target_type: str | None = None, notify: bool = True):
    executor = TradeExecutor(notify_enabled=notify)
    logger.info(f"🚀 开始决策 | 通知: {'开启' if notify else '关闭'} | 时间: {datetime.now()}")

    if codes:
        for code in codes:
            t = target_type or _detect_type(code)
            name = _get_name(code, t)
            if t == "etf":
                process_etf(code, name, executor)
            else:
                process_fund(code, name, executor)
    else:
        for etf in DEFAULT_ETF_TARGETS:
            process_etf(etf["code"], etf["name"], executor)
        for fund in DEFAULT_FUND_TARGETS:
            process_fund(fund["code"], fund["name"], executor)

    logger.info("🏁 所有决策执行完毕")


def _detect_type(code: str) -> str:
    etf_codes = {e["code"] for e in DEFAULT_ETF_TARGETS}
    fund_codes = {f["code"] for f in DEFAULT_FUND_TARGETS}
    if code in etf_codes:
        return "etf"
    if code in fund_codes:
        return "fund"
    return "etf"


def _get_name(code: str, target_type: str) -> str:
    if target_type == "etf":
        for e in DEFAULT_ETF_TARGETS:
            if e["code"] == code:
                return e["name"]
    else:
        for f in DEFAULT_FUND_TARGETS:
            if f["code"] == code:
                return f["name"]
    return code


def main():
    parser = argparse.ArgumentParser(description="基金尾盘决策工具")
    parser.add_argument("--code", nargs="+", help="指定代码，如 --code 588000 110011")
    parser.add_argument("--type", choices=["etf", "fund"], help="指定类型")
    parser.add_argument("--notify", action="store_true", default=True, help="开启通知")
    parser.add_argument("--no-notify", action="store_true", help="关闭通知")
    parser.add_argument("--daemon", action="store_true", help="定时模式（每天14:50）")
    args = parser.parse_args()

    notify = not args.no_notify

    if args.daemon:
        logger.info("⏰ 定时模式：每天 14:50 执行")
        scheduler = BlockingScheduler(timezone="Asia/Shanghai")
        scheduler.add_job(run, "cron", hour=14, minute=50, kwargs={"notify": notify})
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("已停止")
    else:
        run(codes=args.code, target_type=args.type, notify=notify)


def debug_run():
    run(notify=False)


if __name__ == "__main__":
    main()