from ConsoleLog import Console
class Camera():
    def __init__(self, node, side="bottom"):
        self.wb_viewpoint_node = node
        self.side = side
        
    def setViewPoint(self, robotObj):
        Console.log_info(str(robotObj.position))
        if self.side == "top":
            Console.log_info("Top")
            vp = [
                robotObj.position[0],
                robotObj.position[1] + 0.8,
                robotObj.position[2] - 0.5
            ]
            vo = [-0.301184, -0.299742, -0.905231, 1.66967]
        elif self.side == "right":
            Console.log_info("Right")
            vp = [
                robotObj.position[0] + 0.7,
                robotObj.position[1] + 0.8,
                robotObj.position[2]
            ]
            vo = [0.326219, -0.668033, -0.668814, 2.50804]
        elif self.side == "bottom":
            Console.log_info("Bottom")
            vp = [
                robotObj.position[0],
                robotObj.position[1] + 0.8,
                robotObj.position[2] + 0.7
            ]
            vo = [-0.683263, 0.683263, 0.257493, 2.63756]
        elif self.side == "left":
            Console.log_info("left")
            vp = [
                robotObj.position[0] - 0.5,
                robotObj.position[1] + 0.8,
                robotObj.position[2]
            ]
            vo = [-0.794909, 0.429338, -0.428705, 1.79875]
        self.wb_viewpoint_node.getField('position').setSFVec3f(vp)
        self.wb_viewpoint_node.getField('orientation').setSFRotation(vo)    
    
    def follow(self, followPoint):
        self.wb_viewpoint_node.getField('follow').setSFString("e-puck 0")
        self.setViewPoint(followPoint)
    
    def updateView(self, side, followPoint):
        if side != self.side:
            self.side = side
            self.setViewPoint(followPoint)
