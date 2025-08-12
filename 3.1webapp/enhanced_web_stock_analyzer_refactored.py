"""
Web版增强股票分析系统 - 重构版 - 支持AI流式输出 + 港美股分析
Refactored Enhanced Web Stock Analysis System with modular data fetchers
支持市场：A股、港股、美股
"""

import os
import sys
import logging
import warnings
import pandas as pd
import numpy as np
import json
import math
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable, Any
import time

# 导入新的数据获取模块
from data_fetchers import PriceDataFetcher, FundamentalDataFetcher, NewsDataFetcher, MarketUtils

# 忽略警告
warnings.filterwarnings('ignore')

# 设置日志 - 只输出到命令行
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 只保留命令行输出
    ]
)

class EnhancedWebStockAnalyzer:
    """增强版Web股票分析器（支持A股/港股/美股 + AI流式输出）- 重构版"""
    
    def __init__(self, config_file='config.json'):
        """初始化分析器"""
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        
        # 加载配置文件
        self.config = self._load_config()
        
        # 初始化数据获取器
        self.price_fetcher = PriceDataFetcher(self.config)
        self.fundamental_fetcher = FundamentalDataFetcher(self.config)
        self.news_fetcher = NewsDataFetcher(self.config)
        
        # 分析权重配置
        weights = self.config.get('analysis_weights', {})
        self.analysis_weights = {
            'technical': weights.get('technical', 0.4),
            'fundamental': weights.get('fundamental', 0.4),
            'sentiment': weights.get('sentiment', 0.2)
        }
        
        # 流式推理配置
        streaming = self.config.get('streaming', {})
        self.streaming_config = {
            'enabled': streaming.get('enabled', True),
            'show_thinking': streaming.get('show_thinking', True),
            'delay': streaming.get('delay', 0.1)
        }
        
        # AI配置
        ai_config = self.config.get('ai', {})
        self.ai_config = {
            'max_tokens': ai_config.get('max_tokens', 4000),
            'temperature': ai_config.get('temperature', 0.7),
            'model_preference': ai_config.get('model_preference', 'openai')
        }
        
        # 分析参数配置
        params = self.config.get('analysis_params', {})
        self.analysis_params = {
            'max_news_count': params.get('max_news_count', 100),
            'technical_period_days': params.get('technical_period_days', 180),
            'financial_indicators_count': params.get('financial_indicators_count', 25),
            'include_news_content': params.get('include_news_content', True),
            'max_news_tokens': params.get('max_news_tokens', 2000),
            'recent_trading_days': params.get('recent_trading_days', 30),
            'hide_scores': params.get('hide_scores', True)
        }
        
        # 市场配置
        markets = self.config.get('markets', {})
        self.market_config = {
            'a_stock': markets.get('a_stock', {'enabled': True, 'currency': 'CNY', 'timezone': 'Asia/Shanghai'}),
            'hk_stock': markets.get('hk_stock', {'enabled': True, 'currency': 'HKD', 'timezone': 'Asia/Hong_Kong'}),
            'us_stock': markets.get('us_stock', {'enabled': True, 'currency': 'USD', 'timezone': 'America/New_York'})
        }
        
        # API密钥配置
        self.api_keys = self.config.get('api_keys', {})
        
        self.logger.info("增强版Web股票分析器初始化完成（支持A股/港股/美股 + AI流式输出）- 重构版")
        self._log_config_status()

    def _load_config(self):
        """加载JSON配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"成功加载配置文件: {self.config_file}")
                return config
            else:
                self.logger.warning(f"配置文件 {self.config_file} 不存在，使用默认配置")
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}，使用默认配置")
            return self._get_default_config()
    
    def _get_default_config(self):
        """返回默认配置"""
        return {
            "api_keys": {
                "openai": "",
                "anthropic": "",
                "zhipu": ""
            },
            "ai": {
                "model_preference": "openai",
                "models": {
                    "openai": "gpt-4o-mini",
                    "anthropic": "claude-3-haiku-20240307",
                    "zhipu": "chatglm_turbo"
                },
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "analysis_weights": {
                "technical": 0.4,
                "fundamental": 0.4,
                "sentiment": 0.2
            },
            "cache": {
                "price_hours": 1,
                "fundamental_hours": 6,
                "news_hours": 2
            },
            "streaming": {
                "enabled": True,
                "show_thinking": True,
                "delay": 0.1
            },
            "analysis_params": {
                "max_news_count": 100,
                "technical_period_days": 180,
                "financial_indicators_count": 25,
                "include_news_content": True,
                "max_news_tokens": 2000,
                "recent_trading_days": 30,
                "hide_scores": True
            },
            "markets": {
                "a_stock": {"enabled": True, "currency": "CNY", "timezone": "Asia/Shanghai"},
                "hk_stock": {"enabled": True, "currency": "HKD", "timezone": "Asia/Hong_Kong"},
                "us_stock": {"enabled": True, "currency": "USD", "timezone": "America/New_York"}
            }
        }
    
    def _log_config_status(self):
        """记录配置状态"""
        try:
            ai_keys_configured = sum(1 for key, value in self.api_keys.items() 
                                   if value and value != f"your-{key}-api-key-here" and not value.startswith("sk-your-"))
            
            self.logger.info(f"AI密钥配置状态: {ai_keys_configured}/3 个已配置")
            self.logger.info(f"首选AI模型: {self.ai_config['model_preference']}")
            self.logger.info(f"流式输出: {'启用' if self.streaming_config['enabled'] else '禁用'}")
            self.logger.info(f"市场支持: A股: {self.market_config['a_stock']['enabled']}, "
                           f"港股: {self.market_config['hk_stock']['enabled']}, "
                           f"美股: {self.market_config['us_stock']['enabled']}")
        except Exception as e:
            self.logger.warning(f"记录配置状态时发生错误: {e}")
    
    def normalize_stock_code(self, stock_code: str) -> Tuple[str, str]:
        """标准化股票代码并识别市场（使用MarketUtils）"""
        return MarketUtils.normalize_stock_code(stock_code)
    
    def get_stock_data(self, stock_code: str, period: str = '1y') -> Optional[pd.DataFrame]:
        """获取股票价格数据（使用PriceDataFetcher）"""
        return self.price_fetcher.get_stock_data(stock_code, period)
    
    def get_comprehensive_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """获取综合基本面数据（使用FundamentalDataFetcher）"""
        return self.fundamental_fetcher.get_comprehensive_fundamental_data(stock_code)
    
    def get_comprehensive_news_data(self, stock_code: str, days: int = 15) -> Dict[str, Any]:
        """获取综合新闻数据（使用NewsDataFetcher）"""
        return self.news_fetcher.get_comprehensive_news_data(stock_code, days)
    
    def get_price_info(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """获取价格信息（使用PriceDataFetcher）"""
        return self.price_fetcher.get_price_info(price_data)
    
    def calculate_technical_indicators(self, price_data: pd.DataFrame) -> Dict[str, float]:
        """
        计算技术指标
        
        Args:
            price_data: 价格数据DataFrame
            
        Returns:
            Dict[str, float]: 技术指标字典
        """
        if price_data is None or price_data.empty:
            return {}
        
        try:
            indicators = {}
            
            # 确保有足够的数据
            if len(price_data) < 20:
                self.logger.warning("数据量不足，无法计算完整技术指标")
                return indicators
            
            close_prices = price_data['close'].values
            high_prices = price_data['high'].values
            low_prices = price_data['low'].values
            volumes = price_data['volume'].values if 'volume' in price_data.columns else None
            
            # 移动平均线
            if len(close_prices) >= 5:
                indicators['MA5'] = np.mean(close_prices[-5:])
            if len(close_prices) >= 10:
                indicators['MA10'] = np.mean(close_prices[-10:])
            if len(close_prices) >= 20:
                indicators['MA20'] = np.mean(close_prices[-20:])
            if len(close_prices) >= 60:
                indicators['MA60'] = np.mean(close_prices[-60:])
            
            # RSI计算
            if len(close_prices) >= 15:
                deltas = np.diff(close_prices)
                gains = np.where(deltas > 0, deltas, 0)
                losses = np.where(deltas < 0, -deltas, 0)
                
                avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
                avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
                
                if avg_loss != 0:
                    rs = avg_gain / avg_loss
                    indicators['RSI'] = 100 - (100 / (1 + rs))
                else:
                    indicators['RSI'] = 100.0
            
            # MACD计算
            if len(close_prices) >= 26:
                # 指数移动平均
                ema12 = self._calculate_ema(close_prices, 12)
                ema26 = self._calculate_ema(close_prices, 26)
                macd_line = ema12 - ema26
                
                # MACD信号线
                if len(close_prices) >= 35:
                    macd_values = []
                    for i in range(26, len(close_prices)):
                        ema12_i = self._calculate_ema(close_prices[:i+1], 12)
                        ema26_i = self._calculate_ema(close_prices[:i+1], 26)
                        macd_values.append(ema12_i - ema26_i)
                    
                    if macd_values:
                        signal_line = self._calculate_ema(np.array(macd_values), 9)
                        indicators['MACD'] = macd_line
                        indicators['MACD_Signal'] = signal_line
                        indicators['MACD_Histogram'] = macd_line - signal_line
            
            # 布林带
            if len(close_prices) >= 20:
                ma20 = np.mean(close_prices[-20:])
                std20 = np.std(close_prices[-20:])
                indicators['BB_Upper'] = ma20 + (2 * std20)
                indicators['BB_Middle'] = ma20
                indicators['BB_Lower'] = ma20 - (2 * std20)
                
                # 布林带位置
                current_price = close_prices[-1]
                bb_position = (current_price - indicators['BB_Lower']) / (indicators['BB_Upper'] - indicators['BB_Lower'])
                indicators['BB_Position'] = bb_position
            
            # 成交量指标
            if volumes is not None and len(volumes) >= 20:
                indicators['Volume_MA20'] = np.mean(volumes[-20:])
                indicators['Volume_Ratio'] = volumes[-1] / indicators['Volume_MA20'] if indicators['Volume_MA20'] > 0 else 0
            
            return indicators
            
        except Exception as e:
            self.logger.error(f"计算技术指标时发生错误: {e}")
            return {}
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """计算指数移动平均"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    def analyze_technical(self, price_data: pd.DataFrame, indicators: Dict[str, float]) -> Dict[str, Any]:
        """
        技术面分析
        
        Args:
            price_data: 价格数据
            indicators: 技术指标
            
        Returns:
            Dict[str, Any]: 技术分析结果
        """
        if price_data is None or price_data.empty or not indicators:
            return {'score': 0.5, 'signals': [], 'summary': '技术分析数据不足'}
        
        try:
            signals = []
            score = 0.5  # 中性起点
            
            current_price = float(price_data['close'].iloc[-1])
            
            # 移动平均线分析
            ma_signals = []
            if 'MA5' in indicators and 'MA20' in indicators:
                if indicators['MA5'] > indicators['MA20']:
                    ma_signals.append("短期均线在长期均线上方")
                    score += 0.1
                else:
                    ma_signals.append("短期均线在长期均线下方")
                    score -= 0.1
            
            if 'MA20' in indicators:
                if current_price > indicators['MA20']:
                    ma_signals.append("股价在20日均线上方")
                    score += 0.05
                else:
                    ma_signals.append("股价在20日均线下方")
                    score -= 0.05
            
            # RSI分析
            if 'RSI' in indicators:
                rsi = indicators['RSI']
                if rsi > 70:
                    signals.append(f"RSI({rsi:.1f})处于超买区域")
                    score -= 0.1
                elif rsi < 30:
                    signals.append(f"RSI({rsi:.1f})处于超卖区域")
                    score += 0.1
                else:
                    signals.append(f"RSI({rsi:.1f})处于正常范围")
            
            # MACD分析
            if 'MACD' in indicators and 'MACD_Signal' in indicators:
                if indicators['MACD'] > indicators['MACD_Signal']:
                    signals.append("MACD在信号线上方")
                    score += 0.05
                else:
                    signals.append("MACD在信号线下方")
                    score -= 0.05
            
            # 布林带分析
            if 'BB_Position' in indicators:
                bb_pos = indicators['BB_Position']
                if bb_pos > 0.8:
                    signals.append("股价接近布林带上轨")
                    score -= 0.05
                elif bb_pos < 0.2:
                    signals.append("股价接近布林带下轨")
                    score += 0.05
                else:
                    signals.append("股价在布林带中轨附近")
            
            # 成交量分析
            if 'Volume_Ratio' in indicators:
                vol_ratio = indicators['Volume_Ratio']
                if vol_ratio > 2:
                    signals.append("成交量显著放大")
                    score += 0.05
                elif vol_ratio < 0.5:
                    signals.append("成交量萎缩")
                    score -= 0.05
                else:
                    signals.append("成交量正常")
            
            # 限制得分范围
            score = max(0, min(1, score))
            
            # 综合评估
            if score > 0.7:
                summary = "技术面偏强"
            elif score < 0.3:
                summary = "技术面偏弱"
            else:
                summary = "技术面中性"
            
            if ma_signals:
                signals.extend(ma_signals)
            
            return {
                'score': score,
                'signals': signals,
                'summary': summary,
                'indicators': indicators
            }
            
        except Exception as e:
            self.logger.error(f"技术面分析时发生错误: {e}")
            return {'score': 0.5, 'signals': [], 'summary': '技术分析计算错误'}
    
    def analyze_fundamental(self, fundamental_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基本面分析
        
        Args:
            fundamental_data: 基本面数据
            
        Returns:
            Dict[str, Any]: 基本面分析结果
        """
        if not fundamental_data:
            return {'score': 0.5, 'signals': [], 'summary': '基本面数据不足'}
        
        try:
            signals = []
            score = 0.5  # 中性起点
            
            # PE分析
            pe_keywords = ['市盈率', 'PE', 'pe']
            pe_value = None
            for key, value in fundamental_data.items():
                if any(keyword in key for keyword in pe_keywords):
                    try:
                        pe_value = float(str(value).replace(',', ''))
                        break
                    except:
                        continue
            
            if pe_value and pe_value > 0:
                if pe_value < 15:
                    signals.append(f"市盈率({pe_value:.1f})较低，估值合理")
                    score += 0.1
                elif pe_value > 30:
                    signals.append(f"市盈率({pe_value:.1f})较高，估值偏贵")
                    score -= 0.1
                else:
                    signals.append(f"市盈率({pe_value:.1f})适中")
            
            # 营收和利润增长
            growth_keywords = ['营业收入', '净利润', '增长', '同比']
            for key, value in fundamental_data.items():
                if any(keyword in key for keyword in growth_keywords):
                    try:
                        value_str = str(value)
                        if '%' in value_str:
                            growth_rate = float(value_str.replace('%', ''))
                            if growth_rate > 20:
                                signals.append(f"{key}增长良好({growth_rate:.1f}%)")
                                score += 0.05
                            elif growth_rate < -10:
                                signals.append(f"{key}下滑明显({growth_rate:.1f}%)")
                                score -= 0.05
                    except:
                        continue
            
            # ROE分析
            roe_keywords = ['ROE', 'roe', '净资产收益率']
            for key, value in fundamental_data.items():
                if any(keyword in key for keyword in roe_keywords):
                    try:
                        roe_value = float(str(value).replace('%', ''))
                        if roe_value > 15:
                            signals.append(f"净资产收益率({roe_value:.1f}%)优秀")
                            score += 0.1
                        elif roe_value < 5:
                            signals.append(f"净资产收益率({roe_value:.1f}%)较低")
                            score -= 0.05
                        break
                    except:
                        continue
            
            # 限制得分范围
            score = max(0, min(1, score))
            
            # 综合评估
            if score > 0.7:
                summary = "基本面优秀"
            elif score < 0.3:
                summary = "基本面较弱"
            else:
                summary = "基本面一般"
            
            return {
                'score': score,
                'signals': signals,
                'summary': summary
            }
            
        except Exception as e:
            self.logger.error(f"基本面分析时发生错误: {e}")
            return {'score': 0.5, 'signals': [], 'summary': '基本面分析计算错误'}
    
    def analyze_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """情绪面分析（使用NewsDataFetcher）"""
        return self.news_fetcher.analyze_sentiment(news_data)
    
    def calculate_comprehensive_score(self, technical_score: float, fundamental_score: float, sentiment_score: float) -> float:
        """
        计算综合得分
        
        Args:
            technical_score: 技术面得分
            fundamental_score: 基本面得分
            sentiment_score: 情绪面得分
            
        Returns:
            float: 综合得分
        """
        weights = self.analysis_weights
        
        comprehensive_score = (
            technical_score * weights['technical'] +
            fundamental_score * weights['fundamental'] +
            sentiment_score * weights['sentiment']
        )
        
        return max(0, min(1, comprehensive_score))
    
    # 继续添加其他分析方法...
    # 这里省略了AI流式输出等方法，需要从原文件复制过来
    
    def validate_stock_code(self, stock_code: str) -> Tuple[bool, str]:
        """验证股票代码格式（Flask服务器兼容格式）- 基于validate_stock_code_detailed实现"""
        detailed_result = self.validate_stock_code_detailed(stock_code)
        
        if detailed_result['valid']:
            market = detailed_result['market']
            return True, f"有效的{market.upper()}股票代码"
        else:
            return False, detailed_result.get('error', '股票代码验证失败')
    
    def validate_stock_code_detailed(self, stock_code: str) -> Dict[str, Any]:
        """验证股票代码（详细信息格式）"""
        try:
            # 对原始输入进行严格验证
            import re
            stock_code_clean = stock_code.strip().upper()
            
            # A股验证：必须是6位数字
            if re.match(r'^\d{6}$', stock_code_clean):
                if not self.market_config.get('a_stock', {}).get('enabled', True):
                    return {'valid': False, 'error': '市场 A_STOCK 未启用'}
                
                market_info = MarketUtils.get_market_info('a_stock')
                return {
                    'valid': True,
                    'normalized_code': stock_code_clean,
                    'market': 'a_stock',
                    'market_info': market_info
                }
            
            # 港股验证：5位数字，且以特定数字开头
            if re.match(r'^\d{5}$', stock_code_clean):
                if stock_code_clean.startswith(('0', '1', '2', '3', '6', '8', '9')):
                    if not self.market_config.get('hk_stock', {}).get('enabled', True):
                        return {'valid': False, 'error': '市场 HK_STOCK 未启用'}
                    
                    market_info = MarketUtils.get_market_info('hk_stock')
                    return {
                        'valid': True,
                        'normalized_code': stock_code_clean,
                        'market': 'hk_stock',
                        'market_info': market_info
                    }
            
            # 美股验证：1-5位字母，非纯数字
            if re.match(r'^[A-Z]{1,5}$', stock_code_clean) and not stock_code_clean.isdigit():
                if not self.market_config.get('us_stock', {}).get('enabled', True):
                    return {'valid': False, 'error': '市场 US_STOCK 未启用'}
                
                market_info = MarketUtils.get_market_info('us_stock')
                return {
                    'valid': True,
                    'normalized_code': stock_code_clean,
                    'market': 'us_stock',
                    'market_info': market_info
                }
            
            # 如果都不匹配，返回格式错误
            return {
                'valid': False,
                'error': '股票代码格式不正确。A股需6位数字，港股需5位数字，美股需1-5位字母'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'代码验证失败: {str(e)}'
            }
    
    def get_market_status(self) -> Dict[str, Any]:
        """获取市场状态"""
        return {
            'markets': self.market_config,
            'timestamp': datetime.now().isoformat(),
            'system_ready': True
        }
    
    def get_supported_markets(self) -> List[Dict[str, Any]]:
        """获取支持的市场列表"""
        supported_markets = []
        for market, config in self.market_config.items():
            if config.get('enabled', True):
                market_info = {
                    'market': market,
                    'name': market.upper().replace('_', ''),
                    'currency': config.get('currency', 'CNY'),
                    'timezone': config.get('timezone', 'Asia/Shanghai'),
                    'trading_hours': config.get('trading_hours', '09:30-15:00')
                }
                supported_markets.append(market_info)
        
        return supported_markets
    
    def get_stock_name(self, stock_code: str) -> str:
        """获取股票名称（支持多市场）"""
        try:
            stock_code, market = self.normalize_stock_code(stock_code)
            
            import akshare as ak
            
            if market == 'a_stock':
                try:
                    stock_info = ak.stock_individual_info_em(symbol=stock_code)
                    if not stock_info.empty:
                        info_dict = dict(zip(stock_info['item'], stock_info['value']))
                        stock_name = info_dict.get('股票简称', stock_code)
                        if stock_name and stock_name != stock_code:
                            return stock_name
                except Exception as e:
                    self.logger.warning(f"获取A股名称失败: {e}")
            
            elif market == 'hk_stock':
                try:
                    hk_info = ak.stock_hk_spot_em()
                    stock_info = hk_info[hk_info['代码'] == stock_code]
                    if not stock_info.empty:
                        return stock_info['名称'].iloc[0]
                except Exception as e:
                    self.logger.warning(f"获取港股名称失败: {e}")
            
            elif market == 'us_stock':
                try:
                    us_info = ak.stock_us_spot_em()
                    stock_info = us_info[us_info['代码'] == stock_code.upper()]
                    if not stock_info.empty:
                        return stock_info['名称'].iloc[0]
                except Exception as e:
                    self.logger.warning(f"获取美股名称失败: {e}")
            
            return f"{market.upper()}_{stock_code}"
            
        except Exception as e:
            self.logger.warning(f"获取股票名称时出错: {e}")
            return stock_code
    
    def get_price_info(self, price_data):
        """从价格数据中提取关键信息"""
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
                
            return {
                'current_price': current_price,
                'price_change': price_change,
                'volume_ratio': 1.0,
                'volatility': abs(price_change)
            }
        except Exception as e:
            self.logger.error(f"计算价格信息失败: {e}")
            return {'current_price': 0.0, 'price_change': 0.0, 'volume_ratio': 1.0, 'volatility': 0.0}
    
    def calculate_technical_score(self, technical_analysis):
        """计算技术分析得分"""
        if not technical_analysis:
            return 50
        
        score = 50
        indicators = technical_analysis.get('indicators', {})
        
        # RSI评分
        if 'RSI' in indicators:
            rsi = indicators['RSI']
            if 30 <= rsi <= 70:
                score += 10
            elif rsi < 30:
                score += 20  # 超卖，可能反弹
            elif rsi > 70:
                score -= 20  # 超买，可能回调
        
        return max(0, min(100, score))
    
    def calculate_fundamental_score(self, fundamental_data):
        """计算基本面得分（支持多市场）"""
        try:
            score = 50
            
            # 财务指标评分
            financial_indicators = fundamental_data.get('financial_indicators', {})
            if len(financial_indicators) >= 10:  # 调整阈值以适应不同市场
                score += 15
                
                # 通用盈利能力评分（适应不同市场的指标名称）
                roe = (financial_indicators.get('净资产收益率', 0) or 
                      financial_indicators.get('ROE', 0) or 
                      financial_indicators.get('roe', 0))
                if roe > 15:
                    score += 10
                elif roe > 10:
                    score += 5
                elif roe < 5:
                    score -= 5
                
                # 通用估值指标
                pe_ratio = (financial_indicators.get('市盈率', 0) or 
                           financial_indicators.get('PE_Ratio', 0) or 
                           financial_indicators.get('pe_ratio', 0))
                if 0 < pe_ratio < 20:
                    score += 10
                elif pe_ratio > 50:
                    score -= 5
                
                # 债务水平评估
                debt_ratio = (financial_indicators.get('资产负债率', 50) or 
                             financial_indicators.get('debt_ratio', 50))
                if debt_ratio < 30:
                    score += 5
                elif debt_ratio > 70:
                    score -= 10
            
            # 估值评分
            valuation = fundamental_data.get('valuation', {})
            if valuation:
                score += 10
            
            # 业绩预告评分
            performance_forecast = fundamental_data.get('performance_forecast', [])
            if performance_forecast:
                score += 10
            
            score = max(0, min(100, score))
            return score
            
        except Exception as e:
            self.logger.error(f"基本面评分失败: {str(e)}")
            return 50
    
    def calculate_advanced_sentiment_analysis(self, news_data):
        """计算高级情绪分析"""
        return self.news_fetcher.analyze_sentiment(news_data)
    
    def calculate_sentiment_score(self, sentiment_analysis):
        """计算情绪分析得分"""
        try:
            overall_sentiment = sentiment_analysis.get('overall_sentiment', 0.0)
            confidence_score = sentiment_analysis.get('confidence_score', 0.0)
            total_analyzed = sentiment_analysis.get('total_analyzed', 0)
            
            # 基础得分：将情绪得分从[-1,1]映射到[0,100]
            base_score = (overall_sentiment + 1) * 50
            
            # 置信度调整
            confidence_adjustment = confidence_score * 10
            
            # 新闻数量调整
            news_adjustment = min(total_analyzed / 100, 1.0) * 10
            
            final_score = base_score + confidence_adjustment + news_adjustment
            final_score = max(0, min(100, final_score))
            
            return final_score
            
        except Exception as e:
            self.logger.error(f"情绪得分计算失败: {e}")
            return 50
    
    def calculate_comprehensive_score(self, scores):
        """计算综合得分"""
        weights = self.analysis_weights
        technical_score = scores.get('technical', 50)
        fundamental_score = scores.get('fundamental', 50) 
        sentiment_score = scores.get('sentiment', 50)
        
        comprehensive = (
            technical_score * weights['technical'] +
            fundamental_score * weights['fundamental'] +
            sentiment_score * weights['sentiment']
        )
        
        return max(0, min(100, comprehensive))
    
    def generate_recommendation(self, scores, market=None):
        """根据得分生成投资建议（支持多市场）"""
        try:
            comprehensive_score = scores.get('comprehensive', 50)
            technical_score = scores.get('technical', 50)
            fundamental_score = scores.get('fundamental', 50)
            sentiment_score = scores.get('sentiment', 50)
            
            # 基础建议逻辑
            if comprehensive_score >= 80:
                if technical_score >= 75 and fundamental_score >= 75:
                    base_recommendation = "强烈推荐买入"
                else:
                    base_recommendation = "推荐买入"
            elif comprehensive_score >= 65:
                if sentiment_score >= 60:
                    base_recommendation = "建议买入"
                else:
                    base_recommendation = "谨慎买入"
            elif comprehensive_score >= 45:
                base_recommendation = "持有观望"
            elif comprehensive_score >= 30:
                base_recommendation = "建议减仓"
            else:
                base_recommendation = "建议卖出"
            
            # 根据市场特点调整建议
            if market == 'hk_stock':
                base_recommendation += " (港股)"
            elif market == 'us_stock':
                base_recommendation += " (美股)"
            elif market == 'a_stock':
                base_recommendation += " (A股)"
                
            return base_recommendation
                
        except Exception as e:
            self.logger.warning(f"生成投资建议失败: {e}")
            return "数据不足，建议谨慎"
    
    def _build_enhanced_ai_analysis_prompt(self, stock_code, stock_name, scores, technical_analysis, 
                                        fundamental_data, sentiment_analysis, price_info, market=None):
        """构建增强版AI分析提示词（支持多市场）"""
        
        market_info = ""
        if market:
            market_config = self.market_config.get(market, {})
            currency = market_config.get('currency', 'CNY')
            timezone = market_config.get('timezone', 'Asia/Shanghai')
            market_info = f"""
**市场信息：**
- 交易市场：{market.upper().replace('_', '')}
- 计价货币：{currency}
- 时区：{timezone}
"""
        
        # 提取财务指标
        financial_indicators = fundamental_data.get('financial_indicators', {})
        financial_text = ""
        if financial_indicators:
            financial_text = "**财务指标详情：**\n"
            for i, (key, value) in enumerate(financial_indicators.items(), 1):
                if isinstance(value, (int, float)) and value != 0:
                    financial_text += f"{i}. {key}: {value}\n"
        
        # 构建完整的提示词
        prompt = f"""请作为一位资深的全球股票分析师，基于以下详细数据对股票进行深度分析：
**股票基本信息：**
- 股票代码：{stock_code}
- 股票名称：{stock_name}
- 当前价格：{price_info.get('current_price', 0):.2f}
- 涨跌幅：{price_info.get('price_change', 0):.2f}%
- 成交量比率：{price_info.get('volume_ratio', 1):.2f}
- 波动率：{price_info.get('volatility', 0):.2f}%
{market_info}
**技术分析详情：**
- 均线趋势：{technical_analysis.get('ma_trend', '未知')}
- RSI指标：{technical_analysis.get('rsi', 50):.1f}
- MACD信号：{technical_analysis.get('macd_signal', '未知')}
- 布林带位置：{technical_analysis.get('bb_position', 0.5):.2f}
- 成交量状态：{technical_analysis.get('volume_status', '未知')}
{financial_text}
**市场情绪分析：**
- 整体情绪得分：{sentiment_analysis.get('overall_sentiment', 0):.3f}
- 情绪趋势：{sentiment_analysis.get('sentiment_trend', '中性')}
- 置信度：{sentiment_analysis.get('confidence_score', 0):.2f}
- 分析新闻数量：{sentiment_analysis.get('total_analyzed', 0)}条
**综合评分：**
- 技术面得分：{scores.get('technical', 50):.1f}/100
- 基本面得分：{scores.get('fundamental', 50):.1f}/100
- 情绪面得分：{scores.get('sentiment', 50):.1f}/100
- 综合得分：{scores.get('comprehensive', 50):.1f}/100
**分析要求：**
请基于以上数据，从多市场角度进行深度分析：
1. **市场特征分析**：
   - 分析该股票所属市场的特点和投资环境
   - 评估市场流动性、监管环境、交易机制等因素
   - 对比不同市场的估值体系和投资逻辑
2. **跨市场比较**：
   - 如果有同类型公司在其他市场交易，进行对比分析
   - 评估汇率风险和地缘政治因素影响
   - 分析市场间的资金流动和套利机会
3. **投资策略建议**：
   - 针对不同市场特点制定投资策略
   - 考虑市场开放时间、交易成本、税务影响
   - 提供适合该市场的风险管理建议
4. **全球化视角**：
   - 分析公司的国际化程度和全球竞争力
   - 评估宏观经济和政策对该市场的影响
   - 预测市场间的联动效应
请用专业、客观的语言进行分析，确保考虑多市场投资的复杂性。"""
        return prompt
    
    def generate_ai_analysis(self, analysis_data, enable_streaming=False, stream_callback=None):
        """生成AI增强分析（支持多市场）"""
        try:
            self.logger.info("🤖 开始AI深度分析（支持多市场）...")
            
            stock_code = analysis_data.get('stock_code', '')
            stock_name = analysis_data.get('stock_name', stock_code)
            scores = analysis_data.get('scores', {})
            technical_analysis = analysis_data.get('technical_analysis', {})
            fundamental_data = analysis_data.get('fundamental_data', {})
            sentiment_analysis = analysis_data.get('sentiment_analysis', {})
            price_info = analysis_data.get('price_info', {})
            
            # 检测市场
            _, market = self.normalize_stock_code(stock_code)
            
            # 构建增强版AI分析提示词
            prompt = self._build_enhanced_ai_analysis_prompt(
                stock_code, stock_name, scores, technical_analysis, 
                fundamental_data, sentiment_analysis, price_info, market
            )
            
            # 调用AI API（支持流式）
            ai_response = self._call_ai_api(prompt, enable_streaming, stream_callback)
            
            if ai_response:
                self.logger.info("✅ AI深度分析完成（多市场）")
                return ai_response
            else:
                self.logger.warning("⚠️ AI API不可用，使用高级分析模式")
                return self._advanced_rule_based_analysis(analysis_data, market)
                
        except Exception as e:
            self.logger.error(f"AI分析失败: {e}")
            return self._advanced_rule_based_analysis(analysis_data, market)
    
    def _call_ai_api(self, prompt, enable_streaming=False, stream_callback=None):
        """调用AI API - 支持流式输出（多市场通用）"""
        try:
            model_preference = self.config.get('ai', {}).get('model_preference', 'openai')
            
            if model_preference == 'openai' and self.api_keys.get('openai'):
                result = self._call_openai_api(prompt, enable_streaming, stream_callback)
                if result:
                    return result
            
            elif model_preference == 'anthropic' and self.api_keys.get('anthropic'):
                result = self._call_claude_api(prompt, enable_streaming, stream_callback)
                if result:
                    return result
                    
            elif model_preference == 'zhipu' and self.api_keys.get('zhipu'):
                result = self._call_zhipu_api(prompt, enable_streaming, stream_callback)
                if result:
                    return result
            
            # 尝试其他可用的服务
            if self.api_keys.get('openai') and model_preference != 'openai':
                self.logger.info("尝试备用OpenAI API...")
                result = self._call_openai_api(prompt, enable_streaming, stream_callback)
                if result:
                    return result
                    
            if self.api_keys.get('anthropic') and model_preference != 'anthropic':
                self.logger.info("尝试备用Claude API...")
                result = self._call_claude_api(prompt, enable_streaming, stream_callback)
                if result:
                    return result
                    
            if self.api_keys.get('zhipu') and model_preference != 'zhipu':
                self.logger.info("尝试备用智谱AI API...")
                result = self._call_zhipu_api(prompt, enable_streaming, stream_callback)
                if result:
                    return result
            
            return None
                
        except Exception as e:
            self.logger.error(f"AI API调用失败: {e}")
            return None
    
    def _call_openai_api(self, prompt, enable_streaming=False, stream_callback=None):
        """调用OpenAI API（简化版）"""
        try:
            import openai
            
            api_key = self.api_keys.get('openai')
            if not api_key:
                return None
            
            # 使用新版OpenAI API
            client = openai.OpenAI(api_key=api_key)
            
            api_base = self.config.get('ai', {}).get('api_base_urls', {}).get('openai')
            if api_base:
                client.base_url = api_base
            
            model = self.config.get('ai', {}).get('models', {}).get('openai', 'gpt-4o-mini')
            max_tokens = self.config.get('ai', {}).get('max_tokens', 6000)
            temperature = self.config.get('ai', {}).get('temperature', 0.7)
            
            messages = [
                {"role": "system", "content": "你是一位资深的全球股票分析师，具有丰富的多市场投资经验。请提供专业、客观、有深度的股票分析。"},
                {"role": "user", "content": prompt}
            ]
            
            # 使用新版API调用
            if enable_streaming and stream_callback:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True
                )
                
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        if stream_callback:
                            stream_callback(content)
                
                return full_response
            else:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content
                
        except Exception as e:
            self.logger.error(f"OpenAI API调用失败: {e}")
            return None
    
    def _call_claude_api(self, prompt, enable_streaming=False, stream_callback=None):
        """调用Claude API"""
        try:
            import anthropic
            
            api_key = self.api_keys.get('anthropic')
            if not api_key:
                return None
            
            client = anthropic.Anthropic(api_key=api_key)
            
            model = self.config.get('ai', {}).get('models', {}).get('anthropic', 'claude-3-haiku-20240307')
            max_tokens = self.config.get('ai', {}).get('max_tokens', 6000)
            
            if enable_streaming and stream_callback:
                with client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                ) as stream:
                    full_response = ""
                    for text in stream.text_stream:
                        full_response += text
                        if stream_callback:
                            stream_callback(text)
                
                return full_response
            else:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                return response.content[0].text
            
        except Exception as e:
            self.logger.error(f"Claude API调用失败: {e}")
            return None
    
    def _call_zhipu_api(self, prompt, enable_streaming=False, stream_callback=None):
        """调用智谱AI API"""
        try:
            api_key = self.api_keys.get('zhipu')
            if not api_key:
                return None
            
            model = self.config.get('ai', {}).get('models', {}).get('zhipu', 'chatglm_turbo')
            max_tokens = self.config.get('ai', {}).get('max_tokens', 6000)
            temperature = self.config.get('ai', {}).get('temperature', 0.7)
            
            try:
                import zhipuai
                zhipuai.api_key = api_key
                
                if hasattr(zhipuai, 'ZhipuAI'):
                    client = zhipuai.ZhipuAI(api_key=api_key)
                    
                    if enable_streaming and stream_callback:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=True
                        )
                        
                        full_response = ""
                        for chunk in response:
                            if chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                                full_response += content
                                if stream_callback:
                                    stream_callback(content)
                        
                        return full_response
                    else:
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "user", "content": prompt}
                            ],
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        return response.choices[0].message.content
                
                else:
                    response = zhipuai.model_api.invoke(
                        model=model,
                        prompt=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    if isinstance(response, dict):
                        if 'data' in response and 'choices' in response['data']:
                            return response['data']['choices'][0]['content']
                        elif 'choices' in response:
                            return response['choices'][0]['content']
                        elif 'data' in response:
                            return response['data']
                    
                    return str(response)
                    
            except ImportError:
                self.logger.error("智谱AI库未安装")
                return None
            except Exception as api_error:
                self.logger.error(f"智谱AI API调用错误: {api_error}")
                return None
            
        except Exception as e:
            self.logger.error(f"智谱AI API调用失败: {e}")
            return None
    
    def _advanced_rule_based_analysis(self, analysis_data, market=None):
        """高级规则分析（AI不可用时的备选方案）"""
        try:
            scores = analysis_data.get('scores', {})
            comprehensive_score = scores.get('comprehensive', 50)
            technical_score = scores.get('technical', 50)
            fundamental_score = scores.get('fundamental', 50)
            sentiment_score = scores.get('sentiment', 50)
            
            analysis = f"""📊 **基于规则的深度分析报告**

**综合评估：**
- 综合得分：{comprehensive_score:.1f}/100
- 技术面得分：{technical_score:.1f}/100
- 基本面得分：{fundamental_score:.1f}/100
- 情绪面得分：{sentiment_score:.1f}/100

**分析结论：**
"""
            
            if comprehensive_score >= 70:
                analysis += "📈 **投资建议：买入**\n该股票综合表现优秀，各项指标均显示积极信号。"
            elif comprehensive_score >= 60:
                analysis += "🔄 **投资建议：持有**\n该股票表现良好，建议继续观察。"
            elif comprehensive_score >= 40:
                analysis += "⚠️ **投资建议：观望**\n该股票表现中性，建议谨慎观察市场变化。"
            else:
                analysis += "📉 **投资建议：谨慎**\n该股票表现较弱，建议降低仓位或考虑其他投资机会。"
            
            if market:
                analysis += f"\n\n**市场特点：**\n该股票属于{market.upper()}市场，请注意相应的交易时间、汇率风险和监管环境。"
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"规则分析失败: {e}")
            return "分析数据不足，建议人工审核。"
    
    def analyze_stock(self, stock_code, enable_streaming=False, stream_callback=None):
        """分析股票的主方法"""
        try:
            # 标准化股票代码
            normalized_code, market = self.normalize_stock_code(stock_code)
            
            # 获取价格数据
            price_data = self.get_stock_data(normalized_code)
            if price_data is None:
                return {"error": "无法获取价格数据"}
            
            # 计算技术指标
            technical_analysis = self.calculate_technical_indicators(price_data)
            
            # 计算各项得分
            technical_score = self.calculate_technical_score(technical_analysis)
            fundamental_data = self.get_comprehensive_fundamental_data(normalized_code)
            fundamental_score = self.calculate_fundamental_score(fundamental_data)
            
            news_data = self.get_comprehensive_news_data(normalized_code)
            sentiment_analysis = self.calculate_advanced_sentiment_analysis(news_data)
            sentiment_score = self.calculate_sentiment_score(sentiment_analysis)
            
            scores = {
                'technical': technical_score,
                'fundamental': fundamental_score,
                'sentiment': sentiment_score
            }
            scores['comprehensive'] = self.calculate_comprehensive_score(scores)
            
            # 生成建议
            recommendation = self.generate_recommendation(scores, market)
            
            return {
                'stock_code': normalized_code,
                'market': market,
                'scores': scores,
                'recommendation': recommendation,
                'price_info': self.get_price_info(price_data),
                'technical_analysis': technical_analysis,
                'fundamental_data': fundamental_data,
                'news_data': news_data,
                'sentiment_analysis': sentiment_analysis
            }
            
        except Exception as e:
            self.logger.error(f"股票分析失败: {e}")
            return {"error": str(e)}

# 为了保持向后兼容性，保留一些旧的方法名
class EnhancedWebStockAnalyzerLegacy(EnhancedWebStockAnalyzer):
    """向后兼容的增强版分析器"""
    
    def get_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """旧版基本面数据获取方法"""
        return self.get_comprehensive_fundamental_data(stock_code)
    
    def get_news_data(self, stock_code: str, days: int = 30) -> Dict[str, Any]:
        """旧版新闻数据获取方法"""
        return self.get_comprehensive_news_data(stock_code, days)