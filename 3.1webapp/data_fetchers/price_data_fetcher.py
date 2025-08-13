"""
Price Data Fetcher - Handles stock price data retrieval from multiple markets
价格数据获取器 - 处理多市场股票价格数据获取
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .market_utils import MarketUtils
from .data_sources import AkSharePriceDataSource, BasePriceDataSource


class PriceDataFetcher:
    """股票价格数据获取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化价格数据获取器
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # 缓存配置
        cache_config = config.get('cache', {})
        self.cache_duration = timedelta(hours=cache_config.get('price_hours', 1))
        self.price_cache = {}
        
        # 分析参数
        params = config.get('analysis_params', {})
        self.technical_period_days = params.get('technical_period_days', 180)
        
        # 初始化数据源
        self.data_sources = self._initialize_data_sources()
        
    def _initialize_data_sources(self) -> List[BasePriceDataSource]:
        """初始化数据源列表"""
        sources = []
        
        # 添加AkShare数据源
        akshare_source = AkSharePriceDataSource()
        if akshare_source.is_available():
            sources.append(akshare_source)
            self.logger.info("已加载AkShare价格数据源")
        else:
            self.logger.warning("AkShare价格数据源不可用")
        
        # 这里可以添加其他数据源
        # 例如: sources.append(YahooFinanceSource())
        
        return sources
    
    def _get_available_source(self) -> Optional[BasePriceDataSource]:
        """获取可用的数据源"""
        for source in self.data_sources:
            if source.is_available():
                return source
        return None
    
    def get_stock_data(self, stock_code: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """
        获取股票价格数据（支持多市场）
        
        Args:
            stock_code: 股票代码
            period: 时间周期
            
        Returns:
            pd.DataFrame: 股票价格数据
        """
        stock_code, market = MarketUtils.normalize_stock_code(stock_code)
        cache_key = f"{market}_{stock_code}_{period}"
        
        # 检查缓存
        if cache_key in self.price_cache:
            cache_time, data = self.price_cache[cache_key]
            if datetime.now() - cache_time < self.cache_duration:
                self.logger.info(f"使用缓存的价格数据: {cache_key}")
                return data
        
        self.logger.info(f"正在获取 {market.upper()} {stock_code} 的历史数据 (过去{self.technical_period_days}天)...")
        
        # 获取可用的数据源
        source = self._get_available_source()
        if not source:
            self.logger.error("没有可用的价格数据源")
            return None
        
        try:
            # 使用数据源获取数据
            stock_data = source.get_stock_data(stock_code, market, period)
            
            if stock_data is not None and not stock_data.empty:
                # 缓存数据
                self.price_cache[cache_key] = (datetime.now(), stock_data)
                self.logger.info(f"成功获取 {len(stock_data)} 条价格数据")
                return stock_data
            else:
                self.logger.warning(f"获取 {stock_code} 价格数据为空")
                return None
                
        except Exception as e:
            self.logger.error(f"获取 {market} {stock_code} 价格数据时发生错误: {e}")
            return None
    
    def get_price_info(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        从价格数据中提取关键信息
        
        Args:
            price_data: 价格数据DataFrame
            
        Returns:
            Dict[str, Any]: 价格信息字典
        """
        if price_data is None or price_data.empty or 'close' not in price_data.columns:
            return {
                'current_price': 0.0,
                'price_change': 0.0,
                'volume_ratio': 1.0,
                'volatility': 0.0
            }
        
        try:
            latest = price_data.iloc[-1]
            current_price = float(latest['close'])
            
            if len(price_data) > 1:
                prev_price = float(price_data.iloc[-2]['close'])
                price_change = ((current_price - prev_price) / prev_price) * 100
            else:
                price_change = 0.0
                
            # 计算成交量比率
            volume_ratio = 1.0
            if 'volume' in price_data.columns and len(price_data) >= 20:
                current_volume = float(latest['volume']) if not pd.isna(latest['volume']) else 0
                avg_volume = float(price_data['volume'].tail(20).mean())
                if avg_volume > 0:
                    volume_ratio = current_volume / avg_volume
                
            return {
                'current_price': current_price,
                'price_change': price_change,
                'volume_ratio': volume_ratio,
                'volatility': abs(price_change)
            }
        except Exception as e:
            self.logger.error(f"计算价格信息失败: {e}")
            return {'current_price': 0.0, 'price_change': 0.0, 'volume_ratio': 1.0, 'volatility': 0.0}