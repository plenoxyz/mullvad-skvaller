import discord
import logging
import discord.ext.tasks
from typing import Literal
from argparse import ArgumentParser
from os import getenv
from time import sleep, time
from json import load as json_load
from urllib.request import urlopen
from skvaller.differ import MullvadDiff
from skvaller.database import model as database


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents, guild_id: int):
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.guild_id = guild_id

    # Copy the global commands to the discord server.
    async def setup_hook(self):
        MY_GUILD = discord.Object(id=self.guild_id)
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


def argument_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument('--discord-token', type=str, default=getenv('DISCORD_TOKEN'))
    parser.add_argument('--url', type=str, default=getenv('API_URL'))
    parser.add_argument('--db-uri', type=str, default=getenv('DB_URI'))
    parser.add_argument('--db-name', type=str, default=getenv('DB_NAME'))
    parser.add_argument('--guild-id', type=int, default=int(getenv('GUILD_ID')))
    parser.add_argument('--all-changes-channel-id', type=int, default=getenv('ALL_CHANGES_CHANNEL_ID'))
    parser.add_argument('--update-rate', type=int, default=getenv('UPDATE_RATE', 5))
    return parser.parse_args()

def get_api_data(url: str) -> list:
    response = urlopen(url)
    data = json_load(response)
    if response.code != 200:
        logging.error(f'API call failed with HTTP response {response}')
        return []
    if len(data) < 100:
        logging.error('API responded with less than 100 items')
        return []
    return data

def update_data(url: str, state: database.State, changes: database.Changes) -> bool:
    new_data = get_api_data(url)
    if not new_data:
        logging.error('Skipping update')
        return False
    cur_data = state.get()

    logging.debug('Calculating changes')
    try:
        new_changes = MullvadDiff(cur_data, new_data).gen_changes()
    except Exception as e:
        logging.error(f'Error calculating changes: {e}')
        return False
    if new_changes:
        logging.info(f'New {len(new_changes)} changes detected')
        changes.add(new_changes)
        logging.debug('Updating state')
        state.set(new_data)
    else:
        logging.debug(f'No changes detected')
    return True

def main() -> None:
    args = argument_parser()
    client = MyClient(intents=discord.Intents.default(), guild_id=args.guild_id)
    state = database.State(args.db_uri, args.db_name)
    changes = database.Changes(args.db_uri, args.db_name)
    subscriptions = database.Subscriptions(args.db_uri, args.db_name)

    if not state.get():
        logging.info('Fetching initial data from API...')
        data = get_api_data(args.url)
        if not data:
            logging.error('Failed to fetch initial data, exiting')
            return
        state.set(data)

    @discord.ext.tasks.loop(minutes=args.update_rate)
    async def notify_changes(channel: discord.TextChannel):
        logging.debug("Checking for changes...")
        if not update_data(args.url, state, changes):
            return
        for change in changes.get():
            # notify server channel
            if channel:
                logging.info(f"Notifying channel")
                await channel.send(change['message'])
                sleep(0.25)  # to avoid rate limiting
            # notify users
            users = subscriptions.get_by_type(
                server=change['server'],
                country=change['country_name'])
            for user in users:
                logging.info(f"Notifying user {user}")
                try:
                    user_obj = await client.fetch_user(user)
                    await user_obj.send(change['message'])
                    sleep(0.25)  # to avoid rate limiting
                except Exception as e:
                    logging.error(e)
            changes.remove(change['_id'])
        await channel.edit(topic=f'Last check: <t:{int(time())}:F>')

    @client.tree.command()
    @discord.app_commands.describe(type='Adds a subscription')
    async def subscribe(
            interaction: discord.Interaction,
            type: Literal['server', 'country'],
            value: str):
        
        """Subscribes user to a server or country for changes."""
        if type == 'server' and not state.server_exists(value):
            await interaction.response.send_message(
                'Server does not exist', ephemeral=True)
            return
        if type == 'country' and not state.country_exists(value):
            await interaction.response.send_message(
                'Country does not exist', ephemeral=True)
            return

        await interaction.response.send_message(
            subscriptions.add(interaction.user.id, type, value), ephemeral=True)

    @client.tree.command()
    @discord.app_commands.describe(type='Deletes a subscription')
    async def unsubscribe(
            interaction: discord.Interaction,
            type: Literal['server', 'country'],
            value: str):
        """Unsubscribes user from for changes."""
        message = subscriptions.remove(interaction.user.id, type, value)
        await interaction.response.send_message(
            message, ephemeral=True)

    @client.tree.command()
    async def list(
            interaction: discord.Interaction):
        """Lists all current subscriptions."""
        message = subscriptions.get_by_user_id(interaction.user.id)
        await interaction.response.send_message(message, ephemeral=True)

    @client.tree.command()
    async def purge_me(
            interaction: discord.Interaction,
            are_you_sure: Literal['no', 'yes']):
        """Deletes all user subscriptions."""
        if are_you_sure == 'yes':
            message = subscriptions.purge(interaction.user.id)
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message('Be more sure next time', ephemeral=True)

    @client.event
    async def on_ready():
        changes_channel = client.get_channel(args.all_changes_channel_id)
        logging.info(f'Logged in as {client.user} (ID: {client.user.id})')
        notify_changes.start(channel=changes_channel)

    client.run(args.discord_token)

if __name__ == '__main__':
    main()
