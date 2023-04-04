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
    - [Erebus issues](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/issues)
    - [Robot Customization issue page](https://gitlab.com/rcj-rescue-tc/erebus/robot-customisation/-/issues)
- Pull requests
- Through the community Discord server

## [Changelog](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/CHANGELOG.md)

## [Latest Release v23.0.3](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v23.0.3) - 2023-04-04

### Fixed

- Fixed a bug where controllers weren't correctly being uploaded on linux/mac
- Fixed a bug in the map scorer where the last tile wasn't being calculated correctly
