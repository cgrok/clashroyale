import clashroyale
import asyncio
import os
import random

token = os.getenv('crtoken')

# Synchronous
client = clashroyale.Client(token)
print(client.get_player('2QJPUG00Q'))
# Everything is the same but without awaits.

async def main():
    # Asynchronous
    async_client = clashroyale.Client(token, is_async=True)
    player = await async_client.get_player('2QJPUG00Q')
    print(player.clan.tag) # Recursive attribute dictionary
    print(player.deck_link) # Access camelCase via snake_case
    await player.refresh() # Refresh model data
    clan = await player.get_clan() # Get full player clan info.
    # await clan.refresh() 
    random_member = random.choice(clan.members)
    print(await random_member.get_profile()) # Get full player profile for the member
    async_client.close()
    
loop = asyncio.get_event_loop() 
loop.run_until_complete(main())
