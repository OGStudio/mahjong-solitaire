
from pymjin2 import *

GAME_RESOLVER_NAME = "GameResolver"
GAME_LAYOUT_DIR    = "layouts/"
GAME_LAYOUT_EXT    = "layout"
# FEATURE: Tile identity.
GAME_TILE_IDS_NB   = 4

# FEATURE: Tile identity.
class GameTileIDProvider(object):
    def __init__(self):
        self.resetIDs()
    def id(self):
        print "available", self.ids
        # Available ID.
        val = len(self.ids)
        i = rand() % val
        # Allocate it.
        newID = self.ids[i]
        del self.ids[i]
        # Make sure more available IDs exist.
        if (not len(self.ids)):
            self.resetIDs()
        return newID
    def resetIDs(self):
        print "reset"
        self.ids = []
        for i in xrange(0, GAME_TILE_IDS_NB):
            self.ids.append(i)

class GameImpl(object):
    def __init__(self, c):
        self.c = c
        # FEATURE: Tile identity.
        self.provider = GameTileIDProvider()
    def __del__(self):
        # FEATURE: Tile identity.
        del self.provider
        self.c = None
    def composedPositions(self, positions):
        r = []
        # Buffer.
        pos = []
        for item in positions:
            pos.append(item)
            # A complete position has been constructed.
            if (len(pos) == 3):
                r.append(pos)
                # Reset buffer.
                pos = []
        return r
    def createTile(self, pos):
        # Create tile.
        tileName = self.c.get("tileFactory.createTile")[0]
        # Position it.
        self.c.setConst("TILE", tileName)
        val = " ".join(pos)
        self.c.set("tile.$TILE.position", val)
        return tileName
    # FEATURE: Tile identity.
    def generateTileIDs(self, tiles):
        print "generateTileIDs", tiles
        i = 0
        id = self.provider.id()
        print "id", id
        for tileName in tiles:
            print "i", i
            # We only change currently assigned ID once in 2 tiles,
            # because number of IDs should be even.
            if (i % 2):
                id = self.provider.id()
                print "id", id
            i = i + 1
            self.c.setConst("TILE", tileName)
            self.c.set("tile.$TILE.id", str(id))
    def loadLayout(self, fileName):
        self.c.set("layout.parseFileName", fileName)
        error = self.c.get("layout.error")
        if (len(error)):
            return
        # Positions are decomposed as (depth1, x1, y1, depth2, x2, y2, ...).
        rawPositions = self.c.get("layout.positions")
        # Recompose them back.
        positions = self.composedPositions(rawPositions)
        # Create tiles.
        tiles = []
        for pos in positions:
            tiles.append(self.createTile(pos))
        # FEATURE: Field centering.
        self.c.set("tileFactory.centerTiles", "1")
        # FEATURE: Tile identity.
        self.generateTileIDs(tiles)
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

