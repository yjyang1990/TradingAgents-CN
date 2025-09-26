#!/usr/bin/env python3
"""
每日股票分析报告系统
基于 TradingAgents-CN 框架，自动分析股票并发送企业微信通知
"""

import os
import sys
import json
import requests
import datetime
from pathlib import Path
from typing import List, Dict, Any
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.utils.config_loader import load_main_config
from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.data_source_manager import DataSourceManager

# 加载环境变量
load_dotenv()

# 初始化日志
logger = get_logger('daily_report')

class DailyStockReporter:
    """每日股票分析报告生成器"""

    def __init__(self, config_path: str = "config/stock_watchlist.json"):
        """初始化报告生成器

        Args:
            config_path: 股票配置文件路径
        """
        self.config_path = config_path
        self.watchlist = []
        self.wechat_webhook = ""
        self.trading_graph = None
        self.data_manager = None

        # 加载配置
        self._load_config()

        # 初始化交易分析图
        self._init_trading_graph()

        # 初始化数据管理器（用于获取股票名称）
        self._init_data_manager()

    def _load_config(self):
        """加载股票配置"""
        try:
            config_file = project_root / self.config_path

            if not config_file.exists():
                logger.error(f"❌ 配置文件不存在: {config_file}")
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.watchlist = config.get('watchlist', [])
            self.wechat_webhook = config.get('wechat_webhook', '')

            logger.info(f"✅ 配置加载成功: {len(self.watchlist)} 只A股")
            logger.info(f"📋 关注列表: {', '.join(self.watchlist)}")

        except Exception as e:
            logger.error(f"❌ 配置加载失败: {e}")
            self.watchlist = []

    def _init_trading_graph(self):
        """初始化交易分析图"""
        try:
            logger.info("🤖 正在初始化 TradingAgentsGraph...")

            # 加载主配置
            config = load_main_config()

            # 初始化交易分析图
            self.trading_graph = TradingAgentsGraph(debug=False, config=config)

            logger.info("✅ TradingAgentsGraph 初始化成功")

        except Exception as e:
            logger.error(f"❌ TradingAgentsGraph 初始化失败: {e}")
            self.trading_graph = None

    def _init_data_manager(self):
        """初始化数据管理器"""
        try:
            logger.info("📊 正在初始化数据管理器...")
            self.data_manager = DataSourceManager()
            logger.info("✅ 数据管理器初始化成功")
        except Exception as e:
            logger.error(f"❌ 数据管理器初始化失败: {e}")
            self.data_manager = None

    def get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        try:
            if self.data_manager:
                # 使用数据管理器获取股票信息
                stock_info = self.data_manager.get_stock_info(symbol)
                if stock_info and 'name' in stock_info:
                    return stock_info['name']

            # 如果获取失败，返回默认格式
            return f"股票{symbol}"

        except Exception as e:
            logger.debug(f"获取 {symbol} 名称失败: {e}")
            return f"股票{symbol}"

    def analyze_stock(self, symbol: str, date: str = None) -> Dict[str, Any]:
        """分析单只股票

        Args:
            symbol: 股票代码
            date: 分析日期，默认为今天

        Returns:
            分析结果字典
        """
        if not self.trading_graph:
            return {
                'symbol': symbol,
                'error': 'TradingAgentsGraph 未初始化'
            }

        if not date:
            date = datetime.date.today().strftime("%Y-%m-%d")

        try:
            logger.info(f"📊 正在分析 {symbol}...")

            # 使用现有的多智能体分析
            graph_result, decision = self.trading_graph.propagate(symbol, date)

            result = {
                'symbol': symbol,
                'date': date,
                'success': True,
                'action': decision.get('action', '观察'),
                'reasoning': decision.get('reasoning', '继续观察市场变化'),
                'confidence': decision.get('confidence', 'N/A'),
                'price_target': decision.get('price_target', 'N/A'),
                'risk_level': decision.get('risk_level', 'N/A')
            }

            logger.info(f"✅ {symbol} 分析完成: {result['action']}")
            return result

        except Exception as e:
            logger.error(f"❌ {symbol} 分析失败: {e}")
            return {
                'symbol': symbol,
                'date': date,
                'success': False,
                'error': str(e)
            }

    def generate_report(self) -> str:
        """生成完整的分析报告"""

        if not self.watchlist:
            return "❌ 没有配置股票关注列表"

        logger.info(f"🚀 开始生成每日股票分析报告...")
        logger.info(f"📅 分析日期: {datetime.date.today()}")

        # 报告头部
        report_lines = [
            f"📊 每日股票分析报告",
            f"📅 日期: {datetime.date.today().strftime('%Y年%m月%d日')}",
            f"🕕 生成时间: {datetime.datetime.now().strftime('%H:%M')}",
            f"📈 分析股票数量: {len(self.watchlist)}",
            "",
            "=" * 40,
            ""
        ]

        # 分析结果统计
        success_count = 0
        buy_count = 0
        sell_count = 0
        hold_count = 0

        # 逐个分析股票
        for i, symbol in enumerate(self.watchlist, 1):
            logger.info(f"[{i}/{len(self.watchlist)}] 分析 {symbol}...")

            result = self.analyze_stock(symbol)

            if result.get('success'):
                success_count += 1
                action = result.get('action', '观察').upper()

                # 统计操作建议
                if 'BUY' in action or '买' in action:
                    buy_count += 1
                    action_emoji = "🟢"
                elif 'SELL' in action or '卖' in action:
                    sell_count += 1
                    action_emoji = "🔴"
                else:
                    hold_count += 1
                    action_emoji = "🟡"

                # 添加到报告
                stock_name = self.get_stock_name(symbol)
                report_lines.extend([
                    f"{action_emoji} {symbol} ({stock_name})",
                    f"   操作建议: {result.get('action', '观察')}",
                    f"   分析理由: {result.get('reasoning', '继续观察')[:100]}{'...' if len(result.get('reasoning', '')) > 100 else ''}",
                    f"   信心度: {result.get('confidence', 'N/A')}",
                    ""
                ])

            else:
                # 分析失败
                report_lines.extend([
                    f"❌ {symbol}",
                    f"   分析失败: {result.get('error', '未知错误')}",
                    ""
                ])

            # 添加延迟避免API限制
            if i < len(self.watchlist):
                time.sleep(1)

        # 添加总结
        report_lines.extend([
            "=" * 40,
            "📊 分析总结:",
            f"✅ 成功分析: {success_count}/{len(self.watchlist)} 只股票",
            f"🟢 买入建议: {buy_count} 只",
            f"🔴 卖出建议: {sell_count} 只",
            f"🟡 观察持有: {hold_count} 只",
            "",
            "⚠️ 风险提示: 以上分析仅供参考，投资有风险，请谨慎决策！",
            "",
            f"🤖 Generated by TradingAgents-CN at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ])

        report = "\n".join(report_lines)
        logger.info(f"✅ 报告生成完成，共 {len(report_lines)} 行")

        return report

    def send_to_wechat(self, report: str) -> bool:
        """发送报告到企业微信

        Args:
            report: 报告内容

        Returns:
            是否发送成功
        """
        if not self.wechat_webhook:
            logger.error("❌ 企业微信 Webhook 地址未配置")
            return False

        try:
            logger.info("📤 正在发送报告到企业微信...")

            # 构建消息载荷
            payload = {
                "msgtype": "text",
                "text": {
                    "content": report
                }
            }

            # 发送请求
            response = requests.post(
                self.wechat_webhook,
                json=payload,
                timeout=30,
                headers={
                    'Content-Type': 'application/json'
                }
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("✅ 企业微信发送成功")
                    return True
                else:
                    logger.error(f"❌ 企业微信返回错误: {result}")
                    return False
            else:
                logger.error(f"❌ HTTP请求失败: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ 发送到企业微信失败: {e}")
            return False

    def save_report(self, report: str, filename: str = None) -> bool:
        """保存报告到文件

        Args:
            report: 报告内容
            filename: 文件名，默认根据日期生成

        Returns:
            是否保存成功
        """
        if not filename:
            today = datetime.date.today().strftime("%Y%m%d")
            filename = f"reports/daily_stock_report_{today}.txt"

        try:
            # 确保目录存在
            report_file = project_root / filename
            report_file.parent.mkdir(parents=True, exist_ok=True)

            # 保存文件
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            logger.info(f"💾 报告已保存到: {report_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 保存报告失败: {e}")
            return False

    def run_daily_report(self, save_file: bool = True, send_wechat: bool = True):
        """运行每日报告生成流程"""

        logger.info("🚀 启动每日股票分析报告系统")
        logger.info("=" * 50)

        try:
            # 生成报告
            report = self.generate_report()

            if not report or "❌ 没有配置股票关注列表" in report:
                logger.error("❌ 报告生成失败")
                return

            # 打印报告到控制台
            print("\n" + report + "\n")

            # 保存到文件
            if save_file:
                self.save_report(report)

            # 发送到企业微信
            if send_wechat:
                self.send_to_wechat(report)

            logger.info("🎉 每日报告流程完成!")

        except Exception as e:
            logger.error(f"❌ 报告流程执行失败: {e}")

            # 发送错误通知
            if send_wechat:
                error_msg = f"❌ 每日股票分析报告生成失败\n时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n错误: {str(e)}"
                self.send_to_wechat(error_msg)

def main():
    """主函数"""

    # 检查必要的环境变量
    required_env_vars = ['DASHSCOPE_API_KEY']  # 或其他你使用的API密钥
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ 缺少环境变量: {', '.join(missing_vars)}")
        logger.error("请检查 .env 文件配置")
        return

    # 创建报告生成器并运行
    reporter = DailyStockReporter()
    reporter.run_daily_report()

if __name__ == "__main__":
    main()