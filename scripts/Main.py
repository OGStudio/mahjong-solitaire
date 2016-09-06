
from pymjin2 import *

#MAIN_LAYOUT_NAME = "X_shaped"
MAIN_LAYOUT_NAME = "default"

class MainImpl(object):
    def __init__(self, c):
        self.c = c
        self.started = False
    def __del__(self):
        self.c = None
    def onSpace(self, key, value):
        if (self.started):
            return
        self.started = True
        print "Space pressed. Start the game"
        self.c.set("game.layout", MAIN_LAYOUT_NAME)

class Main(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "Main")
        self.impl = MainImpl(self.c)
        #self.c.setConst("SCENE", sceneName)
        self.c.listen("input.SPACE.key", "1", self.impl.onSpace)
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return Main(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

