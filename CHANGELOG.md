# Changelog
All notable changes to this project will be documented in this file.

## [Unreleased] - 4.0.0
### Added
- A changelog
- OfficialAPI: A way to iterate through paginated repsonses (i.e. search_clans, search_tournaments) using asynchronus generators.
- OfficialAPI: Tests for the pagination.
- Requirement: async_generator (For Python 3.5 support)
- Logging URL Requests
- Unit tests for async clients

### Changed
- Repsonses with a `.items` will simply be returned as a list [BREAKING]

### Fixed
- Client.close() now works if the client is async

### Removed
- `clashroyale.*.utils` is no longer in `__init__.py`


[Unreleased]: https://github.com/cgrok/clashroyalecompare/v4.0.0...HEAD
