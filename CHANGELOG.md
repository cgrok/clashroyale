# Changelog
All notable changes to this project will be documented in this file.

## 06/11/2019

### Fixed
- RoyaleAPI: Updated the endpoints URLs to match the latest version of the API. This affects all endpoints for players and clans.

## [4.0.2] - 14/04/2019

### Added
- RoyaleAPI: Added `/top/war/{location_id}` end point

## [4.0.1] - 17/11/2018

### Added
- RuntimeError if you were calling the wrong method (iter/aiter) on an inappropriate client (i.e. async client -> iter/blocking client -> aiter)

## [4.0.0] - 11/11/2018
### Added
- OfficialAPI: A way to iterate through paginated repsonses (i.e. search_clans, search_tournaments) using asynchronus generators.
- OfficialAPI: Tests for the pagination.
- Requirement: async_generator (For Python 3.5 support)
- Logging URL Requests
- Unit tests for async clients

### Changed
- Repsonses with a `.items` will simply be returned as a list
- `OfficialAPI.get_cards()` -> `OfficialAPI.get_all_cards()` (Deprecated till v4.1.0)
- OfficialAPI: `before` and `after` are no longer valid parameters as pagination is natively supported

### Fixed
- Client.close() now works if the client is async
- function(timeout) would sometimes not work

### Removed
- `clashroyale.*.utils` are no longer in `__init__.py`
- Individual models for all data types aren't created anymore


[Unreleased]: https://github.com/cgrok/clashroyalecompare/v4.0.0...HEAD
[4.0.1]: https://github.com/cgrok/clashroyale/compare/v4.0.0...v4.0.1
[4.0.0]: https://github.com/cgrok/clashroyale/compare/6c9215a...v4.0.0
