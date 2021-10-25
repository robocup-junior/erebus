
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
            vo = [0.0, 0.9235793898666079, 0.3834072386035822, 3.141592653589793]
        elif self.side == "right":
            vp = [
                robotObj.position[0] + 0.8,
                robotObj.position[1] + 0.8,
                robotObj.position[2]
            ]
            vo = [-0.357996176885067, 0.8623673664230065,
                0.357996176885067, 1.7183320854248436]
        elif self.side == "bottom":
            vp = [
                robotObj.position[0],
                robotObj.position[1] + 0.8,
                robotObj.position[2] + 0.8
            ]
            vo = [1.0, 0.0, 0.0, 5.4962200048483485]
        elif self.side == "left":
            vp = [
                robotObj.position[0] - 0.8,
                robotObj.position[1] + 0.8,
                robotObj.position[2]
            ]
            vo = [0.357996176885067, 0.8623673664230065,
                0.357996176885067, 4.564853221754743]
        self.wb_viewpoint_node.getField('position').setSFVec3f(vp)
        self.wb_viewpoint_node.getField('orientation').setSFRotation(vo)    
    
    def follow(self, followPoint):
        self.wb_viewpoint_node.getField('follow').setSFString("e-puck 0")
        self.setViewPoint(followPoint)
    
    def updateView(self, side, followPoint):
        if side != self.side:
            self.side = side
            self.setViewPoint(followPoint)
