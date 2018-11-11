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
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.Refreshable
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.PaginatedAttrDict
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.PartialClan
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.PartialPlayer
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.PartialPlayerClan
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.Member
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.FullPlayer
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.FullClan
    :members:
    :inherited-members:

.. autoclass:: clashroyale.official_api.models.rlist
    :members:
    :inherited-members:


RoyaleAPI
---------

.. autoclass:: clashroyale.royaleapi.Client
    :members:


Data Models
~~~~~~~~~~~
.. autoclass:: clashroyale.royaleapi.models.BaseAttrDict
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.Refreshable
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.PartialTournament
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.PartialClan
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.PartialPlayer
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.PartialPlayerClan
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.Member
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.FullPlayer
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.FullClan
    :members:
    :inherited-members:

.. autoclass:: clashroyale.royaleapi.models.rlist
    :members:
    :inherited-members:


Exceptions
----------

The following exceptions are thrown by the library.

.. autoexception:: RequestError
    :members:

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
