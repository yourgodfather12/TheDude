import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import pytz

class MediaCounter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1205951574992486495  # Your channel ID here
        self.daily_count.start()

    def cog_unload(self):
        self.daily_count.cancel()

    async def count_media(self, user_id):
        channel = self.bot.get_channel(self.channel_id)
        count = 0
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        async for message in channel.history(after=start_date, before=end_date):
            if message.author.id == user_id:
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4', '.mov', '.avi', '.mkv')):
                            count += 1

        return count

    async def post_count(self):
        counts = {}
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot:
                    count = await self.count_media(member.id)
                    counts[member.name] = count

        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        count_list = "\n".join([f"{name}: {count} {'image' if count == 1 else 'images'}" for name, count in sorted_counts])

        channel = self.bot.get_channel(self.channel_id)
        await channel.send(f"**Media post counts for the last 7 days:**\n{count_list}")

    @tasks.loop(hours=24)
    async def daily_count(self):
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        if now.hour == 23 and now.minute == 0:  # Run at 11:00 PM EST
            await self.post_count()

def setup(bot):
    bot.add_cog(MediaCounter(bot))

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_connect():
    print("Bot connected")

bot.add_cog(MediaCounter(bot))
bot.run('BOT_TOKEN_HERE')
