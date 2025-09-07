from typing import Optional
from typing import Literal
import discord.ext
import discord.ext.tasks

import time
import discord
# from skvaller import bot_logger
import logging
from os import getenv

import skvaller.database.model as database


import argparse

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


def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--discord-token', type=str, default=getenv('DISCORD_TOKEN'))
    parser.add_argument('--db-uri', type=str, default=getenv('DB_URI'))
    parser.add_argument('--db-name', type=str, default=getenv('DB_NAME'))
    parser.add_argument('--guild-id', type=int, default=int(getenv('GUILD_ID')))
    parser.add_argument('--all-changes-channel-id', type=int, default=getenv('ALL_CHANGES_CHANNEL_ID'))
    return parser.parse_args()


def main():
    args = argument_parser()
    client = MyClient(intents=discord.Intents.default(), guild_id=args.guild_id)
    state = database.State(args.db_uri, args.db_name)
    changes = database.Changes(args.db_uri, args.db_name)
    subscriptions = database.Subscriptions(args.db_uri, args.db_name)

    @discord.ext.tasks.loop(minutes=1)
    async def notify_changes(channel: discord.TextChannel):
        logging.info("Checking for changes...")
        changes_list = changes.get()
        for change in changes_list:
            # notify server channel
            if channel:
                logging.info(f"Notifying channel")
                await channel.send(change['message'])
            # notify users
            users = subscriptions.get_by_type(
                server=change['server'],
                country=change['country_name'])
            for user in users:
                logging.info(f"Notifying user {user}")
                try:
                    user_obj = await client.fetch_user(user)
                    if user_obj:
                        await user_obj.send(change['message'])
                except Exception as e:
                    logging.error(e)
                time.sleep(0.33)
            # remove change from db
            changes.remove(change['_id'])

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
