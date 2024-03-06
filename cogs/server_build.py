import discord
from discord.ext import commands

class ServerBuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def copy_server_layout(self, source_guild, target_guild):
        # Copy roles
        for role in source_guild.roles:
            await target_guild.create_role(
                name=role.name,
                permissions=role.permissions
            )

        # Copy channels
        for category in source_guild.categories:
            new_category = await target_guild.create_category(category.name)
            for channel in category.channels:
                if isinstance(channel, discord.TextChannel):
                    await new_category.create_text_channel(channel.name)
                elif isinstance(channel, discord.VoiceChannel):
                    await new_category.create_voice_channel(channel.name)

    @commands.command(name="build", aliases=["buildserver"])
    async def build_server(self, ctx):
        source_guild = ctx.guild
        guild_name = f"{source_guild.name} Copy"
        try:
            target_guild = await self.bot.create_guild(guild_name)
        except discord.errors.HTTPException as e:
            await ctx.send(f"Error creating server: {e}")
            return

        await self.copy_server_layout(source_guild, target_guild)
        await ctx.send(f"Server layout copied. New server '{guild_name}' created.")

def setup(bot):
    bot.add_cog(ServerBuild(bot))
