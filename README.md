This Discord bot script is designed to provide various moderation and management functionalities for Discord servers, as well as the ability to save images and videos posted by users into directories organized by message content and store file paths in a MySQL database.

## How to Use

1. **Setting up MySQL Database:**
   - Make sure you have a MySQL database set up.
   - Replace `"yourusername"`, `"yourpassword"`, and `"yourdatabase"` in the script with your actual MySQL database credentials and database name.

2. **Setting up Discord Bot:**
   - Create a new Discord application and bot on the Discord Developer Portal.
   - Copy the bot token and replace `"YOUR_BOT_TOKEN"` in the script with your bot token.

3. **Running the Bot:**
   - Run the script using Python (`python script_name.py`).
   - Ensure that the necessary Python packages (`discord.py` and `mysql.connector`) are installed in your environment.

4. **Using the Bot:**
   - Invite the bot to your Discord server using the OAuth2 URL generated on the Discord Developer Portal.
   - Use the commands listed below to interact with the bot.

## Commands

1. `./serverinfo` - Displays information about the server.
2. `./nickname [user] [new_nickname]` - Changes the nickname of a user.
3. `./kick [user] [reason]` - Kicks a member from the server.
4. `./ban [user] [reason]` - Bans a member from the server.
5. `./clear [amount]` - Clears a specified number of messages from the current channel.
6. `./createchannel [channel_name]` - Creates a new text channel in the server.
7. `./createvoicechannel [channel_name]` - Creates a new voice channel in the server.
8. `./dm [user] [message]` - Sends a direct message to a user.
9. `./mute [user]` - Mutes a member in the server.
10. `./unmute [user]` - Unmutes a previously muted member in the server.
11. `./cp [user]` - Checks how many images or videos a user has posted in the past 5 days and saves them, organized by message content.

Please make sure to configure the bot permissions and roles appropriately within your Discord server.
