import os
import logging
import discord
import json  # Add this line
from discord.ext import commands
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import aiofiles
import aiohttp
import asyncio
import re
from collections import defaultdict
from sqlalchemy.exc import OperationalError
import time
from sqlalchemy.orm import scoped_session
from sqlalchemy.pool import QueuePool

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the path to the SQLite database file
DATABASE_FILE = os.path.join(os.getcwd(), 'bot_data.db')

# Construct the SQLite database URL
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Configure SQLAlchemy engine and session with a connection pool
engine = create_engine(DATABASE_URL, poolclass=QueuePool)
Base = declarative_base()
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Define the path to the local folder you want to upload
COUNTY_FOLDER = r'F:\discord'


# Load county configuration from JSON file
with open('county_config.json', 'r') as config_file:
    COUNTY_CONFIG = json.load(config_file)

# Create a separate commands.Bot instance with all permissions
bot = commands.Bot(command_prefix='./', intents=discord.Intents.all())

# Dictionary to store attachment counts per user per day
attachment_counts = defaultdict(lambda: defaultdict(int))

# Function to log attachment
async def log_attachment(user_id, timestamp):
    # Get the day of the week (0 = Monday, 6 = Sunday)
    day_of_week = timestamp.weekday()
    # Increment attachment count for the user and day
    attachment_counts[user_id][day_of_week] += 1

# Function to calculate attachment counts for the week
async def calculate_weekly_counts():
    # Get the current day of the week
    current_day = datetime.now().weekday()

    # Calculate the start of the week (assuming Monday is the first day of the week)
    start_of_week = datetime.now() - timedelta(days=current_day)

    # Initialize a dictionary to store weekly attachment counts per user
    weekly_attachment_counts = defaultdict(int)

    # Iterate over attachment counts for each user
    for user_id, counts_per_day in attachment_counts.items():
        weekly_count = sum(counts_per_day[day] for day in range(7))
        weekly_attachment_counts[user_id] = weekly_count

    return weekly_attachment_counts

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

@bot.command(name='v', aliases=['verify'])
async def verify_member(ctx, member: discord.Member):
    # Check if the command invoker has permission to manage roles or has the "Mod" role
    if ctx.author.guild_permissions.manage_roles or discord.utils.get(ctx.author.roles, name='Mod'):
        # Get the "Must Verify" role
        must_verify_role = discord.utils.get(ctx.guild.roles, name='Must Verify')
        # Get the "Member" role
        member_role = discord.utils.get(ctx.guild.roles, name='Member')

        # Check if both roles exist
        if must_verify_role and member_role:
            # Check if the member has the "Must Verify" role
            if must_verify_role in member.roles:
                try:
                    # Remove the "Must Verify" role and add the "Member" role
                    await member.remove_roles(must_verify_role)
                    await member.add_roles(member_role)
                    await ctx.send(f"{member.mention} has been verified.")
                except discord.Forbidden:
                    await ctx.send("I don't have permission to manage roles.")
            else:
                await ctx.send(f"{member.mention} doesn't have the Must Verify role.")
        else:
            await ctx.send("The Must Verify or Member role doesn't exist.")
    else:
        await ctx.send("You don't have permission to use this command.")


# Function to set up the server
async def setup_server(guild):
    # Create categories
    category_rules_verify = await guild.create_category('Rules & Verify')
    category_misc = await guild.create_category('Misc')
    category_counties = await guild.create_category('Counties')
    category_admin_mods = await guild.create_category('Admin & Mods')

    # Create channels in "Rules & Verify" category
    rules_channel = await category_rules_verify.create_text_channel('rules')
    verify_channel = await category_rules_verify.create_text_channel('verify')

    # Create channels in "Misc" category
    chat_channel = await category_misc.create_text_channel('chat')
    requests_channel = await category_misc.create_text_channel('requests')
    onlyfans_directory_channel = await category_misc.create_text_channel('onlyfans-directory')

    # List of counties in Kentucky
    kentucky_counties = [
        'Adair', 'Allen', 'Anderson', 'Ballard', 'Barren', 'Bath', 'Bell', 'Boone', 'Bourbon', 'Boyd',
        'Boyle', 'Bracken', 'Breathitt', 'Breckinridge', 'Bullitt', 'Butler', 'Caldwell', 'Calloway',
        'Campbell', 'Carlisle', 'Carroll', 'Carter', 'Casey', 'Christian', 'Clark', 'Clay', 'Clinton',
        'Crittenden', 'Cumberland', 'Daviess', 'Edmonson', 'Elliott', 'Estill', 'Fayette', 'Fleming',
        'Floyd', 'Franklin', 'Fulton', 'Gallatin', 'Garrard', 'Grant', 'Graves', 'Grayson', 'Green',
        'Greenup', 'Hancock', 'Hardin', 'Harlan', 'Harrison', 'Hart', 'Henderson', 'Henry', 'Hickman',
        'Hopkins', 'Jackson', 'Jefferson', 'Jessamine', 'Johnson', 'Kenton', 'Knott', 'Knox', 'Larue',
        'Laurel', 'Lawrence', 'Lee', 'Leslie', 'Letcher', 'Lewis', 'Lincoln', 'Livingston', 'Logan',
        'Lyon', 'McCracken', 'McCreary', 'McLean', 'Madison', 'Magoffin', 'Marion', 'Marshall', 'Martin',
        'Mason', 'Meade', 'Menifee', 'Mercer', 'Metcalfe', 'Monroe', 'Montgomery', 'Morgan', 'Muhlenberg',
        'Nelson', 'Nicholas', 'Ohio', 'Oldham', 'Owen', 'Owsley', 'Pendleton', 'Perry', 'Pike', 'Powell',
        'Pulaski', 'Robertson', 'Rockcastle', 'Rowan', 'Russell', 'Scott', 'Shelby', 'Simpson', 'Spencer',
        'Taylor', 'Todd', 'Trigg', 'Trimble', 'Union', 'Warren', 'Washington', 'Wayne', 'Webster', 'Whitley',
        'Wolfe', 'Woodford'
    ]

    # Create channels for each county in "Counties" category
    for county in kentucky_counties:
        try:
            await category_counties.create_text_channel(county)
        except discord.HTTPException:
            # If the current category is full, move to the next category
            logger.warning(f"Category '{category_counties.name}' is full. Moving to the next category.")
            category_counties = await guild.create_category('Counties (continued)')
            await category_counties.create_text_channel(county)

    # Create channels in "Admin & Mods" category
    admin_chat_channel = await category_admin_mods.create_text_channel('admin-chat')
    mod_chat_channel = await category_admin_mods.create_text_channel('mod-chat')

    # Create roles
    must_verify_role = await guild.create_role(name='Must Verify')
    member_role = await guild.create_role(name='Member')
    mod_role = await guild.create_role(name='Mod')
    admin_role = await guild.create_role(name='Admin')

    # Set permissions for each channel
    # Rules channel permissions
    await rules_channel.set_permissions(must_verify_role, read_messages=True, send_messages=False)
    await rules_channel.set_permissions(member_role, read_messages=True, send_messages=False)
    await rules_channel.set_permissions(mod_role, read_messages=True, send_messages=False)
    await rules_channel.set_permissions(admin_role, read_messages=True, send_messages=False)

    # Verify channel permissions
    await verify_channel.set_permissions(must_verify_role, read_messages=True, send_messages=True, read_message_history=False)
    await verify_channel.set_permissions(member_role, read_messages=True, send_messages=True)
    await verify_channel.set_permissions(mod_role, read_messages=True, send_messages=True)
    await verify_channel.set_permissions(admin_role, read_messages=True, send_messages=True)

    # Other channels permissions
    channels = [chat_channel, requests_channel, onlyfans_directory_channel, admin_chat_channel, mod_chat_channel]
    for channel in channels:
        await channel.set_permissions(must_verify_role, read_messages=False)
        await channel.set_permissions(member_role, read_messages=True, send_messages=True)
        await channel.set_permissions(mod_role, read_messages=True, send_messages=True)
        await channel.set_permissions(admin_role, read_messages=True, send_messages=True)


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

