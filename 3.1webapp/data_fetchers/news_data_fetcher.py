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
        
        try:
            if market == 'a_stock':
                data = self._get_a_stock_news_data(stock_code, days)
            elif market == 'hk_stock':
                data = self._get_hk_stock_news_data(stock_code, days)
            elif market == 'us_stock':
                data = self._get_us_stock_news_data(stock_code, days)
            else:
                data = {'news': [], 'sentiment': {}}
            
            # 缓存数据
            if data and data.get('news'):
                self.news_cache[cache_key] = (datetime.now(), data)
                self.logger.info(f"成功获取 {len(data.get('news', []))} 条新闻")
            
            return data
            
        except Exception as e:
            self.logger.error(f"获取 {stock_code} 新闻数据时发生错误: {e}")
            return {'news': [], 'sentiment': {}}
    
    def _get_a_stock_news_data(self, stock_code: str, days: int) -> Dict[str, Any]:
        """获取A股新闻数据"""
        import akshare as ak
        news_data = {'news': [], 'sentiment': {}}
        
        try:
            # 获取股票新闻
            try:
                stock_news = ak.stock_news_em(symbol=stock_code)
                if not stock_news.empty:
                    # 按日期过滤
                    cutoff_date = datetime.now() - timedelta(days=days)
                    filtered_news = []
                    
                    for _, row in stock_news.iterrows():
                        try:
                            news_date = pd.to_datetime(row['发布时间'])
                            if news_date >= cutoff_date:
                                news_item = {
                                    'title': str(row.get('新闻标题', '')),
                                    'content': str(row.get('新闻内容', '')),
                                    'date': news_date.strftime('%Y-%m-%d %H:%M:%S'),
                                    'source': str(row.get('新闻来源', ''))
                                }
                                filtered_news.append(news_item)
                        except Exception as e:
                            continue
                    
                    news_data['news'] = filtered_news[:self.max_news_count]
            except Exception as e:
                self.logger.warning(f"获取A股新闻失败: {e}")
            
            # 获取资金流向作为情绪指标
            try:
                money_flow = ak.stock_individual_fund_flow(stock=stock_code, market="沪深A股")
                if not money_flow.empty:
                    latest_flow = money_flow.iloc[0]
                    news_data['sentiment']['money_flow'] = {
                        '主力净流入': float(latest_flow.get('主力净流入', 0)),
                        '超大单净流入': float(latest_flow.get('超大单净流入', 0)),
                        '大单净流入': float(latest_flow.get('大单净流入', 0)),
                        '中单净流入': float(latest_flow.get('中单净流入', 0)),
                        '小单净流入': float(latest_flow.get('小单净流入', 0))
                    }
            except Exception as e:
                self.logger.warning(f"获取A股资金流向失败: {e}")
            
            # 获取龙虎榜数据作为情绪参考
            try:
                lhb_data = ak.stock_lhb_detail_em(symbol=stock_code, start_date="20240101", end_date=datetime.now().strftime('%Y%m%d'))
                if not lhb_data.empty:
                    recent_lhb = lhb_data.head(5)  # 最近5条记录
                    news_data['sentiment']['lhb_activity'] = len(recent_lhb)
            except Exception as e:
                self.logger.warning(f"获取A股龙虎榜数据失败: {e}")
                
        except Exception as e:
            self.logger.error(f"获取A股 {stock_code} 新闻数据失败: {e}")
        
        return news_data
    
    def _get_hk_stock_news_data(self, stock_code: str, days: int) -> Dict[str, Any]:
        """获取港股新闻数据"""
        import akshare as ak
        news_data = {'news': [], 'sentiment': {}}
        
        try:
            # 港股新闻获取相对有限，尝试获取基本信息
            try:
                # 获取港股基本面信息作为参考
                hk_info = ak.stock_hk_spot_em()
                hk_detail = hk_info[hk_info['代码'] == stock_code]
                if not hk_detail.empty:
                    stock_row = hk_detail.iloc[0]
                    news_data['sentiment']['market_info'] = {
                        '涨跌幅': float(stock_row.get('涨跌幅', 0)),
                        '成交量': float(stock_row.get('成交量', 0)),
                        '换手率': float(stock_row.get('换手率', 0))
                    }
            except Exception as e:
                self.logger.warning(f"获取港股市场信息失败: {e}")
            
            # 模拟新闻条目（实际应用中需要接入港股新闻源）
            news_data['news'] = [{
                'title': f'港股 {stock_code} 市场表现',
                'content': '港股新闻数据获取功能开发中...',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': '港股数据'
            }]
            
        except Exception as e:
            self.logger.error(f"获取港股 {stock_code} 新闻数据失败: {e}")
        
        return news_data
    
    def _get_us_stock_news_data(self, stock_code: str, days: int) -> Dict[str, Any]:
        """获取美股新闻数据"""
        import akshare as ak
        news_data = {'news': [], 'sentiment': {}}
        
        try:
            # 美股新闻获取相对有限，尝试获取基本信息
            try:
                # 获取美股基本面信息作为参考
                us_info = ak.stock_us_spot_em()
                us_detail = us_info[us_info['代码'] == stock_code]
                if not us_detail.empty:
                    stock_row = us_detail.iloc[0]
                    news_data['sentiment']['market_info'] = {
                        '涨跌幅': float(stock_row.get('涨跌幅', 0)),
                        '成交量': float(stock_row.get('成交量', 0)),
                        '市值': float(stock_row.get('总市值', 0))
                    }
            except Exception as e:
                self.logger.warning(f"获取美股市场信息失败: {e}")
            
            # 模拟新闻条目（实际应用中需要接入美股新闻源）
            news_data['news'] = [{
                'title': f'美股 {stock_code} 市场表现',
                'content': '美股新闻数据获取功能开发中...',
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': '美股数据'
            }]
            
        except Exception as e:
            self.logger.error(f"获取美股 {stock_code} 新闻数据失败: {e}")
        
        return news_data
    
    def analyze_sentiment(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析新闻情绪
        
        Args:
            news_data: 新闻数据字典
            
        Returns:
            Dict[str, Any]: 情绪分析结果
        """
        sentiment_result = {
            'overall_sentiment': 0.0,
            'sentiment_trend': 'neutral',
            'confidence_score': 0.0,
            'total_analyzed': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0
        }
        
        try:
            news_list = news_data.get('news', [])
            if not news_list:
                return sentiment_result
            
            # 简单的关键词情绪分析
            positive_keywords = ['上涨', '增长', '利好', '突破', '创新高', '盈利', '收益', '成功', '优秀', '强劲']
            negative_keywords = ['下跌', '下降', '利空', '亏损', '风险', '下调', '担忧', '问题', '困难', '危机']
            
            sentiment_scores = []
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            
            for news_item in news_list[:50]:  # 限制分析数量
                title = news_item.get('title', '')
                content = news_item.get('content', '')
                text = f"{title} {content}"
                
                pos_score = sum(1 for word in positive_keywords if word in text)
                neg_score = sum(1 for word in negative_keywords if word in text)
                
                if pos_score > neg_score:
                    sentiment = 1.0
                    positive_count += 1
                elif neg_score > pos_score:
                    sentiment = -1.0
                    negative_count += 1
                else:
                    sentiment = 0.0
                    neutral_count += 1
                
                sentiment_scores.append(sentiment)
            
            if sentiment_scores:
                overall_sentiment = np.mean(sentiment_scores)
                confidence_score = min(abs(overall_sentiment) + 0.1, 1.0)
                
                if overall_sentiment > 0.1:
                    sentiment_trend = 'positive'
                elif overall_sentiment < -0.1:
                    sentiment_trend = 'negative'
                else:
                    sentiment_trend = 'neutral'
                
                sentiment_result.update({
                    'overall_sentiment': float(overall_sentiment),
                    'sentiment_trend': sentiment_trend,
                    'confidence_score': float(confidence_score),
                    'total_analyzed': len(sentiment_scores),
                    'positive_count': positive_count,
                    'negative_count': negative_count,
                    'neutral_count': neutral_count
                })
            
            # 结合资金流向数据
            money_flow = news_data.get('sentiment', {}).get('money_flow', {})
            if money_flow:
                main_flow = money_flow.get('主力净流入', 0)
                if main_flow > 0:
                    sentiment_result['overall_sentiment'] += 0.2
                elif main_flow < 0:
                    sentiment_result['overall_sentiment'] -= 0.2
                
                # 重新调整sentiment_trend
                if sentiment_result['overall_sentiment'] > 0.1:
                    sentiment_result['sentiment_trend'] = 'positive'
                elif sentiment_result['overall_sentiment'] < -0.1:
                    sentiment_result['sentiment_trend'] = 'negative'
                else:
                    sentiment_result['sentiment_trend'] = 'neutral'
                    
        except Exception as e:
            self.logger.error(f"分析新闻情绪时发生错误: {e}")
        
        return sentiment_result
    
    def format_news_data(self, news_data: Dict[str, Any], include_content: bool = False, max_news: int = 10) -> str:
        """
        格式化新闻数据为文本
        
        Args:
            news_data: 新闻数据字典
            include_content: 是否包含新闻内容
            max_news: 最大新闻数量
            
        Returns:
            str: 格式化后的文本
        """
        if not news_data or not news_data.get('news'):
            return "暂无相关新闻"
        
        formatted_lines = []
        news_list = news_data.get('news', [])[:max_news]
        
        for i, news_item in enumerate(news_list, 1):
            title = news_item.get('title', '无标题')
            date = news_item.get('date', '')
            source = news_item.get('source', '')
            
            news_header = f"{i}. {title}"
            if date:
                news_header += f" ({date})"
            if source:
                news_header += f" - {source}"
            
            formatted_lines.append(news_header)
            
            if include_content:
                content = news_item.get('content', '')
                if content and content != '无内容':
                    # 限制内容长度
                    content = content[:200] + "..." if len(content) > 200 else content
                    formatted_lines.append(f"   内容: {content}")
            
            formatted_lines.append("")  # 空行分隔
        
        # 添加情绪分析摘要
        sentiment = news_data.get('sentiment', {})
        if sentiment:
            formatted_lines.append("情绪分析:")
            
            money_flow = sentiment.get('money_flow', {})
            if money_flow:
                main_flow = money_flow.get('主力净流入', 0)
                formatted_lines.append(f"主力净流入: {main_flow:,.0f}万元")
            
            market_info = sentiment.get('market_info', {})
            if market_info:
                change_pct = market_info.get('涨跌幅', 0)
                formatted_lines.append(f"当日涨跌幅: {change_pct:.2f}%")
        
        return "\n".join(formatted_lines) if formatted_lines else "新闻数据处理中..."