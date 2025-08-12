# Python Dependencies Documentation

This document provides detailed information about the Python packages used in the AI Enhanced Stock Analysis System v3.1.

## Core Dependencies

### Web Framework
- **Flask==3.1.1** - 轻量级Python Web框架，提供HTTP服务和路由功能
- **flask-cors==6.0.1** - Flask跨域资源共享(CORS)扩展，允许前端跨域请求

### Data Processing
- **pandas==2.3.1** - 强大的数据分析和操作库，用于处理股票数据表格
- **numpy==2.2.6** - 科学计算基础库，支持大型多维数组和矩阵运算

### Stock Data Source
- **akshare==1.17.32** - 开源财经数据接口库，提供A股、港股、美股等多市场数据

### HTTP & Network
- **requests==2.32.4** - HTTP请求库，用于调用外部API和获取网络数据
- **aiohttp==3.12.15** - 异步HTTP客户端/服务器框架
- **urllib3==2.5.0** - HTTP库的底层依赖，处理连接池和请求重试

### Web Scraping & Data Parsing
- **beautifulsoup4==4.13.4** - HTML和XML解析库，用于网页数据提取
- **lxml==6.0.0** - XML和HTML处理库，支持XPath和XSLT
- **html5lib==1.1** - HTML5解析器，符合WHATWG HTML5标准

### Excel & Data Export
- **openpyxl==3.1.5** - 读写Excel 2010 xlsx/xlsm/xltx/xltm文件
- **xlrd==2.0.2** - 读取Excel文件(.xls和.xlsx格式)
- **et_xmlfile==2.0.0** - openpyxl的XML文件处理依赖

### Date & Time Processing
- **python-dateutil==2.9.0.post0** - 日期时间解析和操作扩展
- **pytz==2025.2** - 时区信息库，处理不同市场的交易时间
- **tzdata==2025.2** - 时区数据库

### Utility Libraries
- **tqdm==4.67.1** - 进度条显示库，用于长时间数据处理任务
- **tabulate==0.9.0** - 表格格式化输出库
- **jsonpath==0.82.2** - JSON数据路径查询工具
- **six==1.17.0** - Python 2/3兼容性库

### Async & Concurrency
- **nest-asyncio==1.6.0** - 嵌套异步事件循环支持
- **async-timeout==5.0.1** - 异步操作超时控制
- **aiosignal==1.4.0** - 异步信号处理库

### JavaScript Engine (for Data Processing)
- **py-mini-racer==0.6.0** - V8 JavaScript引擎Python绑定，处理JS加密的数据接口

### Web Framework Internal Dependencies
- **Werkzeug==3.1.3** - Flask底层WSGI工具库
- **Jinja2==3.1.6** - Flask模板引擎
- **MarkupSafe==3.0.2** - Jinja2的HTML转义依赖
- **click==8.2.1** - Flask命令行接口
- **itsdangerous==2.2.0** - Flask会话和cookie签名
- **blinker==1.9.0** - Flask信号系统

### Network & Security
- **certifi==2025.8.3** - Mozilla CA证书包，用于HTTPS请求验证
- **charset-normalizer==3.4.3** - 字符编码检测和规范化
- **idna==3.10** - 国际化域名编码处理

### HTTP Client Dependencies
- **multidict==6.6.4** - 多值字典实现，aiohttp依赖
- **yarl==1.20.1** - URL解析和操作库
- **frozenlist==1.7.0** - 不可变列表实现
- **propcache==0.3.2** - 属性缓存装饰器
- **aiohappyeyeballs==2.6.1** - 异步IPv4/IPv6双栈连接优化
- **attrs==25.3.0** - Python类属性定义库
- **aiosignal==1.4.0** - 异步信号处理
- **soupsieve==2.7** - CSS选择器库，BeautifulSoup依赖

### Data Processing Utilities
- **decorator==5.2.1** - 装饰器工具库
- **typing_extensions==4.14.1** - 类型提示扩展
- **webencodings==0.5.1** - Web字符编码处理

### Performance Optimization
- **akracer==0.0.13** - akshare性能优化组件

## AI Model Dependencies (需要单独安装)

根据系统配置，需要安装以下至少一个AI模型SDK：

- **openai>=1.0.0** - OpenAI GPT模型API客户端
- **anthropic>=0.7.0** - Anthropic Claude模型API客户端  
- **zhipuai>=2.0.0** - 智谱AI ChatGLM模型API客户端

## Installation Notes

1. **基础安装**: `pip install -r requirements.txt`
2. **开发环境**: 建议使用虚拟环境 `python -m venv venv`
3. **系统兼容性**: 支持 Python 3.8+，推荐 Python 3.11+
4. **平台支持**: Windows/Linux/macOS

## Version Compatibility

- 所有版本均经过测试，确保在多平台环境下稳定运行
- pandas和numpy版本选择平衡了性能和兼容性
- akshare使用最新版本以获得最全面的市场数据支持
- Flask生态系统组件版本保持同步更新