"""
Market Utilities - Stock code normalization and market detection
市场工具类 - 股票代码规范化和市场识别
"""

import re
import logging
from typing import Tuple

class MarketUtils:
    """市场工具类"""
    
    @staticmethod
    def normalize_stock_code(stock_code: str) -> Tuple[str, str]:
        """
        标准化股票代码并识别市场
        
        Args:
            stock_code: 原始股票代码
            
        Returns:
            Tuple[str, str]: (标准化后的代码, 市场类型)
        """
        logger = logging.getLogger(__name__)
        
        # 移除空格并转换为大写
        stock_code = stock_code.strip().upper()
        
        # 美股识别
        if re.match(r'^[A-Z]{1,5}$', stock_code) and not stock_code.isdigit():
            logger.info(f"识别为美股: {stock_code}")
            return stock_code, 'us_stock'
        
        # 港股识别 - 数字开头，通常4-5位
        if stock_code.isdigit() and (4 <= len(stock_code) <= 5):
            if stock_code.startswith(('0', '1', '2', '3', '6', '8', '9')):
                logger.info(f"识别为港股: {stock_code}")
                return stock_code, 'hk_stock'
        
        # A股识别和格式化
        if stock_code.isdigit():
            if len(stock_code) < 6:
                stock_code = stock_code.zfill(6)
            elif len(stock_code) == 6:
                pass  # 已经是6位
            else:
                # 超过6位，可能是错误输入
                logger.warning(f"A股代码长度异常: {stock_code}")
                stock_code = stock_code[:6]
            
            # 验证A股代码格式
            if stock_code.startswith(('00', '30')):  # 深圳
                logger.info(f"识别为深圳A股: {stock_code}")
                return stock_code, 'a_stock'
            elif stock_code.startswith('60'):  # 上海
                logger.info(f"识别为上海A股: {stock_code}")
                return stock_code, 'a_stock'
            else:
                logger.warning(f"未识别的A股代码模式: {stock_code}")
                return stock_code, 'a_stock'  # 默认为A股
        
        # 带后缀的情况处理
        if '.' in stock_code:
            code_part, suffix = stock_code.split('.', 1)
            suffix = suffix.upper()
            
            if suffix in ['SZ', 'SS']:  # A股
                return MarketUtils.normalize_stock_code(code_part)[0], 'a_stock'
            elif suffix == 'HK':  # 港股
                return code_part, 'hk_stock'
            else:  # 其他后缀，可能是美股
                return stock_code, 'us_stock'
        
        # 默认情况 - 如果是纯数字且长度合适，按A股处理
        if stock_code.isdigit():
            if len(stock_code) < 5:
                stock_code = stock_code.zfill(6)
            logger.info(f"默认识别为A股: {stock_code}")
            return stock_code, 'a_stock'
        
        # 其他情况默认为美股
        logger.info(f"默认识别为美股: {stock_code}")
        return stock_code, 'us_stock'

    @staticmethod
    def get_market_info(market: str) -> dict:
        """
        获取市场信息
        
        Args:
            market: 市场类型 ('a_stock', 'hk_stock', 'us_stock')
            
        Returns:
            dict: 市场信息
        """
        market_info = {
            'a_stock': {
                'name': '中国A股市场',
                'currency': 'CNY',
                'timezone': 'Asia/Shanghai',
                'trading_hours': '09:30-15:00'
            },
            'hk_stock': {
                'name': '香港股票市场',
                'currency': 'HKD',
                'timezone': 'Asia/Hong_Kong',
                'trading_hours': '09:30-16:00'
            },
            'us_stock': {
                'name': '美国股票市场',
                'currency': 'USD',
                'timezone': 'America/New_York',
                'trading_hours': '09:30-16:00'
            }
        }
        
        return market_info.get(market, market_info['a_stock'])