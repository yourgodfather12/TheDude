import discord
from discord.ext import commands
import requests

API_KEY = 'your_api_key_here'

class FakeNude(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.client.user}')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.client.user:
            return

        if message.content.startswith('./fakenude'):
            if len(message.attachments) == 0:
                await message.channel.send('Please upload an image.')
                return

            allowed_roles = ['Admin', 'Moderator', 'Member']
            author_roles = [role.name for role in message.author.roles]

            if any(role in author_roles for role in allowed_roles):
                image_url = message.attachments[0].url
                nude_image = self.create_nude(image_url)
                if nude_image:
                    await message.channel.send(f'{message.author.mention} Here is your nude image:')
                    await message.channel.send(file=discord.File(nude_image, 'nude.jpg'))
                else:
                    await message.channel.send('Failed to generate nude image. Please try again.')
            else:
                await message.channel.send('You do not have permission to use this command.')

    def create_nude(self, image_url):
        try:
            headers = {
                'Authorization': f'Bearer {API_KEY}'
            }
            data = {
                'image_url': image_url
            }
            response = requests.post('https://api.makenude.ai/v1/nude', headers=headers, json=data)
            if response.status_code == 200:
                nude_image_url = response.json()['nude_image_url']
                nude_image = requests.get(nude_image_url).content
                return nude_image
            else:
                return None
        except Exception as e:
            print(f'Error generating nude image: {e}')
            return None

def setup(client):
    client.add_cog(FakeNude(client))
