from enum import Enum
from controller import Node
from Robot import Robot


class FollowSide(Enum):
    TOP = 1
    RIGHT = 2
    BOTTOM = 3
    LEFT = 4


class Camera():
    """Camera class used to update view point angles for automatic camera
        movement
    """

    def __init__(
        self,
        node: Node,
        side: FollowSide = FollowSide.BOTTOM
    ) -> None:
        self.wb_viewpoint_node: Node = node
        self.side: FollowSide = side

    def set_view_point(self, robot: Robot) -> None:
        """Set view point (camera) angle depending on robot position.

        The angle of the view point is always at 90 degree intervals

        Args:
            robot (Robot): Erebus robot to follow
        """
        if self.side == FollowSide.TOP:
            vp = [
                robot.position[0],
                robot.position[1] + 0.8,
                robot.position[2] - 0.8
            ]
            vo = [-0.34, -0.34, -0.88, 1.7]
        elif self.side == FollowSide.RIGHT:
            vp = [
                robot.position[0] + 0.7,
                robot.position[1] + 0.8,
                robot.position[2]
            ]
            vo = [-0.29, 0.68, 0.68, 3.71]
        elif self.side == FollowSide.BOTTOM:
            vp = [
                robot.position[0],
                robot.position[1] + 0.8,
                robot.position[2] + 0.7
            ]
            vo = [-0.683263, 0.683263, 0.257493, 2.63756]
        elif self.side == FollowSide.LEFT:
            vp = [
                robot.position[0] - 0.8,
                robot.position[1] + 0.8,
                robot.position[2]
            ]
            vo = [-0.85, 0.37, -0.37, 1.73]
        else:
            return
        # Set position and rotation of camera
        self.wb_viewpoint_node.getField('position').setSFVec3f(vp)
        self.wb_viewpoint_node.getField('orientation').setSFRotation(vo)

    def follow(self, follow_point: Robot, name: str) -> None:
        """Set the game camera to follow a robot, automatically
        changing the camera angle when needed

        Args:
            follow_point (Robot): Simulation robot to follow 
            name (str): Webots robot node name
        """
        self.wb_viewpoint_node.getField('follow').setSFString(name)
        self.set_view_point(follow_point)

    def update_view(self, side: FollowSide, follow_point: Robot) -> None:
        """Update the camera's viewpoint angle to point towards the
        side specified

        Args:
            side (FollowSide): Side to face
            follow_point (Robot): Simulation robot to rotate camera around
        """
        if side != self.side:
            self.side = side
            self.set_view_point(follow_point)
