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
from urllib.parse import urlencode

import aiohttp
import requests

from ..errors import (NotFoundError, NotResponding, ServerError, Unauthorized,
                      UnexpectedError, RatelimitError)
from .models import (Cards, Clan, ClanInfo, ClanWar, ClanWarLog, Battle, Cycle,
                     Player, Location, Tournament, rlist)
from .utils import API, SqliteDict, clansearch, tournamentsearch, crtag, keys, typecasted

from_timestamp = datetime.fromtimestamp


class Client:
    """A client that requests data from api.clashroyale.com. This class can
    either be async or non async.

    Parameters
    ----------
    token: str
        The api authorization token to be used for requests. https://developer.clashroyale.com/
    is_async: Optional[bool]
        Toggle for asynchronous/synchronous usage of the client.
        Defaults to False.
    error_debug: Optional[bool]
        Toggle for every method to raise ServerError to test error
        handling.
        Defaults to False.
    session: Optional[Session]
        The http (client)session to be used for requests. Can either be a
        requests.Session or aiohttp.ClientSession.
    timeout: Optional[int]
        A timeout for requests to the API, defaults to 10 seconds.
    url: Optional[str]
        A url to use instead of api.clashroyale.com/v1 (defaults to ``https://api.clashroyale.com/v1``)
        Only use this if you know what you are doing.
    cache_fp: Optional[str]
        File path for the sqlite3 database to use for caching requests,
        if this parameter is provided, the client will use its caching system.
    cache_expires: Optional[int]
        The number of seconds to wait before the client will request
        from the api for a specific route, this defaults to 10 seconds.
    table_name: Optional[str]
        The table name to use for the cache database. Defaults to 'cache'
    camel_case: Optional(bool)
        Whether or not to access model data keys in snake_case or camelCase,
        this defaults to False (use snake_case)
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
            'User-Agent': 'python-clashroyale-client (kyb3r/fourjr)'
        }
        self.cache_fp = options.get('cache_fp')
        self.using_cache = bool(self.cache_fp)
        self.cache_reset = options.get('cache_expires', 300)
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
            raise NotResponding()

    async def _wrap_coro(self, arg):
        return arg

    def request(self, url, timeout, refresh=False, **params):
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
            raise NotResponding()

    def _convert_model(self, data, cached, ts, model, resp):
        if isinstance(data, str):
            return data  # version endpoint, not feasable to add refresh functionality.
        if isinstance(data, list):  # extra functionality
            if all(isinstance(x, str) for x in data):  # endpoints endpoint
                return rlist(self, data, cached, ts, resp)  # extra functionality
            return [model(self, d, resp, cached=cached, ts=ts) for d in data]
        else:
            return model(self, data, resp, cached=cached, ts=ts)

    async def _aget_model(self, url, timeout, model=None, **params):
        try:
            data, cached, ts, resp = await self.request(url, timeout, **params)
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
            data, cached, ts, resp = self.request(url, timeout, **params)
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
        url = self.api.PLAYER + '/' + tag
        return self._get_model(url, Player, timeout)

    @typecasted
    def get_player_verify(self, tag: crtag, apikey: str, timeout=None):
        url = self.api.PLAYER + '/' + tag + '/verifytoken'
        return self._get_model(url, Player, timeout, method='POST', json={'token': apikey})

    @typecasted
    def get_player_battles(self, tag: crtag, timeout: int=None):
        url = self.api.PLAYER + '/' + tag + '/battlelog'
        return self._get_model(url, Battle, timeout)

    @typecasted
    def get_player_chests(self, tag: crtag, timeout: int=None):
        url = self.api.PLAYER + '/' + tag + '/upcomingchests'
        return self._get_model(url, Cycle, timeout)

    @typecasted
    def get_clan(self, tag: crtag, timeout: int=None):
        url = self.api.CLAN + '/' + tag
        return self._get_model(url, Clan, timeout)

    @typecasted  # Validate clan search parameters.
    def search_clans(self, **params: clansearch):
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.CLAN
        return self._get_model(url, ClanInfo, timeout, **params)

    @typecasted
    def get_clan_war(self, tag: crtag, timeout: int=None):
        url = self.api.CLAN + '/' + tag + '/currentwar'
        return self._get_model(url, ClanWar, timeout)

    @typecasted
    def get_clan_members(self, tag: crtag, **params: keys):
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.CLAN + '/' + tag + '/members'
        return self._get_model(url, ClanWarLog, timeout, **params)

    @typecasted
    def get_clan_war_log(self, tag: crtag, **params: keys):
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.CLAN + '/' + tag + '/warlog'
        return self._get_model(url, ClanWarLog, timeout, **params)

    @typecasted
    def get_tournament(self, tag: crtag, timeout=0):
        url = self.api.TOURNAMENT + '/' + tag
        return self._get_model(url, Tournament, timeout)

    @typecasted
    def search_tournaments(self, **params: tournamentsearch):
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        return self._get_model(self.api.TOURNAMENT, ClanInfo, timeout, **params)

    @typecasted
    def get_cards(self, timeout: int=None):
        return self._get_model(self.api.CARDS, Cards, timeout)

    @typecasted
    def get_location(self, location_id, timeout: int=None):
        url = self.api.LOCATIONS + '/' + str(location_id)
        return self._get_model(url, Location, timeout)

    @typecasted
    def get_all_locations(self, timeout: int=None):
        return self._get_model(self.API.LOCATIONS, Location, timeout)

    @typecasted
    def get_top_clans(self, location_id='global', **params: keys):
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.LOCATIONS + '/' + str(location_id) + '/rankings/clans'
        return self._get_model(url, ClanInfo, timeout, **params)

    @typecasted
    def get_top_clanwar_clans(self, location_id='global', **params: keys):
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.LOCATIONS + str(location_id) + '/rankings/clanwars'
        return self._get_model(url, ClanInfo, timeout, **params)

    @typecasted
    def get_top_players(self, location_id='global', **params: keys):
        timeout = params.get('timeout')
        try:
            del params['timeout']
        except KeyError:
            pass
        url = self.api.LOCATIONS + '/' + str(location_id) + '/rankings/players'
        return self._get_model(url, ClanInfo, timeout, **params)
