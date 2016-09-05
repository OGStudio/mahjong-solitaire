
from pymjin2 import *

class KMahjonggLayoutParserImpl(object):
    def __init__(self, c):
        self.c = c
    def __del__(self):
        self.c = None
    def setParse(self, key, value):
        print "setParse", key, value

class KMahjonggLayoutParser(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "KMahjonggLayoutParser")
        self.impl = KMahjonggLayoutParserImpl(self.c)
        self.c.setConst("SCENE", sceneName)
        self.c.provide("layout.parse", None, self.impl.setParse)
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return KMahjonggLayoutParser(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

