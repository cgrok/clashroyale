from async_generator import async_generator, yield_
from box import Box, BoxList

from .utils import API

API_ENDPOINTS = API('https://api.clashroyale.com/v1')


class BaseAttrDict:
    """This class is the base class for all models, its a
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
    """
    def __init__(self, client, data, response, cached=False, ts=None):
        self.client = client
        self.response = response
        self.from_data(data, cached, ts, response)

    def from_data(self, data, cached, ts, response):
        self.cached = cached
        self.last_updated = ts
        self.raw_data = data
        self.response = response
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
        """(a)sync function to return clan."""
        if not self.clan.get('tag'):
            raise ValueError('This player does not have a clan.')
        return self.client.get_clan(self.clan.tag)


class FullPlayer(BaseAttrDict):
    def get_player(self):
        return self.client.get_player(self.tag)


class Refreshable(BaseAttrDict):
    """Mixin class for re requesting data from
    the api for the specific model.
    """
    def refresh(self):
        """(a)sync refresh the data."""
        if self.client.is_async:
            return self._arefresh()
        data, cached, ts, response = self.client._request(self.response.url, timeout=None, refresh=True)
        return self.from_data(data, cached, ts, response)

    async def _arefresh(self):
        data, cached, ts, response = await self.client._request(self.response.url, timeout=None, refresh=True)
        return self.from_data(data, cached, ts, response)


class PaginatedAttrDict(BaseAttrDict):
    """Mixin class to allow for the paginated
    endpoints to be iterable
    """
    def __init__(self, client, data, response, model, cached=False, ts=None):
        self.cursor = {'after': data['paging']['cursors'].get('after'), 'before': data['paging']['cursors'].get('before')}
        self.client = client
        self.response = response
        self.model = model
        self.raw_data = [self.model(self.client, d, response, cached=cached, ts=ts) for d in data['items']]

    def __len__(self):
        return len(self.raw_data)

    def __getattr__(self, attr):
        try:
            return self.raw_data[attr]
        except AttributeError:
            try:
                return super().__getattr__(attr)
            except AttributeError:
                return None

    def __getitem__(self, item):
        try:
            return self.raw_data[item]
        except AttributeError:
            raise KeyError('No such key: {}'.format(item))

    @async_generator
    async def __aiter__(self):
        while True:
            index = 0
            for _ in range(index, len(self.raw_data)):
                await yield_(self.raw_data[index])
                index += 1
            if not await self.update_data():
                break

    def __iter__(self):
        while True:
            index = 0
            for _ in range(index, len(self.raw_data)):
                yield self.raw_data[index]
                index += 1
            if not self.update_data():
                break

    async def _aupdate_data(self):
        if self.cursor['after']:
            data, cached, ts, response = await self.client._request(self.response.url, timeout=None, after=self.cursor['after'])
            self.cursor = {'after': data['paging']['cursors'].get('after'), 'before': data['paging']['cursors'].get('before')}
            self.raw_data += [self.model(self.client, d, response, cached=cached, ts=ts) for d in data['items']]
            return True

        return False

    async def _aall_data(self):
        while await self.update_data():
            pass

    def to_json(self):
        return self.raw_data

    def update_data(self):
        """Adds the NEXT data in the raw_data dictionary.
        Returns True if data is added.
        Returns False if data is not added"""
        if self.client.is_async:
            return self._aupdate_data()

        if self.cursor['after']:
            data, cached, ts, response = self.client._request(self.response.url, timeout=None, after=self.cursor['after'])
            self.cursor = {'after': data['paging']['cursors'].get('after'), 'before': data['paging']['cursors'].get('before')}
            self.raw_data += [self.model(self.client, d, response, cached=cached, ts=ts) for d in data['items']]
            return True

        return False

    def all_data(self):
        """Loops through and adds all data to the raw_data

        This has a chance to get 429 RatelimitError"""
        if self.client.is_async:
            return self._ato_list()

        while self.update_data():
            pass


class Player(Refreshable, FullClan):
    """A clash royale player model."""
    pass


class Member(FullPlayer):
    """A clan member model,
    keeps a reference to the clan object it came from.
    """
    def __init__(self, clan, data, response):
        self.clan = clan
        super().__init__(clan.client, data, response)


class PlayerInfo(FullClan, FullPlayer):
    """Brief player model,
    does not contain full data, non refreshable.
    """
    pass


class ClanInfo(FullClan):
    """Brief clan model,
    does not contain full data, non refreshable.
    """
    pass


class Clan(Refreshable):
    """A clash royale clan model, full data + refreshable."""
    def from_data(self, data, cached, ts, response):
        super().from_data(data, cached, ts, response)
        self.members = [Member(self, m, self.response) for m in data.get('member_list', [])]


class ClanWar(Refreshable):
    """Info about the current clan war"""
    pass


class ClanWarLog(Refreshable):
    """A log of the past clan wars"""
    pass


class Battle(BaseAttrDict):
    """Clash Royale Battle"""
    pass


class Cycle(BaseAttrDict):
    """Clash Royale chest cycle"""
    pass


class Tournament(Refreshable):
    """Represents a clash royale tournament."""
    pass


class Deck(Refreshable):
    """Represents a clash royale deck."""
    pass


class Cards(Refreshable):
    """Represents card data"""
    pass


class Location(Refreshable):
    """Represents location data"""
    pass


class Constants(BaseAttrDict):
    """Clash Royale constants storage"""
    pass


class rlist(list, Refreshable):
    def __init__(self, client, data, cached, ts, response):
        self.client = client
        self.from_data(data, cached, ts, response)

    def from_data(self, data, cached, ts, response):
        self.cached = cached
        self.last_updated = ts
        self.response = response
        super().__init__(data)
        return self

    @property
    def url(self):
        return '{}/endpoints'.format(API_ENDPOINTS.BASE)
