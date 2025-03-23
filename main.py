import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agents import Agent, Runner
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class WeatherBot:
    def __init__(self):
        self.agent = Agent(
            name="WeatherAssistant",
            instructions="""You are a weather assistant in a Telegram chat.
            You have access to real-time weather data through the get_weather tool.
            When users ask about weather, use the tool to get current conditions.
            For other questions, politely explain that you can only help with weather queries.
            
            Format weather responses exactly like this:
            🌤️ Current Weather in *{City}*:
            🌡️ Temperature: *{temp}°C*
            ⛅️ Conditions: *{conditions}*
            💨 Wind Speed: *{speed} km/h*
            
            Always use *asterisks* for bold text in Telegram, not underscores.
            Keep the emojis and formatting exactly as shown above.""",
            model="gpt-4o-mini"
        )
        self.mcp_session = None
        self.exit_stack = None
        self.application = None

    async def connect_to_weather_mcp(self, application: Application) -> None:
        """Connect to the weather MCP server."""
        self.exit_stack = AsyncExitStack()
        server_params = StdioServerParameters(
            command="python",
            args=["weather_mcp.py"],
            env=None
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        self.mcp_session = await self.exit_stack.enter_async_context(ClientSession(stdio, write))
        await self.mcp_session.initialize()
        
        tool_list = await self.mcp_session.list_tools()
        logger.info(f"Connected to weather MCP server. Available tools: {[t.name for t in tool_list.tools]}")

    async def cleanup(self, application: Application) -> None:
        """Cleanup resources."""
        logger.info("Starting cleanup...")
        try:
            if self.mcp_session:
                logger.info("Closing MCP session...")
                await self.mcp_session.aclose()
                self.mcp_session = None
            
            if self.exit_stack:
                logger.info("Closing exit stack...")
                await self.exit_stack.aclose()
                self.exit_stack = None
                
            logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        await update.message.reply_text(
            'Hi! I\'m your AI weather assistant powered by weather MCP capabilities. '
            'I can fetch real-time weather data for most cities in the world.\n\n'
            'Try asking: *what\'s the weather in Ubud?*',
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        await update.message.reply_text(
            'I can help you check real-time weather conditions! Just ask me something like:\n'
            '*what\'s the weather in Ubud?*',
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming messages using OpenAI Agent with MCP capabilities."""
        user_message = update.message.text.lower()
        logger.info(f"Received message: {user_message[:50]}...")
        
        try:
            await update.message.chat.send_action(ChatAction.TYPING)
            
            if "weather" in user_message and self.mcp_session:
                # Extract city name (everything after "in" or "for")
                words = user_message.split()
                city = None
                
                for marker in ["in", "for"]:
                    if marker in words:
                        idx = words.index(marker) + 1
                        if idx < len(words):
                            city = " ".join(words[idx:])
                            break
                
                # If no "in" or "for" found, take everything after "weather"
                if not city and "weather" in words:
                    idx = words.index("weather") + 1
                    if idx < len(words):
                        city = " ".join(words[idx:])
                
                if city:
                    # Clean up the city name
                    city = city.strip(" ,.!?")
                    result = await self.mcp_session.call_tool(
                        "get_weather",
                        {"city": city}
                    )
                    weather_text = result.content[0].text if result.content else "Sorry, couldn't get weather data."
                    
                    # Let the agent format the response nicely
                    agent_result = await Runner.run(
                        self.agent, 
                        f"Format this weather data using Telegram formatting (*bold* and _italic_): {weather_text}"
                    )
                    await update.message.reply_text(
                        agent_result.final_output,
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "Please tell me which city you want the weather for.\n"
                        "For example: *what's the weather in Ubud?*",
                        parse_mode='Markdown'
                    )
            else:
                # Use the agent for all responses
                result = await Runner.run(self.agent, user_message)
                await update.message.reply_text(
                    result.final_output,
                    parse_mode='Markdown'
                )
                        
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            await update.message.reply_text("Sorry, I encountered an error while processing your request.")

    def run(self):
        """Start the bot."""
        logger.info("Initializing weather bot...")
        
        # Create the Application
        self.application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Register startup and shutdown actions
        self.application.post_init = self.connect_to_weather_mcp
        self.application.post_shutdown = self.cleanup

        # Start the Bot
        logger.info("Starting bot...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Entry point for the bot."""
    bot = WeatherBot()
    
    try:
        logger.info("Starting weather bot...")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal (Ctrl+C)")
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {str(e)}", exc_info=True)
    finally:
        logger.info("Bot shutdown complete")

if __name__ == '__main__':
    main() 