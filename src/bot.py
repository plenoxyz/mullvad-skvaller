from typing import Optional
from typing import Literal
import discord.ext
import discord.ext.tasks
import traceback
import time
import discord

import dotenv
from os import getenv
from data import MullvadData
from database import DB
dotenv.load_dotenv()

MY_GUILD = discord.Object(id=getenv('GUILD_ID'))
ac_id = int(getenv('ALL_CHANGES_CHANNEL'))

assert getenv('DB_URI')
assert getenv('DB_NAME')
assert getenv('DB_COLLECTION')
assert getenv('DISCORD_TOKEN')
assert getenv('MULLVAD_API_URL')


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to
    # the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

intents = discord.Intents.default()
client = MyClient(intents=intents)
mullvad = MullvadData(getenv('MULLVAD_API_URL'))
database = DB(
            getenv('DB_URI'),
            getenv('DB_NAME'),
            getenv('DB_COLLECTION'))



@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    ac_channel = client.get_channel(ac_id) if ac_id else None
    detect_changes.start(ac_channel)


@discord.ext.tasks.loop(minutes=1)
async def detect_changes(ac_channel: Optional[discord.TextChannel] = None):
    try:
        changes = mullvad.get_changes()
    except Exception:
        print(traceback.format_exc())
        return
    if not changes:
        return

    # sends changes to the server channel
    if ac_channel:
        for change in changes:
            if 'changed' in change['message']:
                await ac_channel.send(change['message'])
                time.sleep(0.5)

    # notify users
    # @TODO


# subscribe
@client.tree.command()
@discord.app_commands.describe(type='Adds a subscription')
async def subscribe(
        interaction: discord.Interaction,
        type: Literal['server', 'country'],
        value: str):
    """Subscribes user to a server or country for changes."""
    if type == 'server' and not mullvad.server_exists(value):
        await interaction.response.send_message(
            'Server does not exist', ephemeral=True)
        return
    if type == 'country' and not mullvad.country_exists(value):
        await interaction.response.send_message(
            'Country does not exist', ephemeral=True)
        return
    message = database.add_subscription(
        interaction.user.id, type, value)
    await interaction.response.send_message(
        message, ephemeral=True)

# unsubscribe
@client.tree.command()
@discord.app_commands.describe(type='Deletes a subscription')
async def unsubscribe(
        interaction: discord.Interaction,
        type: Literal['server', 'country'],
        value: str):
    """Unsubscribes user from for changes."""
    message = database.remove_subscription(
        interaction.user.id, type, value)
    await interaction.response.send_message(
        message, ephemeral=True)


# list current subscriptions
@client.tree.command()
async def list(
        interaction: discord.Interaction):
    """Lists all current subscriptions."""
    message = database.list_user_subscriptions(interaction.user.id)
    await interaction.response.send_message(message, ephemeral=True)


# purge all subscriptions
@client.tree.command()
async def purge_me(
        interaction: discord.Interaction,
        are_you_sure: Literal['no', 'yes']):
    """Deletes all user subscriptions."""
    if are_you_sure == 'yes':
        message = database.purge_user(interaction.user.id)
        await interaction.response.send_message(message, ephemeral=True)
    else:
        await interaction.response.send_message('Be more sure next time', ephemeral=True)


def main():
    client.run(getenv('DISCORD_TOKEN'))

if __name__ == '__main__':
    main()
