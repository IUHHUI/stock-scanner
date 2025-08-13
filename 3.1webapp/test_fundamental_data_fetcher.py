#!/usr/bin/env python3
"""
验证修复后的港股美股基础数据获取
"""

from data_fetchers import FundamentalDataFetcher


def test_fundamental_data():
    """测试基础数据获取"""
    config = {
        "cache": {"fundamental_hours": 6},
        "analysis_params": {"financial_indicators_count": 25},
    }

    fetcher = FundamentalDataFetcher(config)

    test_stocks = [("000001", "A股"), ("00700", "港股"), ("AAPL", "美股")]

    for stock_code, market_name in test_stocks:
        print(f"\n=== 测试 {market_name} {stock_code} ===")
        data = fetcher.get_comprehensive_fundamental_data(stock_code)

        if data:
            print(f"✅ 成功获取数据，包含 {len(data)} 个字段:")
            for key, value in data.items():
                print(f"  - {key}: {value}")
        else:
            print(f"❌ 未获取到数据")


if __name__ == "__main__":
    test_fundamental_data()
