import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configure SQLAlchemy engine and session
DATABASE_URL = "mysql://yourusername:yourpassword@localhost/yourdatabase"
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


# Define ModerationLog table
class ModerationLog(Base):
    __tablename__ = 'moderation_log'

    id = Column(Integer, primary_key=True)
    moderator_id = Column(Integer)
    target_id = Column(Integer)
    action_type = Column(String)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Define intents
intents = discord.Intents.default()
intents.messages = True

# Prefix for bot commands
PREFIX = './'

# Create a separate commands.Bot instance
bot = commands.Bot(command_prefix=PREFIX, intents=intents)


# Function to check if a message contains an image or video attachment
def contains_image_or_video(message):
    return any(attachment.width is not None or attachment.height is not None or attachment.url.endswith(
        ('jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi')) for attachment in message.attachments)


# Event: Bot is ready
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="with code"))


# Event: Error handling
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


# Event: Welcome Message
@bot.event
async def on_member_join(member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f'Welcome {member.mention} to the server!')
    role = discord.utils.get(member.guild.roles, name='Must Verify')
    if role:
        await member.add_roles(role)


# Event: Leave Message
@bot.event
async def on_member_remove(member):
    channel = member.guild.system_channel
    if channel:
        await channel.send(f'{member.display_name} has left the server.')


# Command: Reverse Image Search
def reverse_image_search(attachment):
    pass


@bot.command(name='reverse', help='Performs a reverse image search on an attached image or video.')
async def reverse_image(ctx):
    if ctx.message.attachments:
        for attachment in ctx.message.attachments:
            if attachment.width is not None or attachment.height is not None or attachment.url.endswith(
                    ('jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi')):
                # Perform reverse image search
                reverse_url = reverse_image_search(attachment)
                if reverse_url:
                    await ctx.send(f'Reverse image search: {reverse_url}')
                else:
                    await ctx.send('Reverse image search failed.')
                break
    else:
        await ctx.send('No image or video attachment found.')


# Command: Server Information
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


# Command: Change Nickname
@bot.command(name='nickname', help='Changes the nickname of a user.')
@commands.has_any_role('Admin', 'Moderator')
async def change_nickname(ctx, member: discord.Member, nickname):
    await member.edit(nick=nickname)
    await ctx.send(f'Nickname of {member.mention} has been changed to {nickname}')


# Command: Kick Member
@bot.command(name='kick', help='Kicks a member from the server.')
@commands.has_permissions(kick_members=True)
async def kick_member(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} has been kicked from the server.')


# Command: Ban Member
@bot.command(name='ban', help='Bans a member from the server.')
@commands.has_permissions(ban_members=True)
async def ban_member(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been banned from the server.')


# Command: Clear Messages
@bot.command(name='clear', help='Clears a specified number of messages.')
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'{amount} messages cleared.')


# Command: Create Text Channel
@bot.command(name='createchannel', help='Creates a new text channel.')
@commands.has_permissions(manage_channels=True)
async def create_text_channel(ctx, channel_name):
    guild = ctx.guild
    await guild.create_text_channel(channel_name)
    await ctx.send(f'Text channel {channel_name} created.')


# Command: Create Voice Channel
@bot.command(name='createvoicechannel', help='Creates a new voice channel.')
@commands.has_permissions(manage_channels=True)
async def create_voice_channel(ctx, channel_name):
    guild = ctx.guild
    await guild.create_voice_channel(channel_name)
    await ctx.send(f'Voice channel {channel_name} created.')


# Command: Send Direct Message
@bot.command(name='dm', help='Sends a direct message to a user.')
async def send_dm(ctx, member: discord.Member, *, message):
    try:
        await member.send(message)
        await ctx.send(f'Message sent to {member.name}.')
    except discord.Forbidden:
        await ctx.send(f"Failed to send message to {member.name}. They might have DMs disabled.")


# Command: Mute Member
@bot.command(name='mute', help='Mutes a member in the server.')
@commands.has_permissions(manage_roles=True)
async def mute_member(ctx, member: discord.Member):
    muted_role = await get_or_create_muted_role(ctx.guild)
    await member.add_roles(muted_role)
    await ctx.send(f'{member.mention} has been muted.')
    log_moderation_action(ctx.author.id, member.id, 'mute')


# Command: Unmute Member
@bot.command(name='unmute', help='Unmutes a member in the server.')
@commands.has_permissions(manage_roles=True)
async def unmute_member(ctx, member: discord.Member):
    muted_role = await get_or_create_muted_role(ctx.guild)
    if muted_role in member.roles:
        await member.remove_roles(muted_role)
        await ctx.send(f'{member.mention} has been unmuted.')
        log_moderation_action(ctx.author.id, member.id, 'unmute')
    else:
        await ctx.send(f'{member.mention} is not muted.')


