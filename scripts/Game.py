
from pymjin2 import *

GAME_RESOLVER_NAME = "GameResolver"
GAME_LAYOUT_DIR    = "layouts/"
GAME_LAYOUT_EXT    = "layout"

class GameImpl(object):
    def __init__(self, c):
        self.c = c
    def __del__(self):
        self.c = None
    def loadLayout(self, fileName):
        print "loadLayout", fileName
        self.c.set("layout.parseFileName", fileName)
        error = self.c.get("layout.error")
        if (len(error)):
            return
        # Positions are decomposed as (depth1, x1, y1, depth2, x2, y2, ...).
        positions = self.c.get("layout.positions")
        # Position buffer.
        pos = []
        for item in positions:
            pos.append(int(item))
            # A complete position has been constructed.
            if (len(pos) == 3):
                # Create tile.
                tileName = self.c.get("tileFactory.createTile")[0]
                # Position tile.
                self.c.setConst("TILE", tileName)
                val = "{0} {1} {2}".format(pos[1], pos[0], pos[2])
                self.c.set("node.$SCENE.$TILE.position", val)
                print "set tile '{0}' to pos '{1}'".format(tileName, pos)
                # Reset buffer.
                pos = []
    def setLoadLayout(self, key, value):
        fileName = "{0}/{1}.{2}".format(GAME_LAYOUT_DIR,
                                        value[0],
                                        GAME_LAYOUT_EXT)
        # Resolve file name.
        self.c.setConst("RESOLVER", GAME_RESOLVER_NAME)
        self.c.set("pathResolver.$RESOLVER.resolveFileNameAbs", fileName)
        fileNameAbs = self.c.get("pathResolver.$RESOLVER.fileNameAbs")[0]
        # Load layout.
        self.loadLayout(fileNameAbs)

class Game(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "Game")
        self.impl = GameImpl(self.c)
        self.c.setConst("SCENE", sceneName)
        self.c.provide("game.layout", self.impl.setLoadLayout)
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return Game(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

