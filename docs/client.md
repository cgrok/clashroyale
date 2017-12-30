# Client
This is where you create a client to use the wrapper, and you can pass in several keyword arguments (kwargs).
#### Keyword Arguments:
`token`: str: Pass in your Auth Key/token for the CR-API. You can also pass this in as the first argument. If you need to get one, go to https://discord.me/cr_api and go to #developer-key and type `!crapikey get`<br>
`is_async`: Optional[bool]: Toggle for asynchronous/synchronous usage of the client. Defaults to False.<br>
`session`: Optional[Session]: The http (client)session to be used for requests. Can either be a requests.Session or aiohttp.ClientSession.<br>
`timeout`: Optional[int]: A timeout for requests to the API, defaults to 10 seconds.<br>
`cache_fp`: Optional[str]: Put the path of the database file if you're using cache. Defaults to 'cache.db' (Kyber please approve)<br>
`cache_expires`: Optional[int]: The number of seconds to wait before the client will request from the api for a specific route, this defaults to 10 seconds.<br>
`table_name`: Optional[str]: The table name to use for the cache database. Defaults to 'cache'<br>
`camel_case`: Optional[bool]: Whether or not to access model data keys in snake_case or camelCase, this defaults to False (use snake_case)
#### Example
```
import clashroyale
import asyncio
import os

token = os.getenv('crtoken') # get your token somehow.
# ASYNC FUNCTIONALITY
async def main():
    client = clashroyale.Client(token, is_async=True) # is_async=True argument
    # EVERYTHING IS THE SAME, BUT WITH await's
    profile = await client.get_player('CY8G8VVQ')
    print(repr(profile))
    print(profile.name) 
    print(profile.league_statistics)
    await profile.refresh() 
    print(profile.stats.favorite_card.name)
    clan = await profile.get_clan() 
    print(clan)
    

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```
#### FOR ALL EXAMPLES:
Go to the [examples](https://github.com/cgrok/clashroyale/blob/master/examples) folder in this repository.
