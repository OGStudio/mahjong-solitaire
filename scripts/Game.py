
from pymjin2 import *

# FEATURE: Game over.
GAME_OVER_CAMERA  = "default.camera"
GAME_OVER_LOSS    = "rotate.default.rotateToLoss"
GAME_OVER_VICTORY = "rotate.default.rotateToVictory"

GAME_LAYOUT_DIR     = "layouts/"
GAME_LAYOUT_EXT     = "layout"
# FEATURE: Tile identity.
GAME_RESOLVER_NAME  = "GameResolver"
GAME_TILE_IDS_NB    = 4

class GameImpl(object):
    def __init__(self, c):
        self.c = c
    def __del__(self):
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
    # FEATURE: Game over.
    def finish(self, state):
        self.c.setConst("ACTION", GAME_OVER_LOSS)
        if (state):
            self.c.setConst("ACTION", GAME_OVER_VICTORY)
        self.c.set("$ACTION.$CAMERA.active", "1")
    # FEATURE: Tile identity.
    def generateTileIDs(self, tiles):
        i = 0
        id = 0
        while (len(tiles)):
            tileNameID = rand() % len(tiles)
            tileName = tiles[tileNameID]
            del tiles[tileNameID]
            self.c.setConst("TILE", tileName)
            val = id % GAME_TILE_IDS_NB
            self.c.set("tile.$TILE.id", str(val))
            # We only change currently assigned ID once in 2 tiles,
            # because number of IDs should be even.
            if (i % 2):
                id = id + 1
            i = i + 1
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
        # Index all tiles to have up-to-date 'selectable' property.
        # FEATURE: Tile selection index.
        self.c.set("tileFactory.indexTiles", "1")
    # FEATURE: Game stats.
    def onTurnsTiles(self, key, value):
        turns = int(value[0])
        tiles = int(value[1])
        # FEATURE: Game over.
        if (turns == 0):
            # Victory.
            if (tiles == 0):
                self.finish(True)
            # Loss.
            else:
                self.finish(False)
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
        # FEATURE: Game stats.
        self.c.listen("tileFactory.turnsTiles", None, self.impl.onTurnsTiles)
        # FEATURE: Game over.
        self.c.setConst("CAMERA", GAME_OVER_CAMERA)
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

