import clashroyale
import asyncio
import os


token = os.getenv('crtoken')  # get your token somehow.


# ASYNC FUNCTIONALITY
async def main():
    client = clashroyale.RoyaleAPI(token, is_async=True)  # is_async=True argument
    # EVERYTHING IS THE SAME, BUT WITH await's
    profile = await client.get_player('CY8G8VVQ')
    print(repr(profile))
    print(profile.name)
    print(profile.league_statistics)
    await profile.refresh()
    print(profile.stats.favorite_card.name)
    clan = await profile.get_clan()
    print(clan)
    print(clan.member_count)
    await clan.refresh()
    member = clan.members[0]
    assert member.clan is clan
    assert member.rank == 1
    await member.get_player()  # full player
    clans = await client.get_clans('2CCCP', '2U2GGQJ')  # 7 max amount of arguments
    for clan in clans:
        print(clan.members[0])
    client.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
