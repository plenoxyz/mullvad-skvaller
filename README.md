# Mullvad Relay Tracker

Changes to the [Mullvad servers](https://mullvad.net/en/servers) are not that common, but when they do happen, it's nice to know.

This discord bot lets you subscribe to a server or a country so when a change related to your subscription happens, you get a notification in your DMs (as long as you're still in the server).

You can join my own discord server for this, or host it yourself or even scrape the code and run it on your own.


# Disclaimers

This project is not affiliated with Mullvad in any way, it's a personal project that I made for myself.

If you use my discord server, the commands you use are not public, but seen by you, the bot and probably discord. Info provided by you (with the `/subscribe` command) is stored in a database associated with your discord user ID. If you wish to have all your data removed from my database, you can use the `/purge_me` command. If `/list` doesn't show any subscription, no data is stored associated with you. Any doubts, feel free to ask me or look at the code yourself.

If you're paranoid about your data, host it yourself and/or scrape the code to not even use discord at all (easily done, just discard the `bot.py`).

# Contribute

If you want to contribute, feel free to propose improvements and suggestions.

# TODO
- add timestamps to failures/exceptions
- notify users feature
- when listing existing subscriptions, flag if server/country is not found anymore
- consider adding existing data to database (instead session var) so the changes survive bot downtime 
- comment all methods that need a bit of clarity
- improve the README?
