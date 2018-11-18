import asyncio
import logging
import json
from datetime import datetime
from time import time
from urllib.parse import urlencode

import aiohttp
import requests

from ..errors import (NotFoundError, NotResponding, NetworkError, ServerError, Unauthorized, NotTrackedError,
                      UnexpectedError, RatelimitError, RatelimitErrorDetected)
from .models import (BaseAttrDict, Refreshable, PartialTournament, PartialClan,
                     PartialPlayerClan, FullPlayer, FullClan, rlist)
from .utils import API, SqliteDict, clansearch, crtag, keys, tournamentfilter, typecasted

from_timestamp = datetime.fromtimestamp
log = logging.getLogger(__name__)


class Client:
    """A client that requests data from royaleapi.com. This class can
    either be async or non async.

    Parameters
    ----------
    token: str
        The api authorization token to be used for requests
        https://docs.royaleapi.com/#/authentication
    is_async: Optional[bool] = False
        Toggle for asynchronous/synchronous usage of the client
    error_debug: Optional[bool] = False
        Toggle for every method to raise ServerError to test error
        handling
    session: Optional[Session] = None
        The http (client)session to be used for requests. Can either be a
        requests.Session or aiohttp.ClientSession
    timeout: Optional[int] = 10
        A timeout for requests to the API
    url: Optional[str] = https://api.royaleapi.com
        A url to use instead of api.royaleapi.com
        Only use this if you know what you are doing
    cache_fp: Optional[str]
        File path for the sqlite3 database to use for caching requests,
        if this parameter is provided, the client will use its caching system
    cache_expires: Optional[int] = 10
        The number of seconds to wait before the client will request
        from the api for a specific route
    table_name: Optional[str] = 'cache'
        The table name to use for the cache database
    camel_case: Optional[bool] = False
        Whether or not to access model data keys in snake_case or camelCase,
        this defaults use snake_case
    user_agent: Optional[str] = None
        Appends to the default user-agent
    """

    REQUEST_LOG = '{method} {url} has received {text}, has returned {status}'

    def __init__(self, token, session=None, is_async=False, **options):
        self.token = token
        self.is_async = is_async
        self.error_debug = options.get('error_debug', False)
        self.timeout = options.get('timeout', 10)
        self.api = API(options.get('url', 'https://api.royaleapi.com'))
        self.session = session or (aiohttp.ClientSession() if is_async else requests.Session())
        self.camel_case = options.get('camel_case', False)
        self.headers = {
            'Authorization': 'Bearer {}'.format(token),
            'User-Agent': 'python-clashroyale-client (fourjr/kyb3r) ' + options.get('user_agent', '')
        }
        self.cache_fp = options.get('cache_fp')
        self.using_cache = bool(self.cache_fp)
        self.cache_reset = options.get('cache_expires', 300)
        self.ratelimit = [10, 10, 0]
        if self.using_cache:
            table = options.get('table_name', 'cache')
            self.cache = SqliteDict(self.cache_fp, table)

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

    @classmethod
    def Async(cls, token, session=None, **options):
        '''Returns the client in async mode.'''
        return cls(token, session=session, is_async=True, **options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.close()

    def __repr__(self):
        return '<RoyaleAPI Client async={}>'.format(self.is_async)

    def close(self):
        return self.session.close()

    def _raise_for_status(self, resp, text, *, method=None):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = text
        code = getattr(resp, 'status', None) or getattr(resp, 'status_code')
        log.debug(self.REQUEST_LOG.format(method=method or resp.request_info.method, url=resp.url, text=text, status=code))
        if self.error_debug:
            raise ServerError(resp, data)
        if 300 > code >= 200:  # Request was successful
            if self.using_cache:
                cached_data = {
                    'c_timestamp': datetime.utcnow().timestamp(),
                    'data': data
                }
                self.cache[str(resp.url)] = cached_data
            if resp.headers.get('x-ratelimit-limit'):
                self.ratelimit = [
                    int(resp.headers['x-ratelimit-limit']),
                    int(resp.headers['x-ratelimit-remaining']),
                    int(resp.headers.get('x-ratelimit-reset', 0))
                ]
            return data, False, datetime.utcnow(), resp  # value, cached, last_updated, response
        if code == 401:  # Unauthorized request - Invalid token
            raise Unauthorized(resp, data)
        if code in (400, 404):  # Tag not found
            raise NotFoundError(resp, data)
        if code == 417:
            raise NotTrackedError(resp, data)
        if code == 429:
            raise RatelimitError(resp, data)
        if code >= 500:  # Something wrong with the api servers :(
            raise ServerError(resp, data)

        raise UnexpectedError(resp, data)

    async def _arequest(self, url, **params):
        timeout = params.pop('timeout', None) or self.timeout
        try:
            async with self.session.get(url, timeout=timeout, headers=self.headers, params=params) as resp:
                return self._raise_for_status(resp, await resp.text())
        except asyncio.TimeoutError:
            raise NotResponding
        except aiohttp.ServerDisconnectedError:
            raise NetworkError

    async def _wrap_coro(self, arg):
        return arg

    def _request(self, url, refresh=False, **params):
        if self.using_cache and refresh is False:  # refresh=True forces a request instead of using cache
            cache = self._resolve_cache(url, **params)
            if cache is not None:
                return cache
        if self.ratelimit[1] == 0 and time() < self.ratelimit[2] / 1000:
            if not url.endswith('/auth/stats'):
                raise RatelimitErrorDetected(self.ratelimit[2] / 1000 - time())
        if self.is_async:  # return a coroutine
            return self._arequest(url, **params)
        timeout = params.pop('timeout', None) or self.timeout
        try:
            with self.session.get(url, timeout=timeout, headers=self.headers, params=params) as resp:
                return self._raise_for_status(resp, resp.text, method='GET')
        except requests.Timeout:
            raise NotResponding
        except requests.ConnectionError:
            raise NetworkError

    def _convert_model(self, data, cached, ts, model, resp):
        if model is None and isinstance(data, list):
            model = BaseAttrDict
        else:
            model = Refreshable

        if isinstance(data, str):
            return data  # version endpoint, not feasable to add refresh functionality.
        if isinstance(data, list):  # extra functionality
            if all(isinstance(x, str) for x in data):  # endpoints endpoint
                return rlist(self, data, cached, ts, resp)  # extra functionality
            return [model(self, d, resp, cached=cached, ts=ts) for d in data]
        else:
            return model(self, data, resp, cached=cached, ts=ts)

    async def _aget_model(self, url, model=None, **params):
        try:
            data, cached, ts, resp = await self._request(url, **params)
        except Exception as e:
            if self.using_cache:
                cache = self._resolve_cache(url, **params)
                if cache is not None:
                    data, cached, ts = cache
            if 'data' not in locals():
                raise e

        return self._convert_model(data, cached, ts, model, resp)

    def _get_model(self, url, model=None, **params):
        if self.is_async:  # return a coroutine
            return self._aget_model(url, model, **params)
        # Otherwise, do everything synchronously.
        try:
            data, cached, ts, resp = self._request(url, **params)
        except Exception as e:
            if self.using_cache:
                cache = self._resolve_cache(url, **params)
                if cache is not None:
                    data, cached, ts = cache
            if 'data' not in locals():
                raise e

        return self._convert_model(data, cached, ts, model, resp)

    def get_version(self):
        """Gets the version of RoyaleAPI. Returns a string"""
        return self._get_model(self.api.VERSION)

    def get_endpoints(self):
        """Gets a list of endpoints available in RoyaleAPI"""
        return self._get_model(self.api.ENDPOINTS)

    @typecasted
    def get_constants(self, **params: keys):
        """Get the CR Constants

        Parameters
        ----------
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CONSTANTS
        return self._get_model(url, **params)

    @typecasted
    def get_player(self, *tags: crtag, **params: keys):
        """Get a player information

        Parameters
        ----------
        \*tags: str
            Valid player tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + ','.join(tags)
        return self._get_model(url, FullPlayer, **params)

    @typecasted
    def get_player_verify(self, tag: crtag, apikey: str, **params: keys):
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
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + tag + '/verify'
        params.update({'token': apikey})
        return self._get_model(url, FullPlayer, **params)

    @typecasted
    def get_player_battles(self, *tags: crtag, **params: keys):
        """Get a player's battle log

        Parameters
        ----------
        \*tags: str
            Valid player tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + ','.join(tags) + '/battles'
        return self._get_model(url, **params)

    @typecasted
    def get_player_chests(self, *tags: crtag, **params: keys):
        """Get information about a player's chest cycle

        Parameters
        ----------
        \*tags: str
            Valid player tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.PLAYER + '/' + ','.join(tags) + '/chests'
        return self._get_model(url, **params)

    @typecasted
    def get_clan(self, *tags: crtag, **params: keys):
        """Get a clan information

        Parameters
        ----------
        \*tags: str
            Valid clan tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + ','.join(tags)
        return self._get_model(url, FullClan, **params)

    @typecasted  # Validate clan search parameters.
    def search_clans(self, **params: clansearch):
        """Search for a clan. At least one
        of the filters must be present

        Parameters
        ----------
        name: Optional[str]
            The name of a clan
        minMembers: Optional[int]
            The minimum member count
            of a clan
        maxMembers: Optional[int]
            The maximum member count
            of a clan
        score: Optional[int]
            The minimum trophy score of
            a clan
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/search'
        return self._get_model(url, PartialClan, **params)

    def get_tracking_clans(self, **params: keys):
        """Get a list of clans that are being
        tracked by having either cr-api.com or
        royaleapi.com in the description

        Parameters
        ----------
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/tracking'
        return self._get_model(url, **params)

    @typecasted
    def get_clan_tracking(self, *tags: crtag, **params: keys):
        """Returns if the clan is currently being tracked
        by the API by having either cr-api.com or royaleapi.com
        in the clan description

        Parameters
        ----------
        \*tags: str
            Valid clan tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + ','.join(tags) + '/tracking'
        return self._get_model(url, **params)

    @typecasted
    def get_clan_battles(self, *tags: crtag, **params: keys):
        """Get the battle log from everyone in the clan

        Parameters
        ----------
        \*tags: str
            Valid player tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*type: str
            Filters what kind of battles. Pick from:
            :all:, :war:, :clanMate:
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + ','.join(tags) + '/battles'
        return self._get_model(url, **params)

    @typecasted
    def get_clan_history(self, *tags: crtag, **params: keys):
        """Get the clan history. Only works if the clan is being tracked
        by having either cr-api.com or royaleapi.com in the clan's
        description

        Parameters
        ----------
        \*tags: str
            Valid clan tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + ','.join(tags) + '/history'
        return self._get_model(url, **params)

    @typecasted
    def get_clan_war(self, tag: crtag, **params: keys):
        """Get inforamtion about a clan's current clan war

        Parameters
        ----------
        *tag: str
            A valid clan tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + tag + '/war'
        return self._get_model(url, **params)

    @typecasted
    def get_clan_war_log(self, tag: crtag, **params: keys):
        """Get a clan's war log

        Parameters
        ----------
        \*tags: str
            Valid clan tags. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.CLAN + '/' + tag + '/warlog'
        return self._get_model(url, **params)

    @typecasted
    def get_tournament(self, tag: crtag, **params: keys):
        """Get a tournament information

        Parameters
        ----------
        tag: str
            A valid tournament tag. Minimum length: 3
            Valid characters: 0289PYLQGRJCUV
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/' + tag
        return self._get_model(url, **params)

    @typecasted
    def search_tournaments(self, **params: keys):
        """Search for a tournament

        Parameters
        ----------
        name: str
            The name of the tournament
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/search'
        return self._get_model(url, PartialClan, **params)

    @typecasted
    def get_top_clans(self, country_key='', **params: keys):
        """Get a list of top clans by trophy

        location_id: Optional[str] = ''
            A location ID or '' (global)
            See https://github.com/RoyaleAPI/cr-api-data/blob/master/json/regions.json
            for a list of acceptable location IDs
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOP + '/clans/' + str(country_key)
        return self._get_model(url, PartialClan, **params)

    @typecasted
    def get_top_players(self, country_key='', **params: keys):
        """Get a list of top players

        location_id: Optional[str] = ''
            A location ID or '' (global)
            See https://github.com/RoyaleAPI/cr-api-data/blob/master/json/regions.json
            for a list of acceptable location IDs
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOP + '/players/' + str(country_key)
        return self._get_model(url, PartialPlayerClan, **params)

    @typecasted
    def get_popular_clans(self, **params: keys):
        """Get a list of most queried clans

        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.POPULAR + '/clans'
        return self._get_model(url, PartialClan, **params)

    @typecasted
    def get_popular_players(self, **params: keys):
        """Get a list of most queried players

        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.POPULAR + '/players'
        return self._get_model(url, PartialPlayerClan, **params)

    @typecasted
    def get_popular_tournaments(self, **params: keys):
        """Get a list of most queried tournaments

        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.POPULAR + '/tournament'
        return self._get_model(url, PartialTournament, **params)

    @typecasted
    def get_popular_decks(self, **params: keys):
        """Get a list of most queried decks

        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.POPULAR + '/decks'
        return self._get_model(url, **params)

    @typecasted
    def get_known_tournaments(self, **params: tournamentfilter):
        """Get a list of queried tournaments

        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/known'
        return self._get_model(url, PartialTournament, **params)

    @typecasted
    def get_open_tournaments(self, **params: tournamentfilter):
        """Get a list of open tournaments

        \*\*1k: Optional[int] = 0
            Set to 1 to filter tournaments that have
            at least 1000 max players
        \*\*full: Optional[int] = 0
            Set to 1 to filter tournaments that are
            full
        \*\*inprep: Optional[int] = 0
            Set to 1 to filter tournaments that are
            in preperation
        \*\*joinable: Optional[int] = 0
            Set to 1 to filter tournaments that are
            joinable
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/open'
        return self._get_model(url, PartialTournament, **params)

    @typecasted
    def get_1k_tournaments(self, **params: tournamentfilter):
        """Get a list of tournaments that have at least 1000
        max players

        \*\*open: Optional[int] = 0
            Set to 1 to filter tournaments that are
            open
        \*\*full: Optional[int] = 0
            Set to 1 to filter tournaments that are
            full
        \*\*inprep: Optional[int] = 0
            Set to 1 to filter tournaments that are
            in preperation
        \*\*joinable: Optional[int] = 0
            Set to 1 to filter tournaments that are
            joinable
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/1k'
        return self._get_model(url, PartialTournament, **params)

    @typecasted
    def get_prep_tournaments(self, **params: tournamentfilter):
        """Get a list of tournaments that are in preperation

        \*\*1k: Optional[int] = 0
            Set to 1 to filter tournaments that have
            at least 1000 max players
        \*\*open: Optional[int] = 0
            Set to 1 to filter tournaments that are
            open
        \*\*full: Optional[int] = 0
            Set to 1 to filter tournaments that are
            full
        \*\*joinable: Optional[int] = 0
            Set to 1 to filter tournaments that are
            joinable
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/inprep'
        return self._get_model(url, PartialTournament, **params)

    @typecasted
    def get_joinable_tournaments(self, **params: tournamentfilter):
        """Get a list of tournaments that are joinable

        \*\*1k: Optional[int] = 0
            Set to 1 to filter tournaments that have
            at least 1000 max players
        \*\*open: Optional[int] = 0
            Set to 1 to filter tournaments that are
            open
        \*\*full: Optional[int] = 0
            Set to 1 to filter tournaments that are
            full
        \*\*inprep: Optional[int] = 0
            Set to 1 to filter tournaments that are
            in preperation
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/joinable'
        return self._get_model(url, PartialTournament, **params)

    @typecasted
    def get_full_tournaments(self, **params: tournamentfilter):
        """Get a list of tournaments that are full

        \*\*1k: Optional[int] = 0
            Set to 1 to filter tournaments that have
            at least 1000 max players
        \*\*open: Optional[int] = 0
            Set to 1 to filter tournaments that are
            open
        \*\*inprep: Optional[int] = 0
            Set to 1 to filter tournaments that are
            in preperation
        \*\*joinable: Optional[int] = 0
            Set to 1 to filter tournaments that are
            joinable
        \*\*keys: Optional[list] = None
            Filter which keys should be included in the
            response
        \*\*exclude: Optional[list] = None
            Filter which keys should be excluded from the
            response
        \*\*max: Optional[int] = None
            Limit the number of items returned in the response
        \*\*page: Optional[int] = None
            Works with max, the zero-based page of the
            items
        \*\*timeout: Optional[int] = None
            Custom timeout that overwrites Client.timeout
        """
        url = self.api.TOURNAMENT + '/full'
        return self._get_model(url, PartialTournament, **params)
