'''
MIT License

Copyright (c) 2017 kyb3r

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
'''

import asyncio
import json

import aiohttp
import requests

from .models import Player, Clan, PlayerInfo, ClanInfo, Constants, Tournament
from .errors import NotFoundError, ServerError, NotResponding, Unauthorized
from .utils import Endpoints, typecasted, crtag, clansearch

class Client:
    '''Represents an async client connection to cr-api.com

    Parameters
    ----------
    token: str
        The api authorization token to be used for requests.
    is_async: bool
        Toggle for asynchronous/synchronous usage of the client.
        Defaults to False
    session: (requests.Session, aiohttp.ClientSession)
        The http session to be used for requests
    timeout: int
        A timeout for requests to the API, defaults to 10 seconds.
    camel_case: bool
        Whether or not to access keys in snake_case or camelCase
    '''

    get_players = get_player
    get_clans = get_clan

    def __init__(self, token, session=None, timeout=10, is_async=False, camel_case=False):
        self.token = token
        self.is_async = is_async
        self.timeout = timeout
        self.session = session or (aiohttp.ClientSession() if is_async else requests.Session())
        self.camel_case = camel_case
        self.headers = {
            'auth': token,
            'user-agent': 'python-clashroyale (kyb3r)'
            }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self.session.close()
    
    def __repr__(self):
        return f'<ClashRoyaleClient async={self.is_async}>'

    def close(self):
        self.session.close()
    
    def _raise_for_status(self, resp, text):
        try:
            data = json.loads(text)
        except:
            data = text
        code = getattr(resp, 'status', getattr(resp, 'status_code'))
        if 300 > code >= 200: # Request was successful
            return data
        if code == 401: # Unauthorized request - Invalid token
            raise Unauthorized(resp, data) 
        if code == 404: # Tag not found
            raise NotFoundError(resp, data)
        if code > 500: # Something wrong with the api servers :(
            raise ServerError(resp, data)

    async def _arequest(self, url, **params):
        try:
            async with self.session.get(url, timeout=self.timeout, headers=self.headers, params=params) as resp:
                return self._raise_for_status(resp, await resp.text())
        except asyncio.TimeoutError:
            raise NotResponding()
    
    def request(self, url, **params):
        if self.is_async:
            return self._arequest(url, **params)
        try:
            resp = self.session.get(url, timeout=self.timeout, headers=self.headers, params=params)
            return self._raise_for_status(resp, resp.text)
        except requests.Timeout:
            raise NotResponding()

    async def _aget_model(self, url, model, **params):
        data = await self.request(url, **params)

        if isinstance(data, list):
            return [model(self, c) for c in data]
        else:
            return model(self, data)

    def _get_model(self, url, model, **params):
        if self.is_async:
            return self._aget_model(url, model, **params)

        data = self.request(url, **params)

        if isinstance(data, list):
            return [model(self, c) for c in data]
        else:
            return model(self, data)

    @typecasted()
    def get_tournament(self, tag: crtag):
        url = Endpoints.TOURNAMENT + '/' + tag
        return self._get_model(url, Tournament)
    
    @typecasted()
    def get_player(self, *tags: crtag):
        url = Endpoints.PLAYER + '/' + ','.join(tags)
        return self._get_model(url, Player)
    
    @typecasted()
    def get_clan(self, *tags: crtag):
        url = Endpoints.CLAN + '/' + ','.join(tags)
        return self._get_model(url, Clan)

    @typecasted()
    def search_clans(self, **params: clansearch):
        return self._get_model(Endpoints.SEARCH, ClanInfo, **params)

    def get_constants(self):
        return self._get_model(Endpoints.CONSTANTS, Constants)

    def get_version(self):
        return self.request(Endpoints.VERSION)

    def get_endpoints(self):
        return self.request(Endpoints.ENDPOINTS)

    def get_top_clans(self, country_key=None):
        url = Endpoints.TOP + '/clans/' + (country_key or '')
        return self._get_model(url, ClanInfo)

    def get_top_players(self, country_key=None):
        url = Endpoints.TOP + '/players/' + (country_key or '')
        return self._get_model(url, PlayerInfo)

    def get_popular_clans(self):
        url = Endpoints.POPULAR + '/clans'
        return self._get_model(url, Clan)

    def get_popular_players(self):
        url = Endpoints.POPULAR + '/players'
        return self._get_model(url, PlayerInfo)