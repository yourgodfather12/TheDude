import asyncio
import discord
from discord.ext import commands

class ServerBuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def copy_server_layout(self, source_guild, target_guild):
        try:
            # Copy roles
            for role in source_guild.roles:
                if role.name != "@everyone":  # Skip @everyone role
                    new_role = await target_guild.create_role(
                        name=role.name,
                        permissions=role.permissions,
                        color=role.color,  # Preserve role color
                        hoist=role.hoist,  # Preserve role hoist
                        mentionable=role.mentionable  # Preserve role mentionable
                    )
                    await new_role.edit(position=role.position)  # Preserve role position

            # Copy channels
            for category in source_guild.categories:
                new_category = await target_guild.create_category(category.name)
                for channel in category.channels:
                    overwrites = {}
                    for overwrite in channel.overwrites:
                        # Filter out role overwrites for roles that don't exist in the target guild
                        if isinstance(overwrite[0], discord.Role) and overwrite[0] not in target_guild.roles:
                            continue
                        overwrites[overwrite[0]] = overwrite[1]
                    if isinstance(channel, discord.TextChannel):
                        await new_category.create_text_channel(channel.name, overwrites=overwrites)
                    elif isinstance(channel, discord.VoiceChannel):
                        await new_category.create_voice_channel(channel.name, overwrites=overwrites)
        except discord.errors.HTTPException as e:
            raise RuntimeError(f"Error copying server layout: {e}")

    @commands.command(name="build", aliases=["buildserver"])
    @commands.has_permissions(administrator=True)
    async def build_server(self, ctx):
        source_guild = ctx.guild
        guild_name = f"{source_guild.name} Copy"

        # Confirmation message
        confirmation_message = await ctx.send(
            f"Are you sure you want to copy the server layout of '{source_guild.name}' to a new server called '{guild_name}'?")

        # Wait for user confirmation
        try:
            await confirmation_message.add_reaction('✅')  # Add a checkmark reaction
            await self.bot.wait_for('reaction_add',
                                    check=lambda reaction, user: user == ctx.author and reaction.emoji == '✅',
                                    timeout=30.0)
        except asyncio.TimeoutError:
            await ctx.send("Server layout copy cancelled.")
            return

        # Create the guild
        try:
            target_guild = await self.bot.create_guild(guild_name)
        except discord.errors.HTTPException as e:
            await ctx.send(f"Error creating server: {e}")
            return

        try:
            await self.copy_server_layout(source_guild, target_guild)
            await ctx.send(f"Server layout copied. New server '{guild_name}' created.")
        except RuntimeError as e:
            await ctx.send(str(e))


def setup(bot):
    bot.add_cog(ServerBuild(bot))
