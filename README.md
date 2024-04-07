# Erebus
Erebus is a simulation competition environment for a sub-league of [RoboCupJunior(RCJ) Rescue](https://junior.robocup.org/), that was first introduced as a demonstration in 2021. Since 2022, simulation (Erebus) has been an integral part of RCJ Rescue. The challenge is designed for semi-experienced to highly experienced programmers. The aim of the competition is to program a customizable robot to autonomously navigate and map a complex maze environment whilst detecting victims and avoiding obstacles.

Erebus is under constant development and will continue to serve as the basis for future RCJ Rescue international events. The competitions will be conducted under the [official rules](https://junior.robocup.org/wp-content/uploads/2024/01/RCJRescueSimulation2024-final.pdf).

### [Erebus Official Website](https://erebus.rcj.cloud/)

<div align="center"><img src="/docs/images/environment_v23_0_0.png" width=80%></div>

## Quick Start

1. Download and install [Python 3.9+](https://www.python.org/). Don't forget to add a path to the "Python".
2. Download and install [Webots 2023b](https://cyberbotics.com/).
3. Download our [latest release](https://github.com/robocup-junior/erebus/releases) and extract the zip file. Old releases can be found [here](https://github.com/robocup-junior/erebus/tags).
4. Open world1.wbt in the [/game/worlds folder](https://github.com/robocup-junior/erebus/tree/master/game/worlds). Load the example program in the [/player_controllers folders](https://github.com/robocup-junior/erebus/blob/master/player_controllers/ExamplePlayerController_updated.py).


## Documentation

Documentation for the platform can be accessed through [this link](https://v23.erebus.rcj.cloud/docs/).  
However, some pages are currently under construction.

## Robot Customization

The robot customizer can be accessed through [this link](https://v24.robot.erebus.rcj.cloud/).

## Map Generator

The map generator can be accessed through [this link](https://osaka.rcj.cloud/service/editor/simulation/2024).


## Communication

### Announcements

Announcements will be made in a number of different locations.

- Community [Discord server](https://discord.gg/5QQntAPg7K)
- [RCJ official forum](https://junior.forum.robocup.org/)
- [RCJ Rescue mailing list](http://eepurl.com/g-II71)

### For discussions and questions

- For technical and platform specific questions and discussions please use the community [Discord server](https://discord.gg/5QQntAPg7K) 
- For other RCJ related questions and discussions please use the [RCJ official forum](https://junior.forum.robocup.org/)

### Known issues

- The robot customization wheel rotations are off by 0.5*pi in the y axis compared to the sensor values. However, what you see in the 3d output in the webpage is still what Erebus generates.

### Reporting bugs and fixes

Please report bugs and potential fixes either through:

- Raising issues on this repository
    - [Erebus issues page](https://github.com/robocup-junior/erebus/issues)
    - [Robot Customization issue page](https://github.com/robocup-junior/erebus-robot-customisation/issues)
- Pull requests
- Through the community Discord server

## [Changelog](https://github.com/robocup-junior/erebus/blob/master/CHANGELOG.md)

## [Release v24.0.0](https://github.com/robocup-junior/erebus/releases) - 2024-04-06

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