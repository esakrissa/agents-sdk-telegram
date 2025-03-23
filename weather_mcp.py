import httpx
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
GEOCODING_API = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_API = "https://api.open-meteo.com/v1/forecast"

@mcp.tool()
async def get_weather(city: str) -> str:
    """Get current weather for a city.
    
    Args:
        city: Name of the city (e.g. 'London', 'New York', 'Tokyo')
    """
    logger.info(f"Getting weather for city: {city}")
    
    # First get coordinates for the city
    async with httpx.AsyncClient() as client:
        # Get coordinates
        params = {"name": city, "count": 1}
        logger.info(f"Fetching coordinates from: {GEOCODING_API}")
        response = await client.get(GEOCODING_API, params=params)
        data = response.json()
        logger.info(f"Geocoding response: {data}")
        
        if not data.get("results"):
            return f"Could not find location: {city}"
            
        location = data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        logger.info(f"Found coordinates: {lat}, {lon}")
        
        # Get weather data
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "weather_code", "wind_speed_10m"],
            "timezone": "auto"
        }
        
        logger.info(f"Fetching weather from: {WEATHER_API}")
        response = await client.get(WEATHER_API, params=params)
        weather = response.json()
        logger.info(f"Weather response: {weather}")
        
        if "error" in weather:
            return f"Error getting weather: {weather['error']}"
            
        current = weather["current"]
        
        # Map weather codes to descriptions
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow",
            73: "Moderate snow",
            75: "Heavy snow",
            95: "Thunderstorm"
        }
        
        weather_desc = weather_codes.get(current["weather_code"], "Unknown")
        
        return f"""Weather in {location['name']}:
🌡️ Temperature: {current['temperature_2m']}°C
🌤️ Conditions: {weather_desc}
💨 Wind Speed: {current['wind_speed_10m']} km/h"""

if __name__ == "__main__":
    try:
        logger.info("Starting weather MCP server...")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("Received shutdown signal for MCP server")
    except Exception as e:
        logger.error(f"MCP server error: {str(e)}")
    finally:
        logger.info("MCP server shutdown complete") 