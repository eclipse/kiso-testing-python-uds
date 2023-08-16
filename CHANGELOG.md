# Changelog
All notable changes to this project will be documented in this file.

## [3.0.4]

### Features
- ``Ubs``: add repsonse time and list of response pending times as attribute 

## [3.0.3]

### Features
- ``ResettableTimer``: add properties ``elapsedTime`` and ``remainingTime``
- ``CanTp``: replace polling with blocking queues
- ``CanTp``: add ``st_min`` attribute and ``encode_st_min`` method

## [3.0.2]

### Features
- ``UdsConfigTool``: handle parsing of dynamic response lengths in ODX files
- ``CanTp``: Make reception polling interval configurable through the ``polling_interval`` attribute 

### Changes
- ``CanTp``: log a warning instead of raising an error instead of any unexpected received message

### Bugfixes
- ``CanTp``: Fix padding of consecutive frames over CAN
- ``CanTp``: Avoid deletion of received CAN messages when sending a message

## [3.0.1]

## Bugfixes
- SecurityAccess service never created by ODX configuration due to a mis-migrated flag 

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
