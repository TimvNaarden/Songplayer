import discord
import os
import asyncio
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
token = os.getenv('TOKEN')
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="/", intents=intents)


async def main():
    await bot.login(token)
    await bot.connect()

    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.logout()


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    # Load the music_cog extension
    try:
        await bot.load_extension('MusicCog')
    except Exception as e:
        print(f'Failed to load extension MusicCog: {e}')

if __name__ == '__main__':
    asyncio.run(main())
   