# Event handler for when a member joins the server
@bot.event
async def on_member_join(member):
    # Get the "Must Verify" role
    must_verify_role = discord.utils.get(member.guild.roles, name='Must Verify')
    if must_verify_role:
        # Assign the "Must Verify" role to the new member
        await member.add_roles(must_verify_role)

import sqlalchemy.exc

# Maximum number of retries
MAX_RETRIES = 5

# Function to create session with connection pooling
def get_session():
    return Session()

# Command: Upload
@bot.command()
async def upload(ctx):
    # Iterate through county configurations
    for county, channel_name in COUNTY_CONFIG.items():
        # Find the channel in the guild
        channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
        if not channel:
            logger.error(f'Failed to find channel "{channel_name}" for county "{county}" in server "{ctx.guild.name}"')
            continue

        # Traverse the directory structure and upload files
        county_folder_path = os.path.join(COUNTY_FOLDER, county)
        if not os.path.exists(county_folder_path):
            os.makedirs(county_folder_path)
        for root, dirs, files in os.walk(county_folder_path):
            for file in files:
                if file.endswith('.jpg') or file.endswith('.jpeg') or file.endswith('.png'):
                    file_path = os.path.join(root, file)
                    try:
                        await channel.send(file=discord.File(file_path))
                        os.remove(file_path)
                        logger.info(f'Uploaded file: {file_path}')
                    except discord.HTTPException as e:
                        logger.error(f'Failed to upload file: {file_path}')

@bot.command(name='cp')
async def check_posts_with_attachments(ctx):
    # Check if the invoker has the "Member" role
    member_role = discord.utils.get(ctx.guild.roles, name='Member')
    if member_role in ctx.author.roles:
        # Get the current date and time
        current_time = datetime.now(timezone.utc)
        # Calculate the start date for the past 7 days
        start_date = current_time - timedelta(days=7)

        # Retry the database query with exponential backoff
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                # Query the database to count the number of posts with attachments made by the user in the past 7 days
                session = get_session()
                attachment_count = session.query(UserAttachment).filter(UserAttachment.user_id == bool(ctx.author.id),
                                                                        UserAttachment.posted_at >= start_date).count()
                await ctx.send(f"You have made {attachment_count} post(s) with attachments in the past 7 days.")
                session.close()  # Close the session after use
                break  # Exit the loop if the query is successful
            except sqlalchemy.exc.OperationalError as e:
                if 'database is locked' in str(e):
                    await ctx.send("Failed to fetch post count due to database lock. Please try again later.")
                else:
                    raise  # Re-raise any other exceptions
                break  # Exit the loop if the database is locked
            except Exception as e:
                logger.error(f"Error querying database: {e}")
                if retry_count < MAX_RETRIES - 1:
                    delay = 2 ** retry_count  # Exponential backoff: 1, 2, 4, 8, 16 seconds...
                    logger.info(f"Retrying database query in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    await ctx.send("Failed to fetch post count due to unexpected error. Please try again later.")
                retry_count += 1
    else:
        await ctx.send("You need to have the Member role to use this command.")

# Command to build/setup the server
@bot.command(name='build', aliases=['setup'])
async def build_server(ctx):
    guild = ctx.guild
    await setup_server(guild)
    await ctx.send('Server setup complete.')

# Run the bot with the provided token
bot.run('YOUR_TOKEN_HERE')
