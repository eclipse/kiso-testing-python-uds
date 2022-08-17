# Changelog
All notable changes to this project will be documented in this file.

## Current version

## [3.0.0]

## Refactor
 - remove unused code (Lin/Tests folders, CANConnection...)
 - create new module config.py to handle/store isotp and uds layer configuration
 - remove CreatesUdsConnection and replace it by UdsTool object
 - move overwrite_transmit_method and overwrite_receive_method method from CanTp to UDS object

## [2.1.1]

### Bugfixes
- Restore support for other int sequences in fillArray

## [2.1.0]

### Features
- Add support for ISO TP for server simulation
- Add possibility to change the CAN TP padding pattern

### Refactor
- Run code formatting tools

## [1.2.0]

### Features
- Added overwrite_transmit_method in CanTp to use external transmission methods

## [1.1.0] - 2019-08-14

### Features
- Added socket can interface for linux support, tested with MCP2515 shield
- Added UDS retry on response pending negative response code

### Changed
- Changed config path to make it OS agnostic for Linux support. Tested on Ubuntu 18.04 and Raspbian Stretch
