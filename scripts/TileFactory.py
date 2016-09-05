
from pymjin2 import *

TILE_FACTORY_NAME_PREFIX = "tile"
TILE_FACTORY_MATERIAL    = "tile"
TILE_FACTORY_MODEL       = "models/tile.osgt"

class TileFactoryImpl(object):
    def __init__(self, c, parentNode):
        self.c = c
        self.parentNode = parentNode
        self.tileID = 0
    def __del__(self):
        self.c = None
    def createTile(self, key):
        name = self.tileName()
        self.c.setConst("TILE", name)
        self.c.set("node.$SCENE.$TILE.parent",   self.parentNode)
        self.c.set("node.$SCENE.$TILE.model",    TILE_FACTORY_MODEL)
        self.c.set("node.$SCENE.$TILE.material", TILE_FACTORY_MATERIAL)
        return [name]
    # Generate unique tile name.
    def tileName(self):
        self.tileID = self.tileID + 1
        return TILE_FACTORY_NAME_PREFIX + str(self.tileID)

class TileFactory(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "TileFactory")
        self.impl = TileFactoryImpl(self.c, nodeName)
        self.c.setConst("SCENE", sceneName)
        self.c.provide("tileFactory.createTile", None, self.impl.createTile)
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

