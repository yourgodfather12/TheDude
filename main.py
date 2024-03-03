import discord
from discord.ext import commands

# Create a bot instance
bot = commands.Bot(command_prefix='.')

# Bot token
TOKEN = 'MTIwOTczMDY4Mjk1NjU1NDM0Mg.GFHpPP.etbdsOFlbD0ahdPcitrWrTyexhUT_DpCuGodkM'

# Event: Bot is ready
@bot.event
async def on_ready():
    print('Bot is ready.')

# Define your commands here

# Run the bot
bot.run(TOKEN)
