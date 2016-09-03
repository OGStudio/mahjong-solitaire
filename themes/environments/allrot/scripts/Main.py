
from pymjin2 import *

class MainImpl(object):
    def __init__(self, c):
        self.c = c
        self.active = False
    def __del__(self):
        self.c = None
    def onSpace(self, key, value):
        # Only allow it once.
        if (self.active):
            return
        print "Space pressed. Start background theme"
        self.c.report("background.start", "1")
        self.active = True

class Main(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "Main")
        self.impl = MainImpl(self.c)
        self.c.setConst("SCENE",    sceneName)
        self.c.listen("input.SPACE.key", "1", self.impl.onSpace)
        self.c.provide("background.start")
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

