import asyncio
import asynctest
import logging
import os

import aiohttp
import clashroyale
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv('../.env'))

TOKEN = os.getenv('royaleapi')
URL = os.getenv('url', 'https://api.royaleapi.com')


class TestBlockingClient(asynctest.TestCase):
    """Tests all methods in the blocking client that
    uses the `aiohttp` module in `clashroyale`
    """
    async def setUp(self):
        self.cr = clashroyale.RoyaleAPI(TOKEN, url=URL, is_async=True, loop=self.loop, timeout=30)

    async def tearDown(self):
        await self.cr.close()
        await asyncio.sleep(2)

    # MISC METHODS #
    async def test_get_constants(self):
        """This test will test out:
        - Constants endpoint
        """
        constants = await self.cr.get_constants()
        self.assertTrue(constants.raw_data, dict)

    async def test_get_endpoints(self):
        """This test will test out:
        - Endpoints endpoint
        """
        self.assertTrue(await self.cr.get_endpoints(), list)

    async def test_get_version(self):
        """This test will test out:
        - Version endpoint
        """
        self.assertTrue(await self.cr.get_version(), str)

    # PLAYER METHODS #
    async def test_get_player(self):
        """This test will test out:
        - Normal profile fetching
        - Invalid characters in tag profile fetching
        - Invalid profile fetching
        """

        tag = '2P0LYQ'
        player = await self.cr.get_player(tag)
        self.assertEqual(player.tag, tag)

        async def request():
            self.cr.get_player(invalid_tag)

        invalid_tag = '293R8FV'
        self.assertAsyncRaises(ValueError, request)

        invalid_tag = '2P0LYQLYLY20P'
        self.assertAsyncRaises(clashroyale.NotFoundError, request)

    async def test_get_player_battles(self):
        """This test will test out:
        - Normal profile battle fetching
        """

        tag = '2P0LYQ'
        battles = await self.cr.get_player_battles(tag)
        self.assertTrue(isinstance(battles, list))

    async def test_get_player_chests(self):
        """This test will test out:
        - Normal profile chests fetching
        """

        tag = '2P0LYQ'
        chests = await self.cr.get_player_chests(tag)
        self.assertTrue(isinstance(chests.upcoming, list))

        self.assertTrue(isinstance(chests.super_magical, int) or chests.super_magical is None)

    async def test_get_response(self):
        """This test will test out:
        - BaseAttrDict.response
        """
        tag = '2P0LYQ'
        chests = await self.cr.get_player_chests(tag)
        self.assertTrue(isinstance(chests.response, aiohttp.ClientResponse))

    async def test_get_top_players(self):
        """This test will test out:
        - Top players endpoint
        """
        players = await self.cr.get_top_players()
        self.assertTrue(isinstance(players, list))

    async def test_get_popular_players(self):
        """This test will test out:
        - Popular players endpoint
        """
        players = await self.cr.get_popular_players()
        self.assertTrue(isinstance(players, list) or isinstance(players, clashroyale.royaleapi.BaseAttrDict))

    # ClAN METHODS #
    async def test_get_clan(self):
        """This test will test out:
        - Normal clan fetching
        - Invalid characters in tag clan fetching
        - Invalid clan fetching
        """
        tag = '29UQQ282'
        clan = await self.cr.get_clan(tag)
        self.assertEqual(clan.tag, tag)

        async def request():
            await self.cr.get_player(invalid_tag)

        invalid_tag = '293R8FV'
        self.assertAsyncRaises(ValueError, request)

        invalid_tag = '2P0LYQLYLY20P'
        self.assertAsyncRaises(clashroyale.NotFoundError, request)

    async def test_get_clan_battles(self):
        """This test will test out:
        - Normal clan battles fetching
        - All battles fetching
        - Clan war battles only fetching
        """

        tag = '29UQQ282'
        battles = await self.cr.get_clan_battles(tag)
        self.assertTrue(isinstance(battles, list))
        await asyncio.sleep(2)
        battles = await self.cr.get_clan_battles(tag, type='all')
        self.assertTrue(isinstance(battles, list))
        await asyncio.sleep(2)
        battles = await self.cr.get_clan_battles(tag, type='war')
        self.assertTrue(isinstance(battles, list))

    async def test_get_clan_war(self):
        """This test will test out:
        - Normal clan war fetching
        """

        tag = '29UQQ282'
        clan_war = await self.cr.get_clan_war(tag)
        self.assertTrue(isinstance(clan_war.raw_data, dict))

    async def test_get_clan_war_log(self):
        """This test will test out:
        - Normal clan war log fetching
        """

        tag = '29UQQ282'
        log = await self.cr.get_clan_war_log(tag)
        self.assertTrue(isinstance(log, list))

    async def test_get_clan_history(self):
        """This test will test out:
        - Clan with history enabled history fetching
        - Clan without history enabled history fetching
        """

        get_clan_history = await self.cr.get_clan_history()

        tag = '2U2GGQJ'
        history = get_clan_history(tag)
        self.assertTrue(isinstance(history.raw_data, dict))

        async def request():
            await self.cr.get_player(tag)

        tag = '29UQQ282'
        self.assertAsyncRaises(clashroyale.NotTrackedError, request)

    async def test_get_clan_tracking(self):
        """This test will test out:
        - Clan with history enabled history fetching
        - Clan without history enabled history fetching
        """

        get_clan_tracking = await self.cr.get_clan_tracking()

        tag = '2U2GGQJ'
        history = get_clan_tracking(tag)
        self.assertTrue(history.available)

        tag = '29UQQ282'
        history = get_clan_tracking(tag)
        self.assertFalse(history.available)

    async def test_get_tracking_clans(self):
        """This test will test out:
        - Tracking clans endpoint
        """
        clans = await self.cr.get_tracking_clans()
        self.assertTrue(isinstance(clans, list))

    async def test_get_top_clans(self):
        """This test will test out:
        - Top clans endpoint
        """
        clans = await self.cr.get_top_clans()
        self.assertTrue(isinstance(clans, list))

    async def test_get_top_war_clans(self):
        """This test will test out:
        - Top war clans endpoint
        """
        clans = await self.cr.get_top_war_clans()
        self.assertTrue(isinstance(clans, list))

    async def test_get_popular_clans(self):
        """This test will test out:
        - Popular clans endpoint
        """
        clans = await self.cr.get_popular_clans()
        self.assertTrue(isinstance(clans, list) or isinstance(clans, clashroyale.royaleapi.BaseAttrDict))

    # TOURNAMENT METHODS #
    async def test_get_tournament(self):
        """This test will test out:
        - Normal tournament fetching
        - Invalid characters in tag tournament fetching
        - Invalid tournament fetching
        """
        tag = 'CU2RG8V'
        player = await self.cr.get_tournament(tag)
        self.assertEqual(player.tag, tag)

        async def request():
            await self.cr.get_clan(invalid_tag)

        invalid_tag = '293R8FV'
        self.assertAsyncRaises(ValueError, request)

        invalid_tag = '2P0LYQLYLY20P'
        self.assertAsyncRaises(clashroyale.NotFoundError, request)

    async def test_get_known_tournaments(self):
        """This test will test out:
        - Known tournaments endpoint
        """
        tournaments = await self.cr.get_known_tournaments()
        self.assertTrue(isinstance(tournaments, list))

    async def test_get_open_tournaments(self):
        """This test will test out:
        - Open tournaments endpoint
        """
        tournaments = await self.cr.get_open_tournaments()
        self.assertTrue(isinstance(tournaments, list))

    async def test_get_popular_tournaments(self):
        """This test will test out:
        - Popular tournaments endpoint
        """
        tournaments = await self.cr.get_popular_tournaments()
        self.assertTrue(isinstance(tournaments, list) or isinstance(tournaments, clashroyale.royaleapi.BaseAttrDict))

    # DECKS METHODS #
    async def test_get_popular_decks(self):
        """This test will test out:
        - Popular decks endpoint
        """
        decks = await self.cr.get_popular_decks()
        self.assertTrue(isinstance(decks, list) or isinstance(decks, clashroyale.royaleapi.BaseAttrDict))

    # OTHERS #
    async def test_logging(self):
        logger = 'clashroyale.royaleapi.client'
        with self.assertLogs(logger=logger, level=logging.DEBUG) as cm:
            await self.cr.get_player('2P0LYQ')
        self.assertEqual(len(cm.output), 1)


if __name__ == '__main__':
    asynctest.main()
