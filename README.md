# Mullvad Skvaller

Changes to the [Mullvad servers](https://mullvad.net/en/servers) are not that common, but when they do happen, it's nice to know.

This discord bot lets you subscribe to a server or a country so when a change related to your subscription happens, you get a notified in your DMs (as long as you're still in the server).

You can join [my own discord server](https://discord.gg/Xztjxs6H7X) for this, or host it yourself or even scrape the code and run it on your own by ignoring the `bot.py`.

## Commands supported:

- `/subscribe`
- `/unsubscribe`
- `/list`
- `/purge_me`

# Disclaimers

This project is not affiliated with Mullvad in any way.

If you use my discord server, the commands you use are only seen by you, the bot and probably Discord. Info provided by you (with the `/subscribe` command) is stored in a database associated with your discord user ID (check the [model.py](skvaller/database/model.py)). If you wish to have all your data removed from my database, you can use the `/purge_me` command, that's it, no logs nor history is kept.

# Contribute

If you want to contribute, feel free to propose improvements and suggestions.
