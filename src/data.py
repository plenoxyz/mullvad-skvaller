from time import strftime as time 
import urllib.request
from json import load
from differ import MullvadDiff
from database import DB
import os
import sys

class MullvadData():
    def __init__(self, url):
        self.url = url
        self.data = self.__update_data(init=True)

    def __get_time(self):
        return time('%Y-%m-%d %H:%M:%S')

    def __data_canary(self, response, data):
        if response.code != 200:
            raise Exception(f'HTTP code {response.code}')
        if len(data) < 100:
            raise Exception('Data with less than 100 items')
        return True

    def __update_data(self, init=False):
        response = urllib.request.urlopen(self.url)
        data = load(response)
        canary = self.__data_canary(response, data)
        if canary:
            return data
        else:
            if init:
                sys.exit('Canary failed on start, exiting')
            raise Exception('Canary failed, data not updated')

    def get_changes(self):
        old_data = self.data
        self.data = self.__update_data()
        differential = MullvadDiff(old_data, self.data)
        return differential.gen_changes()

    def server_exists(self, server):
        if server in [server['hostname'] for server in self.data]:
            return True
        return False

    def country_exists(self, country):
        if country in [server['country_name'] for server in self.data]:
            return True
        return False
