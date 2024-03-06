import discord
from discord.ext import commands, tasks
import asyncio
import datetime
import random
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurrencyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.currency_data = {}  # Dictionary to store currency data {member_id: currency_amount}
        self.leaderboard_channel_id = 1205951574992486495  # Channel ID to post leaderboard
        self.decay_interval = 86400  # Currency decay interval in seconds (1 day)
        self.decay_amount = 0.5  # Currency decay amount per interval
        self.earn_cooldown = commands.CooldownMapping.from_cooldown(1, 60, commands.BucketType.user)  # 60 seconds cooldown for earning currency

        # Start the currency decay loop
        self.decay_currency_loop.start()

    def cog_unload(self):
        self.decay_currency_loop.cancel()

    @tasks.loop(hours=24)  # Currency decay loop
    async def decay_currency_loop(self):
        for user_id in list(self.currency_data):
            self.currency_data[user_id] = max(0, self.currency_data[user_id] - self.decay_amount)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Bot is ready.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message contains an attachment (picture or video)
        if message.attachments:
            user_id = message.author.id

            # Check cooldown before awarding currency
            bucket = self.earn_cooldown.get_bucket(message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                return  # User is on cooldown

            post_currency = 5  # You can adjust the amount of currency awarded per post

            # Award currency to the user
            if user_id in self.currency_data:
                self.currency_data[user_id] += post_currency
            else:
                self.currency_data[user_id] = post_currency

            logger.info(f"{message.author} earned {post_currency} currency for their post.")

    @commands.command()
    async def balance(self, ctx, member: discord.Member = None):
        # Command to check user's balance
        member = member or ctx.author

        if member.bot:
            await ctx.send("Bots do not have currency balances.")
            return

        user_id = member.id
        balance = self.currency_data.get(user_id, 0)

        # Create a clean and simple embed for the balance message
        embed = discord.Embed(title="Currency Balance", color=discord.Color.green())
        embed.set_author(name=member.display_name, icon_url=member.avatar.url)
        embed.add_field(name="Balance", value=f"{balance} currency", inline=False)

        # Send the user a direct message with their balance
        await ctx.author.send(embed=embed)

    @commands.command()
    async def leaderboard(self, ctx):
        # Command to display the currency leaderboard
        await self.update_leaderboard_cache()

        channel = self.bot.get_channel(self.leaderboard_channel_id)
        if channel:
            leaderboard_message = "```css\n[Currency Leaderboard]\n\n"
            for index, (user_id, balance) in enumerate(self.leaderboard_cache, start=1):
                user = self.bot.get_user(user_id)
                if user:
                    leaderboard_message += f"{index}. {user.display_name}: {balance} currency\n"
            leaderboard_message += "```"
            await channel.send(leaderboard_message)
        else:
            logger.warning("Leaderboard channel not found. Please check the channel ID.")

    @balance.error
    async def balance_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please mention a valid user to check their balance.")

def setup(bot):
    bot.add_cog(CurrencyCog(bot))

bot = commands.Bot(command_prefix=".")

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")

bot.load_extension("currency")

bot.run("YOUR_BOT_TOKEN")
