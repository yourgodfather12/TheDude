import os
import discord
from discord.ext import commands
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import logging
from tqdm import tqdm

# Load environment variables from a .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Configure SQLAlchemy engine and session
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Define SQLAlchemy models
class UserAttachment(Base):
    __tablename__ = 'user_attachments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    message_id = Column(Integer)
    file_path = Column(String)
    posted_at = Column(DateTime, default=datetime.utcnow)

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

# Function to save attachments
async def save_attachments(message, channel_name, total_downloads_left):
    for attachment in tqdm(message.attachments, desc=f'Downloading attachments ({total_downloads_left} left)', unit='B', unit_scale=True, leave=False):
        directory_path = f"F:/discord/{message.guild.id}/{channel_name}/"
        file_path = os.path.join(directory_path, attachment.filename)
        if not os.path.exists(file_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.info(f"Downloading attachment: {attachment.filename}")
            try:
                await attachment.save(file_path)
                logger.info(f"Attachment saved: {attachment.filename} at {file_path}")
            except Exception as e:
                logger.error(f"Error saving attachment {attachment.filename}: {e}")
        else:
            logger.info(f"Skipping attachment: {attachment.filename} (already exists)")

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    logger.info('Bot is ready.')

    total_downloads_left = 0

    # Loop through all guilds the bot is a member of
    for guild in bot.guilds:
        # Loop through all channels in the guild
        for channel in guild.channels:
            # Check if the channel is a text channel
            if isinstance(channel, discord.TextChannel):
                logger.info(f"Fetching message history for channel: {channel.name}")
                async for message in channel.history(limit=None):  # Fetch all messages in the channel
                    total_downloads_left += len(message.attachments)
                    await save_attachments(message, channel.name, total_downloads_left)
                    total_downloads_left -= len(message.attachments)

# Event handler for command errors
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
        logger.error("An error occurred", exc_info=error)

# Event handler for logging command usage
@bot.event
async def on_command(ctx):
    with open('logs.txt', 'a') as f:
        f.write(f"{datetime.now()} - {ctx.author.id} - {ctx.guild.id} - {ctx.command.name}\n")

# Run the bot with the provided token
bot.run("BOT_TOKEN_HERE")
