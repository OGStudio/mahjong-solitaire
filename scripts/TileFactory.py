
from pymjin2 import *

TILE_FACTORY_NAME_PREFIX = "tile"
TILE_FACTORY_MATERIAL    = "tile"
TILE_FACTORY_MODEL       = "models/tile.osgt"
TILE_FACTORY_ID_MATERIAL = "tile0"

# FEATURE: Tile selection.
class TileFactoryMahjong(object):
    def __init__(self, client):
        self.c = client
        self.c.listen("tile..position", None, self.onPosition)
        self.c.provide("tile..selectable", None, self.selectable)
        # Position -> Tile.
        self.positions = {}
        # Tile -> Position.
        self.tiles = {}
    def __del__(self):
        self.c = None
    def hasLeftRightNeighbour(self, pos, left):
        # Left.
        column = pos[2] - 2
        # We use 2, because each tile takes 2 columns in width.
        # Right.
        if (not left):
            column = pos[2] + 2
        # Neighbour directly to the left/right
        #   ----- -----      ----- ----- 
        #   |   | |   |      |   | |   | 
        #   | L | |(X)|  or  |(X)| | R |  
        #   |   | |   |      |   | |   | 
        #   ----- -----      ----- ----- 
        posDirectly = "{0} {1} {2}".format(pos[0], pos[1], column)
        # Neighbour in the upper row to the left/right
        #   -----                  -----
        #   |   |                  |   |
        #   | L | -----      ----- | R |
        #   |   | |   |      |   | |   |
        #   ----- |(X)|  or  |(X)| -----
        #         |   |      |   |
        #         -----      -----
        rowUp = pos[1] - 1
        posUpper = "{0} {1} {2}".format(pos[0], rowUp, column)
        # Neighbour in the lower row to the left/right
        #         -----      -----
        #         |   |      |   |
        #   ----- |(X)|  or  |(X)| -----
        #   |   | |   |      |   | |   |
        #   | L | -----      ----- | R |
        #   |   |                  |   |
        #   -----                  -----
        rowDown = pos[1] + 1
        posLower = "{0} {1} {2}".format(pos[0], rowDown, column)
        if ((posDirectly in self.positions) or
            (posUpper    in self.positions) or
            (posLower    in self.positions)):
            return True
        return False
    def hasTopNeighbour(self, pos, columnOffset):
        column = pos[2] + columnOffset
        depth = pos[0] + 1
        # Top neighbour in the same row.
        #   --------      -----      -------- 
        #   |   |  |      |   |      |  |   | 
        #   | L |X)|  or  | C |  or  |(X| R |  
        #   |   |  |      |   |      |  |   | 
        #   --------      -----      -------- 
        posDirectly = "{0} {1} {2}".format(depth, pos[1], column)
        # Top neighbour in the upper row.
        #   -----         -----         -----
        #   |   |         |   |         |   |
        #   | L |---      | C |      ---| R |
        #   |   |  |      |   |      |  |   |
        #   -----X)|  or  -----  or  |(X-----
        #      |   |      |   |      |   |
        #      -----      -----      -----
        rowUp = pos[1] - 1
        posUpper = "{0} {1} {2}".format(depth, rowUp, column)
        # Top neighbour in the lower row.
        #      -----      -----      -----
        #      |   |      |   |      |   |
        #   -----X)|  or  -----  or  |(X-----
        #   |   |  |      |   |      |  |   |
        #   | L |---      | C |      ---| R |
        #   |   |         |   |         |   |
        #   -----         -----         -----
        rowDown = pos[1] + 1
        posLower = "{0} {1} {2}".format(depth, rowDown, column)
        if ((posDirectly in self.positions) or
            (posUpper    in self.positions) or
            (posLower    in self.positions)):
            return True
        return False
    def onPosition(self, key, value):
        tileName = key[1]
        pos = value[0]
        self.positions[pos] = tileName
        self.tiles[tileName] = pos
    def selectable(self, key):
        tileName = key[1]
        pos = self.tiles[tileName]
        vpos = pos.split(" ")
        ipos = []
        for item in vpos:
            ipos.append(int(item))
        # Tile is unselectable, if it has neighbours at both sides at once.
        if (self.hasLeftRightNeighbour(ipos, True) and
            self.hasLeftRightNeighbour(ipos, False)):
            print "SIDES"
            return ["0"]
        # Tile is unselectable, if it has neighbour at the top.
        if (self.hasTopNeighbour(ipos, -1) or
            self.hasTopNeighbour(ipos, 0) or
            self.hasTopNeighbour(ipos, 1)):
            print "TOP"
            return ["0"]
        # It's free otherwise.
        return ["1"]

