from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class MongoCollection:
    def __init__(self, uri, db_name, db_collection):
        self.client = MongoClient(uri, server_api=ServerApi('1'))
        self.db = self.client[db_name]
        self.collection = self.db[db_collection]

class State(MongoCollection):
    def __init__(self, uri, db_name, db_collection='state'):
        super().__init__(uri, db_name, db_collection)
        self.data = list(self.collection.find({}, {'_id': False}))

    def set(self, data: list) -> None:
        self.collection.delete_many({})
        self.collection.insert_many(data)
        self.data = data
        return

    def get(self) -> list:
        return self.data

    def server_exists(self, server) -> bool:
        if server in [server['hostname'] for server in self.data]:
            return True
        return False

    def country_exists(self, country) -> bool:
        if country in [server['country_name'] for server in self.data]:
            return True
        return False


class Changes(MongoCollection):
    def __init__(self, uri, db_name, db_collection='changes'):
        super().__init__(uri, db_name, db_collection)

    def add(self, data: list) -> None:
        self.collection.insert_many(data)
        return

    def get(self) -> list:
        return list(self.collection.find({}))

    def remove(self, change_id) -> None:
        self.collection.delete_one({'_id': change_id})
        return

class Subscriptions(MongoCollection):
    def __init__(self, uri, db_name, db_collection='subscriptions'):
        super().__init__(uri, db_name, db_collection)

    def add(self, discord_user_id: int, key: str, value: str) -> str:
        result = self.collection.find_one({'discord_user_id': discord_user_id, key: value})
        if result:
            return f'Subscription already exists'
        result = self.collection.insert_one({'discord_user_id': discord_user_id, key: value})
        if result.acknowledged:
            return 'Subscription added'
        else:
            return 'Failed to add subscription'

    def remove(self, discord_user_id: int, key: str, value: str) -> str:
        result = self.collection.find_one_and_delete({'discord_user_id': discord_user_id, key: value})
        if result:
            return 'Removed subscription'
        return 'Subscription not found'

    def get_by_user_id(self, discord_user_id: int) -> dict:
        ''' Returns all subscriptions for a given user'''
        subscriptions = [sub for sub in self.collection.find({'discord_user_id': discord_user_id})]
        if subscriptions:
            servers = [sub['server'] for sub in subscriptions if 'server' in sub]
            countries = [sub['country'] for sub in subscriptions if 'country' in sub]
            message = ''
            if servers:
                message += '\n - Servers'
                for server in servers:
                    message += f'\n  - {server}'
            if countries:
                message += '\n - Countries'
                for country in countries:
                    message += f'\n  - {country}'
            return 'Active subscriptions:' + message
        return 'No active subscriptions found'

    def get_by_type(self, server, country) -> list:
        ''' Returns list of discord_user_id subscribed to server or country'''
        matches = self.collection.find({'$or': [{'server': server}, {'country': country}]})
        users = [user['discord_user_id'] for user in matches]
        return users

    def purge(self, discord_user_id) -> str:
        self.collection.delete_many({'discord_user_id': discord_user_id})
        return 'Deleted all associated subscriptions with your user'
