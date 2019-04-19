import asynctest
import logging
import os
from datetime import datetime

import clashroyale
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv('../.env'))

TOKEN = os.getenv('official_api')
URL = os.getenv('official_api_url', 'https://api.clashroyale.com/v1')


class TestAsyncClient(asynctest.TestCase):
    """Tests all methods in the asynchronus client that
    uses the `aiohttp` module in `clashroyale`
    """
    async def setUp(self):
        self.location_id = ['global', 57000249]  # united states
        self.player_tags = ['#2P0LYQ', '#2PP']
        self.clan_tags = ['#9Q8PYRLL', '#8LQ2P0RL']
        self.tournament_tags = ['#2PPV2VUL', '#20RUCV8Q']
        self.cr = clashroyale.OfficialAPI(TOKEN, url=URL, is_async=True, loop=self.loop, timeout=30)

    async def tearDown(self):
        await self.cr.close()

    async def test_get_player(self):
        player = await self.cr.get_player(self.player_tags[0])
        self.assertEqual(player.tag, self.player_tags[0])

    async def test_get_player_timeout(self):
        player = await self.cr.get_player(self.player_tags[1], timeout=100)
        self.assertEqual(player.tag, self.player_tags[1])

    # get_player_verify is NOT tested

    async def test_get_player_battles(self):
        player = await self.cr.get_player_battles(self.player_tags[0])
        self.assertTrue(isinstance(player, list))

    async def test_get_player_battles_timeout(self):
        player = await self.cr.get_player_battles(self.player_tags[1], timeout=100)
        self.assertTrue(isinstance(player, list))

    async def test_get_player_chests(self):
        player = await self.cr.get_player_chests(self.player_tags[0])
        self.assertTrue(isinstance(player, list))

    async def test_get_player_chests_timeout(self):
        player = await self.cr.get_player_chests(self.player_tags[1], timeout=100)
        self.assertTrue(isinstance(player, list))

    async def test_get_clan(self):
        clan = await self.cr.get_clan(self.clan_tags[0])
        self.assertEqual(clan.tag, self.clan_tags[0])

    async def test_get_clan_timeout(self):
        clan = await self.cr.get_clan(self.clan_tags[1], timeout=100)
        self.assertEqual(clan.tag, self.clan_tags[1])

    async def test_search_clans_exc(self):
        self.assertAsyncRaises(clashroyale.BadRequest, self.cr.search_clans)

    async def test_search_clans(self):
        options = {
            'name': 'aaa',
            'locationId': self.location_id[1],
            'minMembers': 5,
            'maxMembers': 30,
            'minScore': 1000
        }
        clans = await self.cr.search_clans(**options)
        self.assertTrue(isinstance(clans, clashroyale.official_api.PaginatedAttrDict))

    async def test_search_clans_all_data(self):
        clans = await self.cr.search_clans(name='aaa', limit=3)
        await clans.all_data()
        self.assertGreater(len(clans), 3)

    async def test_get_clan_war(self):
        clan = await self.cr.get_clan_war(self.clan_tags[0])
        self.assertTrue(isinstance(clan.state, str))

    async def test_get_clan_war_timeout(self):
        clan = await self.cr.get_clan_war(self.clan_tags[1], timeout=100)
        self.assertTrue(isinstance(clan.state, str))

    async def test_get_clan_members(self):
        clan = await self.cr.get_clan_members(self.clan_tags[0])
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_clan_members_timeout(self):
        clan = await self.cr.get_clan_members(self.clan_tags[1], timeout=100)
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_clan_war_log(self):
        clan = await self.cr.get_clan_war_log(self.clan_tags[0])
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_clan_war_log_timeout(self):
        clan = await self.cr.get_clan_war_log(self.clan_tags[1], timeout=100)
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_tournament(self):
        tournament = await self.cr.get_tournament(self.tournament_tags[0])
        self.assertEqual(tournament.tag, self.tournament_tags[0])

    async def test_get_tournament_timeout(self):
        tournament = await self.cr.get_tournament(self.tournament_tags[1])
        self.assertEqual(tournament.tag, self.tournament_tags[1])

    async def test_search_tournaments(self):
        tournament = await self.cr.search_tournaments('aaa')
        self.assertTrue(isinstance(tournament, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_all_cards(self):
        cards = await self.cr.get_all_cards()
        self.assertTrue(isinstance(cards, list))

    async def test_get_all_locations(self):
        location = await self.cr.get_all_locations()
        self.assertTrue(isinstance(location, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_location_exc(self):
        async def request():
            await self.cr.get_location(self.location_id[0])
        self.assertAsyncRaises(ValueError, request)

    async def test_get_location(self):
        location = await self.cr.get_location(self.location_id[1])
        self.assertEqual(location.id, self.location_id[1])

    async def test_get_top_clans(self):
        clan = await self.cr.get_top_clans(self.location_id[0])
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_top_clans_timeout(self):
        clan = await self.cr.get_top_clans(self.location_id[1], timeout=100)
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_top_clanwar_clans(self):
        clan = await self.cr.get_top_clanwar_clans(self.location_id[0])
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_top_clanwar_clans_timeout(self):
        clan = await self.cr.get_top_clanwar_clans(self.location_id[1], timeout=100)
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_top_players(self):
        clan = await self.cr.get_top_players(self.location_id[0])
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    async def test_get_top_players_timeout(self):
        clan = await self.cr.get_top_players(self.location_id[1], timeout=100)
        self.assertTrue(isinstance(clan, clashroyale.official_api.PaginatedAttrDict))

    # Others

    async def test_logging(self):
        logger = 'clashroyale.official_api.client'
        with self.assertLogs(logger=logger, level=logging.DEBUG) as cm:
            await self.cr.get_player(self.player_tags[0])
        self.assertEqual(len(cm.output), 1)

    async def test_invalid_param(self):
        async def request():
            await self.cr.get_player_battles(self.player_tags[0], invalid=1)
        self.assertAsyncRaises(ValueError, request)

    async def test_invalid_tag(self):
        async def request():
            await self.cr.get_player(invalid_tag)
        invalid_tag = 'P'
        self.assertAsyncRaises(ValueError, request)
        invalid_tag = 'AAA'
        self.assertAsyncRaises(ValueError, request)
        invalid_tag = '2PP0PP0PP'
        self.assertAsyncRaises(clashroyale.NotFoundError, request)

    # Utility Functions
    async def test_get_clan_image(self):
        clan = await self.cr.get_clan(self.clan_tags[0])
        image = self.cr.get_clan_image(clan)

        self.assertTrue(isinstance(image, str))
        self.assertTrue(image.startswith('https://i.imgur.com') or image.startswith('https://royaleapi.github.io'))

    async def test_get_arena_image(self):
        player = await self.cr.get_player(self.player_tags[0])
        image = self.cr.get_arena_image(player)

        self.assertTrue(isinstance(image, str))
        self.assertTrue(image.startswith('https://i.imgur.com') or image.startswith('https://royaleapi.github.io'))

    async def test_get_card_info(self):
        card_name = 'Knight'
        card = self.cr.get_card_info(card_name)
        self.assertEqual(card.name, card_name)

    async def test_get_rarity_info(self):
        rarity_name = 'Common'
        rarity = self.cr.get_rarity_info(rarity_name)
        self.assertEqual(rarity.name, rarity_name)

    async def test_get_deck_link(self):
        player = await self.cr.get_player(self.player_tags[1])
        image = self.cr.get_deck_link(player.current_deck)

        self.assertTrue(isinstance(image, str))
        self.assertTrue(image.startswith('https://link.clashroyale.com/deck/en?deck='))

    async def test_get_datetime_hardcode(self):
        str_time = '20181105T070410.000Z'
        time = self.cr.get_datetime(str_time)
        self.assertTrue(isinstance(time, int))

    async def test_get_datetime_hardcode_noUnix(self):
        str_time = '20181105T070410.000Z'
        time = self.cr.get_datetime(str_time, unix=False)
        self.assertTrue(isinstance(time, datetime))

    async def test_get_datetime_tournament(self):
        tournament = await self.cr.get_tournament(self.tournament_tags[0])
        self.assertIn('createdTime', tournament.to_dict().keys())

        time = self.cr.get_datetime(tournament.created_time, unix=False)
        self.assertTrue(isinstance(time, datetime))


if __name__ == '__main__':
    asynctest.main()
