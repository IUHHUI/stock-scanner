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
from .data_sources import AkShareFundamentalDataSource, BaseFundamentalDataSource


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
        
        # 初始化数据源
        self.data_sources = self._initialize_data_sources()
        
    def _initialize_data_sources(self) -> List[BaseFundamentalDataSource]:
        """初始化数据源列表"""
        sources = []
        
        # 添加AkShare数据源
        akshare_source = AkShareFundamentalDataSource()
        if akshare_source.is_available():
            sources.append(akshare_source)
            self.logger.info("已加载AkShare基本面数据源")
        else:
            self.logger.warning("AkShare基本面数据源不可用")
        
        # 这里可以添加其他数据源
        # 例如: sources.append(YahooFinanceSource())
        
        return sources
    
    def _get_available_source(self) -> Optional[BaseFundamentalDataSource]:
        """获取可用的数据源"""
        for source in self.data_sources:
            if source.is_available():
                return source
        return None
    
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
        
        # 获取可用的数据源
        source = self._get_available_source()
        if not source:
            self.logger.error("没有可用的基本面数据源")
            return {}
        
        try:
            # 使用数据源获取数据
            fundamental_data = {}
            
            # 获取基本信息
            stock_info = source.get_stock_info(stock_code, market)
            fundamental_data.update(stock_info)
            
            # 获取财务指标
            financial_indicators = source.get_financial_indicators(stock_code, market)
            fundamental_data.update(financial_indicators)
            
            # 获取估值指标
            valuation_metrics = source.get_valuation_metrics(stock_code, market)
            fundamental_data.update(valuation_metrics)
            
            # 缓存数据
            if fundamental_data:
                self.fundamental_cache[cache_key] = (datetime.now(), fundamental_data)
                self.logger.info(f"成功获取基本面数据，包含 {len(fundamental_data)} 个指标")
            
            return fundamental_data
            
        except Exception as e:
            self.logger.error(f"获取 {stock_code} 基本面数据时发生错误: {e}")
            return {}
    
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