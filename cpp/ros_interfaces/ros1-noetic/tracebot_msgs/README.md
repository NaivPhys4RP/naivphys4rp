# Tracebot-specific ROS interface definitions

This repository holds all Tracebot-specific ROS interface definitions, including _messages_, _services_ and _actions_.

Following the recommended practices, this repository follows the recommended layout:

* `msg` folder stores ROS _message_ definitions
* `srv` folder stores ROS _service_ definitions
* `action` folder stores ROS _action_ definitions

Also according to best practices, this package _exclusively contains the interface definitions_.
The implementation any nodes either providing or using these interfaces is located in separate repositories.
