#!/usr/bin/env python3
"""
测试重构后的数据源层
"""

from data_fetchers.data_sources import AkSharePriceDataSource, AkShareFundamentalDataSource, AkShareNewsDataSource

def test_data_sources():
    """测试数据源层"""
    
    print("=== 测试数据源层重构 ===")
    
    # 测试价格数据源
    print("\n--- 价格数据源测试 ---")
    price_source = AkSharePriceDataSource()
    print(f"价格数据源可用: {price_source.is_available()}")
    
    # 测试港股价格数据
    hk_data = price_source.get_stock_data('00700', 'hk_stock', '1y')
    if hk_data is not None and not hk_data.empty:
        print(f"✅ 港股价格数据: {len(hk_data)} 条记录")
    else:
        print("⚠ 港股价格数据获取失败")
    
    # 测试美股价格数据  
    us_data = price_source.get_stock_data('AAPL', 'us_stock', '1y')
    if us_data is not None and not us_data.empty:
        print(f"✅ 美股价格数据: {len(us_data)} 条记录")
    else:
        print("⚠ 美股价格数据获取失败")
    
    # 测试基本面数据源
    print("\n--- 基本面数据源测试 ---")
    fundamental_source = AkShareFundamentalDataSource()
    print(f"基本面数据源可用: {fundamental_source.is_available()}")
    
    hk_info = fundamental_source.get_stock_info('00700', 'hk_stock')
    print(f"✅ 港股基本信息: {len(hk_info)} 个字段")
    
    us_info = fundamental_source.get_stock_info('AAPL', 'us_stock')
    print(f"✅ 美股基本信息: {len(us_info)} 个字段")
    
    # 测试新闻数据源
    print("\n--- 新闻数据源测试 ---")
    news_source = AkShareNewsDataSource()
    print(f"新闻数据源可用: {news_source.is_available()}")
    
    hk_news = news_source.get_stock_news('00700', 'hk_stock', 15)
    print(f"✅ 港股新闻数据: {len(hk_news)} 条新闻")
    
    us_news = news_source.get_stock_news('AAPL', 'us_stock', 15)
    print(f"✅ 美股新闻数据: {len(us_news)} 条新闻")
    
    print("\n🎉 数据源层测试完成！")

if __name__ == "__main__":
    test_data_sources()