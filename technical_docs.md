# Technical Docs

Erebus is build on Webots, an open source robot simulator. You can find out more about Webots [here](https://github.com/cyberbotics/webots), and read the User Guide [here](https://www.cyberbotics.com/doc/guide/getting-started-with-webots).

## Project Structure

The structure of the Erebus Repo directories can be seen represented below:

``` text
Erebus
├── game
│   ├── controllers
│   ├── logs
│   ├── nodes
│   ├── plugins
│   │   └── controller
│   │       └── robot_windows
│   │           └── MainSupervisorWindow
│   ├── protos
│   └── worlds
├── docs
└── player_controllers
```

player_controllers holds test robot code to use within the simulation.

## Game directory

The directory where the main project code is located.

| Directory      | Description |
| -------------- | ----------- |
| [controllers](#Controllers-directory)     | *Predefined Webots directory*. Where Webots reads robot controller code for a world. We use it to hold all the MainSupervisor code for running the simulation.       |
| logs           | Contains files holding log data about a simulation run.        |
| nodes          | *Predefined Webots directory*. Where Webots reads pre-defined nodes to use within the world.        |
| plugins        | *Predefined Webots directory*. Where Webots reads robot window code. We use it for the MainSupervisor robot window as the interface for the Erebus Simulation.        |
| protos         | *Predefined Webots directory*. Where Webots reads protos (custom objects within a world) to use within the world       |
| worlds         | A directory to hold all the Erebus worlds to run in the current version of Erebus.        |

### Controllers directory

Holds all the webots robot controller code used within Erebus, code used to control robots within the world. You can read more about Webots controllers [here](https://www.cyberbotics.com/doc/guide/controller-programming).

#### MainSupervisor

Most of the project's code is within the MainSupervisor directory, which holds robot controller code for a Webots Supervisor, a robot with extra functions that allows it to control the simulation process and modify the Scene Tree.

#### ObjectPlacementSupervisor

Object Placer in a world. Currently not in use.

#### robot0Controller

Holds the webots robot controller code for the team's robot within the world. The file used (of .py, .exe, .jar, .class, .bsg, .m) is copied via the LOAD controller code button in the MainSupervisor robot window.

