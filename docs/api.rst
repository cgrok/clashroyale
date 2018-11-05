.. currentmodule:: clashroyale

API Reference
=============

The following section outlines the API of :clashroyale: and how to access the
Official API and the unofficial RoyaleAPI.


OfficialAPI
-----------

.. autoclass:: clashroyale.official_api.Client
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
