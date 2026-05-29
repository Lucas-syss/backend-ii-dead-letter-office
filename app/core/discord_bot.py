import os
import discord
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_ERROR_CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot ligado como {client.user}")

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("✅ Bot ligado e pronto para receber erros do backend.")
    else:
        print("Canal não encontrado. Verifica o DISCORD_ERROR_CHANNEL_ID.")


client.run(TOKEN)
