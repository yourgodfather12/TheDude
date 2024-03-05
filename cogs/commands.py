import discord
from discord.ext import commands


class CommandCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command: Ping
    @commands.command()
    async def ping(self, ctx):
        """Check bot's latency."""
        latency = self.bot.latency * 1000  # Convert to milliseconds
        await ctx.send(f'Pong! Latency: {latency:.2f} ms')

    # Command: Hello
    @commands.command()
    async def hello(self, ctx):
        """Greet the user."""
        await ctx.send(f'Hello, {ctx.author.mention}!')

    # Command: Echo
    @commands.command()
    async def echo(self, ctx, *, message):
        """Echo back the provided message."""
        await ctx.send(message)

    # Command: Kick
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: commands.MemberConverter, *, reason=None):
        """Kick a member from the server."""
        await member.kick(reason=reason)
        await ctx.send(f'{member.mention} has been kicked.')

    # Command: Ban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: commands.MemberConverter, *, reason=None):
        """Ban a member from the server."""
        await member.ban(reason=reason)
        await ctx.send(f'{member.mention} has been banned.')

    # Command: Unban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        """Unban a member from the server."""
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user

            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user.mention} has been unbanned.')
                return

        await ctx.send(f'{member} was not found in the ban list.')

    # Command: Clear
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Clear a specified number of messages."""
        if amount <= 0:
            await ctx.send("Please provide a positive number of messages to clear.")
            return
        elif amount > 100:
            await ctx.send("You can only clear up to 100 messages at a time.")
            return

        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'{amount} messages have been cleared.')

    # Command: Avatar
    @commands.command()
    async def avatar(self, ctx, member: commands.MemberConverter = None):
        """Show the avatar of a user."""
        member = member or ctx.author
        embed = discord.Embed(title=f"{member.display_name}'s Avatar", color=member.color)
        embed.set_image(url=member.avatar_url)
        await ctx.send(embed=embed)

    # Command: Userinfo
    @commands.command()
    async def userinfo(self, ctx, member: commands.MemberConverter = None):
        """Display detailed information about a user."""
        member = member or ctx.author
        roles = [role.name for role in member.roles[1:]]  # Exclude @everyone role
        joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
        created_at = member.created_at.strftime("%Y-%m-%d %H:%M:%S")
        embed = discord.Embed(title=f"{member.display_name}'s Info", color=member.color)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(name="Nickname", value=member.nick, inline=False)
        embed.add_field(name="Roles", value=", ".join(roles), inline=False)
        embed.add_field(name="Joined Server", value=joined_at, inline=False)
        embed.add_field(name="Account Created", value=created_at, inline=False)
        await ctx.send(embed=embed)

    # Command: Serverinfo
    @commands.command()
    async def serverinfo(self, ctx):
        """Display information about the current server."""
        guild = ctx.guild
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        creation_date = guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
        embed = discord.Embed(title=f"{guild.name}'s Info", color=discord.Color.blue())
        embed.set_thumbnail(url=guild.icon_url)
        embed.add_field(name="Owner", value=guild.owner.display_name, inline=False)
        embed.add_field(name="Members", value=f"Total: {total_members}\nOnline: {online_members}", inline=False)
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}", inline=False)
        embed.add_field(name="Creation Date", value=creation_date, inline=False)
        await ctx.send(embed=embed)

    # Command: List all commands
    @commands.command(name="help")
    async def list_commands(self, ctx, command_name: str = None):
        """List all available commands or show help for a specific command."""
        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                await ctx.send(f"```{command.help}```")
            else:
                await ctx.send("Command not found.")
        else:
            command_list = "\n".join([f"• {command.name}: {command.help}" for command in self.bot.commands])
            await ctx.send(f"**Available commands:**\n{command_list}")

    # Setup function to add the cog
    @classmethod
    def setup(cls, bot):
        bot.add_cog(cls(bot))

# You may need to replace `bot.add_cog(cls(bot))` with `bot.add_cog(CommandCog(bot))` if necessary
