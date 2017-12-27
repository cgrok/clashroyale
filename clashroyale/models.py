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
import json
from os import path
from . import core
from box import Box, BoxList
import re

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')

def _to_snake_case(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()

class BaseAttrDict:
    def __init__(self, client, data):
        self.client = client
        self.from_data(data)
        
    def from_data(self, data):
        self.raw_data = data
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
        _type = self.__class__.__name__.title()
        return f'<{_type}: {self}>'

    def __str__(self):
        try:
            return f'{self.name} (#{self.tag})'
        except AttributeError:
            return super().__str__()

class Refreshable:
    def refresh(self):
        '''(a)sync refresh the data.'''
        client = self.client
        if client.is_async:
            return self._arefresh()
        else:
            data = client.request(self.url)
            return self.from_data(data)

    async def _arefresh(self):
        client = self.client
        data = await client.request(self.url)
        return self.from_data(data)

    @property
    def url(self):
        endpoint = self.__class__.__name__.lower()
        return f'{self.client.base}/{endpoint}/{self.tag}'


class Player(BaseAttrDict, Refreshable):
    # TODO: Badge URL
    def get_clan(self):
        '''(a)sync function to return clan.'''
        if not self.clan.get('tag'):
            raise ValueError('This player does not have a clan.')
        return self.client.get_clan(self.clan.tag)

class Member(BaseAttrDict):
    def __init__(self, clan, data):
        self.clan = clan
        super().__init__(clan.client, data)

    def get_profile(self):
        '''Returns the full player object corresponding to the member.'''
        return self.client.get_player(self.tag)

class Clan(BaseAttrDict, Refreshable):
    # TODO: Badge URL
    def from_data(self, data):
        super().from_data(data)
        self.members = [Member(self, m) for m in data['members']]

class Arena(BaseAttrDict):
    def __str__(self):
        return self.name

    @property
    def image_url(self):
        return "http://api.cr-api.com" + self.image_url


class Constants(BaseAttrDict, Refreshable):
    # TODO: Special cases
    pass


# NOTE: Not done
# TODO: Documentation
