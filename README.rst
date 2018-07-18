clashroyale
===========

.. image:: https://img.shields.io/pypi/v/clashroyale.svg
   :alt: PyPi


This library is currently an (a)sync wrapper for
https://royaleapi.com and the official Clash Royale API with
great functionality.

Installation
============

.. code-block:: python

    pip install clashroyale

Documentation
============

How to use
----------

1. Install the pip package ``pip install clashroyale``
2. Import the module ``import clashroyale``
3. Get a RoyaleAPI Developer Key, instructions `here`_
4. Initiate a client

   -  Blocking - ``client = clashroyale.RoyaleAPI(THEDEVKEY)``
   -  Async - ``client = clashroyale.RoyaleAPI(THEDEVKEY, is_async=True)``

5. Now you can call the `methods`_ to access the API!

Methods
-------

.. raw:: html

   <!--
   for n, i in enumerate(a):
       func = getattr(clashroyale.Client, i)
       print(f'{n+1}. {i}{str(inspect.signature(func)).replace("self, ", "").replace("<function crtag at 0x00000247BF669C80>", " crtag").replace("<function keys at 0x00000247BF669620>", " keys").replace("<function clansearch at 0x00000247BF669488>", " clansearch").replace("<function tournamentsearch at 0x00000247BF669510>", " tournamentsearch").replace("self", "")}')
   -->

1.  ``get_auth_stats(**params: keys)``
2.  ``get_clan(*tags: crtag, **params: keys)``
3.  ``get_clan_battles(*tags: crtag, **params: keys)``
4.  ``get_clan_history(*tags: crtag, **params: keys)``
5.  ``get_clan_tracking(*tags: crtag, **params: keys)``
6.  ``get_clan_war(tag: crtag, **params: keys)``
7.  ``get_clan_war_log(tag: crtag, **params: keys)``
8.  ``get_clans(*tags: crtag, **params: keys)``
9.  ``get_constants(**params: keys)``
10. ``get_endpoints()``
11. ``get_known_tournaments(**params: keys)``
12. ``get_open_tournaments(**params: keys)``
13. ``get_player(*tags: crtag, **params: keys)``
14. ``get_player_battles(*tags: crtag, **params: keys)``
15. ``get_player_chests(*tags: crtag, **params: keys)``
16. ``get_players(*tags: crtag, **params: keys)``
17. ``get_popular_clans(**params: keys)``
18. ``get_popular_decks(**params: keys)``
19. ``get_popular_players(**params: keys)``
20. ``get_popular_tournaments(**params: keys)``
21. ``get_top_clans(country_key='', **params: keys)``
22. ``get_top_players(country_key='', **params: keys)``
23. ``get_tournament(tag: crtag, **params: keys)``
24. ``get_tracking_clans()``
25. ``get_version()``
26. ``search_clans(**params: clansearch)``
27. ``search_tournaments(**params: tournamentsearch)``

Access
------

| You should access the data via dot notation and snake_case, example:
| Assuming `this`_ is the data returned

.. code:: py

   import clashroyale

   client = clashroyale.RoyaleAPI(SECRETDEVKEY)

   chests = client.get_player_chests('2P0LYQ')
   print(type(chests.upcoming))
   print(type(chests.super_magical))

The output should be

::

   list
   int

Client
------

::

   A client that requests data from royaleapi.com. This class can
   either be async or non async.
   Parameters
   ----------
   token: str
       The api authorization token to be used for requests.
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

Errors
------

`Source`_

| `RequestError`_
| Base error class
| `StatusError`_
| Base error class for all errors that actually do a request and get a
  response
|
| `NotResponding`_
| Raised if timeout exceeds timeout provided on Client
  init (default: 10)
| `NotFoundError`_
| Raised if a 404 status code (or 400) is returned,
  usually a player/clan not found. (Special case: 400 error code can be
  returned if the Developer Key is on the wrong version)
| `ServerError`_
| Raised if a status code of more than 500 is returned,
  most of the time it’s a Cloudflare error page returned
|  `Unauthorized`_
| Raised if a 401 status code is returned, usally if
  the developer key is invalid
| `NotTrackedError`_
| Raised if a 417
  status code is returned, usually the clan is not being tracked and you
  are requesting a ``history`` endpoint

| `RatelimitError`_
| Raised if a 429 status code is returned, usually
  you have gone past your ratelimit, cool down!
| `RatelimitErrorDetected`_
| Raised if according to calculations, you
  will go past your ratelimit and the request **is not sent**.

Misc
====

If you have any clash royale related code you would like to share, we
could incorporate it into this library since its name is very generic,
i.e. it refers to the game as a whole.

Tests
=====

Follow the instructions in ``test/config.yaml``

.. _Source: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L72-L79
.. _RequestError: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L25-L27
.. _StatusError: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L29-L43
.. _NotResponding: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L45-L50
.. _NotFoundError: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L52-L54
.. _ServerError: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L56-L58
.. _Unauthorized: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L60-L62
.. _NotTrackedError: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L64-L66
.. _RatelimitError: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L68-L70
.. _RatelimitErrorDetected: https://github.com/cgrok/clashroyale/blob/master/clashroyale/errors.py#L68-L70
.. _here: https://docs.royaleapi.com/#/authentication?id=generating-new-keys
.. _methods: #methods
.. _this: https://gist.github.com/fourjr/1354377b85c41a86961e54c06554b163#file-get_player_chests-2p0lyq-json
