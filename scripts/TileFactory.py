
from pymjin2 import *

TILE_FACTORY_NAME_PREFIX = "tile"
TILE_FACTORY_MATERIAL    = "tile"
TILE_FACTORY_MODEL       = "models/tile.osgt"
# FEATURE: Tile identity.
TILE_FACTORY_IDS_NB      = 4

# FEATURE: Tile identity.
#class TileFactoryIdentity(object):
#    def __init__(self, client):
#        self.c = client
#        # Tile -> ID.
#        self.ids = {}
#        self.resetAvailableIDs()
#
#        # TMP.
#        self.tmp = {}
#        for i in xrange(0, TILE_FACTORY_IDS_NB):
#            self.tmp[i] = 0
#
#    def __del__(self):
#        self.c = None
#    def allocateID(self, tileName):
#        # Get available ID.
#        print "available", self.availableIDs
#        val = len(self.availableIDs)
#        id = rand() % val
#        # Allocate it.
#        tileID = self.availableIDs[id]
#        self.ids[tileName] = tileID
#
#        # TMP.
#        self.tmp[tileID] = self.tmp[tileID] + 1
#
#        print "allocateID", tileName, self.ids[tileName]
#        # Make sure more available IDs exist.
#        del self.availableIDs[id]
#        if (not len(self.availableIDs)):
#            print "reset"
#            self.resetAvailableIDs()
#    def id(self, tileName):
#        return self.ids[tileName]
#    def resetAvailableIDs(self):
#        self.availableIDs = []
#        for i in xrange(0, TILE_FACTORY_IDS_NB):
#            self.availableIDs.append(i)

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
        # FEATURE: Position translation
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
        return [name]
    def generateTileName(self):
        self.tileID = self.tileID + 1
        return TILE_FACTORY_NAME_PREFIX + str(self.tileID)
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

class TileFactory(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "TileFactory")
        self.impl = TileFactoryImpl(self.c, nodeName)
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
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return TileFactory(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

