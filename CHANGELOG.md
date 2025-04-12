# Changelog
All notable changes to this project will be documented in this file

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## [Release v25.0.0](https://github.com/robocup-junior/erebus/releases/tag/v25.0.0) - 2025-04-12
TBU

## [Release v24.1.0](https://github.com/robocup-junior/erebus/releases/tag/v24.1.0) - 2024-07-15

### Changed

- Updated the remote controller tooltip help link to now point to the [wiki](https://erebus.rcj.cloud/docs/tutorials/remotecontroller/).

### Fixed

- Fixed a bug where generated robots would ignore custom names for Lidar and Accelerometer sensors.
  - **This may cause errors in your code so please double check your custom robot sensor names.**
- Fixed a bug where UI signals to the Erebus client could crash on decoding.
- Fixed a bug where the supervisor would award infinite points for the mapping bonus. Thanks @MasterOfRespawn.
- Fixed `MapScorerExample.py` having `'20'` characters for room 4 instead of `'*'`.

## [Release v24.0.0](https://github.com/robocup-junior/erebus/releases/tag/v24.0.0) - 2024-04-06

> Please note this version only works with Webots R2023b, please update your Webots client before using this version.

**New v24 versions of the [world generator](https://osaka.rcj.cloud/service/editor/simulation/2024) and [robot customizer](https://v24.robot.erebus.rcj.cloud/) are intended to be used along side this new client update.**

### Added

- Added real-world timer info to the "game info" data from the supervisor. 
  - Previously, the received data packet was in the form `char float int` - "G", game score, remaining time (e.g. `G 15 100`)
  - The received data is now in the form `char float int int` - "G", game score, remaining time, remaining real world time (e.g. `G 15 100 50`)
- Added support to run controllers within docker containers (**Note: This may become the official way to run controllers for international competitions, so please familiarise yourself with this**)
  - An input field in the web UI is used to input the local directory of your docker project containing a `Dockerfile`.
  - Pressing the run docker button next to the play button will build and run your controller within a docker container. **Please note any GUI components (e.g. `cv2.imshow`) will not work**
  - For more information about running controllers in docker containers, see this the [dockerfiles](https://github.com/robocup-junior/erebus-dockerfiles) repository
- Added preview thumbnails to the world selection UI
- Added a settings option to keep the remote controller toggled
- Added a settings option to enable debug output to the console
- Added a favicon to the Erebus web UI
- Added a link to the changelog in the Erebus settings UI
- Added new Erebus automated tests and `.Tests.wbt` world.
  - Automated tests can now only be run with this world, and isn't designed to be used as a normal competition world.
- Added debug log file saving

### Changed

- Converted worlds to be compatible with Webots R2023b. Erebus v24.0.0 must be run with Webots R2023b, download it [here](https://github.com/cyberbotics/webots/releases/tag/R2023b).
- Reworked swamps
  - Swamps no longer slow, instead multiplies the game's timer countdown rate by 5.0x.
- Reworked hazard/victim detection logic
  - Detection is now based on the nearest victim to the sent estimated score (previously, this was arbitrary if two victims were both within valid detection range)
  - The semi-circle detection area logic has been reworked. Previously this was calculated at fixed 90° intervals, corresponding to the 4 different wall angles a victim could face. However, this didn't work well for complex wall regions (curved or in room 4). The semi-circle detection area is now based on the surface normal of the hazard/victim, allowing for more accurate detection regions. See the diagram below for more details (for illustration purposes only):
<img alt="Detection example" src="/docs/images/2024_detection_example.png" width=50%/>

- Changed map submission legend.
  - Connection tiles: Changed to lower case letters. Passages from 1 to 2 as 'b', 1 to 3 as 'y', 1 to 4 as 'g', 2 to 3 as 'p', 2 to 4 as 'o' and 3 to 4 as 'r' (as per 2024 rules).
  - Area 4: Changed from `20` to `*`
- Implemented new robot customiser rules to specify camera resolution. 
  - New camera pixel counts cost different amounts: `32: 0, 40: 0, 64: 100, 128: 200, 256: 300`. Costs are applied for both width and height. For example, creating a camera with width = 256, height = 128 will cost `300 + 200 = 500`.
- Robots can now exit the world regardless of world position, to align with the official rules
- Game log scores are now rounded to two decimal places
- Improved robot history event descriptions
- Improved debug console logging
- Updated `MapScorerExample.py` example controller to work with all supplied example worlds
- Updated documentation and code style for a majority of the code base

### Fixed

- Moved black-hole tiles down slightly to help reduce wheel physics issues when moving over them.
- Fixed a bug where the custom robot json button state isn't correctly updated when remote controllers are enabled.  

### Removed

- Removed old unused code

## [Release v23.0.5](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.5) - 2023-06-12

### Changed

- Updated room4_small json to work with the new world generator room 4 scoring bug update (Thanks @aZeroTickPulse)

- Changed a victim in the room4_small world's room 4 to be a hazard.

### Fixed

- Fixed a bug causing the map scorer to not count a starting tile if it was the last tile (Thanks @aZeroTickPulse)

## [Release v23.0.4](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.4) - 2023-05-03

### Added

- Added a new example world containing a 4th room. The corresponding json file is also included in the worlds folder.

### Fixed

- Hazard maps now give +20 score bonus for the correct type bonus (from 10 before, to reflect the Erebus rules).
- Moved default robot distance sensors to be more symmetrical.

## [Release v23.0.3](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.3) - 2023-04-04

### Fixed

- Fixed a bug where controllers weren't correctly being uploaded on linux/mac
- Fixed a bug in the map scorer where the last tile wasn't being calculated correctly

## [Release v23.0.2](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.2) - 2023-02-19

### Changed

- Linux/Mac users can now use controller files with no file extension

### Fixed

- Fixed deprecated Python `getData` methods in example player controller code
- Fixed deprecated `setDaemon` warning for Python versions 3.10+
- Fixed a bug where controllers weren't working on linux/mac users

## [Release v23.0.1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.1) - 2023-02-02

> Please see the changelog for v23.0.0 as well, since this update builds upon it.

### Fixed

- 🐛: Fixed a bug where the map bonus answer matrix wasn't being calculated correctly for room 4 entrances.

## [Release v23.0.0](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.0) - 2023-01-27

> Please see the changelog for v22.0.0 as well, since this update builds upon it.

### Added

- ✨: Added support for Webots extern remote controllers to allow for remote controllers via tcp or locally. Read more about it on the Webots website [here](https://cyberbotics.com/doc/guide/running-extern-robot-controllers), and read our documentation to get started [here](https://docs.google.com/document/d/19yIzfaxb6fx1lw7hKTE6EkX7_Pi2NzfE_oGaks76Kgo/edit?usp=sharing).
- ✨: Added a new real-world timer (below the main timer) to ensure controllers don't take too long to run during competitions.
    - The max real world time is `max(maxTime + 60, maxTime * 1.25)` where `maxTime` is the maximum time for a given world
- ✨: Added a world selector refresh button.
- ✨: Added links to the world generator and robot customiser under settings.
- ✨: Added support for room 4. Please refer to the 2023 rules for more details.
- 🔨: Added some development unit tests that can be run under settings.

### Changed

- ❗: The recommended Python version is now 3.9+.
- ❗: Ported to Webots version 2023a. Erebus must be run with Webots version 2023a. Download it [here](https://github.com/cyberbotics/webots/releases/tag/R2023a).
- ❗: Due to 2023a port, previous worlds (for v21 and before) may no longer work.
- ❗: Due to 2023a port, the Erebus UI robot window now runs in the browser.
    - **Note**: If the window doesn't appear, go to `Scene Tree > DEF MAINSUPERVISOR Robot > (Right click) > Show Robot Window`
- ❗: Reduced the velocity threshold for checking whether a robot is stopped. **Please make sure this change doesn't affect your victim detection code**. In some instances, you may need to delay movement after sending a victim identification, in case you begin to move too quickly after the message is received.
- ❗: Added small spherical collision bounding objects to all sensors (excluding the colour sensor) within the custom and the default robot. These have a radius of 0.3cm for all sensors except cameras, which have a larger radius of 0.7cm.
- ⚡️: Updated UI styling to worlds and settings.
- ⚡️: Victims, hazards and sky map now use local textures instead of being generated or online.
- ⚡️: Victims box geometry is now thinner.

### Fixed

- 🐛: Fixed a bug where the map bonus score wasn't being correctly added to the final score.
- 🐛: Fixed a bug where custom sensor z and y axis were not being handled correctly.
- 🐛: Fixed a bug where victim misidentifications weren't being applied when trying to identify an already identified robot.

### Removed

- 🗑️: Removed `robot0.wbt` file
- 🗑️: Removed unused proto template files

### Communication

We would love for teams to share the new worlds they create for practicing. Feel free to share them in the "#share-worlds" channel in the discord.

Since this is a large update to the erebus code base, there may be some bugs. Please feel free to create bug issues on the respective Gitlab repos to help us fix any issues:

- [Erebus issue page](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/issues)
- [Robot Customization issue page](https://gitlab.com/rcj-rescue-tc/erebus/robot-customisation/-/issues)

## [Release v22.0.1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v22.0.1) - 2022-12-13

> For the major changes, see the changelog for v22.0.0

### Changed

- 🐛: Fixed bug with distance and lidar sensors not placing in the correct positions on the robot

## [Release v22.0.0](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v22.0.0) - 2022-09-07

### Added

- ✨: Added a world selector.
- ✨: Added a new warning within the swamp when Erebus detects that a team's controller may not be setting it's wheel velocities every time step.

### Changed

- ❗: Erebus must be run with Webots version 2022a. Download [here](https://github.com/cyberbotics/webots/releases/tag/R2022a).
- ❗: Old custom robot JSON files will no longer work and have to be recreated using the new robot customization v22.0.0.
- ❗: Various sensor axis (rotations) have been changed to be more consistent with eachother and the world axis system. Generally the sensor axis should now be, relative to the robot pointing forwards, **X: Right, Y: Up, Z: Back.**
- ⚡️: Reworked internal code.
- ⚡️: Updated code to align with [new Webots coordinate changes](https://github.com/cyberbotics/webots/wiki/How-to-adapt-your-world-or-PROTO-to-Webots-R2022a).
- ⚡️: Reworked how swamps slow the robot.
- ⚡️: Improved the look of Erebus console outputs to help distinguish them from Webots warnings/errors.
- 🐛: Obstacles not implemented properly.

### Extra notes

#### Swamp warning

A new warning message may appear when a robot stops in the swamp:

```text
[EREBUS WARNING] Detected the robot stopped moving in a swamp. This could be due to not setting the wheel motor velocities every frame.
[EREBUS WARNING] See Erebus 22.0.0 changelog for more details.
```

Under some conditions, the robot can stop when entering the swamp if you're not setting the robot's wheel's velocities very time step. **Please note: Teams can be disqualified if their robot doesn't slow down when entering a swamp by avoiding the slow penalty in any way. For an easy fix, make sure you always update your robot's current wheel velocity every time step.** 

#### New coordinate changes

The changes to the coordinate system within Webots 2022a can be viewed [here](https://github.com/cyberbotics/webots/wiki/How-to-adapt-your-world-or-PROTO-to-Webots-R2022a), but as a simple summary:
> Before, Webots was using NUE as the global coordinate system and we switched it to be new ENU by default.  

> The object's axis system of Webots is now FLU (x-Forward, y-Left, z-Up).

We are continuing to use the NUE global coordinate system as we did before. Internal Erebus code had to be changed to accommodate the new FLU object axis system change, along with robot customiser updates and bug fixes. As a result, sensor axis have changed to be more consistent with eachother and the world axis (see changes section). **Changes to your team's code will have to be made to accommodate these new changes. Please make sure to test the new sensor axis changes since they will now be different.**

That being said, your team's **custom robot JSON files will have to be re-created** due to the changes to the custom robot generator to accommodate the new coordinate system using the new robot customization v22.0.0.

Since this is a large update to the erebus code base, there may be some bugs. Please feel free to create bug issues on the respective Gitlab repos to help us fix any issues:

- [Erebus issues](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/issues)
- [Robot Customization issue page](https://gitlab.com/rcj-rescue-tc/erebus/robot-customisation/-/issues)

## [Release v21.2.2](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.2.2) - 2021-10-10

### Changed
- 🐛: The map answer generator did not work correctly under some conditions

- 🗑️: Unused obstacle code

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
