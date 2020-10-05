# Dave the Robot

# Imports
import os
from dotenv import load_dotenv
from gateway import Gateway

# Load environment variables
load_dotenv(override=True)
bot_token = os.getenv("BOT_TOKEN")
server_id = os.getenv("SERVER_ID")
channel_id = os.getenv("CHANNEL_ID")

base_url = "https://discord.com/api/v6"

if __name__ == "__main__":
    Gateway(
        base_url=base_url,
        bot_token=bot_token,
        server_id=server_id,
        channel_id=channel_id,
    ).start()
