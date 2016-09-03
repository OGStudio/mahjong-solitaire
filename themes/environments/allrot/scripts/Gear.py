
from pymjin2 import *

GEAR_ROTATE_ACTION = "rotate.default.rotateGear"

class GearImpl(object):
    def __init__(self, c):
        self.c = c
    def __del__(self):
        self.c = None
    def onStart(self, key, value):
        print "start gear rotation"
        self.c.set("$ROTATE.$SCENE.$GEAR.active", "1")

class Gear(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "Gear/" + sceneName + "/" + nodeName)
        self.impl = GearImpl(self.c)
        self.c.setConst("SCENE",  sceneName)
        self.c.setConst("GEAR",   nodeName)
        self.c.setConst("ROTATE", GEAR_ROTATE_ACTION)
        self.c.listen("background.start", "1", self.impl.onStart)
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return Gear(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

