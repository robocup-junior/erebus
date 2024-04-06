# Technical Docs

Erebus is build on Webots, an open source robot simulator. You can find out more about Webots [here](https://github.com/cyberbotics/webots), and read the User Guide [here](https://www.cyberbotics.com/doc/guide/getting-started-with-webots). It's recommended to familiarise yourself with Webots beforehand.

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

`player_controllers` dir holds example python robot controller code to use within the simulation.

## Game directory

The directory where the main project code is located.

| Directory      | Description |
| -------------- | ----------- |
| [controllers](#Controllers-directory)     | *Predefined Webots directory*. Where Webots reads robot controller code for a world. We use it to hold all the MainSupervisor code for running the simulation.       |
| logs           | Contains files holding log data about a simulation run.        |
| nodes          | *Predefined Webots directory*. Where Webots reads pre-defined nodes to use within the world.        |
| plugins        | *Predefined Webots directory*. Where Webots reads robot window code. We use it for the MainSupervisor robot window as the interface for the Erebus Simulation.        |
| protos         | *Predefined Webots directory*. Where Webots reads [protos](https://cyberbotics.com/doc/reference/proto-definition) (custom objects within a world) to use within the world       |
| worlds         | A directory to hold all the Erebus worlds to run in the current version of Erebus.        |

### Controllers directory

Holds all the webots robot controller code used within Erebus, code used to control robots within the world. You can read more about Webots controllers [here](https://www.cyberbotics.com/doc/guide/controller-programming).

#### MainSupervisor

Most of the project's code is within the MainSupervisor directory, which holds robot controller code for a Webots Supervisor, a robot with extra functions that allows it to control the simulation process and modify the Scene Tree.

#### robot0Controller

Holds the webots robot controller code for the team's robot within the world. The file used (of .py, .exe, .jar, .class, .bsg, .m) is copied via the LOAD controller code button in the MainSupervisor robot window.

### Protos Directory

Holds all the custom [proto](https://cyberbotics.com/doc/reference/proto-definition) files to define the:

- World tiles

- Victims

- Hazards

- Robot (default and custom created via the MainSupervisor)

### Plugins Directory

Holds directories required for a [robot window](https://cyberbotics.com/doc/guide/controller-plugin#robot-window). These are HTML rendered windows that we use to as a GUI to control the MainSupervisor and the whole Erebus simulation.


## MainSupervisor Programming

For python code style, stay as close as possible to the recommendations found in the [Google style guide](https://google.github.io/styleguide/pyguide.html).

As a quick summary: Stick to 80 character lines, detailed doc strings, type hinting for all variables (unless deemed unnecessary), and keeping to the following variable styling:


| Type                        | Public              | Internal                 |
|-----------------------------|---------------------|--------------------------|
| Packages                    | `lower_with_under`    |                          |
| Modules                     | `lower_with_under`    | `_lower_with_under`     |
| Classes                     | `CapWords`          | `_CapWords`              |
| Exceptions                  | `CapWords`          |                          |
| Functions                   | `lower_with_under()` | `_lower_with_under()`   |
| Global/Class Constants      | `CAPS_WITH_UNDER`   | `_CAPS_WITH_UNDER`      |
| Global/Class Variables      | `lower_with_under`    | `_lower_with_under`     |
| Instance Variables          | `lower_with_under`    | `_lower_with_under` (protected) |
| Method Names               | `lower_with_under()` | `_lower_with_under()` (protected) |
| Function/Method Parameters | `lower_with_under`    |                          |
| Local Variables            | `lower_with_under`    |                          |

For instances where a `type | None` type hint is required, prefer the syntax `Optional[type]`. 

### Note regarding Webots controllers

When programming, especially for the MainSupervisor, there are a few things we need to consider due to how Webots works.

To play and pause the simulation, we control the [stepping](https://www.cyberbotics.com/doc/reference/robot#wb_robot_step) of the simulation using the MainSupervisor. When paused, the MainSupervisor continues in the main 'simulation loop' without updating Webot's step.

Using this same techinique, instead of using the systems `sleep` which will halt Webots as a whole, we control the stepping of the simulation to stop the simulation for a controlled amount of time. A function for this can be found within the MainSupervisor:

```python
def wait(self, sec: float) -> None:
    """Waits for x amount of seconds, while still stepping the Webots
    simulation to avoid simulation pauses

    Args:
        sec (float): Seconds to wait
    """
    first: float = self.getTime()
    while True:
        self.step(TIME_STEP)
        if self.getTime() - first > sec:
            break
```

### The MainSupervisor Structure

Code for the MainSupervisor is split over many python file, generally split up into a class per file.

The entry point for the Supervisor controller is within `MainSupervisor.py`.

Most of the code should hopefully be traceable, however, the MainSupervisor communicates with the robot window via `supervisor.wwiSendText` and `supervisor.wwiReceiveText`. You can read more about it [here](https://cyberbotics.com/doc/guide/controller-plugin#robot-window). We send command signals such as 'run' or 'pause' from the robot window from the MainSupervisor to control the simulation. A small example is shown below:

```text
        MainSupervisor Robot Window                          MainSupervisor

 Time
  |         Send         Receive                           Send         Receive 
  V                                                    
                                                      
                                         
         'robotJson' ----------------------------------------------> Create custom robot proto

           'run' --------------------------------------------------> Play simulation
           
                       Update clock <----------------- 'update, 7:59'
```

The MainSupervisor's robot window's function for recieving messages is `receive` in `MainSupervisorWindow.js` and for the MainSupervisor, it is also `_process_rw_message` in `MainSupervisor.py`.

When the team's robot needs to communicate with the MainSupervisor, data revieved by the reciever on the Supervisor robot in the world, and sent via the emitter. These use the simulation API provided by Webots for [emitter](https://www.cyberbotics.com/doc/reference/emitter) and [receiver](https://cyberbotics.com/doc/reference/receiver), sending data through byte packets.

The emitter sends signals to the team's robot about:

- Robot relocates
- The current time and score.

The reciever recieves data from the team's robot such as:

- The location and type of victim/hazard to gain points.
- Data for the world map to be scored.
- Request for relocate.
- Exit message to end simulation.

## Testing

Automated tests are run through the `.Tests.wbt` world. Starting tests can be done via the UI, under settings. Note this button isn't available on other worlds.

Within `MainSupervisor/Test.py` contains all automated tests to run, using the `MainSupervisor/test.py` robot controller code to communicate test stages and complete detection/wheel movements.