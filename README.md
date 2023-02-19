# Erebus
Erebus is a simulation competition environment for a new sub-league for [RoboCupJunior(RCJ) Rescue](https://rescue.rcj.cloud/), running as a demonstration in 2021. The challenge is designed for semi-experienced to highly experienced programmers. The aim of the competition is to program a customizable robot to autonomously navigate and map a complex maze environment whilst detecting victims and avoiding obstacles.

Later releases of this platform will be used for the RCJ Rescue 2021 International Event as a demonstration competition based on [these rules](https://cdn.robocup.org/junior/wp/2021/06/2021_RescueSimulation_Rules_final02.pdf).

### [Erebus Official Website](https://erebus.rcj.cloud/)

<div align="center"><img src="/docs/images/environment_v23_0_0.png" width=80%></div>

## Quick Start

1. Download and install [Python 3.9+](https://www.python.org/). Don't forget to add a path to the "Python".
2. Download and install [Webots 2023a](https://cyberbotics.com/).
3. Download our [latest release](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases) and extract the zip file.
4. Open world1.wbt in the [/game/worlds folder](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/tree/master/game/worlds). Load the example program in the [/player_controllers folders](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/player_controllers/ExamplePlayerController_updated.py).


## Documentation

Documentation for the platform can be accessed through [this link](https://v23.erebus.rcj.cloud/docs/).  
However, some pages are currently under construction.

## Robot Customization

The robot customizer can be accessed through [this link](https://v23.robot.erebus.rcj.cloud/).

## Map Generator

The map generator can be accessed through [this link](https://osaka.rcj.cloud/service/editor/simulation/2023).


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
- Moving sensor sliders very fast within robot customizer v23 can result in visual bugs where some sensors are not removed correctly. This is purely visual, and does not affect the resulting JSON.

### Reporting bugs and fixes

Please report bugs and potential fixes either through:

- Raising issues on this repository
- Pull requests
- Through the community Discord server

## [Changelog](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/CHANGELOG.md)

## [Latest Release v23.0.2](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.2) - 2023-02-19

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