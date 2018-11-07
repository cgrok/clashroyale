.. currentmodule:: clashroyale

API Reference
=============

The following section outlines the API of :clashroyale: and how to access the
Official API and the unofficial RoyaleAPI.


OfficialAPI
-----------

.. autoclass:: clashroyale.official_api.Client
    :members:


Data Models
~~~~~~~~~~~
.. autoclass:: clashroyale.official_api.models.BaseAttrDict
    :members:

.. autoclass:: clashroyale.official_api.models.Refreshable
    :members:

.. autoclass:: clashroyale.official_api.models.PaginatedAttrDict
    :members:

.. autoclass:: clashroyale.official_api.models.Battle
    :members:

.. autoclass:: clashroyale.official_api.models.Cards
    :members:

.. autoclass:: clashroyale.official_api.models.Clan
    :members:

.. autoclass:: clashroyale.official_api.models.ClanInfo
    :members:

.. autoclass:: clashroyale.official_api.models.ClanWar
    :members:

.. autoclass:: clashroyale.official_api.models.ClanWarLog
    :members:

.. autoclass:: clashroyale.official_api.models.Constants
    :members:

.. autoclass:: clashroyale.official_api.models.Cycle
    :members:

.. autoclass:: clashroyale.official_api.models.Deck
    :members:

.. autoclass:: clashroyale.official_api.models.FullClan
    :members:

.. autoclass:: clashroyale.official_api.models.FullPlayer
    :members:

.. autoclass:: clashroyale.official_api.models.Location
    :members:

.. autoclass:: clashroyale.official_api.models.Member
    :members:

.. autoclass:: clashroyale.official_api.models.Player
    :members:

.. autoclass:: clashroyale.official_api.models.PlayerInfo
    :members:

.. autoclass:: clashroyale.official_api.models.Tournament
    :members:


RoyaleAPI
---------

.. autoclass:: clashroyale.royaleapi.Client
    :members:


Exceptions
----------

The following exceptions are thrown by the library.

.. autoexception:: RequestError

.. autoexception:: StatusError
    :members:

.. autoexception:: NotResponding
    :members:

.. autoexception:: NetworkError
    :members:

.. autoexception:: BadRequest

.. autoexception:: NotFoundError

.. autoexception:: ServerError

.. autoexception:: Unauthorized

.. autoexception:: NotTrackedError

.. autoexception:: RatelimitError

.. autoexception:: UnexpectedError

.. autoexception:: RatelimitErrorDetected
    :members:
