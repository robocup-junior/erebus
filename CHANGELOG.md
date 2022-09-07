# Changelog
All notable changes to this project will be documented in this file

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Release v22.0.0](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v22.0.0) - 2022-09-07

### Added
- ✨: Added world selector
- ✨: Added a new warning within the swamp when Erebus detects that a team's controller may not be setting it's wheel velocities every time step.

### Changed
- ❗: Erebus must be run with Webots version 2022a. Download [here](https://github.com/cyberbotics/webots/releases/tag/R2022a).
- ❗: Old custom robot JSON files will no longer work and have to be recreated using the new robot customization v22.0.0
- ⚡️: Reworked internal code
- ⚡️: Updated code to align with [new Webots coordinate changes](https://github.com/cyberbotics/webots/wiki/How-to-adapt-your-world-or-PROTO-to-Webots-R2022a).
- ⚡️: Reworked how the swamp slows the robot
- 🐛: Obstacles not implemented properly

### Removed
- 🗑️: Unused obstacle code

### Extra notes

#### Swamp warning

A new warning message may appear when a robot stops in the swamp:

```
[EREBUS WARNING] Detected the robot stopped moving in a swamp. This could be due to not setting the wheel motor velocities every frame.
[EREBUS WARNING] See Erebus 22.0.0 changelog for more details.
```

Under some conditions, the robot can stop when entering the swamp if you're not setting the robot's wheel's velocities very time step. **Please note: Teams can be disqualified if their robot doesn't slow down when entering a swamp by avoiding the slow penalty in any way. For an easy fix, make sure you always update your robot's current wheel velocity every time step.** 

#### New coordinate changes

The changes to the coordinate system within Webots 2022a can be viewed [here](https://github.com/cyberbotics/webots/wiki/How-to-adapt-your-world-or-PROTO-to-Webots-R2022a), but as a simple summary:
> Before, Webots was using NUE as the global coordinate system and we switched it to be new ENU by default.  

> The object's axis system of Webots is now FLU (x-Forward, y-Left, z-Up).

We are continuing to use the NUE global coordinate system as we did before. However, internal Erebus code had to be changed to accommodate the new FLU object axis system change, therefore your team's code may experience axis sign (+/-) inversions in your sensor readings.

That being said, your team's **custom robot JSON files will have to be re-created** due to the changes to the custom robot generator to accommodate the new coordinate system using the new robot customization v22.0.0.

Since this is a large update to the erebus code base, there may be some bugs. Please feel free to create bug issues on the respective Gitlab repos to help us fix any issues:
- [Erebus issues](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/issues)
- [Robot Customization issue page](https://gitlab.com/rcj-rescue-tc/erebus/robot-customisation/-/issues)

## [Release v21.2.1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.2.1) - 2021-06-11

### Changed
- 🐛: The map answer generator did not work correctly under some conditions

## [Release v21.2.0](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.2.0) - 2021-06-02

### Added
- ✨: Reflects the loading status of the controller program and custom robots in the GUI after reset it

### Changed
- ⚡️: Make objects in the world unpickable
- 🐛: Reset the camera location when LoP occurs
- 🐛: Controller remove function
- 🐛: The log export function does not work properly
- ⚡️: Reduce the frequency of Physics Issues
- 🐛: The colour of the load button does not change even after loading the custom robot
- ⚡️:  Make the robot model simpler

### Removed
- 🔇: Some unnessesary logging
- 🗑️: Unused supervisor code
- 🔥: World generator

## [Release v21.1.2](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.1.2) - 2021-05-21

### Added
- ✨: Added the ability to request LoPs autonomously
- ✨: Added the ability to request game information (score and time remaining) autonomously

### Removed
- 🗑️: "using detection api" flag from ther default robot

## [Release v21.1.1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.1.1) - 2021-05-16

### Added
- 🎨: Display platform version at the start of recording

### Changed
- 🐛: Position of the spotlight for the colour sensor on custom robots
- 🐛: UNLOAD button for custom robot does not work under some conditions
- 🐛: Disable the custom robot button(LOAD/UNLOAD) at the start of the game

## [Release v21.1.0](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.1.0) - 2021-05-08

### Added
- Automatic adjustment of the camera angle(viewpoint)
- Ability to record games
- Give-up button

### Changed
- Fixed missing bounding objects for curved walls

## [Release v21.0.1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.0.1) - 2021-05-01

### Changed
- Changed Lidar field of view from 90 to 360 degrees
- Addresses the problem of robots firing like rocket :rocket: near the swamps in some environments.

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
