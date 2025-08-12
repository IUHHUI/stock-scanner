# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This is an AI-Enhanced Stock Analysis System (v3.1) that provides comprehensive analysis of A-shares (Chinese), Hong Kong stocks, and US stocks. It combines technical analysis, fundamental analysis, and sentiment analysis using AI models with streaming output capabilities.

## Development Commands

### Start the Application
```bash
python enhanced_flask_server.py
```
The server runs on http://localhost:5000 by default.

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up -d --build

# Access at http://localhost:8102
```

## Architecture Overview

### Core Components

1. **enhanced_flask_server.py** - Flask web server with SSE streaming
   - Main API routes at enhanced_flask_server.py:1950+ (various @app.route decorators)
   - SSEManager class at enhanced_flask_server.py:66 for real-time streaming
   - Authentication system with require_auth decorator at enhanced_flask_server.py:199
   - Multi-threaded analysis task management

2. **enhanced_web_stock_analyzer.py** - Core analysis engine
   - EnhancedWebStockAnalyzer class at enhanced_web_stock_analyzer.py:32
   - Supports A股/港股/美股 markets via akshare data source
   - AI integration with OpenAI, Anthropic Claude, and ZhipuAI models
   - Streaming analysis with callback functions

3. **config.json** - Central configuration file
   - API keys for AI models (OpenAI, Anthropic, ZhipuAI)
   - Analysis weights and parameters
   - Market configurations for different exchanges
   - Caching and streaming settings

### Key API Endpoints

- `GET /` - Main web interface
- `POST /api/analyze_stream` - Streaming stock analysis
- `POST /api/batch_analyze_stream` - Batch analysis with streaming
- `GET /api/sse` - Server-Sent Events endpoint for real-time updates
- `GET /api/status` - System health check
- `POST /api/validate_stock` - Stock code validation

### Data Flow

1. User submits stock code via web interface
2. Flask server validates and queues analysis task
3. EnhancedWebStockAnalyzer fetches data from multiple sources:
   - Price data via akshare
   - Financial indicators
   - News sentiment data
4. AI model processes data with streaming output
5. Results streamed back to client via SSE

### Configuration Management

The system uses a comprehensive config.json with these sections:
- `api_keys` - AI model API credentials
- `ai` - Model preferences and parameters
- `analysis_weights` - Technical/fundamental/sentiment analysis weights
- `markets` - A股/港股/美股 market configurations
- `streaming` - Real-time output settings
- `cache` - Data caching durations

### Supported Markets

- **A股 (Chinese A-shares)**: Shanghai/Shenzhen exchanges
- **港股 (Hong Kong)**: HK Exchange
- **美股 (US stocks)**: NASDAQ/NYSE

### AI Integration

The system supports multiple AI providers:
- OpenAI (GPT models) - configured to use DeepSeek via api_base_urls
- Anthropic (Claude models)
- ZhipuAI (ChatGLM models)

Currently configured to prefer OpenAI with deepseek-reasoner model via DeepSeek API.

### Authentication

Optional web authentication via password protection:
- Configured in config.json under `web_auth`
- Session-based authentication with configurable timeout
- Can be disabled for development

## Development Notes

- The application uses Flask with CORS enabled for API access
- SSE (Server-Sent Events) for real-time streaming of analysis results
- Multi-threaded task processing for concurrent analysis
- Comprehensive error handling and logging
- Docker support with health checks and non-root user security