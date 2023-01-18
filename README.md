# Erebus
Erebus is a simulation competition environtment for a new sub-league for [RoboCupJunior(RCJ) Rescue](https://rescue.rcj.cloud/), running as a demonstration in 2021. The challenge is designed for semi-experienced to highly experienced programmers. The aim of the competition is to program a customizable robot to autonomously navigate and map a complex maze environemnt whilst detecting victims and avoiding obstacles. 

Later releases of this platform will be used for the RCJ Rescue 2021 International Event as a demonstration competition based on [these rules](https://cdn.robocup.org/junior/wp/2021/06/2021_RescueSimulation_Rules_final02.pdf).

### [Erebus Official Website](https://erebus.rcj.cloud/)

<div align="center"><img src="/docs/images/environment_v21_0_0_b2.png" width=80%></div>

## Quick Start
1. Download and install [Python 3.x](https://www.python.org/). Don't forget to add a path to the "Python".
1. Download and install [Webots 2021a](https://cyberbotics.com/).
1. Download our [latest release](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/releases) and extract the zip file.
1. Open world1.wbt in the [/game/worlds folder](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/tree/master/game/worlds). Load the example program in the [/player_controllers folders](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/player_controllers/ExamplePlayerController_updated.py).


## Documentation
Documentation for the platform can be accessed through [this link](https://v22.erebus.rcj.cloud/docs/).  
However, some pages are currently under construction.

## Robot Customization
The robot customizer can be accessed through [this link](https://v23.robot.erebus.rcj.cloud/).

## Map Generator
The map generator can be accessed through [this link](https://osaka.rcj.cloud/service/editor/simulation/2023).


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
- The robot customization wheel rotations are off by 0.5*pi in the y axis compared to the sensor values. However, what you see in the 3d output in the webpage is still what Erebus generates.

### Reporting bugs and fixes
Please report bugs and potential fixes either through: 
- Raising issues on this repository
- Pull requests
- Through the community Discord server


## [Changelog](https://gitlab.com/rcj-rescue-tc/erebus/erebus/-/blob/master/CHANGELOG.md)

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