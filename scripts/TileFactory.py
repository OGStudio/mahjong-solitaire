
from pymjin2 import *

TILE_FACTORY_NAME_PREFIX = "tile"
TILE_FACTORY_MATERIAL    = "tile"
TILE_FACTORY_MODEL       = "models/tile.osgt"

class TileFactoryTranslator(object):
    def __init__(self, client):
        self.c = client
        # X, Y, Z factors.
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
        self.translator = TileFactoryTranslator(c)
    def __del__(self):
        del self.translator
        self.c = None
    def createTile(self, key):
        name = self.generateTileName()
        self.c.setConst("TILE", name)
        self.c.set("node.$SCENE.$TILE.parent",   self.parentNode)
        self.c.set("node.$SCENE.$TILE.model",    TILE_FACTORY_MODEL)
        self.c.set("node.$SCENE.$TILE.material", TILE_FACTORY_MATERIAL)
        return [name]
    def generateTileName(self):
        self.tileID = self.tileID + 1
        return TILE_FACTORY_NAME_PREFIX + str(self.tileID)
    def setTilePosition(self, key, value):
        name = key[1]
        self.c.setConst("TILE", name)
        # Translate unit position to relative coordinates.
        pos = self.translator.translate(value[0])
        self.c.set("node.$SCENE.$TILE.position", pos)

class TileFactory(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "TileFactory")
        self.impl = TileFactoryImpl(self.c, nodeName)
        self.c.setConst("SCENE", sceneName)
        self.c.provide("tileFactory.createTile", None, self.impl.createTile)
        self.c.provide("tile..position", self.impl.setTilePosition)
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

