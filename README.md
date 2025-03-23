# Weather Bot with OpenAI Agents SDK

A Telegram bot that provides real-time weather information using OpenAI's Agents SDK and Model Context Protocol (MCP). The bot can fetch current weather conditions for cities worldwide using natural language queries, powered by GPT-4o-mini model.

## Features

- Real-time weather data using Open-Meteo API
- Natural language processing with OpenAI Agents SDK (GPT-4o-mini)
- Simple MCP server implementation for weather data retrieval
- Telegram-native message formatting
- Easy-to-use interface with simple weather queries

## Technology Stack

- Python 3.11+
- OpenAI Agents SDK
- Model Context Protocol (MCP)
- python-telegram-bot
- Open-Meteo API (no API key required)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/esakrissa/agents-sdk-telegram.git
cd agents-sdk-telegram
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the project root:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the bot:
```bash
python main.py
```

## Usage

Simply send a message to the bot asking about weather in any city:
```
what's the weather in Ubud?
```

The bot will respond with current weather conditions including:
- Temperature
- Weather conditions
- Wind speed

## Architecture

### OpenAI Agents SDK Integration
The bot uses OpenAI's Agents SDK with GPT-4o-mini model to process natural language queries and generate human-like responses. The Agent is configured with specific instructions for handling weather-related queries and maintaining conversation context.

### Model Context Protocol (MCP)
The project implements a simple MCP server (`weather_mcp.py`) that provides the `get_weather` tool. This demonstrates how to:
- Create custom MCP tools
- Handle tool requests and responses
- Integrate external APIs (Open-Meteo) with MCP

## License

MIT © Esa Krissa 