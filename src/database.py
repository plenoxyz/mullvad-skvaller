from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi



class DB:
    def __init__(self, uri, db_name, db_collection):
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client[db_name]
        self.collection = self.db[db_collection]


    def add_subscription(self, discord_user_id: int, key: str, value: str) -> str:
        # check if key exists in other collection named 'data'

        result = self.collection.find_one({'discord_user_id': discord_user_id, key: value})
        if result:
            return 'You are already subscribed to this'

        result = self.collection.insert_one({'discord_user_id': discord_user_id, key: value})
        if result.acknowledged:
            return f'Added subscription for {key} {value}'

        return 'Failed to add subscription'


    def remove_subscription(self, discord_user_id: str, key: str, value: str) -> str:
        result = self.collection.find_one_and_delete({'discord_user_id': discord_user_id, key: value})
        if result:
            return 'Removed subscription'

        return 'Subscription not found'


    def list_user_subscriptions(self, discord_user_id: int) -> dict:
        subscriptions = [sub for sub in self.collection.find({'discord_user_id': discord_user_id})]
        if subscriptions:
            servers = [sub['server'] for sub in subscriptions if 'server' in sub]
            countries = [sub['country'] for sub in subscriptions if 'country' in sub]
            message = ''
            if servers:
                message += '\nServers'
                for server in servers:
                    message += f'\n- {server}'
            if countries:
                message += '\nCountries'
                for country in countries:
                    message += f'\n- {country}'
            return 'Active subscriptions:' + message

        return 'No subscriptions found'


    def purge_user(self, discord_user_id) -> str:
        self.collection.delete_many({'discord_user_id': discord_user_id})
        return 'Deleted all associated subscriptions'


    def get_all_server_subscriptions(self, server: str) -> list:
        return (user for user in self.collection.find({'server': server}))


    def get_all_country_subscriptions(self, country: str) -> list:
        return (user for user in self.collection.find({'country': country}))
