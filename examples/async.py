import clashroyale
import asyncio
import os

token = os.getenv('crtoken') # get your token somehow.

# ASYNC FUNCTIONALITY
async def main():
    client = clashroyale.Client(token, is_async=True) # is_async=True argument
    # EVERYTHING IS THE SAME, BUT WITH await's
    profile = await client.get_player('#8l9l9gl')
    print(repr(profile))
    print(profile.name) 
    await profile.refresh() 
    print(profile.stats.favorite_card.name)
    clan = await profile.get_clan() 
    print(clan)
    print(clan.clan_chest) 
    await clan.refresh() 
    member = clan.members[0] 
    assert member.clan is clan 
    assert member.rank == 1
    full_player = await member.get_profile()
    clans = await client.get_clans('2CCCP', '2U2GGQJ') # indefinite amount of arguments
    for clan in clans:
        print(clan.members[0]) 
    client.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())