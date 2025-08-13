"""
News Data Fetcher - Handles news and sentiment data retrieval
新闻数据获取器 - 处理新闻和情感分析数据获取
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from .market_utils import MarketUtils
from .data_sources import AkShareNewsDataSource, BaseNewsDataSource


class NewsDataFetcher:
    """新闻数据获取器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化新闻数据获取器
        
        Args:
            config: 配置字典
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # 缓存配置
        cache_config = config.get('cache', {})
        self.news_cache_duration = timedelta(hours=cache_config.get('news_hours', 2))
        self.news_cache = {}
        
        # 分析参数
        params = config.get('analysis_params', {})
        self.max_news_count = params.get('max_news_count', 100)
        
        # 初始化数据源
        self.data_sources = self._initialize_data_sources()
        
    def _initialize_data_sources(self) -> List[BaseNewsDataSource]:
        """初始化数据源列表"""
        sources = []
        
        # 添加AkShare数据源
        akshare_source = AkShareNewsDataSource()
        if akshare_source.is_available():
            sources.append(akshare_source)
            self.logger.info("已加载AkShare新闻数据源")
        else:
            self.logger.warning("AkShare新闻数据源不可用")
        
        # 这里可以添加其他数据源
        # 例如: sources.append(TushareNewsSource())
        
        return sources
    
    def _get_available_source(self) -> Optional[BaseNewsDataSource]:
        """获取可用的数据源"""
        for source in self.data_sources:
            if source.is_available():
                return source
        return None
    
    def get_comprehensive_news_data(self, stock_code: str, days: int = 15) -> Dict[str, Any]:
        """
        获取综合新闻数据
        
        Args:
            stock_code: 股票代码
            days: 获取天数
            
        Returns:
            Dict[str, Any]: 新闻数据字典
        """
        stock_code, market = MarketUtils.normalize_stock_code(stock_code)
        cache_key = f"news_{market}_{stock_code}_{days}"
        
        # 检查缓存
        if cache_key in self.news_cache:
            cache_time, data = self.news_cache[cache_key]
            if datetime.now() - cache_time < self.news_cache_duration:
                self.logger.info(f"使用缓存的新闻数据: {cache_key}")
                return data
        
        self.logger.info(f"正在获取 {market.upper()} {stock_code} 的新闻数据 (过去{days}天)...")
        
        # 获取可用的数据源
        source = self._get_available_source()
        if not source:
            self.logger.error("没有可用的新闻数据源")
            return {'news': [], 'sentiment': {}}
        
        try:
            # 使用数据源获取新闻数据
            news_list = source.get_stock_news(stock_code, market, days)
            
            # 构建新闻数据结构
            news_data = {
                'news': news_list,
                'sentiment': self._calculate_basic_sentiment(news_list)
            }
            
            # 缓存数据
            if news_data and news_data.get('news'):
                self.news_cache[cache_key] = (datetime.now(), news_data)
                self.logger.info(f"成功获取 {len(news_data.get('news', []))} 条新闻")
            
            return news_data
            
        except Exception as e:
            self.logger.error(f"获取 {stock_code} 新闻数据时发生错误: {e}")
            return {'news': [], 'sentiment': {}}
    
    def _calculate_basic_sentiment(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算基础情绪分析
        
        Args:
            news_list: 新闻列表
            
        Returns:
            Dict[str, Any]: 情绪分析结果
        """
        if not news_list:
            return {
                'overall_sentiment': 0.0,
                'sentiment_trend': '中性',
                'confidence_score': 0.0,
                'total_analyzed': 0
            }
        
        try:
            # 计算平均情绪
            sentiments = [news.get('sentiment', 0.0) for news in news_list if 'sentiment' in news]
            overall_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            
            # 情绪趋势
            if overall_sentiment > 0.1:
                sentiment_trend = '积极'
            elif overall_sentiment < -0.1:
                sentiment_trend = '消极'
            else:
                sentiment_trend = '中性'
            
            # 置信度评分（基于新闻数量）
            confidence_score = min(len(news_list) / 50.0, 1.0)
            
            return {
                'overall_sentiment': overall_sentiment,
                'sentiment_trend': sentiment_trend,
                'confidence_score': confidence_score,
                'total_analyzed': len(news_list)
            }
            
        except Exception as e:
            self.logger.error(f"计算情绪分析失败: {e}")
            return {
                'overall_sentiment': 0.0,
                'sentiment_trend': '中性',
                'confidence_score': 0.0,
                'total_analyzed': len(news_list)
            }
    
    def analyze_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析新闻情绪（兼容旧接口）
        
        Args:
            news_data: 新闻数据
            
        Returns:
            Dict[str, Any]: 情绪分析结果
        """
        if not news_data or not news_data.get('news'):
            return {
                'overall_sentiment': 0.0,
                'sentiment_trend': '中性',
                'confidence_score': 0.0,
                'total_analyzed': 0
            }
        
        # 如果已经有情绪分析结果，直接返回
        if 'sentiment' in news_data:
            return news_data['sentiment']
        
        # 否则重新计算
        return self._calculate_basic_sentiment(news_data['news'])