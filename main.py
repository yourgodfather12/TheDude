import os
import logging
import discord
from discord.ext import commands
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv
import aiofiles
import aiohttp
import asyncio
import re

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
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

# Prefix for bot commands
PREFIX = '!'

# Create a separate commands.Bot instance with all permissions
bot = commands.Bot(command_prefix=PREFIX, intents=discord.Intents.all())

# Function to download attachment asynchronously
async def download_attachment(session, attachment, file_path):
    try:
        async with session.get(attachment.url) as resp:
            if resp.status == 200:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await resp.read())
                logger.info(f"Attachment saved: {file_path}")
            else:
                logger.error(f"Failed to download attachment: {attachment.url}")
    except aiohttp.ClientError as e:
        logger.error(f"Error downloading attachment: {e}")

# Function to save attachments with optimized file handling
async def save_attachments_with_progress(message, channel_name):
    attachments = message.attachments
    total_attachments = len(attachments)
    data_dir = 'data'  # Directory named 'data' within the tool

    # Ensure the 'data' directory exists
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Create subdirectory for the channel if it doesn't exist
    channel_dir = os.path.join(data_dir, channel_name)
    if not os.path.exists(channel_dir):
        os.makedirs(channel_dir)

    # Get first two words of each post with an attachment
    post_content = message.content.split(maxsplit=2)[:2]
    post_dir_name = ' '.join(re.findall(r'\w+', ' '.join(post_content))).lower()

    # Create subdirectory for the post if it doesn't exist
    post_dir = os.path.join(channel_dir, post_dir_name)
    if not os.path.exists(post_dir):
        os.makedirs(post_dir)

    async with aiohttp.ClientSession() as session:
        tasks = []
        for index, attachment in enumerate(attachments, start=1):
            filename = attachment.filename
            file_name_without_extension, extension = os.path.splitext(filename)
            file_path = os.path.join(post_dir, f"{file_name_without_extension}_{index}{extension}")

            # Check if the file already exists
            if not os.path.exists(file_path):
                # Schedule the download task
                task = asyncio.create_task(download_attachment(session, attachment, file_path))
                tasks.append(task)
            else:
                logger.info(f"Skipping already saved attachment: {file_path}")

        # Wait for all download tasks to complete
        await asyncio.gather(*tasks)

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    logger.info('Bot is ready and running.')
    # Print feedback in terminal
    print('Bot is ready and running.')

    # Example: Fetch message history for all channels in all guilds and save attachments
    for guild in bot.guilds:
        for channel in guild.text_channels:
            logger.info(f"Fetching message history for channel: {channel.name}")
            try:
                async for message in channel.history(limit=None):
                    if message.attachments:
                        # Call the function to save attachments with progress
                        await save_attachments_with_progress(message, channel.name)
            except discord.HTTPException as e:
                logger.error(f"Error fetching message history: {e}")

# Run the bot with the provided token
bot.run('your_bot_token')
