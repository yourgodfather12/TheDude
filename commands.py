import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import mysql.connector

# Establish MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="yourusername",
    password="yourpassword",
    database="yourdatabase"
)
cursor = db.cursor()

# Define intents
intents = discord.Intents.default()
intents.messages = True  # Enable the 'messages' intent to track message events

# Prefix for bot commands
PREFIX = './'

# Create a separate commands.Bot instance
bot = commands.Bot(command_prefix=PREFIX, intents=intents)


# Function to check if a message contains an image or video attachment
def contains_image_or_video(message):
    return any(attachment.width is not None or attachment.height is not None or attachment.url.endswith(
        ('jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi')) for attachment in message.attachments)


# Command to display server information
@bot.command(name='serverinfo', help='Displays information about the server.')
async def server_info(ctx):
    guild = ctx.guild
    embed = discord.Embed(title='Server Information', color=discord.Color.blue())
    embed.set_thumbnail(url=guild.icon_url)
    embed.add_field(name='Server Name', value=guild.name, inline=False)
    embed.add_field(name='Server Owner', value=guild.owner, inline=False)
    embed.add_field(name='Server Region', value=guild.region, inline=False)
    embed.add_field(name='Total Members', value=guild.member_count, inline=False)
    embed.add_field(name='Creation Date', value=guild.created_at.strftime('%Y-%m-%d %H:%M:%S'), inline=False)
    await ctx.send(embed=embed)


# Command to change nickname
@bot.command(name='nickname', help='Changes the nickname of a user.')
@commands.has_any_role('Admin', 'Moderator')
async def change_nickname(ctx, member: discord.Member, nickname):
    await member.edit(nick=nickname)
    await ctx.send(f'Nickname of {member.mention} has been changed to {nickname}')


# Command to kick a member
@bot.command(name='kick', help='Kicks a member from the server.')
@commands.has_permissions(kick_members=True)
async def kick_member(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} has been kicked from the server.')


# Command to ban a member
@bot.command(name='ban', help='Bans a member from the server.')
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been banned from the server.')


# Command to clear messages
@bot.command(name='clear', help='Clears a specified number of messages.')
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'{amount} messages cleared.')


# Command to create a text channel
@bot.command(name='createchannel', help='Creates a new text channel.')
@commands.has_permissions(manage_channels=True)
async def create_text_channel(ctx, channel_name):
    guild = ctx.guild
    await guild.create_text_channel(channel_name)
    await ctx.send(f'Text channel {channel_name} created.')


# Command to create a voice channel
@bot.command(name='createvoicechannel', help='Creates a new voice channel.')
@commands.has_permissions(manage_channels=True)
async def create_voice_channel(ctx, channel_name):
    guild = ctx.guild
    await guild.create_voice_channel(channel_name)
    await ctx.send(f'Voice channel {channel_name} created.')


# Command to send a direct message to a user
@bot.command(name='dm', help='Sends a direct message to a user.')
async def send_dm(ctx, member: discord.Member, *, message):
    try:
        await member.send(message)
        await ctx.send(f'Message sent to {member.name}.')
    except discord.Forbidden:
        await ctx.send(f"Failed to send message to {member.name}. They might have DMs disabled.")


# Command to mute a member
@bot.command(name='mute', help='Mutes a member in the server.')
@commands.has_permissions(manage_roles=True)
async def mute_member(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if not muted_role:
        muted_role = await ctx.guild.create_role(name='Muted')

    await member.add_roles(muted_role)
    await ctx.send(f'{member.mention} has been muted.')


# Command to unmute a member
@bot.command(name='unmute', help='Unmutes a member in the server.')
@commands.has_permissions(manage_roles=True)
async def unmute_member(ctx, member: discord.Member):
    muted_role = discord.utils.get(ctx.guild.roles, name='Muted')
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f'{member.mention} has been unmuted.')
    else:
        await ctx.send(f'{member.mention} is not muted.')


# Command to check posts (images or videos) by a user in the past 5 days and store data in MySQL
@bot.command(name='cp',
             help='Checks images or videos posted by a user in the past 5 days and saves them, organized by message content.')
async def check_posts(ctx, member: discord.Member):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)

    # Fetch messages in the past 5 days
    messages = await ctx.channel.history(limit=None, after=start_date, before=end_date).flatten()

    # Filter messages with attachments (images or videos) posted by the member
    user_messages = [message for message in messages if message.author == member and contains_image_or_video(message)]

    # Create a directory to store the files
    directory_name = f"{member.id}_{member.name}"  # Using member ID and name to create a unique directory name
    os.makedirs(directory_name, exist_ok=True)

    # Store data in MySQL database and save attachments
    try:
        for message in user_messages:
            # Get the first couple of words from the message content
            content_words = message.content.split()[:2]
            subdir_name = '_'.join(content_words) if content_words else 'no_content'

            for attachment in message.attachments:
                # Save the attachment to the appropriate directory
                file_path = os.path.join(directory_name, subdir_name, attachment.filename)
                await attachment.save(file_path)

                # Store data in MySQL database
                cursor.execute("INSERT INTO user_posts (user_id, file_path) VALUES (%s, %s)", (member.id, file_path))
                db.commit()

        await ctx.send(
            f'Images or videos posted by {member.mention} in the past 5 days have been saved and data stored successfully.')
    except Exception as e:
        db.rollback()
        await ctx.send(f'Error storing data: {str(e)}')


# Run the bot with the token
bot.run("MTIwOTczMDY4Mjk1NjU1NDM0Mg.GFHpPP.etbdsOFlbD0ahdPcitrWrTyexhUT_DpCuGodkM")