# Command: Check Posts
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

    # Store data in database and save attachments
    try:
        session = Session()
        for message in user_messages:
            # Get the first couple of words from the message content
            content_words = message.content.split()[:2]
            subdir_name = '_'.join(content_words) if content_words else 'no_content'

            for attachment in message.attachments:
                # Save the attachment to the appropriate directory
                file_path = os.path.join(directory_name, subdir_name, attachment.filename)
                await attachment.save(file_path)

                # Insert the file path into the database
                attachment_entry = UserAttachment(user_id=member.id, message_id=message.id, file_path=file_path)
                session.add(attachment_entry)

        session.commit()
        session.close()
        await ctx.send(
            f'{len(user_messages)} images or videos posted by {member.mention} in the past 5 days have been saved and data stored successfully.')
    except Exception as e:
        await ctx.send(f'Error storing data: {str(e)}')


# Command: Help
@bot.command(name='help', help='Shows a list of available commands or provides information about a specific command.')
async def help_command(ctx, command_name: str = None):
    if command_name:
        # Get help for a specific command
        command = bot.get_command(command_name)
        if command:
            embed = discord.Embed(title=f'Command: {command.name}', description=command.help,
                                  color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            await ctx.send('Command not found.')
    else:
        # List all available commands
        embed = discord.Embed(title='Available Commands', color=discord.Color.green())
        for command in bot.commands:
            embed.add_field(name=command.name, value=command.help, inline=False)
        await ctx.send(embed=embed)


# Command: Verify Member
@bot.command(name='v', help='Verifies a member with the Must Verify role and assigns them the Member role.')
@commands.has_permissions(manage_roles=True)
async def verify_member(ctx, member: discord.Member):
    must_verify_role = discord.utils.get(ctx.guild.roles, name='Must Verify')
    member_role = discord.utils.get(ctx.guild.roles, name='Member')
    if must_verify_role in member.roles:
        await member.remove_roles(must_verify_role)
        await member.add_roles(member_role)
        await ctx.send(f'{member.mention} has been verified and assigned the Member role.')
    else:
        await ctx.send(f'{member.mention} does not have the Must Verify role.')


# Command: Call Posts
@bot.command(name='callposts', help='Lists users with the role "Member" and the number of image or video posts they\'ve made in the last 7 days.')
@commands.has_permissions(manage_roles=True)
async def call_posts(ctx):
    member_role = discord.utils.get(ctx.guild.roles, name='Member')
    if member_role:
        members_with_role = member_role.members
        posts_info = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        for member in members_with_role:
            try:
                user_posts_count = get_user_posts_count(member, start_date, end_date)
                posts_info.append((member.display_name, user_posts_count))
            except Exception as e:
                print(f'Error querying posts count for {member.display_name}: {str(e)}')

        if posts_info:
            # Sort posts_info by the number of image or video posts in descending order
            posts_info.sort(key=lambda x: x[1], reverse=True)

            # Create an embed to display the information
            embed = discord.Embed(title='Image/Video Posts in the Last 7 Days', color=discord.Color.blue())
            for member_name, post_count in posts_info:
                embed.add_field(name=member_name, value=f'Posts: {post_count}', inline=False)

            await ctx.send(embed=embed)
        else:
            await ctx.send('No members with the "Member" role found or no image/video posts in the last 7 days.')
    else:
        await ctx.send('The "Member" role does not exist in this server.')


# Function: Log Moderation Action
def log_moderation_action(moderator_id, target_id, action_type, reason=None):
    session = Session()
    log_entry = ModerationLog(moderator_id=moderator_id, target_id=target_id, action_type=action_type, reason=reason)
    session.add(log_entry)
    session.commit()
    session.close()


# Function: Get or Create Muted Role
async def get_or_create_muted_role(guild):
    muted_role = discord.utils.get(guild.roles, name='Muted')
    if not muted_role:
        muted_role = await guild.create_role(name='Muted')
    return muted_role


# Function: Get User Posts Count
def get_user_posts_count(member, start_date, end_date):
    session = Session()
    user_posts_count = session.query(UserAttachment).filter(
        UserAttachment.user_id == member.id,
        UserAttachment.posted_at >= start_date,
        UserAttachment.posted_at <= end_date
    ).count()
    session.close()
    return user_posts_count


# Run the bot with the token
bot.run("MTIwOTczMDY4Mjk1NjU1NDM0Mg.GFHpPP.etbdsOFlbD0ahdPcitrWrTyexhUT_DpCuGodkM")
