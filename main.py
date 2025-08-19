import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from commands import setup_commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")

setup_commands(bot)

bot.run(TOKEN)