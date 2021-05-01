# Changelog
All notable changes to this project will be documented in this file

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Unreleased]

### Added

### Changed

### Removed


## [Release v21.0.1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.0.1) - 2021-05-01

### Changed
- Changed Lidar field of view from 90 to 360 degrees
- Addresses the problem of robots firing like rocket:rocket: near the swamps in some environments.

## [Release v21.0.0](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.0.0) - 2021-04-20

### Changed
- Refactored version check function

## [Release v21.0.0 Beta-3](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.0.0_Beta-3) - 2021-04-12

### Added
- Cost checks to custom robots introduced

### Changed
- The budget limit for custom robots has been increased to 3000
- The maximum number of cameras for custom robots has been increased to 3

### Removed
- Removed temperature sensor from default robot

## [Release v21.0.0 Beta-2](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.0.0_Beta-2) - 2021-04-09

### Added
- Added the ability to configure the following settings for the simulator
    - Keep controller and robot files
    - Disable automatic LoP [#1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/issues/1)
- Added new sample worlds

### Changed
- Fixed map solving (Map bonus)
- History will no longer be rotated, it will be added
- Fix of score calculation (handling of decimal points)
- Fixed a problem that robot stuck at entrance of swamp/checkpoint with using default robot
- Fixed a problem where the rescue of a victim could be successful even if the robot was not completely stopped
- The stopping time duration required to score a victim was fixed to fit the rules
- Improved behaviour of the LoP button
- Fixed implementation of map bonuses
- You can no longer earn EB without identifying at least one victim
- Refactored the main supervisor
- Improved display items and handling in the history view
- Fixed the removal of robot when time is up
- Made the hazard map lighter in colour when found it
- Full implementation of map bonus

### Removed
- Removed setting of a detection API from robot0.wbo

## [Release v21.0.0 Beta-1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.0.0_Beta-1) - 2021-04-05
- First Beta release

[Unreleased]: https://gitlab.com/rcj-rescue-tc/erebus/erebus  
<!-- [Release v21.0.0 Beta-1]: URL HERE!!  -->
