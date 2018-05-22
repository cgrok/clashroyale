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

from box import Box, BoxList
from .utils import API

class BaseAttrDict:
    '''This class is the base class for all models, its a
    wrapper around the `python-box`_ which allows access to data
    via dot notation, in this case, API data will be accessed
    using this class. This class shouldnt normally be used by the
    user since its a base class for the actual models returned from
    the client.

    .. _python-box: https://github.com/cdgriffith/Box

    Examples
    --------

    Accessing data via dot notation: ::

        sample_data = {
            "stats": {
                "maxTrophies": 5724,
                "favoriteCard": {
                    "name": "P.E.K.K.A"
                        }
                    }
                }

        model = SomeModel(client, sample_data)
        x = sample_data['stats']['maxTrophies']
        # Same as
        x = model['stats']['max_trophies']
        # Same as
        x = model.stats.max_trophies

    This functionality allows this library to present API
    data in a clean dynamic way.

    Attributes
    ----------
    raw_data: dict
        The raw data in the form of a dictionary being used
    cached: bool
        Whether or not the data being used is cached data from
        the cache database.
    last_updated: datetime.datetime
        When the data which is currently being used was last updated.
    response: requests.Response or aiohttp.ClientResponse or None
        Response object containing headers and more information. Returns None if cached
    '''
    def __init__(self, client, data, response, cached=False, ts=None):
        self.client = client
        self.response = response
        self.from_data(data, cached, ts)

    def from_data(self, data, cached, ts):
        self.cached = cached
        self.last_updated = ts
        self.raw_data = data
        if isinstance(data, list):
            self._boxed_data = BoxList(
                data, camel_killer_box=not self.client.camel_case
                )
        else:
            self._boxed_data = Box(
                data, camel_killer_box=not self.client.camel_case
                )
        return self

    def __getattr__(self, attr):
        try:
            return getattr(self._boxed_data, attr)
        except AttributeError:
            try:
                return super().__getattr__(attr)
            except AttributeError:
                return None

    def __getitem__(self, item):
        try:
            return getattr(self._boxed_data, item)
        except AttributeError:
            raise KeyError('No such key: {}'.format(item))

    def __repr__(self):
        _type = self.__class__.__name__
        return "<{}: {}>".format(_type, self.raw_data)

class FullClan(BaseAttrDict):
    def get_clan(self):
        '''(a)sync function to return clan.'''
        if not self.clan.get('tag'):
            raise ValueError('This player does not have a clan.')
        return self.client.get_clan(self.clan.tag)

class FullPlayer(BaseAttrDict):
    def get_profile(self):
        return self.client.get_player(self.tag)

    get_player = get_profile # consistancy

class Refreshable(BaseAttrDict):
    '''Mixin class for re requesting data from
    the api for the specific model.
    '''
    def refresh(self):
        '''(a)sync refresh the data.'''
        if self.client.is_async:
            return self._arefresh()
        data, cached, ts = self.client.request(self.url, refresh=True)
        return self.from_data(data, cached, ts)

    async def _arefresh(self):
        data, cached, ts = await self.client.request(self.url, refresh=True)
        return self.from_data(data, cached, ts)

    @property
    def url(self):
        endpoint = self.__class__.__name__.lower()
        return '{}/{}/{}'.format(API.BASE, endpoint, self.tag)

class Player(Refreshable, FullClan):
    '''A clash royale player model.'''
    pass

class Member(FullPlayer):
    '''A clan member model, 
    keeps a reference to the clan object it came from.
    '''
    def __init__(self, clan, data, response):
        self.clan = clan
        super().__init__(clan.client, data, response)

class PlayerInfo(FullClan, FullPlayer):
    '''Brief player model, 
    does not contain full data, non refreshable.
    '''
    pass

class ClanInfo(FullClan):
    '''Brief clan model, 
    does not contain full data, non refreshable.
    '''
    pass

class Clan(Refreshable):
    '''A clash royale clan model, full data + refreshable.
    '''
    def from_data(self, data, cached, ts):
        super().from_data(data, cached, ts)
        self.members = [Member(self, m, self.response) for m in data.get('members', [])]

class ClanHistory(Refreshable):
    '''A history that RoyaleAPI saves'''
    pass

class ClanWar(Refreshable):
    '''Info about the current clan war'''
    pass

class ClanWarLog(Refreshable):
    '''A log of the past clan wars'''
    pass

class Battle(BaseAttrDict):
    '''Clash Royale Battle'''
    pass

class Cycle(BaseAttrDict):
    '''Clash Royale chest cycle'''
    pass

class Constants(Refreshable):
    '''Clash Royale constants storage'''
    pass

class Tournament(Refreshable):
    '''Represents a clash royale tournament.'''
    pass

class Deck(Refreshable):
    '''Represents a clash royale deck.'''
    pass

class AuthStats(Refreshable):
    '''Represents client request statistics'''
    pass

class rlist(list, Refreshable):
    def __init__(self, client, data, cached, ts):
        self.client = client
        self.from_data(data, cached, ts)

    def from_data(self, data, cached, ts):
        self.cached = cached
        self.last_updated = ts
        super().__init__(data)
        return self

    @property
    def url(self):
        return '{}/endpoints'.format(API.BASE)
