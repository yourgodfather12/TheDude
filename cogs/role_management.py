import discord
from discord.ext import commands

class RoleManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Get the server and the role named "Must Verify"
        server = member.guild
        must_verify_role = discord.utils.get(server.roles, name="Must Verify")

        if must_verify_role:
            # Assign the "Must Verify" role to the member
            await member.add_roles(must_verify_role)
        else:
            # If the "Must Verify" role doesn't exist, create it
            must_verify_role = await server.create_role(name="Must Verify")
            # Assign the role to the member
            await member.add_roles(must_verify_role)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def list_roles(self, ctx):
        """List all roles in the server."""
        roles = [role.name for role in ctx.guild.roles]
        await ctx.send(f"Roles in this server: {', '.join(roles)}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def create_role(self, ctx, role_name):
        """Create a new role."""
        server = ctx.guild
        existing_role = discord.utils.get(server.roles, name=role_name)
        if existing_role:
            await ctx.send(f"The role '{role_name}' already exists.")
        else:
            new_role = await server.create_role(name=role_name)
            await ctx.send(f"Role '{role_name}' created successfully.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def delete_role(self, ctx, role_name):
        """Delete an existing role."""
        server = ctx.guild
        role = discord.utils.get(server.roles, name=role_name)
        if role:
            await role.delete()
            await ctx.send(f"Role '{role_name}' deleted successfully.")
        else:
            await ctx.send(f"The role '{role_name}' does not exist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def assign_role(self, ctx, member: discord.Member, role_name):
        """Assign a role to a member."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
            await ctx.send(f"Role '{role_name}' assigned to {member.display_name}.")
        else:
            await ctx.send(f"The role '{role_name}' does not exist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def remove_role(self, ctx, member: discord.Member, role_name):
        """Remove a role from a member."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await member.remove_roles(role)
            await ctx.send(f"Role '{role_name}' removed from {member.display_name}.")
        else:
            await ctx.send(f"The role '{role_name}' does not exist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def v(self, ctx, member: discord.Member):
        """Move the mentioned user to the 'Member' role."""
        # Check if the command invoker has the 'Admin' or 'Moderator' role
        if any(role.name in ['Admin', 'Moderator'] for role in ctx.author.roles):
            member_role = discord.utils.get(ctx.guild.roles, name='Member')
            if member_role:
                await member.add_roles(member_role)
                await ctx.send(f'{member.mention} has been moved to the Member role.')
            else:
                await ctx.send("The 'Member' role does not exist.")
        else:
            await ctx.send("You do not have permission to use this command.")

    # Setup function to add the cog
    @classmethod
    def setup(cls, bot):
        bot.add_cog(cls(bot))
