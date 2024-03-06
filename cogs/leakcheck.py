import os
import discord
from discord.ext import commands
import requests

class LeakCheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dehashed_api_key = "YOUR_DEHASHED_API_KEY"  # Replace with your DeHashed API key

    async def cog_check(self, ctx):
        allowed_roles = self.get_allowed_roles(ctx.guild)
        if any(role.name in allowed_roles for role in ctx.author.roles):
            return True
        else:
            await ctx.send("You don't have permission to use this command.")
            return False

    def get_allowed_roles(self, guild):
        allowed_roles = ["Admin", "Moderator", "Member"]
        return allowed_roles

    @commands.command(name="search")
    async def search(self, ctx, query: str):
        """Search for a query on LeakCheck and DeHashed"""
        leakcheck_results = self.search_leakcheck(query)
        dehashed_results = self.search_dehashed(query)

        embed = discord.Embed(title=f"Search Results for '{query}'", color=0x7289DA)
        embed.add_field(name="LeakCheck", value=leakcheck_results, inline=False)
        embed.add_field(name="DeHashed", value=dehashed_results, inline=False)

        await ctx.send(embed=embed)

    def search_leakcheck(self, query):
        url = "https://api.leakcheck.io/v1/search"

        params = {
            "query": query
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()

            if response.status_code == 200:
                return data
            else:
                return f"Error: Unable to fetch results from LeakCheck. Status Code: {response.status_code}"
        except Exception as e:
            print(f"Error: {e}")
            return "Error: Something went wrong with LeakCheck search. Please try again later."

    def search_dehashed(self, query):
        url = "https://api.dehashed.com/search"

        headers = {
            "Authorization": f"Basic {self.dehashed_api_key}"
        }
        params = {
            "query": query
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if response.status_code == 200:
                return data
            else:
                return f"Error: Unable to fetch results from DeHashed. Status Code: {response.status_code}"
        except Exception as e:
            print(f"Error: {e}")
            return "Error: Something went wrong with DeHashed search. Please try again later."

def setup(bot):
    bot.add_cog(LeakCheckCog(bot))
