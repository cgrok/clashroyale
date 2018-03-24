import time
import unittest

import clashroyale
import yaml


with open('config.yaml') as f:
    CONFIG = yaml.load(f)

TOKEN = CONFIG.get('token')

class TestBlockingClient(unittest.TestCase):
    '''Tests all methods in the blocking client that
    uses the `requests` module in `clashroyale`

    Powered by RoyaleAPI
    '''
    def __init__(self, *args, **kwargs):
        self.clashroyale_client = clashroyale.Client(TOKEN, timeout=5)
        super().__init__(*args, **kwargs)

    ## PAUSE IN BETWEEN TESTS ##
    def tearDown(self):
        time.sleep(1)

    ## MISC METHODS ##
    def test_get_auth_stats(self):
        '''This test will test out:
        - User ID is numeric
        '''
        stats = self.clashroyale_client.get_auth_stats()
        self.assertTrue(stats.id.isnumeric())

    def test_get_constants(self):
        '''This test will test out:
        - Constants endpoint
        '''
        self.assertTrue(self.clashroyale_client.get_constants().raw_data, dict)

    def test_get_endpoints(self):
        '''This test will test out:
        - Endpoints endpoint
        '''
        self.assertTrue(self.clashroyale_client.get_endpoints(), list)

    def test_get_version(self):
        '''This test will test out:
        - Version endpoint
        '''
        self.assertTrue(self.clashroyale_client.get_version(), str)

    ## PLAYER METHODS ##
    def test_get_player(self):
        '''This test will test out:
        - Normal profile fetching
        - Invalid characters in tag profile fetching
        - Invalid profile fetching
        '''

        get_player = self.clashroyale_client.get_player
        tag = '2P0LYQ'
        player = get_player(tag)
        self.assertEqual(player.tag, tag)

        invalid_tag = '293R8FV'
        self.assertRaises(ValueError, get_player, invalid_tag)

        invalid_tag = '2P0LYQLYLY20P'
        self.assertRaises(clashroyale.NotFoundError, get_player, invalid_tag)

    def test_get_player_battles(self):
        '''This test will test out:
        - Normal profile battle fetching
        '''

        tag = '2P0LYQ'
        battles = self.clashroyale_client.get_player_battles(tag)
        self.assertTrue(isinstance(battles, list))

    def test_get_player_chests(self):
        '''This test will test out:
        - Normal profile chests fetching
        '''

        tag = '2P0LYQ'
        chests = self.clashroyale_client.get_player_chests(tag)
        self.assertTrue(isinstance(chests.upcoming, list))

        self.assertTrue(isinstance(chests.super_magical, int) or\
                        chests.super_magical is None)

    def test_get_top_players(self):
        '''This test will test out:
        - Top players endpoint
        '''
        players = self.clashroyale_client.get_top_players()
        self.assertTrue(isinstance(players, list))

    def test_get_popular_players(self):
        '''This test will test out:
        - Popular players endpoint
        '''
        players = self.clashroyale_client.get_popular_players()
        self.assertTrue(isinstance(players, list))

    ## ClAN METHODS ##
    def test_get_clan(self):
        '''This test will test out:
        - Normal clan fetching
        - Invalid characters in tag clan fetching
        - Invalid clan fetching
        '''
        tag = '29UQQ282'
        player = self.clashroyale_client.get_clan(tag)
        self.assertEqual(player.tag, tag)

        invalid_tag = '293R8FV'
        self.assertRaises(ValueError, self.clashroyale_client.get_clan, invalid_tag)

        invalid_tag = '2P0LYQLYLY20P'
        self.assertRaises(clashroyale.NotFoundError, self.clashroyale_client.get_clan, invalid_tag)

    def test_get_clan_battles(self):
        '''This test will test out:
        - Normal clan battles fetching
        '''

        tag = '29UQQ282'
        battles = self.clashroyale_client.get_clan_battles(tag)
        self.assertTrue(isinstance(battles, list))

    def test_get_clan_history(self):
        '''This test will test out:
        - Clan with history enabled history fetching
        - Clan without history enabled history fetching
        '''

        get_clan_history = self.clashroyale_client.get_clan_history

        tag = '2U2GGQJ'
        history = get_clan_history(tag)
        self.assertTrue(isinstance(history.raw_data, dict))

        tag = '29UQQ282'
        self.assertRaises(clashroyale.NotTrackedError, get_clan_history, tag)

    def test_get_clan_tracking(self):
        '''This test will test out:
        - Clan with history enabled history fetching
        - Clan without history enabled history fetching
        '''

        get_clan_tracking = self.clashroyale_client.get_clan_tracking

        tag = '2U2GGQJ'
        history = get_clan_tracking(tag)
        self.assertTrue(history[0].available)

        tag = '29UQQ282'
        history = get_clan_tracking(tag)
        self.assertFalse(history[0].available)

    def test_get_tracking_clans(self):
        '''This test will test out:
        - Tracking clans endpoint
        '''
        clans = self.clashroyale_client.get_tracking_clans()
        self.assertTrue(isinstance(clans, list))

    def test_get_top_clans(self):
        '''This test will test out:
        - Top clans endpoint
        '''
        clans = self.clashroyale_client.get_top_clans()
        self.assertTrue(isinstance(clans, list))

    def test_get_popular_clans(self):
        '''This test will test out:
        - Popular clans endpoint
        '''
        clans = self.clashroyale_client.get_popular_clans()
        self.assertTrue(isinstance(clans, list))

    ## TOURNAMENT METHODS ##
    def test_get_tournament(self):
        '''This test will test out:
        - Normal tournament fetching
        - Invalid characters in tag tournament fetching
        - Invalid tournament fetching
        '''
        tag = 'CU2RG8V'
        player = self.clashroyale_client.get_tournament(tag)
        self.assertEqual(player.tag, tag)

        invalid_tag = '293R8FV'
        self.assertRaises(ValueError, self.clashroyale_client.get_clan, invalid_tag)

        invalid_tag = '2P0LYQLYLY20P'
        self.assertRaises(clashroyale.NotFoundError, self.clashroyale_client.get_clan, invalid_tag)

    def test_get_known_tournaments(self):
        '''This test will test out:
        - Known tournaments endpoint
        '''
        tournaments = self.clashroyale_client.get_known_tournaments()
        self.assertTrue(isinstance(tournaments, list))

    def test_get_open_tournaments(self):
        '''This test will test out:
        - Open tournaments endpoint
        '''
        tournaments = self.clashroyale_client.get_open_tournaments()
        self.assertTrue(isinstance(tournaments, list))

    def test_get_popular_tournaments(self):
        '''This test will test out:
        - Popular tournaments endpoint
        '''
        tournaments = self.clashroyale_client.get_popular_tournaments()
        self.assertTrue(isinstance(tournaments, dict))

    ## DECKS METHODS ##
    def test_get_popular_decks(self):
        '''This test will test out:
        - Popular decks endpoint
        '''
        decks = self.clashroyale_client.get_popular_decks()
        self.assertTrue(isinstance(decks, list))

if __name__ == '__main__':
    unittest.main()
