"""
Price Data Fetcher - Handles stock price data retrieval from multiple markets
价格数据获取器 - 处理多市场股票价格数据获取
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .market_utils import MarketUtils


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
        cache_key = f"{market}_{stock_code}"
        
        # 检查缓存
        if cache_key in self.price_cache:
            cache_time, data = self.price_cache[cache_key]
            if datetime.now() - cache_time < self.cache_duration:
                self.logger.info(f"使用缓存的价格数据: {cache_key}")
                return data
        
        try:
            import akshare as ak
            
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=self.technical_period_days)).strftime('%Y%m%d')
            
            self.logger.info(f"正在获取 {market.upper()} {stock_code} 的历史数据 (过去{self.technical_period_days}天)...")
            
            stock_data = None
            
            if market == 'a_stock':
                stock_data = self._get_a_stock_data(stock_code, start_date, end_date, ak)
            elif market == 'hk_stock':
                stock_data = self._get_hk_stock_data(stock_code, start_date, end_date, ak)
            elif market == 'us_stock':
                stock_data = self._get_us_stock_data(stock_code, start_date, end_date, ak)
            
            if stock_data is not None and not stock_data.empty:
                # 标准化列名
                stock_data = self._standardize_columns(stock_data)
                
                # 缓存数据
                self.price_cache[cache_key] = (datetime.now(), stock_data)
                self.logger.info(f"成功获取 {len(stock_data)} 条价格数据")
                return stock_data
            else:
                self.logger.error(f"获取 {stock_code} 价格数据失败或数据为空")
                return None
                
        except Exception as e:
            self.logger.error(f"获取股票 {stock_code} 价格数据时发生错误: {e}")
            return None
    
    def _get_a_stock_data(self, stock_code: str, start_date: str, end_date: str, ak) -> Optional[pd.DataFrame]:
        """获取A股数据"""
        try:
            return ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        except Exception as e:
            self.logger.error(f"获取A股 {stock_code} 数据失败: {e}")
            return None
    
    def _get_hk_stock_data(self, stock_code: str, start_date: str, end_date: str, ak) -> Optional[pd.DataFrame]:
        """获取港股数据"""
        try:
            # 主接口
            return ak.stock_hk_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        except Exception as e:
            self.logger.warning(f"使用港股历史数据接口失败: {e}，尝试备用接口...")
            try:
                # 备用接口
                data = ak.stock_hk_daily(symbol=stock_code, adjust="qfq")
                if data is not None and not data.empty:
                    # 过滤日期范围
                    data = data[data.index >= start_date]
                    return data
            except Exception as e2:
                self.logger.error(f"港股备用接口也失败: {e2}")
                return None
    
    def _get_us_stock_data(self, stock_code: str, start_date: str, end_date: str, ak) -> Optional[pd.DataFrame]:
        """获取美股数据"""
        try:
            # 主接口
            return ak.stock_us_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
        except Exception as e:
            self.logger.warning(f"使用美股历史数据接口失败: {e}，尝试备用接口...")
            try:
                # 备用接口
                data = ak.stock_us_daily(symbol=stock_code, adjust="qfq")
                if data is not None and not data.empty:
                    # 过滤日期范围
                    data = data[data.index >= start_date]
                    return data
            except Exception as e2:
                self.logger.error(f"美股备用接口也失败: {e2}")
                return None
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame列名
        
        Args:
            df: 原始数据框
            
        Returns:
            pd.DataFrame: 标准化后的数据框
        """
        # 常见的列名映射
        column_mapping = {
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close', 
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'change_pct',
            '涨跌额': 'change',
            '换手率': 'turnover',
            'Open': 'open',
            'Close': 'close',
            'High': 'high', 
            'Low': 'low',
            'Volume': 'volume',
            'Amount': 'amount'
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        # 确保必要的列存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                self.logger.warning(f"缺少必要列: {col}")
        
        return df
    
    def get_price_info(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """
        从价格数据中提取关键信息
        
        Args:
            price_data: 价格数据DataFrame
            
        Returns:
            Dict[str, Any]: 价格信息字典
        """
        if price_data is None or price_data.empty:
            return {}
        
        try:
            # 获取最新数据
            latest = price_data.iloc[-1]
            previous = price_data.iloc[-2] if len(price_data) > 1 else latest
            
            current_price = float(latest['close'])
            previous_price = float(previous['close'])
            
            # 计算变化
            price_change = current_price - previous_price
            price_change_pct = (price_change / previous_price) * 100 if previous_price != 0 else 0
            
            # 成交量信息
            current_volume = float(latest.get('volume', 0))
            avg_volume = float(price_data['volume'].tail(20).mean()) if 'volume' in price_data.columns else 0
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # 波动率计算（20日）
            if len(price_data) >= 20:
                returns = price_data['close'].pct_change().dropna()
                volatility = float(returns.tail(20).std() * np.sqrt(252) * 100)  # 年化波动率
            else:
                volatility = 0.0
            
            return {
                'current_price': current_price,
                'previous_price': previous_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'volatility': volatility,
                'high_52w': float(price_data['high'].max()),
                'low_52w': float(price_data['low'].min()),
                'data_points': len(price_data)
            }
            
        except Exception as e:
            self.logger.error(f"提取价格信息时发生错误: {e}")
            return {}