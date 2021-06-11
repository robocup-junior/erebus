# Erebus
Erebus is a simulation competition environtment for a new sub-league for [RoboCupJunior(RCJ) Rescue](https://rescue.rcj.cloud/), running as a demonstration in 2021. The challenge is designed for semi-experienced to highly experienced programmers. The aim of the competition is to program a customizable robot to autonomously navigate and map a complex maze environemnt whilst detecting victims and avoiding obstacles. 

Later releases of this platform will be used for the RCJ Rescue 2021 International Event as a demonstration competition based on [these rules](https://cdn.robocup.org/junior/wp/2021/03/2021_RescueNewSimulationDemo_Rules_draft01.pdf).

### [Erebus Official Website](https://erebus.rcj.cloud/)

<div align="center"><img src="/docs/images/environment_v21_0_0_b2.png" width=80%></div>

## Quick Start
1. Download and install [Python 3.x](https://www.python.org/). Don't forget to add a path to the "Python".
1. Download and install [Webots 2021a](https://cyberbotics.com/).
1. Download our [latest release](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases) and extract the zip file.
1. Open world1.wbt in the [/game/worlds folder](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/tree/master/game/worlds). Load the example program in the [/player_controllers folders](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/player_controllers/ExamplePlayerController_updated.py).


## Documentation
Documentation for the platform can be accessed through [this link](https://erebus.rcj.cloud/docs/).  
However, some pages are currently under construction.

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


### Known issues
- 

### Reporting bugs and fixes
Please report bugs and potential fixes either through: 
- Raising issues on this repository
- Pull requests
- Through the community Discord server


## [Changelog](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/CHANGELOG.md)

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