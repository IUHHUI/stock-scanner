import akshare as ak
import pandas as pd

def get_cash_flow_data(stock_code):
    """
    使用 akshare 获取指定股票的现金流量表数据 (按报告期)
    :param stock_code: 股票代码，例如 '000001'
    :return: 包含现金流量表数据的 pandas DataFrame
    """
    try:
        # 调用 akshare 函数获取数据
        # 注意：akshare 的部分接口可能需要处理 symbol 格式，例如 'sh600519' 或 'sz000001'
        # 但 stock_cash_flow_sheet_by_report_em 通常直接接受纯数字代码
        df = ak.stock_cash_flow_sheet_by_report_em(symbol=stock_code)
        
        # akshare 返回的数据列名可能包含特殊字符或空格，为了便于处理，可以进行清理
        # 例如，将列名中的空格替换为下划线
        df.columns = [col.strip().replace(' ', '_') for col in df.columns]
        
        return df
    except Exception as e:
        print(f"获取数据时发生错误: {e}")
        return pd.DataFrame() # 返回空的 DataFrame

if __name__ == "__main__":
    # 示例：查询平安银行 (000001) 的现金流量表数据
    stock_code = "sz000001"
    
    print(f"正在获取股票 {stock_code} 的现金流量表数据...")
    cash_flow_df = get_cash_flow_data(stock_code)
    
    if not cash_flow_df.empty:
        print(f"成功获取股票 {stock_code} 的现金流量表数据:")
        print(cash_flow_df.head()) # 打印前几行数据
        print("\n数据列名:")
        print(list(cash_flow_df.columns)) # 打印所有列名
    else:
        print(f"未能获取到股票 {stock_code} 的现金流量表数据。")




