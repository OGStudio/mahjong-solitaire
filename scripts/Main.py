
from pymjin2 import *

#MAIN_LAYOUT_FILE_NAME = "layouts/X_shaped.layout"
MAIN_LAYOUT_FILE_NAME = "layouts/default.layout"
MAIN_RESOLVER_NAME    = "MahjongResolver"

class MainImpl(object):
    def __init__(self, c, resolver):
        self.c = c
        self.resolver = resolver
        self.started = False
    def __del__(self):
        self.c = None
        self.resolver = None
    def onSpace(self, key, value):
        if (self.started):
            return
        self.started = True
        print "Space pressed. Start the game"
        print self.c.get("tileFactory.createTile")
        fileName = self.resolver.resolve(MAIN_LAYOUT_FILE_NAME)
        self.c.set("layout.parseFileName", fileName)

class MainResolver(object):
    def __init__(self, client):
        self.c = client
        self.fileNameAbs = None
        self.c.setConst("RESOLVER", MAIN_RESOLVER_NAME)
        self.c.listen("pathResolver.$RESOLVER.fileNameAbs",
                      None,
                      self.onFileNameAbs)
    def __del__(self):
        self.c = None
    def onFileNameAbs(self, key, value):
        self.fileNameAbs = value[0]
    def resolve(self, fileName):
        self.c.set("pathResolver.$RESOLVER.resolveFileNameAbs", fileName)
        return self.fileNameAbs

class Main(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "Main")
        self.resolver = MainResolver(self.c)
        self.impl = MainImpl(self.c, self.resolver)
        self.c.setConst("SCENE", sceneName)
        self.c.listen("input.SPACE.key", "1", self.impl.onSpace)
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        del self.impl
        del self.resolver
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return Main(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

