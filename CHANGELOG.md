# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [3.1.3] - 2025-06-13

### Added
- Introduced a static reply keyboard builder via `ReplyKeyboardMeta` for defining reply menus using class-style syntax.
- Added `carry_over` option to time selectors for automatic hour adjustment on minute overflow/underflow.
- Added support for custom labels on "Done" and "Back" buttons in time selector widgets.
- Included new examples demonstrating reply keyboards and updated time selector usage.
- Created [CHANGELOG.md](./CHANGELOG.md) to track versioned changes.
- Added version tags for releases.
- Added CI/CD workflow for automated PyPI publishing.

### Fixed
- Updated [pyproject.toml](pyproject.toml) to include only the `aiogramx` package.

### Changed
- Refactored internal codebase for improved readability and maintainability.


## [v3.1.2] - 2025-05-30

### Fixed
- Removed erroneous `await` call in a synchronous `Checkbox` method
- Fixed import issues in demo code

### Changed
- Cleaned up `WidgetBase` by removing debug print statements
- Improved type hints:
  - Generalized `lang` argument from `Literal[...]` to `str`
  - Soften type hint for `Checkbox.options` to reduce IDE false positives
- Corrected method signatures: converted incorrectly marked `async` methods to `sync`
- Added `lang` option support to `Paginator` for improved localization control

### Added
- Introduced a demo bot to illustrate basic usage
- Added development dependencies to `pyproject.toml` for easier contribution

### Documentation
- Updated `README.md` for clarity
- Added `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and issue/PR templates to guide contributors



## [v3.1.0] - 2025-05-28
### Added
- Implemented `Calendar` and `Checkbox` widgets
- Implemented `WidgetBase` and `WidgetMeta` classes as a base for widget creation.
- Introduced widgets with optional language-specific text lookup
- Added `CheckboxResult` return value for standalone mode in `process_cb`

### Changed
- Refactored time selector: renamed `time.py` to `time_selector.py` and improved structure/callback logic
- Improved `Calendar`, `Checkbox`, and `Paginator` modules for better UX, documentation, and localization
- Improved input validation, internal option handling, and code clarity in widgets
- Improved usage example code for the `Checkbox` widget
- Improved `examples/` folder with a setup guide and consistent naming
  - Introduced `config_example.py` for easier bot token configuration

### Documentation
- Revamped `README.md` with badges, quick links, clearer examples, and detailed feature descriptions
- Enhanced docstrings and inline code documentation across the core widget modules

### Localization
- Added emoji-enhanced warning messages and better language fallback support

### Other
- Updated `.gitignore` to exclude development artifacts

## [v3.0.0] - 2025-05-20
### Added
- Paginator:
    - Add `on_select` and `on_back` callback support
    - Add key based storage of Paginators (using LRUDict from flipcache)
    - Add callback query handler registrator method
    - Add docstrings for Paginator
    - Update `__init__` validators
    - Add examples in examples folder, as well as in README.md
    - Implement lazy loading
    - Add unique identifier for paginator
- Time selectors:
  - Add `TimeSelectorModern`
  - Add `TimeSelectorGrid`
- Others:
  - Add utility functions for key generation and inline button creation



