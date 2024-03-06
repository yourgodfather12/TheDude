import os
import discord
from discord.ext import commands
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)

# Configure SQLAlchemy engine and session
DATABASE_URL = "sqlite:///bot_data.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Define SQLAlchemy Base
Base = declarative_base()

# Define UserAttachment table
class UserAttachment(Base):
    __tablename__ = 'user_attachments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    message_id = Column(Integer)
    file_path = Column(String)
    posted_at = Column(DateTime, default=datetime.utcnow)

# Define ServerChannel table
class ServerChannel(Base):
    __tablename__ = 'server_channels'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer)
    channel_id = Column(Integer)
    name = Column(String)
    type = Column(String)
    position = Column(Integer)

# Define intents
intents = discord.Intents.all()

# Prefix for bot commands
PREFIX = './'

# Create a separate commands.Bot instance with all permissions
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Load cogs
@bot.event
async def on_ready():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            bot.load_extension(f'cogs.{filename[:-3]}')
    print('Bot is ready.')

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to do that.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required argument.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument provided.")
    else:
        await ctx.send(f"An error occurred: {error}")

# Command logging
@bot.event
async def on_command(ctx):
    with open('logs.txt', 'a') as f:
        f.write(f"{datetime.now()} - {ctx.author.id} - {ctx.guild.id} - {ctx.command.name}\n")

# Run the bot with the token
bot.run("BOT_TOKEN_HERE")
