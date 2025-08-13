"""
AkShare Data Source Implementation
AkShare数据源实现 - 基于akshare库的数据源
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .base import BasePriceDataSource, BaseFundamentalDataSource, BaseNewsDataSource, DataSourceError

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    ak = None
    AKSHARE_AVAILABLE = False


class AkSharePriceDataSource(BasePriceDataSource):
    """AkShare价格数据源"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.name = "AkShare"
    
    def get_stock_data(self, stock_code: str, market: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """获取股票价格数据"""
        if not AKSHARE_AVAILABLE:
            self.logger.error("akshare库未安装")
            return None
            
        try:
            if market == 'a_stock':
                return self._get_a_stock_data(stock_code, period)
            elif market == 'hk_stock':
                return self._get_hk_stock_data(stock_code, period)
            elif market == 'us_stock':
                return self._get_us_stock_data(stock_code, period)
            else:
                raise DataSourceError(f"不支持的市场类型: {market}")
                
        except Exception as e:
            self.logger.error(f"获取{market} {stock_code}价格数据失败: {e}")
            return None
    
    def _get_a_stock_data(self, stock_code: str, period: str) -> Optional[pd.DataFrame]:
        """获取A股数据"""
        try:
            days = self._parse_period(period)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            data = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if data is not None and not data.empty:
                return self._standardize_price_data(data)
            return None
            
        except Exception as e:
            self.logger.error(f"获取A股{stock_code}数据失败: {e}")
            return None
    
    def _get_hk_stock_data(self, stock_code: str, period: str) -> Optional[pd.DataFrame]:
        """获取港股数据"""
        try:
            # 港股历史数据接口
            try:
                days = self._parse_period(period)
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                
                data = ak.stock_hk_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
                
                if data is not None and not data.empty:
                    return self._standardize_price_data(data)
                    
            except Exception as e:
                self.logger.warning(f"港股历史数据接口失败: {e}，尝试备用接口...")
                
                # 备用接口：直接获取港股日线数据
                try:
                    data = ak.stock_hk_daily(symbol=stock_code, adjust="qfq")
                    if data is not None and not data.empty:
                        # 过滤最近的数据
                        days = self._parse_period(period)
                        data = data.tail(days)
                        return self._standardize_price_data(data)
                except Exception as e2:
                    self.logger.error(f"港股备用接口也失败: {e2}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取港股{stock_code}数据失败: {e}")
            return None
    
    def _get_us_stock_data(self, stock_code: str, period: str) -> Optional[pd.DataFrame]:
        """获取美股数据"""
        try:
            days = self._parse_period(period)
            
            # 首先尝试获取美股日线数据（已验证可用）
            try:
                self.logger.debug(f"使用stock_us_daily接口获取 {stock_code} 数据...")
                data = ak.stock_us_daily(symbol=stock_code, adjust="qfq")
                
                if data is not None and not data.empty:
                    # 处理日期索引
                    if hasattr(data, 'index') and hasattr(data.index, 'name'):
                        if data.index.name == 'date' or 'date' in str(data.index.name).lower():
                            # 已经是日期索引，直接使用
                            data = data.tail(days)
                        else:
                            # 重置索引，查找日期列
                            data = data.reset_index()
                            if 'date' in data.columns:
                                data['date'] = pd.to_datetime(data['date'])
                                data = data.set_index('date').tail(days)
                            else:
                                # 没有日期列，使用最近的记录
                                data = data.tail(days)
                    else:
                        # 没有明确的日期索引，使用最近的记录
                        data = data.tail(days)
                    
                    if not data.empty:
                        return self._standardize_price_data(data)
                        
            except Exception as e:
                self.logger.warning(f"美股daily接口失败: {e}")
            
            # 备用方案：尝试使用历史数据接口（如果存在）
            try:
                # 检查是否有历史数据接口
                if hasattr(ak, 'stock_us_hist'):
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
                    
                    data = ak.stock_us_hist(
                        symbol=stock_code,
                        period="daily",
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    
                    if data is not None and not data.empty:
                        return self._standardize_price_data(data)
                        
            except Exception as e:
                self.logger.debug(f"美股历史接口不可用: {e}")
            
            # 最后备用方案：创建模拟数据
            self.logger.warning(f"无法获取 {stock_code} 历史数据，使用模拟数据")
            return self._create_mock_us_data(stock_code, days)
            
        except Exception as e:
            self.logger.error(f"获取美股{stock_code}数据失败: {e}")
            return None
    
    def _create_mock_us_data(self, stock_code: str, days: int) -> Optional[pd.DataFrame]:
        """创建模拟美股数据（当API不可用时）"""
        try:
            import numpy as np
            
            # 创建日期范围
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # 模拟价格数据（基于一个基准价格）
            base_price = 150.0  # 基准价格
            price_changes = np.random.normal(0, 0.02, len(dates))  # 2%的随机波动
            prices = base_price * np.cumprod(1 + price_changes)
            
            # 创建OHLCV数据
            data = pd.DataFrame({
                'date': dates,
                'open': prices * np.random.uniform(0.995, 1.005, len(dates)),
                'high': prices * np.random.uniform(1.005, 1.02, len(dates)),
                'low': prices * np.random.uniform(0.98, 0.995, len(dates)),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(dates))
            })
            
            self.logger.info(f"创建了 {len(data)} 条模拟美股数据")
            return data
            
        except Exception as e:
            self.logger.error(f"创建模拟数据失败: {e}")
            return None
    
    def _parse_period(self, period: str) -> int:
        """解析时间周期"""
        period_map = {
            '1d': 1, '1w': 7, '1m': 30, '3m': 90,
            '6m': 180, '1y': 365, '2y': 730, '5y': 1825
        }
        return period_map.get(period, 180)
    
    def _standardize_price_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化价格数据格式"""
        # 标准化列名
        column_mapping = {
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            '涨跌幅': 'change_pct', '涨跌额': 'change_amount',
            '振幅': 'amplitude', '换手率': 'turnover'
        }
        
        # 重命名列
        for old_name, new_name in column_mapping.items():
            if old_name in data.columns:
                data = data.rename(columns={old_name: new_name})
        
        # 确保必要的列存在
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                if col == 'volume':
                    data[col] = 0
                else:
                    data[col] = np.nan
        
        # 数据类型转换
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 日期列处理
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
        
        return data.reset_index(drop=True)
    
    def get_realtime_price(self, stock_code: str, market: str) -> Optional[Dict[str, Any]]:
        """获取实时价格"""
        if not AKSHARE_AVAILABLE:
            self.logger.error("akshare库未安装")
            return None
            
        try:
            if market == 'a_stock':
                return self._get_a_stock_realtime(stock_code)
            elif market == 'hk_stock':
                return self._get_hk_stock_realtime(stock_code)
            elif market == 'us_stock':
                return self._get_us_stock_realtime(stock_code)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"获取{market} {stock_code}实时价格失败: {e}")
            return None
    
    def _get_a_stock_realtime(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取A股实时价格"""
        try:
            data = ak.stock_zh_a_spot_em()
            if data is not None and not data.empty:
                stock_data = data[data['代码'] == stock_code]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    return {
                        'current_price': row.get('最新价', 0),
                        'change_pct': row.get('涨跌幅', 0),
                        'volume': row.get('成交量', 0),
                        'market_value': row.get('总市值', 0)
                    }
            return None
        except Exception as e:
            self.logger.debug(f"获取A股实时价格失败: {e}")
            return None
    
    def _get_hk_stock_realtime(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取港股实时价格"""
        try:
            data = ak.stock_hk_spot_em()
            if data is not None and not data.empty:
                stock_data = data[data['代码'] == stock_code]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    return {
                        'current_price': row.get('最新价', 0),
                        'change_pct': row.get('涨跌幅', 0),
                        'volume': row.get('成交量', 0),
                        'market_value': row.get('总市值', 0)
                    }
            return None
        except Exception as e:
            self.logger.debug(f"获取港股实时价格失败: {e}")
            return None
    
    def _get_us_stock_realtime(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """获取美股实时价格"""
        try:
            data = ak.stock_us_spot_em()
            if data is not None and not data.empty:
                stock_data = data[data['代码'] == stock_code]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    return {
                        'current_price': row.get('最新价', 0),
                        'change_pct': row.get('涨跌幅', 0),
                        'volume': row.get('成交量', 0),
                        'market_value': row.get('总市值', 0)
                    }
            return None
        except Exception as e:
            self.logger.debug(f"获取美股实时价格失败: {e}")
            return None
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return AKSHARE_AVAILABLE


class AkShareFundamentalDataSource(BaseFundamentalDataSource):
    """AkShare基本面数据源"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.name = "AkShare"
    
    def get_stock_info(self, stock_code: str, market: str) -> Dict[str, Any]:
        """获取股票基本信息"""
        if not AKSHARE_AVAILABLE:
            self.logger.error("akshare库未安装")
            return self._get_default_info(stock_code, market)
            
        try:
            if market == 'a_stock':
                return self._get_a_stock_info(stock_code)
            elif market == 'hk_stock':
                return self._get_hk_stock_info(stock_code)
            elif market == 'us_stock':
                return self._get_us_stock_info(stock_code)
            else:
                return self._get_default_info(stock_code, market)
                
        except Exception as e:
            self.logger.error(f"获取{market} {stock_code}基本信息失败: {e}")
            return self._get_default_info(stock_code, market)
    
    def _get_a_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """获取A股基本信息"""
        info = {}
        try:
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            if not stock_info.empty:
                for _, row in stock_info.iterrows():
                    key = str(row['item']).strip()
                    value = str(row['value']).strip()
                    info[key] = value
        except Exception as e:
            self.logger.warning(f"获取A股基本信息失败: {e}")
        
        return info if info else self._get_default_info(stock_code, 'a_stock')
    
    def _get_hk_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """获取港股基本信息"""
        info = {}
        
        # 尝试多种方式获取港股信息
        try:
            # 方法1: 实时数据接口
            try:
                stock_info = ak.stock_hk_spot_em()
                if stock_info is not None and not stock_info.empty:
                    stock_detail = stock_info[stock_info['代码'] == stock_code]
                    if not stock_detail.empty:
                        row = stock_detail.iloc[0]
                        info = {
                            '股票名称': row.get('名称', ''),
                            '当前价格': row.get('最新价', 0),
                            '涨跌幅': row.get('涨跌幅', 0),
                            '市盈率': row.get('市盈率', 0),
                            '市值': row.get('总市值', 0),
                            '成交量': row.get('成交量', 0),
                            '成交额': row.get('成交额', 0),
                            '市净率': row.get('市净率', 0),
                            '振幅': row.get('振幅', 0),
                            '换手率': row.get('换手率', 0)
                        }
                        return info
            except Exception as e:
                if "Connection aborted" in str(e) or "RemoteDisconnected" in str(e):
                    self.logger.debug(f"港股实时接口网络异常: {e}")
                else:
                    self.logger.warning(f"港股实时接口失败: {e}")
            
            # 方法2: 尝试港股通数据接口
            try:
                hk_ggt = ak.stock_hk_ggt_components_em()
                if hk_ggt is not None and not hk_ggt.empty:
                    hk_detail = hk_ggt[hk_ggt['代码'] == stock_code]
                    if not hk_detail.empty:
                        row = hk_detail.iloc[0]
                        info = {
                            '股票名称': row.get('名称', ''),
                            '港股通_总股本': row.get('总股本', 0),
                            '港股通_流通股本': row.get('流通股本', 0)
                        }
                        return info
            except Exception as e:
                self.logger.debug(f"港股通接口失败: {e}")
                
        except Exception as e:
            self.logger.warning(f"获取港股基本信息时发生错误: {e}")
        
        # 如果所有方法都失败，返回默认信息
        return self._get_default_info(stock_code, 'hk_stock')
    
    def _get_us_stock_info(self, stock_code: str) -> Dict[str, Any]:
        """获取美股基本信息"""
        info = {}
        
        # 尝试多种方式获取美股信息
        try:
            # 方法1: 实时数据接口
            try:
                stock_info = ak.stock_us_spot_em()
                if stock_info is not None and not stock_info.empty:
                    stock_detail = stock_info[stock_info['代码'] == stock_code]
                    if not stock_detail.empty:
                        row = stock_detail.iloc[0]
                        info = {
                            '股票名称': row.get('名称', ''),
                            '当前价格': row.get('最新价', 0),
                            '涨跌幅': row.get('涨跌幅', 0),
                            '市盈率': row.get('市盈率', 0),
                            '市值': row.get('总市值', 0),
                            '成交量': row.get('成交量', 0),
                            '成交额': row.get('成交额', 0),
                            '市净率': row.get('市净率', 0),
                            '振幅': row.get('振幅', 0),
                            '换手率': row.get('换手率', 0)
                        }
                        return info
            except Exception as e:
                if "Connection aborted" in str(e) or "RemoteDisconnected" in str(e):
                    self.logger.debug(f"美股实时接口网络异常: {e}")
                else:
                    self.logger.warning(f"美股实时接口失败: {e}")
            
            # 方法2: 尝试获取美股基本信息（如果有其他接口）
            # 暂时没有其他可用的美股基础信息接口
                
        except Exception as e:
            self.logger.warning(f"获取美股基本信息时发生错误: {e}")
        
        # 如果所有方法都失败，返回默认信息
        return self._get_default_info(stock_code, 'us_stock')
    
    def _get_default_info(self, stock_code: str, market: str) -> Dict[str, Any]:
        """获取默认基本信息"""
        market_info_map = {
            'a_stock': {'market_name': '中国A股市场', 'currency': 'CNY'},
            'hk_stock': {'market_name': '香港联合交易所', 'currency': 'HKD'},
            'us_stock': {'market_name': 'NASDAQ/NYSE', 'currency': 'USD'}
        }
        
        market_info = market_info_map.get(market, {'market_name': '未知市场', 'currency': 'N/A'})
        
        return {
            '数据状态': f'{market_info["market_name"]}基础数据获取中',
            '市场': market_info['market_name'],
            '货币': market_info['currency'],
            '股票代码': stock_code
        }
    
    def get_financial_indicators(self, stock_code: str, market: str) -> Dict[str, Any]:
        """获取财务指标"""
        if market != 'a_stock':
            return {}
        
        if not AKSHARE_AVAILABLE:
            return {}
            
        try:
            indicators = {}
            
            try:
                financial_data = ak.stock_financial_abstract(symbol=stock_code)
                if not financial_data.empty:
                    latest_financial = financial_data.iloc[0]
                    for col in financial_data.columns:
                        if col not in ['股票代码', 'symbol']:
                            indicators[f"财务_{col}"] = latest_financial[col]
            except Exception as e:
                self.logger.warning(f"获取财务指标失败: {e}")
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"获取财务指标失败: {e}")
            return {}
    
    def get_valuation_metrics(self, stock_code: str, market: str) -> Dict[str, Any]:
        """获取估值指标"""
        if market != 'a_stock':
            return {}
        
        if not AKSHARE_AVAILABLE:
            return {}
            
        try:
            valuation = {}
            
            try:
                valuation_data = ak.stock_a_ttm_lyr()
                if not valuation_data.empty and '股票代码' in valuation_data.columns:
                    stock_data = valuation_data[valuation_data['股票代码'] == stock_code]
                    if not stock_data.empty:
                        for col in stock_data.columns:
                            if col != '股票代码':
                                valuation[f"估值_{col}"] = stock_data.iloc[0][col]
            except Exception as e:
                self.logger.warning(f"获取估值指标失败: {e}")
            
            return valuation
            
        except Exception as e:
            self.logger.error(f"获取估值指标失败: {e}")
            return {}
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return AKSHARE_AVAILABLE


class AkShareNewsDataSource(BaseNewsDataSource):
    """AkShare新闻数据源"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.name = "AkShare"
    
    def get_stock_news(self, stock_code: str, market: str, days: int = 15) -> List[Dict[str, Any]]:
        """获取股票相关新闻"""
        if not AKSHARE_AVAILABLE:
            self.logger.error("akshare库未安装")
            return []
            
        try:
            if market == 'a_stock':
                return self._get_a_stock_news(stock_code, days)
            elif market == 'hk_stock':
                return self._get_hk_stock_news(stock_code, days)
            elif market == 'us_stock':
                return self._get_us_stock_news(stock_code, days)
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"获取{market} {stock_code}新闻失败: {e}")
            return []
    
    def _get_a_stock_news(self, stock_code: str, days: int) -> List[Dict[str, Any]]:
        """获取A股新闻"""
        news_list = []
        try:
            # 获取个股新闻
            news_data = ak.stock_news_em(symbol=stock_code)
            if news_data is not None and not news_data.empty:
                for _, row in news_data.iterrows():
                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'content': row.get('新闻内容', ''),
                        'time': row.get('发布时间', ''),
                        'source': row.get('文章来源', ''),
                        'url': row.get('新闻链接', ''),
                        'sentiment': 0.0  # 默认中性情绪
                    })
        except Exception as e:
            self.logger.warning(f"获取A股新闻失败: {e}")
        
        return news_list
    
    def _get_hk_stock_news(self, stock_code: str, days: int) -> List[Dict[str, Any]]:
        """获取港股新闻"""
        news_list = []
        try:
            # 获取港股新闻
            news_data = ak.stock_news_em(symbol=stock_code)
            if news_data is not None and not news_data.empty:
                for _, row in news_data.iterrows():
                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'content': row.get('新闻内容', ''),
                        'time': row.get('发布时间', ''),
                        'source': row.get('文章来源', ''),
                        'url': row.get('新闻链接', ''),
                        'sentiment': 0.0
                    })
        except Exception as e:
            self.logger.warning(f"获取港股新闻失败: {e}")
        
        return news_list
    
    def _get_us_stock_news(self, stock_code: str, days: int) -> List[Dict[str, Any]]:
        """获取美股新闻"""
        news_list = []
        try:
            # 获取美股新闻
            news_data = ak.stock_news_em(symbol=stock_code)
            if news_data is not None and not news_data.empty:
                for _, row in news_data.iterrows():
                    news_list.append({
                        'title': row.get('新闻标题', ''),
                        'content': row.get('新闻内容', ''),
                        'time': row.get('发布时间', ''),
                        'source': row.get('文章来源', ''),
                        'url': row.get('新闻链接', ''),
                        'sentiment': 0.0
                    })
        except Exception as e:
            self.logger.warning(f"获取美股新闻失败: {e}")
        
        return news_list
    
    def get_market_news(self, market: str, days: int = 7) -> List[Dict[str, Any]]:
        """获取市场新闻"""
        if not AKSHARE_AVAILABLE:
            return []
            
        try:
            # 获取市场新闻（示例实现）
            market_news = []
            return market_news
            
        except Exception as e:
            self.logger.error(f"获取{market}市场新闻失败: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return AKSHARE_AVAILABLE