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
from .utils import _to_snake_case, API

class BaseAttrDict:
    '''Uses a python-box for data storage, this class 
    is used as a base class so we can easily add extra 
    methods without interfering with the box itself.
    '''
    def __init__(self, client, data, cached=False, ts=None):
        self.client = client
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
            return super().__getattr__(attr)

    def __repr__(self):
        _type = self.__class__.__name__
        return f'<{_type}: {self}>'

    def __str__(self):
        try:
            return f'{self.name} (#{self.tag})'
        except AttributeError:
            return super().__str__()
    
class FullClan:
    def get_clan(self):
        '''(a)sync function to return clan.'''
        if not self.clan.get('tag'):
            raise ValueError('This player does not have a clan.')
        return self.client.get_clan(self.clan.tag)

class FullPlayer:
    def get_profile(self):
        return self.client.get_player(self.tag)

    get_player = get_profile # consistancy

class Refreshable:
    '''Mixin class for re requesting data from 
    the api for the specific model.
    '''
    def refresh(self):
        '''(a)sync refresh the data.'''
        if self.client.is_async:
            return self._arefresh()
        else:
            data, cached, ts = self.client.request(self.url, refresh=True)
            return self.from_data(data, cached, ts)

    async def _arefresh(self):
        data, cached, ts = await self.client.request(self.url, refresh=True)
        return self.from_data(data, cached, ts)

    @property
    def url(self):
        endpoint = self.__class__.__name__.lower()
        return f'{API.BASE}/{endpoint}/{self.tag}'

class Player(BaseAttrDict, Refreshable, FullClan):
    '''A clash royale player model.'''
    pass

class Member(BaseAttrDict, FullPlayer):
    '''A clan member model, 
    keeps a reference to the clan object it came from.
    '''
    def __init__(self, clan, data):
        self.clan = clan
        super().__init__(clan.client, data)

class PlayerInfo(BaseAttrDict, FullClan, FullPlayer):
    '''Brief player model, 
    does not contain full data, non refreshable.
    '''
    pass

class ClanInfo(BaseAttrDict, FullClan):
    '''Brief clan model, 
    does not contain full data, non refreshable.
    '''
    pass

class Clan(BaseAttrDict, Refreshable):
    '''A clash royale clan model, full data + refreshable.
    '''
    def from_data(self, data):
        super().from_data(data)
        self.members = [Member(self, m) for m in data['members']]

class Constants(BaseAttrDict, Refreshable):
    '''Clash Royale constants storage'''
    pass

class Tournament(BaseAttrDict, Refreshable):
    '''Represents a clash royale tournament.'''
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
        return f'{API.BASE}/endpoints'
