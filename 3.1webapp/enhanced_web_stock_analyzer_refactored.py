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
    
    def validate_stock_code(self, stock_code: str) -> Dict[str, Any]:
        """验证股票代码"""
        try:
            normalized_code, market = self.normalize_stock_code(stock_code)
            market_info = MarketUtils.get_market_info(market)
            
            return {
                'valid': True,
                'normalized_code': normalized_code,
                'market': market,
                'market_info': market_info
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def get_market_status(self) -> Dict[str, Any]:
        """获取市场状态"""
        return {
            'markets': self.market_config,
            'timestamp': datetime.now().isoformat(),
            'system_ready': True
        }

# 为了保持向后兼容性，保留一些旧的方法名
class EnhancedWebStockAnalyzerLegacy(EnhancedWebStockAnalyzer):
    """向后兼容的增强版分析器"""
    
    def get_fundamental_data(self, stock_code: str) -> Dict[str, Any]:
        """旧版基本面数据获取方法"""
        return self.get_comprehensive_fundamental_data(stock_code)
    
    def get_news_data(self, stock_code: str, days: int = 30) -> Dict[str, Any]:
        """旧版新闻数据获取方法"""
        return self.get_comprehensive_news_data(stock_code, days)