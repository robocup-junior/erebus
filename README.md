# Erebus
Erebus is a simulation competition environtment for a new sub-league for [RoboCupJunior(RCJ) Rescue](https://rescue.rcj.cloud/), running as a demonstration in 2021. The challenge is designed for semi-experienced to highly experienced programmers. The aim of the competition is to program a customizable robot to autonomously navigate and map a complex maze environemnt whilst detecting victims and avoiding obstacles. 

Later releases of this platform will be used for the RCJ Rescue 2021 International Event as a demonstration competition based on [these rules](https://cdn.robocup.org/junior/wp/2021/03/2021_RescueNewSimulationDemo_Rules_draft01.pdf).

<div align="center"><img src="/docs/images/environment_v21_0_0_b1.png" width=80%></div>

## Quick Start
1. Download and install [Python 3.x](https://www.python.org/).
1. Download and install [Webots 2021a](https://cyberbotics.com/).
1. Download our [latest release](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases) and extract the zip file.
1. Open world1.wbt in the [/game/worlds folder](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/tree/master/game/worlds). Load the example program in the [/player_controllers folders](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/player_controllers/ExamplePlayerController_updated.py).


## Documentation
The offical documentaion is under development. 

In the meanwhile, the [documentation and tutorial](https://github.com/Shadow149/RescueMaze/wiki) from the 2020 development cycle may be useful (some functionalities are likely to be depreciated). 

## Robot Customization
The robot customizer can be accessed through [this link](https://robot.erebus.rcj.cloud/). 

## Map Generator
The map generator can be accessed through [this link](https://osaka.rcj.cloud/service/).


## Communication

### Annoucements 
Annoucements will be made in a number of different locations. 
- Community [Discord server](https://discord.gg/5QQntAPg7K) 
- [RCJ official forum](https://junior.forum.robocup.org/)
- [RCJ Rescue mailing list](http://eepurl.com/g-II71)

### For discussions and questions 
- For technical and platform specific questions and discussions please use the community [Discord server](https://discord.gg/5QQntAPg7K) 
- For other RCJ related questions and discussions please use the [RCJ official forum](https://junior.forum.robocup.org/)


## About the current version (beta release)
The platform is currently in its beta release phase (v21.0.0 Beta-1). There are still bugs (both known and unknown), and the documentation is under development. 

### Known issues
- The map bonus will not calculated correctly.

### Reporting bugs and fixes
Please report bugs and potential fixes either through: 
- Raising issues on this repository
- Pull requests
- Through the community Discord server


## [Changelog](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/CHANGELOG.md)

## [Release v21.0.0 Beta-1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases/v21.0.0_Beta-1) - 2021-04-05

## [Release v21.0.0 Beta-2] - TBD

### Added
- Added the ability to configure the following settings for the simulator
    - Keep controller and robot files
    - Disable automatic LoP [#1](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/issues/1)
- Added a sample world (Only Area1.wbt)

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

