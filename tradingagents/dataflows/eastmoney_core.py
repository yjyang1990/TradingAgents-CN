#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
东方财富核心财务指标获取模块
参考adata项目实现，专门用于获取更全面的财务数据

@desc: 主要指标获取
@reference: adata/stock/finance/core.py
@url: https://emweb.securities.eastmoney.com/pc_hsf10/pages/index.html?type=web&code=SZ300059&color=b#/cwfx/zyzb
"""

import pandas as pd
import requests
from typing import Dict, Optional, Any
import time

from tradingagents.utils.logging_init import get_logger

logger = get_logger("eastmoney_core")


class EastMoneyCore:
    """东方财富核心财务指标获取类"""

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        初始化东方财富数据获取器

        Args:
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        self.timeout = timeout
        self.max_retries = max_retries

        # 字段重命名映射，基于adata项目
        self.rename_mapping = {
            'SECURITY_CODE': 'stock_code',
            'SECURITY_NAME_ABBR': 'short_name',
            'REPORT_DATE': 'report_date',
            'REPORT_TYPE': 'report_type',
            'NOTICE_DATE': 'notice_date',

            # 每股指标
            'EPSJB': 'basic_eps',                  # 基本每股收益
            'EPSKCJB': 'diluted_eps',              # 稀释每股收益
            'EPSXS': 'non_gaap_eps',               # 扣非每股收益
            'BPS': 'net_asset_ps',                 # 每股净资产
            'MGZBGJ': 'cap_reserve_ps',            # 每股资本公积金
            'MGWFPLR': 'undist_profit_ps',         # 每股未分配利润
            'MGJYXJJE': 'oper_cf_ps',              # 每股经营性现金流

            # 收入与利润
            "TOTALOPERATEREVE": 'total_rev',        # 营业总收入
            "MLR": "gross_profit",                  # 毛利率
            "PARENTNETPROFIT": "net_profit_attr_sh", # 归母净利润
            "KCFJCXSYJLR": "non_gaap_net_profit",   # 扣非净利润

            # 增长率
            "TOTALOPERATEREVETZ": "total_rev_yoy_gr",      # 营收同比增长
            "PARENTNETPROFITTZ": "net_profit_yoy_gr",      # 净利润同比增长
            "KCFJCXSYJLRTZ": "non_gaap_net_profit_yoy_gr", # 扣非净利润同比增长
            "YYZSRGDHBZC": "total_rev_qoq_gr",             # 营收环比增长
            "NETPROFITRPHBZC": "net_profit_qoq_gr",        # 净利润环比增长
            "KFJLRGDHBZC": "non_gaap_net_profit_qoq_gr",   # 扣非净利润环比增长

            # 盈利能力
            "ROEJQ": "roe_wtd",                    # 加权ROE
            "ROEKCJQ": "roe_non_gaap_wtd",         # 扣非ROE
            "ZZCJLL": "roa_wtd",                   # 总资产收益率
            "XSMLL": "gross_margin",               # 销售毛利率
            "XSJLL": "net_margin",                 # 销售净利率

            # 现金流比率
            "YSZKYYSR": 'adv_receipts_to_rev',     # 预收款/营收
            "XSJXLYYSR": 'net_cf_sales_to_rev',    # 销售商品收现/营收
            "JYXJLYYSR": 'oper_cf_to_rev',         # 经营现金流/营收
            "TAXRATE": 'eff_tax_rate',             # 实际税率

            # 偿债能力
            "LD": 'curr_ratio',                    # 流动比率
            "SD": 'quick_ratio',                   # 速动比率
            "XJLLB": 'cash_flow_ratio',            # 现金流动负债比
            "ZCFZL": 'asset_liab_ratio',           # 资产负债率
            "QYCS": 'equity_multiplier',           # 权益乘数
            "CQBL": 'equity_ratio',                # 产权比率

            # 营运能力
            "ZZCZZTS": 'total_asset_turn_days',    # 总资产周转天数
            "CHZZTS": 'inv_turn_days',             # 存货周转天数
            "YSZKZZTS": 'acct_recv_turn_days',     # 应收账款周转天数
            "TOAZZL": 'total_asset_turn_rate',     # 总资产周转率
            "CHZZL": 'inv_turn_rate',              # 存货周转率
            "YSZKZZL": 'acct_recv_turn_rate',      # 应收账款周转率
        }

    def _compile_exchange_by_stock_code(self, stock_code: str) -> str:
        """
        根据股票代码编译交易所后缀

        Args:
            stock_code: 原始股票代码

        Returns:
            str: 带交易所后缀的股票代码
        """
        if '.' in stock_code:
            return stock_code

        # A股代码处理
        if stock_code.startswith(('000', '001', '002', '003')):
            return f"{stock_code}.SZ"
        elif stock_code.startswith(('600', '601', '603', '605')):
            return f"{stock_code}.SH"
        elif stock_code.startswith('300'):
            return f"{stock_code}.SZ"
        elif stock_code.startswith('688'):
            return f"{stock_code}.SH"
        else:
            # 默认深交所
            return f"{stock_code}.SZ"

    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """
        发送HTTP请求，带重试机制

        Args:
            url: 请求URL
            params: 请求参数

        Returns:
            Dict: 响应数据，失败返回None
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://emweb.securities.eastmoney.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()

                data = response.json()
                if data.get('code') == 0:
                    return data
                else:
                    logger.warning(f"API返回错误代码: {data.get('code')}, 消息: {data.get('message', '')}")
                    return None

            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # 递增等待时间

        logger.error(f"请求最终失败，已重试 {self.max_retries} 次")
        return None

    def get_core_index(self, stock_code: str) -> Optional[pd.DataFrame]:
        """
        获取核心财务指标

        Args:
            stock_code: 股票代码（如：300059, 002115）

        Returns:
            pd.DataFrame: 财务指标数据框，失败返回None
        """
        logger.info(f"📊 [东方财富] 获取核心指标: {stock_code}")

        # 1. 编译股票代码
        full_stock_code = self._compile_exchange_by_stock_code(stock_code)
        logger.debug(f"📊 [东方财富] 完整股票代码: {full_stock_code}")

        # 2. 准备请求参数
        report_types = ['年报', '中报', '三季报', '一季报']
        all_data = []

        # 3. 分别获取各种报告类型的数据
        for report_type in report_types:
            logger.debug(f"📊 [东方财富] 获取{report_type}数据...")

            url = 'https://datacenter.eastmoney.com/securities/api/data/get'
            params = {
                'type': 'RPT_F10_FINANCE_MAINFINADATA',
                'sty': 'APP_F10_MAINFINADATA',
                'quoteColumns': '',
                'filter': f'(SECUCODE="{full_stock_code}")(REPORT_TYPE="{report_type}")',
                'p': 1,
                'ps': 100,
                'sr': -1,
                'st': 'REPORT_DATE',
                'source': 'HSF10',
                'client': 'PC',
                'v': f'03890754131799983{int(time.time())}'
            }

            data = self._make_request(url, params)
            if data and 'result' in data and 'data' in data['result']:
                records = data['result']['data']
                if records:
                    all_data.extend(records)
                    logger.debug(f"✅ [东方财富] {report_type}数据获取成功，{len(records)}条记录")
                else:
                    logger.debug(f"⚠️ [东方财富] {report_type}数据为空")
            else:
                logger.warning(f"❌ [东方财富] {report_type}数据获取失败")

            # 避免请求过快
            time.sleep(0.5)

        if not all_data:
            logger.error(f"❌ [东方财富] 未获取到任何数据: {stock_code}")
            return None

        # 4. 数据处理
        try:
            # 创建DataFrame
            df = pd.DataFrame(all_data)

            # 重命名列
            available_columns = [col for col in self.rename_mapping.keys() if col in df.columns]
            df_renamed = df[available_columns].rename(columns=self.rename_mapping)

            # 添加未重命名的重要列
            important_cols = ['SECUCODE', 'ORG_CODE', 'CURRENCY']
            for col in important_cols:
                if col in df.columns:
                    df_renamed[col.lower()] = df[col]

            # 格式化日期
            if 'report_date' in df_renamed.columns:
                df_renamed['report_date'] = pd.to_datetime(df_renamed['report_date']).dt.strftime('%Y-%m-%d')
            if 'notice_date' in df_renamed.columns:
                df_renamed['notice_date'] = pd.to_datetime(df_renamed['notice_date']).dt.strftime('%Y-%m-%d')

            # 按报告日期排序
            if 'report_date' in df_renamed.columns:
                df_renamed = df_renamed.sort_values(by='report_date', ascending=False)

            logger.info(f"✅ [东方财富] 数据处理完成: {len(df_renamed)}条记录, {len(df_renamed.columns)}个字段")

            return df_renamed

        except Exception as e:
            logger.error(f"❌ [东方财富] 数据处理失败: {e}")
            return None

    def get_latest_metrics(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取最新一期的关键财务指标

        Args:
            stock_code: 股票代码

        Returns:
            Dict: 最新财务指标字典
        """
        df = self.get_core_index(stock_code)
        if df is None or df.empty:
            return None

        # 获取最新一期数据
        latest = df.iloc[0].to_dict()

        # 构建关键指标摘要
        key_metrics = {
            'stock_code': latest.get('stock_code'),
            'short_name': latest.get('short_name'),
            'report_date': latest.get('report_date'),
            'report_type': latest.get('report_type'),

            # 盈利能力
            'roe_wtd': latest.get('roe_wtd'),              # ROE加权
            'roa_wtd': latest.get('roa_wtd'),              # ROA
            'gross_margin': latest.get('gross_margin'),    # 毛利率
            'net_margin': latest.get('net_margin'),        # 净利率

            # 每股指标
            'basic_eps': latest.get('basic_eps'),          # 基本每股收益
            'diluted_eps': latest.get('diluted_eps'),      # 稀释每股收益
            'net_asset_ps': latest.get('net_asset_ps'),    # 每股净资产
            'oper_cf_ps': latest.get('oper_cf_ps'),        # 每股经营现金流

            # 增长能力
            'total_rev_yoy_gr': latest.get('total_rev_yoy_gr'),      # 营收同比增长
            'net_profit_yoy_gr': latest.get('net_profit_yoy_gr'),    # 净利润同比增长

            # 偿债能力
            'curr_ratio': latest.get('curr_ratio'),         # 流动比率
            'quick_ratio': latest.get('quick_ratio'),       # 速动比率
            'asset_liab_ratio': latest.get('asset_liab_ratio'),  # 资产负债率

            # 营运能力
            'total_asset_turn_days': latest.get('total_asset_turn_days'),  # 总资产周转天数
            'acct_recv_turn_days': latest.get('acct_recv_turn_days'),      # 应收账款周转天数
            'inv_turn_days': latest.get('inv_turn_days'),                  # 存货周转天数
        }

        return key_metrics

    def format_analysis_report(self, stock_code: str) -> str:
        """
        格式化生成分析报告

        Args:
            stock_code: 股票代码

        Returns:
            str: 格式化的分析报告
        """
        logger.info(f"📊 [东方财富] 生成分析报告: {stock_code}")

        df = self.get_core_index(stock_code)
        if df is None or df.empty:
            return f"❌ 无法获取 {stock_code} 的财务数据"

        latest = df.iloc[0]

        # 生成报告
        report_lines = [
            f"# {stock_code} 东方财富核心财务指标分析",
            "",
            f"**股票代码**: {latest.get('stock_code', 'N/A')}",
            f"**公司简称**: {latest.get('short_name', 'N/A')}",
            f"**报告期**: {latest.get('report_date', 'N/A')} ({latest.get('report_type', 'N/A')})",
            f"**公告日期**: {latest.get('notice_date', 'N/A')}",
            "",
            "## 📈 盈利能力指标",
            f"- **净资产收益率(ROE)**: {self._format_percent(latest.get('roe_wtd'))}",
            f"- **总资产收益率(ROA)**: {self._format_percent(latest.get('roa_wtd'))}",
            f"- **销售毛利率**: {self._format_percent(latest.get('gross_margin'))}",
            f"- **销售净利率**: {self._format_percent(latest.get('net_margin'))}",
            "",
            "## 💰 每股指标",
            f"- **基本每股收益**: {self._format_number(latest.get('basic_eps'))} 元",
            f"- **稀释每股收益**: {self._format_number(latest.get('diluted_eps'))} 元",
            f"- **每股净资产**: {self._format_number(latest.get('net_asset_ps'))} 元",
            f"- **每股经营现金流**: {self._format_number(latest.get('oper_cf_ps'))} 元",
            "",
            "## 📊 增长能力",
            f"- **营业收入同比增长**: {self._format_percent(latest.get('total_rev_yoy_gr'))}",
            f"- **净利润同比增长**: {self._format_percent(latest.get('net_profit_yoy_gr'))}",
            f"- **扣非净利润同比增长**: {self._format_percent(latest.get('non_gaap_net_profit_yoy_gr'))}",
            "",
            "## 🏦 偿债能力",
            f"- **流动比率**: {self._format_number(latest.get('curr_ratio'))}",
            f"- **速动比率**: {self._format_number(latest.get('quick_ratio'))}",
            f"- **资产负债率**: {self._format_percent(latest.get('asset_liab_ratio'))}",
            "",
            "## ⚡ 营运能力",
            f"- **总资产周转天数**: {self._format_number(latest.get('total_asset_turn_days'))} 天",
            f"- **应收账款周转天数**: {self._format_number(latest.get('acct_recv_turn_days'))} 天",
            f"- **存货周转天数**: {self._format_number(latest.get('inv_turn_days'))} 天",
            "",
            "## 📋 历史数据概览",
            f"- **数据期数**: {len(df)} 个报告期",
            f"- **最早报告期**: {df.iloc[-1].get('report_date', 'N/A')}",
            f"- **数据字段**: {len(df.columns)} 个指标",
            "",
            "---",
            "*数据来源：东方财富 | 指标定义遵循中国会计准则*"
        ]

        report = "\n".join(report_lines)
        logger.info(f"✅ [东方财富] 报告生成完成，长度: {len(report)} 字符")

        return report

    def _format_number(self, value, decimals: int = 2) -> str:
        """格式化数字"""
        if value is None or pd.isna(value):
            return "N/A"
        try:
            return f"{float(value):.{decimals}f}"
        except (ValueError, TypeError):
            return str(value)

    def _format_percent(self, value, decimals: int = 2) -> str:
        """格式化百分比"""
        if value is None or pd.isna(value):
            return "N/A"
        try:
            return f"{float(value):.{decimals}f}%"
        except (ValueError, TypeError):
            return str(value)


# 单例实例
eastmoney_core = EastMoneyCore()


# 便捷函数
def get_stock_core_metrics(stock_code: str) -> Optional[pd.DataFrame]:
    """
    获取股票核心财务指标

    Args:
        stock_code: 股票代码

    Returns:
        pd.DataFrame: 财务指标数据
    """
    return eastmoney_core.get_core_index(stock_code)


def get_stock_latest_metrics(stock_code: str) -> Optional[Dict[str, Any]]:
    """
    获取股票最新财务指标

    Args:
        stock_code: 股票代码

    Returns:
        Dict: 最新财务指标
    """
    return eastmoney_core.get_latest_metrics(stock_code)


def generate_stock_analysis_report(stock_code: str) -> str:
    """
    生成股票财务分析报告

    Args:
        stock_code: 股票代码

    Returns:
        str: 格式化的分析报告
    """
    return eastmoney_core.format_analysis_report(stock_code)


if __name__ == "__main__":
    # 测试代码
    test_codes = ["002115", "300059", "002115"]

    for code in test_codes:
        print(f"\n{'='*60}")
        print(f"测试股票: {code}")
        print(f"{'='*60}")

        # 生成分析报告
        report = generate_stock_analysis_report(code)
        print(report)

        print("\n" + "-"*60)