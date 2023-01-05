from ConsoleLog import Console
class Camera():
    def __init__(self, node, side="bottom"):
        self.wb_viewpoint_node = node
        self.side = side
        
    def setViewPoint(self, robotObj):
        if self.side == "top":
            vp = [
                robotObj.position[0],
                robotObj.position[1] + 0.8,
                robotObj.position[2] - 0.8
            ]
            vo = [-0.34, -0.34, -0.88, 1.7]
        elif self.side == "right":
            vp = [
                robotObj.position[0] + 0.7,
                robotObj.position[1] + 0.8,
                robotObj.position[2]
            ]
            vo = [-0.29, 0.68, 0.68, 3.71]
        elif self.side == "bottom":
            vp = [
                robotObj.position[0],
                robotObj.position[1] + 0.8,
                robotObj.position[2] + 0.7
            ]
            vo = [-0.683263, 0.683263, 0.257493, 2.63756]
        elif self.side == "left":
            vp = [
                robotObj.position[0] - 0.8,
                robotObj.position[1] + 0.8,
                robotObj.position[2]
            ]
            vo = [-0.85, 0.37, -0.37, 1.73]
        self.wb_viewpoint_node.getField('position').setSFVec3f(vp)
        self.wb_viewpoint_node.getField('orientation').setSFRotation(vo)    
    
    def follow(self, followPoint, name):
        self.wb_viewpoint_node.getField('follow').setSFString(name)
        self.setViewPoint(followPoint)
    
    def updateView(self, side, followPoint):
        if side != self.side:
            self.side = side
            self.setViewPoint(followPoint)
