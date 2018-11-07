"""
MIT License

Copyright (c) 2017 fourjr/kyb3r

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import aiohttp
import requests

from ..errors import (BadRequest, NotFoundError, NotResponding, NetworkError,
                      ServerError, Unauthorized, UnexpectedError, RatelimitError)
from .models import (BaseAttrDict, PaginatedAttrDict, Cards, Clan, ClanInfo, ClanWar, ClanWarLog,
                     Battle, Cycle, Player, Location, Tournament, Constants, rlist)
from .utils import API, SqliteDict, clansearch, tournamentsearch, crtag, keys, typecasted

from_timestamp = datetime.fromtimestamp


class Client:
    """A client that requests data from api.clashroyale.com. This class can
    either be async or non async.

    Parameters
    ----------
    token: str
        The api authorization token to be used for requests. https://developer.clashroyale.com/
    is_async: Optional[bool] = False
        Toggle for asynchronous/synchronous usage of the client
    error_debug: Optional[bool] = False
        Toggle for every method to raise ServerError to test error
        handling.
    session: Optional[Session] = None
        The http (client)session to be used for requests. Can either be a
        requests.Session or aiohttp.ClientSession.
    timeout: Optional[int] = 10
        A timeout for requests to the API
    url: Optional[str] = 'https://api.clashroyale.com/v1'
        A url to use instead of api.clashroyale.com/v1
        Only use this if you know what you are doing.
    cache_fp: Optional[str] = None
        File path for the sqlite3 database to use for caching requests,
        if this parameter is provided, the client will use its caching system
    cache_expires: Optional[int] = 10
        The number of seconds to wait before the client will request
        from the api for a specific route
    table_name: Optional[str] = 'cache'
        The table name to use for the cache database.
    camel_case: Optional[bool] = False
        Whether or not to access model data keys in snake_case or camelCase,
        this defaults to use snake_case
    constants: Optional[dict] = None
        Constants to use instead of the ones updated when the package is re-installed.
        To extract a ``dict`` from a ``BaseAttrDict``, do ``BaseAttrDict.to_dict()``
    user_agent: Optional[str] = None
        Appends to the default user-agent
    """

    def __init__(self, token, session=None, is_async=False, **options):
        self.token = token
        self.is_async = is_async
        self.error_debug = options.get('error_debug', False)
        self.timeout = options.get('timeout', 10)
        self.api = API(options.get('url', 'https://api.clashroyale.com/v1'))
        self.session = session or (aiohttp.ClientSession() if is_async else requests.Session())
        self.camel_case = options.get('camel_case', False)
        self.headers = {
            'Authorization': 'Bearer {}'.format(token),
            'User-Agent': 'python-clashroyale-client (fourjr/kyb3r) ' + options.get('user_agent', '')
        }
        self.cache_fp = options.get('cache_fp')
        self.using_cache = bool(self.cache_fp)
        self.cache_reset = options.get('cache_expires', 300)
        if self.using_cache:
            table = options.get('table_name', 'cache')
            self.cache = SqliteDict(self.cache_fp, table)

        constants = options.get('constants')
        if not constants:
            with Path(__file__).parent.parent.joinpath('constants.json').open(encoding='utf8') as f:
                constants = json.load(f)
        self.constants = Constants(self, constants, None)

    def _resolve_cache(self, url, **params):
        bucket = url + (('?' + urlencode(params)) if params else '')
        cached_data = self.cache.get(bucket)
        if not cached_data:
            return None
        last_updated = from_timestamp(cached_data['c_timestamp'])
        if (datetime.utcnow() - last_updated).total_seconds() < self.cache_reset:
            ret = (cached_data['data'], True, last_updated, None)
            if self.is_async:
                return self._wrap_coro(ret)
            return ret
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return '<OfficialAPI Client async={}>'.format(self.is_async)

    def close(self):
        self.session.close()

    def _raise_for_status(self, resp, text):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = text
        code = getattr(resp, 'status', None) or getattr(resp, 'status_code')
        if self.error_debug:
            raise ServerError(resp, data)
        if 300 > code >= 200:  # Request was successful
            if self.using_cache:
                cached_data = {
                    'c_timestamp': datetime.utcnow().timestamp(),
                    'data': data
                }
                self.cache[str(resp.url)] = cached_data
            return data, False, datetime.utcnow(), resp  # value, cached, last_updated, response
        if code == 400:
            raise BadRequest(resp, data)
        if code in (401, 403):  # Unauthorized request - Invalid token
            raise Unauthorized(resp, data)
        if code == 404:  # Tag not found
            raise NotFoundError(resp, data)
        if code == 429:
            raise RatelimitError(resp, data)
        if code == 503:  # Maintainence
            raise ServerError(resp, data)

        raise UnexpectedError(resp, data)

    async def _arequest(self, url, **params):
        method = params.get('method', 'GET')
        json_data = params.get('json', {})
        try:
            async with self.session.request(
                method, url, timeout=self.timeout, headers=self.headers, params=params, data=json_data
            ) as resp:
                return self._raise_for_status(resp, await resp.text())
        except asyncio.TimeoutError:
            raise NotResponding
        except aiohttp.ServerDisconnectedError:
            raise NetworkError

    async def _wrap_coro(self, arg):
        return arg

    def _request(self, url, timeout, refresh=False, **params):
        if self.using_cache and refresh is False:  # refresh=True forces a request instead of using cache
            cache = self._resolve_cache(url, **params)
            if cache is not None:
                return cache
        method = params.get('method', 'GET')
        json_data = params.get('json', {})
        if self.is_async:  # return a coroutine
            return self._arequest(url, **params)
        try:
            with self.session.request(
                method, url, timeout=timeout, headers=self.headers, params=params, json=json_data
            ) as resp:
                return self._raise_for_status(resp, resp.text)
        except requests.Timeout:
            raise NotResponding
        except requests.ConnectionError:
            raise NetworkError

    def _convert_model(self, data, cached, ts, model, resp):
        if isinstance(data, str):
            return data  # version endpoint, not feasable to add refresh functionality.
        if isinstance(data, list):  # extra functionality
            if all(isinstance(x, str) for x in data):  # endpoints endpoint
                return rlist(self, data, cached, ts, resp)  # extra functionality
            return [model(self, d, resp, cached=cached, ts=ts) for d in data]
        else:
            if 'items' in data:
                if data.get('paging'):
                    return PaginatedAttrDict(self, data, resp, model, cached=cached, ts=ts)
                return self._convert_model(data['items'], cached, ts, model, resp)
            else:
                return model(self, data, resp, cached=cached, ts=ts)

    async def _aget_model(self, url, timeout, model=None, **params):
        try:
            data, cached, ts, resp = await self._request(url, timeout, **params)
        except Exception as e:
            if self.using_cache:
                cache = self._resolve_cache(url, **params)
                if cache is not None:
                    data, cached, ts = cache
            if 'data' not in locals():
                raise e

        return self._convert_model(data, cached, ts, model, resp)

    def _get_model(self, url, model=None, timeout=None, **params):
        timeout = timeout or self.timeout
        if self.is_async:  # return a coroutine
            return self._aget_model(url, timeout, model, **params)
        # Otherwise, do everything synchronously.
        try:
            data, cached, ts, resp = self._request(url, timeout, **params)
        except Exception as e:
            if self.using_cache:
                cache = self._resolve_cache(url, **params)
                if cache is not None:
                    data, cached, ts = cache
            if 'data' not in locals():
                raise e

        return self._convert_model(data, cached, ts, model, resp)

    @typecasted
    def get_player(self, tag: crtag, timeout=None):
        """Get information about a player

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + tag
        return self._get_model(url, Player, timeout)

    @typecasted
    def get_player_verify(self, tag: crtag, apikey: str, timeout=None):
        """Check the API Key of a player.
        This endpoint has been **restricted** to
        certain members of the community

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        apikey: str
            The API Key in the player's settings
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + tag + '/verifytoken'
        return self._get_model(url, Player, timeout, method='POST', json={'token': apikey})

    @typecasted
    def get_player_battles(self, tag: crtag, timeout: int=None):
        """Get a player's battle log

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + tag + '/battlelog'
        return self._get_model(url, Battle, timeout)

    @typecasted
    def get_player_chests(self, tag: crtag, timeout: int=None):
        """Get information about a player's chest cycle

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + tag + '/upcomingchests'
        return self._get_model(url, Cycle, timeout)

    @typecasted
    def get_clan(self, tag: crtag, timeout: int=None):
        """Get inforamtion about a clan

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + tag
        return self._get_model(url, Clan, timeout)

    @typecasted
    def search_clans(self, **params: clansearch):
        """Search for a clan. At least one
        of the filters must be present

        Parameters
        ----------
        name: Optional[str]
            The name of a clan
            (has to be at least 3 characters long)
        locationId: Optional[int]
            A location ID
        minMembers: Optional[int]
            The minimum member count
            of a clan
        maxMembers: Optional[int]
            The maximum member count
            of a clan
        minScore: Optional[int]
            The minimum trophy score of
            a clan
        **limit: Optional[int] = None
            Limit the number of items returned in the response
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.CLAN
        return self._get_model(url, ClanInfo, timeout, **params)

    @typecasted
    def get_clan_war(self, tag: crtag, timeout: int=None):
        """Get inforamtion about a clan's current clan war

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + tag + '/currentwar'
        return self._get_model(url, ClanWar, timeout)

    @typecasted
    def get_clan_members(self, tag: crtag, **params: keys):
        """Get the clan's members

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        **limit: Optional[int] = None
            Limit the number of items returned in the response
        **after: Optional[int] = None
            Return only items that occur after this marker.
            After marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **before: Optional[int] = None
            Return only items that occur before this marker.
            Before marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.CLAN + '/' + tag + '/members'
        return self._get_model(url, ClanWarLog, timeout, **params)

    @typecasted
    def get_clan_war_log(self, tag: crtag, **params: keys):
        """Get a clan's war log

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        **limit: Optional[int] = None
            Limit the number of items returned in the response
        **after: Optional[int] = None
            Return only items that occur after this marker.
            After marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **before: Optional[int] = None
            Return only items that occur before this marker.
            Before marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.CLAN + '/' + tag + '/warlog'
        return self._get_model(url, ClanWarLog, timeout, **params)

    @typecasted
    def get_tournament(self, tag: crtag, timeout=0):
        """Get a tournament information

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/' + tag
        return self._get_model(url, Tournament, timeout)

    @typecasted
    def search_tournaments(self, name: str, **params: tournamentsearch):
        """Search for a tournament by its name

        Parameters
        ----------
        name: str
            The name of a tournament
        **limit: Optional[int] = None
            Limit the number of items returned in the response
        **after: Optional[int] = None
            Return only items that occur after this marker.
            After marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **before: Optional[int] = None
            Return only items that occur before this marker.
            Before marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        params['name'] = name
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        return self._get_model(self.api.TOURNAMENT, ClanInfo, timeout, **params)

    @typecasted
    def get_all_cards(self, timeout: int=None):
        """Get a list of all the cards in the game

        Parameters
        ----------
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        return self._get_model(self.api.CARDS, Cards, timeout)

    def get_cards(self, timeout: int=None):
        raise DeprecationWarning('Use Client.get_all_cards instead.')
        return self.get_all_cards(timeout)

    @typecasted
    def get_all_locations(self, timeout: int=None):
        """Get a list of all locations

        Parameters
        ----------
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        return self._get_model(self.api.LOCATIONS, Location, timeout)

    @typecasted
    def get_location(self, location_id: int, timeout: int=None):
        """Get a location information

        Parameters
        ----------
        location_id: int
            A location ID
            See https://github.com/RoyaleAPI/cr-api-data/blob/master/json/regions.json
            for a list of acceptable location IDs
        timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.LOCATIONS + '/' + str(location_id)
        return self._get_model(url, Location, timeout)

    @typecasted
    def get_top_clans(self, location_id='global', **params: keys):
        """Get a list of top clans by trophy

        Parameters
        ----------
        location_id: Optional[str] = 'global'
            A location ID or global
            See https://github.com/RoyaleAPI/cr-api-data/blob/master/json/regions.json
            for a list of acceptable location IDs
        **limit: Optional[int] = None
            Limit the number of items returned in the response
        **after: Optional[int] = None
            Return only items that occur after this marker.
            After marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **before: Optional[int] = None
            Return only items that occur before this marker.
            Before marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.LOCATIONS + '/' + str(location_id) + '/rankings/clans'
        return self._get_model(url, ClanInfo, timeout, **params)

    @typecasted
    def get_top_clanwar_clans(self, location_id='global', **params: keys):
        """Get a list of top clan war clans

        Parameters
        ----------
        location_id: Optional[str] = 'global'
            A location ID or global
            See https://github.com/RoyaleAPI/cr-api-data/blob/master/json/regions.json
            for a list of acceptable location IDs
        **limit: Optional[int] = None
            Limit the number of items returned in the response
        **after: Optional[int] = None
            Return only items that occur after this marker.
            After marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **before: Optional[int] = None
            Return only items that occur before this marker.
            Before marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.LOCATIONS + '/' + str(location_id) + '/rankings/clanwars'
        return self._get_model(url, ClanInfo, timeout, **params)

    @typecasted
    def get_top_players(self, location_id='global', **params: keys):
        """Get a list of top players

        Parameters
        ----------
        location_id: Optional[str] = 'global'
            A location ID or global
            See https://github.com/RoyaleAPI/cr-api-data/blob/master/json/regions.json
            for a list of acceptable location IDs
        **limit: Optional[int] = None
            Limit the number of items returned in the response
        **after: Optional[int] = None
            Return only items that occur after this marker.
            After marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **before: Optional[int] = None
            Return only items that occur before this marker.
            Before marker can be found from the response,
            inside the 'paging' property. Note that only after
            or before can be specified for a request, not both
        **timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.LOCATIONS + '/' + str(location_id) + '/rankings/players'
        return self._get_model(url, ClanInfo, timeout, **params)

    # Utility Functions
    def get_clan_image(self, obj: BaseAttrDict):
        """Get the clan badge image URL

        Parameters
        ---------
        obj: BaseAttrDict
            An object that has the clan badge ID either in ``.clan.badge_id`` or ``.badge_id``
            Can be ``Clan`` or ``Profile`` for example.

        Returns str
        """

        try:
            badge_id = obj.clan.badge_id
        except AttributeError:
            try:
                badge_id = obj.badge_id
            except AttributeError:
                return 'https://i.imgur.com/Y3uXsgj.png'

        if badge_id is None:
            return 'https://i.imgur.com/Y3uXsgj.png'

        for i in self.constants.alliance_badges:
            if i.id == badge_id:
                return 'https://royaleapi.github.io/cr-api-assets/badges/' + i.name + '.png'

    def get_arena_image(self, obj: BaseAttrDict):
        """Get the arena image URL

        Parameters
        ---------
        obj: BaseAttrDict
            An object that has the arena ID in ``.arena.id``
            Can be ``Profile`` for example.

        Returns None or str
        """
        badge_id = obj.arena.id
        for i in self.constants.arenas:
            if i.id == badge_id:
                return 'https://royaleapi.github.io/cr-api-assets/arenas/arena{}.png'.format(i.arena_id)

    def get_card_info(self, card_name: str):
        """Returns card info from constants

        Parameters
        ---------
        card_name: str
            A card name

        Returns None or Constants
        """
        for c in self.constants.cards:
            if c.name == card_name:
                return c

    def get_rarity_info(self, rarity: str):
        """Returns card info from constants

        Parameters
        ---------
        rarity: str
            A rarity name

        Returns None or Constants
        """
        for c in self.constants.rarities:
            if c.name == rarity:
                return c

    def get_deck_link(self, deck: BaseAttrDict):
        """Form a deck link

        Parameters
        ---------
        deck: BaseAttrDict
            An object is a deck. Can be retrieved from ``Player.current_deck``

        Returns str
        """
        deck_link = 'https://link.clashroyale.com/deck/en?deck='

        for i in deck:
            card = self.get_card_info(i.name)
            deck_link += '{0.id};'.format(card)

        return deck_link

    def get_datetime(self, timestamp: str, unix=True):
        """Converts a %Y%m%dT%H%M%S.%fZ to a UNIX timestamp
        or a datetime.datetime object

        Parameters
        ---------
        timestamp: str
            A timstamp in the %Y%m%dT%H%M%S.%fZ format, usually returned by the API
            in the ``created_time`` field for example (eg. 20180718T145906.000Z)
        unix: Optional[bool] = True
            Whether to return a POSIX timestamp (seconds since epoch) or not

        Returns int or datetime.datetime
        """
        time = datetime.strptime(timestamp, '%Y%m%dT%H%M%S.%fZ')
        if unix:
            return int(time.timestamp())
        else:
            return time
