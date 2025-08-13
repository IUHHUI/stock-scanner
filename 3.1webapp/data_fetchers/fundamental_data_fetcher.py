"""
Fundamental Data Fetcher - Handles fundamental analysis data retrieval
基本面数据获取器 - 处理基本面分析数据获取
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .market_utils import MarketUtils


class FundamentalDataFetcher:
    """基本面数据获取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化基本面数据获取器
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # 缓存配置
        cache_config = config.get('cache', {})
        self.fundamental_cache_duration = timedelta(hours=cache_config.get('fundamental_hours', 6))
        self.fundamental_cache = {}
        
        # 分析参数
        params = config.get('analysis_params', {})
        self.financial_indicators_count = params.get('financial_indicators_count', 25)
    
    def get_comprehensive_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取综合基本面数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            Dict[str, Any]: 基本面数据字典
        """
        stock_code, market = MarketUtils.normalize_stock_code(stock_code)
        cache_key = f"fundamental_{market}_{stock_code}"
        
        # 检查缓存
        if cache_key in self.fundamental_cache:
            cache_time, data = self.fundamental_cache[cache_key]
            if datetime.now() - cache_time < self.fundamental_cache_duration:
                self.logger.info(f"使用缓存的基本面数据: {cache_key}")
                return data
        
        self.logger.info(f"正在获取 {market.upper()} {stock_code} 的基本面数据...")
        
        try:
            if market == 'a_stock':
                data = self._get_a_stock_fundamental_data(stock_code)
            elif market == 'hk_stock':
                data = self._get_hk_stock_fundamental_data(stock_code)
            elif market == 'us_stock':
                data = self._get_us_stock_fundamental_data(stock_code)
            else:
                data = {}
            
            # 缓存数据
            if data:
                self.fundamental_cache[cache_key] = (datetime.now(), data)
                self.logger.info(f"成功获取基本面数据，包含 {len(data)} 个指标")
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取 {stock_code} 基本面数据时发生错误: {e}")
            return {}
    
    def _get_a_stock_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """获取A股基本面数据"""
        import akshare as ak
        fundamental_data = {}
        
        try:
            # 获取个股信息
            try:
                stock_info = ak.stock_individual_info_em(symbol=stock_code)
                if not stock_info.empty:
                    for _, row in stock_info.iterrows():
                        key = str(row['item']).strip()
                        value = str(row['value']).strip()
                        fundamental_data[key] = value
            except Exception as e:
                self.logger.warning(f"获取A股个股信息失败: {e}")
            
            # 获取财务指标 - 使用可用的API
            try:
                financial_data = ak.stock_financial_abstract(symbol=stock_code)
                if not financial_data.empty:
                    latest_financial = financial_data.iloc[0]
                    for col in financial_data.columns:
                        if col not in ['股票代码', 'symbol']:
                            fundamental_data[f"财务_{col}"] = latest_financial[col]
            except Exception as e:
                self.logger.warning(f"获取A股财务指标失败: {e}")
                
            # 尝试同花顺财务数据
            try:
                ths_data = ak.stock_zyjs_ths(symbol=stock_code)
                if not ths_data.empty:
                    for _, row in ths_data.iterrows():
                        key = str(row.get('item', row.get('指标', ''))).strip()
                        value = str(row.get('value', row.get('值', ''))).strip()
                        if key and value:
                            fundamental_data[f"同花顺_{key}"] = value
            except Exception as e:
                self.logger.warning(f"获取同花顺财务数据失败: {e}")
            
            # 获取主要财务指标
            try:
                main_indicators = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="主要财务指标")
                if not main_indicators.empty:
                    latest_indicators = main_indicators.iloc[0]
                    for col in main_indicators.columns:
                        if col not in ['股票代码', '股票简称']:
                            fundamental_data[f"指标_{col}"] = latest_indicators[col]
            except Exception as e:
                self.logger.warning(f"获取A股主要财务指标失败: {e}")
            
            # 获取估值指标
            try:
                valuation_data = ak.stock_a_ttm_lyr()
                if not valuation_data.empty:
                    # 检查数据结构并查找对应股票
                    if '股票代码' in valuation_data.columns:
                        stock_data = valuation_data[valuation_data['股票代码'] == stock_code]
                        if not stock_data.empty:
                            for col in stock_data.columns:
                                if col != '股票代码':
                                    fundamental_data[f"估值_{col}"] = stock_data.iloc[0][col]
                    elif 'code' in valuation_data.columns:
                        # 备用列名
                        stock_data = valuation_data[valuation_data['code'] == stock_code]
                        if not stock_data.empty:
                            for col in stock_data.columns:
                                if col != 'code':
                                    fundamental_data[f"估值_{col}"] = stock_data.iloc[0][col]
                    else:
                        self.logger.info(f"估值数据列名: {list(valuation_data.columns)}")
                        # 如果找不到股票代码列，跳过此数据源
                        pass
            except Exception as e:
                self.logger.warning(f"获取A股估值指标失败: {e}")
                
        except Exception as e:
            self.logger.error(f"获取A股 {stock_code} 基本面数据失败: {e}")
        
        return fundamental_data
    
    def _get_hk_stock_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """获取港股基本面数据"""
        import akshare as ak
        fundamental_data = {}
        
        try:
            # 获取港股基本信息 - 使用实时数据
            try:
                stock_info = ak.stock_hk_spot_em()
                if stock_info is not None and not stock_info.empty:
                    stock_detail = stock_info[stock_info['代码'] == stock_code]
                    if not stock_detail.empty:
                        stock_row = stock_detail.iloc[0]
                        fundamental_data.update({
                            '股票名称': stock_row.get('名称', ''),
                            '当前价格': stock_row.get('最新价', 0),
                            '涨跌幅': stock_row.get('涨跌幅', 0),
                            '市盈率': stock_row.get('市盈率', 0),
                            '市值': stock_row.get('总市值', 0),
                            '成交量': stock_row.get('成交量', 0),
                            '成交额': stock_row.get('成交额', 0),
                            '市净率': stock_row.get('市净率', 0),
                            '振幅': stock_row.get('振幅', 0),
                            '换手率': stock_row.get('换手率', 0)
                        })
                        self.logger.info(f"成功获取港股 {stock_code} 基本信息")
                    else:
                        self.logger.warning(f"港股 {stock_code} 在实时数据中未找到")
                else:
                    self.logger.warning("港股实时数据接口返回空数据")
            except Exception as e:
                if "RemoteDisconnected" in str(e) or "Connection aborted" in str(e):
                    self.logger.debug(f"港股基本信息网络连接异常: {e}")
                else:
                    self.logger.warning(f"获取港股基本信息失败: {e}")
            
            # 尝试获取额外的港股财务数据
            try:
                # 使用港股通数据接口获取更多信息
                hk_ggt = ak.stock_hk_ggt_components_em()
                if hk_ggt is not None and not hk_ggt.empty:
                    hk_detail = hk_ggt[hk_ggt['代码'] == stock_code]
                    if not hk_detail.empty:
                        row = hk_detail.iloc[0]
                        fundamental_data.update({
                            '港股通_股票名称': row.get('名称', ''),
                            '港股通_总股本': row.get('总股本', 0),
                            '港股通_流通股本': row.get('流通股本', 0)
                        })
                        self.logger.info(f"成功获取港股通数据")
            except Exception as e:
                self.logger.debug(f"获取港股通数据失败: {e}")
            
            # 如果仍然没有数据，添加默认信息
            if not fundamental_data:
                fundamental_data = {
                    '数据状态': '港股基础数据获取中',
                    '市场': '香港联合交易所',
                    '货币': 'HKD',
                    '股票代码': stock_code
                }
                self.logger.info(f"港股 {stock_code} 使用默认基础数据")
                
        except Exception as e:
            self.logger.error(f"获取港股 {stock_code} 基本面数据失败: {e}")
            # 返回基本信息以避免完全失败
            fundamental_data = {
                '数据状态': '数据获取异常',
                '市场': '香港联合交易所',
                '货币': 'HKD',
                '股票代码': stock_code,
                '错误信息': str(e)
            }
        
        return fundamental_data
    
    def _get_us_stock_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """获取美股基本面数据"""
        import akshare as ak
        fundamental_data = {}
        
        try:
            # 获取美股基本信息 - 使用实时数据
            try:
                stock_info = ak.stock_us_spot_em()
                if stock_info is not None and not stock_info.empty:
                    stock_detail = stock_info[stock_info['代码'] == stock_code]
                    if not stock_detail.empty:
                        stock_row = stock_detail.iloc[0]
                        fundamental_data.update({
                            '股票名称': stock_row.get('名称', ''),
                            '当前价格': stock_row.get('最新价', 0),
                            '涨跌幅': stock_row.get('涨跌幅', 0),
                            '市盈率': stock_row.get('市盈率', 0),
                            '市值': stock_row.get('总市值', 0),
                            '成交量': stock_row.get('成交量', 0),
                            '成交额': stock_row.get('成交额', 0),
                            '市净率': stock_row.get('市净率', 0),
                            '振幅': stock_row.get('振幅', 0),
                            '换手率': stock_row.get('换手率', 0)
                        })
                        self.logger.info(f"成功获取美股 {stock_code} 基本信息")
                    else:
                        self.logger.warning(f"美股 {stock_code} 在实时数据中未找到")
                else:
                    self.logger.warning("美股实时数据接口返回空数据")
            except Exception as e:
                if "RemoteDisconnected" in str(e) or "Connection aborted" in str(e):
                    self.logger.debug(f"美股基本信息网络连接异常: {e}")
                else:
                    self.logger.warning(f"获取美股基本信息失败: {e}")
            
            # 尝试获取美股概念板块信息
            try:
                # 获取美股概念数据
                us_concept = ak.stock_us_spot_em()  # 使用相同接口但添加更多字段
                if us_concept is not None and not us_concept.empty:
                    us_detail = us_concept[us_concept['代码'] == stock_code]
                    if not us_detail.empty:
                        row = us_detail.iloc[0]
                        # 添加更多详细信息
                        additional_fields = ['开盘', '昨收', '最高', '最低', '量比']
                        for field in additional_fields:
                            if field in row:
                                fundamental_data[f'美股_{field}'] = row.get(field, 0)
                        self.logger.info(f"成功获取美股详细数据")
            except Exception as e:
                self.logger.debug(f"获取美股详细数据失败: {e}")
            
            # 如果仍然没有数据，添加默认信息
            if not fundamental_data:
                fundamental_data = {
                    '数据状态': '美股基础数据获取中',
                    '市场': 'NASDAQ/NYSE',
                    '货币': 'USD',
                    '股票代码': stock_code
                }
                self.logger.info(f"美股 {stock_code} 使用默认基础数据")
                
        except Exception as e:
            self.logger.error(f"获取美股 {stock_code} 基本面数据失败: {e}")
            # 返回基本信息以避免完全失败
            fundamental_data = {
                '数据状态': '数据获取异常',
                '市场': 'NASDAQ/NYSE',
                '货币': 'USD',
                '股票代码': stock_code,
                '错误信息': str(e)
            }
        
        return fundamental_data
    
    def format_fundamental_data(self, data: Dict[str, Any]) -> str:
        """
        格式化基本面数据为文本
        
        Args:
            data: 基本面数据字典
            
        Returns:
            str: 格式化后的文本
        """
        if not data:
            return "无基本面数据"
        
        formatted_lines = []
        
        # 基本信息
        basic_info = []
        if '股票名称' in data:
            basic_info.append(f"股票名称: {data['股票名称']}")
        if '当前价格' in data:
            basic_info.append(f"当前价格: {data['当前价格']}")
        if '涨跌幅' in data:
            basic_info.append(f"涨跌幅: {data['涨跌幅']}%")
        
        if basic_info:
            formatted_lines.extend(basic_info)
            formatted_lines.append("")
        
        # 估值指标
        valuation_metrics = []
        for key, value in data.items():
            if any(metric in key.lower() for metric in ['市盈率', 'pe', '市净率', 'pb', '市值']):
                if value and str(value) != 'nan' and str(value) != '--':
                    valuation_metrics.append(f"{key}: {value}")
        
        if valuation_metrics:
            formatted_lines.append("估值指标:")
            formatted_lines.extend(valuation_metrics[:8])  # 限制显示数量
            formatted_lines.append("")
        
        # 财务指标
        financial_metrics = []
        for key, value in data.items():
            if any(metric in key for metric in ['营业收入', '净利润', 'ROE', 'ROA', '毛利率', '净利率']):
                if value and str(value) != 'nan' and str(value) != '--':
                    financial_metrics.append(f"{key}: {value}")
        
        if financial_metrics:
            formatted_lines.append("财务指标:")
            formatted_lines.extend(financial_metrics[:10])  # 限制显示数量
        
        # 如果没有找到特定指标，显示前N个非空数据
        if len(formatted_lines) < 5:
            other_metrics = []
            count = 0
            for key, value in data.items():
                if count >= self.financial_indicators_count:
                    break
                if value and str(value) != 'nan' and str(value) != '--':
                    other_metrics.append(f"{key}: {value}")
                    count += 1
            
            if other_metrics:
                formatted_lines.append("其他指标:")
                formatted_lines.extend(other_metrics)
        
        return "\n".join(formatted_lines) if formatted_lines else "基本面数据处理中..."