# FEATURE: Position translation
class TileFactoryTranslator(object):
    def __init__(self, client):
        self.c = client
        self.factors = None
    def __del__(self):
        self.c = None
    def calculateFactorsOnce(self):
        if (self.factors):
            return
        # SCENE and TILE must be set beforehand.
        bbox = self.c.get("node.$SCENE.$TILE.bbox")[0].split(" ")
        self.factors = (float(bbox[1]) - float(bbox[0]), # X.
                        float(bbox[3]) - float(bbox[2]), # Y.
                        float(bbox[5]) - float(bbox[4])) # Z.
    def translate(self, position):
        self.calculateFactorsOnce()
        v = position.split(" ")
        # We use 1, 2, 0 indexes in that order, because
        # input position is in format (depth, x, y).
        k = 0.5
        return "{0} {1} {2}".format(float(v[1]) * self.factors[0] * k,
                                    float(v[2]) * self.factors[1] * k,
                                    float(v[0]) * self.factors[2])

class TileFactoryImpl(object):
    def __init__(self, c, parentNode):
        self.c = c
        self.parentNode = parentNode
        self.tileID = 0
        # FEATURE: Position translation
        self.translator = TileFactoryTranslator(c)
        # FEATURE: Tile identity.
        self.ids = {}
        # FEATURE: Field centering.
        self.maxX = 0
    def __del__(self):
        # FEATURE: Position translation
        del self.translator
        self.c = None
    def createTile(self, key):
        name = self.generateTileName()
        self.c.setConst("TILE", name)
        self.c.set("node.$SCENE.$TILE.parent",     self.parentNode)
        self.c.set("node.$SCENE.$TILE.model",      TILE_FACTORY_MODEL)
        self.c.set("node.$SCENE.$TILE.material",   TILE_FACTORY_MATERIAL)
        # FEATURE: Tile selection.
        self.c.set("node.$SCENE.$TILE.selectable", "1")
        self.c.listen("node.$SCENE.$TILE.selected", "1", self.onTileSelection)
        return [name]
    def generateTileName(self):
        self.tileID = self.tileID + 1
        return TILE_FACTORY_NAME_PREFIX + str(self.tileID)
    def onTileSelection(self, key, value):
        print "onTileSelection", key, value
        tileName = key[2]
        self.c.setConst("TILE", tileName)
        print "tile is selectable", self.c.get("tile.$TILE.selectable")
    # FEATURE: Field centering.
    def setCenterTiles(self, key, value):
        offset = (self.maxX + self.translator.factors[0]) * -0.5
        pos = self.c.get("node.$SCENE.$PARENT_NODE.position")[0]
        v = pos.split(" ")
        v[0] = str(float(v[0]) + offset)
        v[1] = str(float(v[1]) + offset)
        pos = " ".join(v)
        self.c.set("node.$SCENE.$PARENT_NODE.position", pos)
    def setTilePosition(self, key, value):
        name = key[1]
        self.c.setConst("TILE", name)
        # FEATURE: Position translation
        # Translate unit position to relative coordinates.
        pos = self.translator.translate(value[0])
        self.c.set("node.$SCENE.$TILE.position", pos)
        # FEATURE: Field centering.
        v = pos.split(" ")
        self.maxX = max(self.maxX, float(v[0]))
    # FEATURE: Tile identity.
    def tileID(self, key):
        tileName = key[1]
        return stringToStringList(str(self.ids[tileName]))
    # FEATURE: Tile identity.
    def setTileID(self, key, value):
        tileName = key[1]
        id = int(value[0])
        self.ids[tileName] = id
        self.c.setConst("TILE", tileName)
        val = TILE_FACTORY_ID_MATERIAL + str(id)
        self.c.set("node.$SCENE.$TILE.material", val)

class TileFactory(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "TileFactory")
        self.impl = TileFactoryImpl(self.c, nodeName)
        # FEATURE: Tile selection.
        self.mahjong = TileFactoryMahjong(self.c)
        self.c.setConst("SCENE", sceneName)
        self.c.setConst("PARENT_NODE", nodeName)
        # FEATURE: Field centering.
        self.c.provide("tileFactory.centerTiles", self.impl.setCenterTiles)
        self.c.provide("tileFactory.createTile", None, self.impl.createTile)
        self.c.provide("tile..position", self.impl.setTilePosition)
        # FEATURE: Tile identity.
        self.c.provide("tile..id", self.impl.setTileID, self.impl.tileID)
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        # FEATURE: Tile selection.
        del self.mahjong
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return TileFactory(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

