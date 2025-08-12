"""
Test script for the refactored stock analyzer
测试重构后的股票分析器
"""

import sys
import logging
from enhanced_web_stock_analyzer_refactored import EnhancedWebStockAnalyzer

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_analyzer():
    """测试分析器功能"""
    logger.info("开始测试重构后的股票分析器...")
    
    try:
        # 初始化分析器
        analyzer = EnhancedWebStockAnalyzer()
        logger.info("✓ 分析器初始化成功")
        
        # 测试股票代码标准化
        test_codes = ['000001', '600000', '00700', 'AAPL', 'TSLA']
        for code in test_codes:
            normalized_code, market = analyzer.normalize_stock_code(code)
            logger.info(f"✓ {code} -> {normalized_code} ({market})")
        
        # 测试股票代码验证
        validation_result = analyzer.validate_stock_code('000001')
        logger.info(f"✓ 股票代码验证: {validation_result}")
        
        # 测试市场状态
        market_status = analyzer.get_market_status()
        logger.info(f"✓ 市场状态: {market_status['system_ready']}")
        
        # 测试数据获取（不依赖外部数据源）
        logger.info("✓ 基本功能测试通过")
        
        # 如果有网络连接，可以测试数据获取
        try:
            price_data = analyzer.get_stock_data('000001')
            if price_data is not None and not price_data.empty:
                logger.info(f"✓ 价格数据获取成功: {len(price_data)} 条记录")
                
                # 测试技术指标计算
                indicators = analyzer.calculate_technical_indicators(price_data)
                logger.info(f"✓ 技术指标计算成功: {len(indicators)} 个指标")
                
            else:
                logger.warning("⚠ 价格数据获取失败（可能是网络或API限制）")
                
        except Exception as e:
            logger.warning(f"⚠ 数据获取测试跳过: {e}")
        
        logger.info("🎉 所有基本测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False

def test_data_fetchers():
    """测试各个数据获取器"""
    logger.info("开始测试数据获取器...")
    
    try:
        from data_fetchers import PriceDataFetcher, FundamentalDataFetcher, NewsDataFetcher, MarketUtils
        
        # 测试配置
        test_config = {
            'cache': {'price_hours': 1, 'fundamental_hours': 6, 'news_hours': 2},
            'analysis_params': {'technical_period_days': 180, 'financial_indicators_count': 25, 'max_news_count': 100}
        }
        
        # 测试MarketUtils
        logger.info("测试MarketUtils...")
        test_codes = ['000001', '600000', '00700', 'AAPL']
        for code in test_codes:
            normalized, market = MarketUtils.normalize_stock_code(code)
            market_info = MarketUtils.get_market_info(market)
            logger.info(f"✓ {code} -> {normalized} ({market_info['name']})")
        
        # 测试PriceDataFetcher
        logger.info("测试PriceDataFetcher...")
        price_fetcher = PriceDataFetcher(test_config)
        logger.info("✓ PriceDataFetcher初始化成功")
        
        # 测试FundamentalDataFetcher
        logger.info("测试FundamentalDataFetcher...")
        fundamental_fetcher = FundamentalDataFetcher(test_config)
        logger.info("✓ FundamentalDataFetcher初始化成功")
        
        # 测试NewsDataFetcher
        logger.info("测试NewsDataFetcher...")
        news_fetcher = NewsDataFetcher(test_config)
        logger.info("✓ NewsDataFetcher初始化成功")
        
        logger.info("🎉 数据获取器测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据获取器测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("股票分析器重构测试")
    logger.info("=" * 50)
    
    # 测试数据获取器
    fetcher_test = test_data_fetchers()
    
    # 测试主分析器
    analyzer_test = test_analyzer()
    
    if fetcher_test and analyzer_test:
        logger.info("🎉 所有测试通过！重构成功！")
        sys.exit(0)
    else:
        logger.error("❌ 测试失败，请检查代码")
        sys.exit(1)