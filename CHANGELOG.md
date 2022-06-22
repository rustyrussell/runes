# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2022-06-22

### Added
 - to_str()/from_str() API for encoding Runes without base64.

## [0.4.0] - 2021-08-11

## Changed
 - empty field without hypen ignored by default (unless in values dict)

### Added
 - Callables in dict allow custom evaluation
 - id field parameters added to constructors for convenience
 - New examples for blacklisting and ratelimiting.

## [0.3.1] - 2021-08-02

## Fixed
 - copy() now correctly copies (original not modified when restrictions added!)

## [0.3] - 2021-08-01

## Changed
 - Punctuation is now allowed in field values; \ is the escape mechanism

### Added
 - Not equals operator (/) added.

## [0.2] - 2021-07-31

### Added

 - examples/decode.py: pretty print output into english phrases
 - Rune.copy() helper, and copy utils now work (eg. copy.deepcopy(Rune))
 - Simple check() and check_with_reason() routines for simplest usage.

## [0.1] - 2021-07-30

Initial release.
