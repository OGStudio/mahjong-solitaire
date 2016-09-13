
from pymjin2 import *

TILE_FACTORY_NAME_PREFIX     = "tile"
TILE_FACTORY_MATERIAL        = "tile"
TILE_FACTORY_MODEL           = "models/tile.osgt"
TILE_FACTORY_ID_MATERIAL     = "tile0"
# FEATURE: Tile selection depiction.
TILE_FACTORY_ID_MATERIAL_SEL = "tile0{0}_selected"
# FEATURE: Tile selection index depiction.
TILE_FACTORY_ID_MATERIAL_BLK = "tile0{0}_unavailable"

# FEATURE: Tile matching.
class TileFactoryMatching(object):
    def __init__(self, client):
        self.c = client
        self.c.listen("node...selected", "1", self.onSelection)
        self.lastTileID = None
        self.lastTile = None
    def __del__(self):
        self.c = None
    def tileID(self, tileName):
        # TODO: use 'tile..id' call.
        self.c.setConst("TILE", tileName)
        # Get ID from current material name.
        mat = self.c.get("node.$SCENE.$TILE.material")[0]
        sid = mat.split(TILE_FACTORY_ID_MATERIAL)[1]
        return int(sid[0])
    def onSelection(self, key, value):
        tileName = key[2]
        id = self.tileID(tileName)
        # Tiles are different, but their IDs match.
        if (self.lastTile and
            (self.lastTile != tileName) and
            (self.lastTileID == id)):
            # Remove them.
            self.c.set("tileFactory.destroyTile", [self.lastTile,
                                                   tileName])
            # Reset buffer.
            tileName = None
            id = None
        self.lastTile = tileName
        self.lastTileID = id

# FEATURE: Tile selection depiction.
class TileFactorySelectionDepiction(object):
    def __init__(self, client):
        self.c = client
        self.c.listen("node...selected", "1", self.onSelection)
        self.c.listen("tileFactory.destroyTile", None, self.onDestroyTile)
        self.lastSelectedTile = None
    def __del__(self):
        self.c = None
    def currentTileID(self):
        # TODO: use 'tile..id' call.
        # Get ID from current material name.
        mat = self.c.get("node.$SCENE.$TILE.material")[0]
        sid = mat.split(TILE_FACTORY_ID_MATERIAL)[1]
        return int(sid[0])
    def markSelected(self, tileName, state):
        print "markSelected", tileName, state
        self.c.setConst("TILE", tileName)
        id = self.currentTileID()
        # Assign new material.
        mat = TILE_FACTORY_ID_MATERIAL + str(id)
        if (state):
            mat = TILE_FACTORY_ID_MATERIAL_SEL.format(id)
        print "set node '{0}' material to '{1}'".format(tileName, mat)
        self.c.set("node.$SCENE.$TILE.material", mat)
    def onDestroyTile(self, key, value):
        tileNames = value
        for tileName in tileNames:
            if (self.lastSelectedTile == tileName):
                self.lastSelectedTile = None
                return
    def onSelection(self, key, value):
        tileName = key[2]
        # Deselect previous tile.
        if (self.lastSelectedTile):
            self.markSelected(self.lastSelectedTile, False)
        # Select new tile.
        self.lastSelectedTile = tileName
        self.markSelected(tileName, True)

# FEATURE: Tile selection.
class TileFactorySelection(object):
    def __init__(self, client):
        self.c = client
        self.c.listen("tile..position", None, self.onPosition)
        # FEATURE: Tile selection index.
        self.c.provide("tileFactory.indexTiles", self.setIndexTiles)
        self.c.listen("tileFactory.destroyTile", None, self.onDestroyTile)
        # Position -> Tile.
        self.positions = {}
        # Tile -> Position.
        self.tiles = {}
    def __del__(self):
        self.c = None
    # FEATURE: Game stats.
    def calcTurnsTiles(self):
        tiles = len(self.tiles)
        turns = 0
        # TODO: Calculate real number of turns, not just 'has-turns'.
        # Group ID -> Number of tiles.
        ids = {}
        for tileName in self.tiles:
            if (self.free(tileName)):
                self.c.setConst("TILE", tileName)
                id = self.currentTileID()
                if (id not in ids):
                    ids[id] = 0
                ids[id] = ids[id] + 1
                # If any group has more than 1 tile,
                # that's enough for 'has-turns'.
                ok = False
                for id in ids:
                    if (ids[id] > 1):
                        ok = True
                        break
                if (ok):
                    # Just a flag is enough for now.
                    turns = 1
                    break
        self.c.report("tileFactory.turnsTiles", [str(turns),
                                                 str(tiles)])
    # WARNING: Duplicates TileFactorySelectionDepiction.
    # TODO: Get rid of it.
    def currentTileID(self):
        # Get ID from current material name.
        mat = self.c.get("node.$SCENE.$TILE.material")[0]
        sid = mat.split(TILE_FACTORY_ID_MATERIAL)[1]
        return int(sid[0])
    def free(self, tileName):
        pos = self.tiles[tileName]
        vpos = pos.split(" ")
        ipos = []
        for item in vpos:
            ipos.append(int(item))
        # Tile is not free, if it has neighbours at both sides at once.
        if (self.hasNeighbour(ipos, 0, -2) and
            self.hasNeighbour(ipos, 0, 2)):
            return False
        # Tile is not free, if it has at least one neighbour at the top.
        if (self.hasNeighbour(ipos, 1, -1) or
            self.hasNeighbour(ipos, 1, 0) or
            self.hasNeighbour(ipos, 1, 1)):
            return False
        # It's free otherwise.
        return True
    def hasNeighbour(self, pos, depthOffset, columnOffset):
        depth = pos[0] + depthOffset
        column = pos[2] + columnOffset
        # Same row neighbour.
        # Top neighbours' depiction:
        #   --------      -----      -------- 
        #   |   |  |      |   |      |  |   | 
        #   | L |X)|  or  | C |  or  |(X| R |  
        #   |   |  |      |   |      |  |   | 
        #   --------      -----      -------- 
        # Side neighbours' depiction:
        #   ----- -----      ----- ----- 
        #   |   | |   |      |   | |   | 
        #   | L | |(X)|  or  |(X)| | R |  
        #   |   | |   |      |   | |   | 
        #   ----- -----      ----- ----- 
        posDirectly = "{0} {1} {2}".format(depth, pos[1], column)
        # Upper row neighbour.
        # Top neighbours' depiction:
        #   -----         -----         -----
        #   |   |         |   |         |   |
        #   | L |---      | C |      ---| R |
        #   |   |  |      |   |      |  |   |
        #   -----X)|  or  -----  or  |(X-----
        #      |   |      |   |      |   |
        #      -----      -----      -----
        # Side neighbours' depiction:
        #   -----                  -----
        #   |   |                  |   |
        #   | L | -----      ----- | R |
        #   |   | |   |      |   | |   |
        #   ----- |(X)|  or  |(X)| -----
        #         |   |      |   |
        #         -----      -----
        rowUp = pos[1] - 1
        posUpper = "{0} {1} {2}".format(depth, rowUp, column)
        # Lower row neighbour.
        # Top neighbours' depiction:
        #      -----      -----      -----
        #      |   |      |   |      |   |
        #   -----X)|  or  -----  or  |(X-----
        #   |   |  |      |   |      |  |   |
        #   | L |---      | C |      ---| R |
        #   |   |         |   |         |   |
        #   -----         -----         -----
        # Side neighbours' depiction:
        #         -----      -----
        #         |   |      |   |
        #   ----- |(X)|  or  |(X)| -----
        #   |   | |   |      |   | |   |
        #   | L | -----      ----- | R |
        #   |   |                  |   |
        #   -----                  -----
        rowDown = pos[1] + 1
        posLower = "{0} {1} {2}".format(depth, rowDown, column)
        if ((posDirectly in self.positions) or
            (posUpper    in self.positions) or
            (posLower    in self.positions)):
            return True
        return False
    def onDestroyTile(self, key, value):
        tileNames = value
        # Re-index neighbours of the removed tiles.
        for tileName in tileNames:
            pos = self.tiles[tileName]
            del self.tiles[tileName]
            del self.positions[pos]
        # TODO: re-index their neighbours only, not all tiles.
        self.setIndexTiles(key, value)
        # FEATURE: Game stats.
        self.calcTurnsTiles()
    def onPosition(self, key, value):
        tileName = key[1]
        pos = value[0]
        self.positions[pos] = tileName
        self.tiles[tileName] = pos
    # FEATURE: Tile selection index.
    def setIndexTiles(self, key, value):
        # Index all tiles.
        for tileName in self.tiles:
            state = self.free(tileName)
            val = "1" if state else "0"
            self.c.setConst("TILE", tileName)
            self.c.set("node.$SCENE.$TILE.selectable", val)
            # FEATURE: Tile selection index depiction.
            # TODO: use 'tile..id' call.
            id = self.currentTileID()
            mat = TILE_FACTORY_ID_MATERIAL + str(id)
            if (not state):
                mat = TILE_FACTORY_ID_MATERIAL_BLK.format(id)
            self.c.set("node.$SCENE.$TILE.material", mat)
    # FEATURE: Tile selection index.

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
        print "tileID", key
        tileName = key[1]
        return stringToStringList(str(self.ids[tileName]))
    def setDestroyTile(self, key, value):
        print "destroy tile", key, value
        tileNames = value
        for tileName in tileNames:
            self.c.setConst("TILE", tileName)
            self.c.set("node.$SCENE.$TILE.parent", "")
            del self.ids[tileName]
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
        self.selection = TileFactorySelection(self.c)
        # FEATURE: Tile selection depiction.
        self.selectionDepiction = TileFactorySelectionDepiction(self.c)
        # FEATURE: Tile matching.
        self.matching = TileFactoryMatching(self.c)
        self.c.setConst("SCENE", sceneName)
        self.c.setConst("PARENT_NODE", nodeName)
        # FEATURE: Field centering.
        self.c.provide("tileFactory.centerTiles", self.impl.setCenterTiles)
        self.c.provide("tileFactory.createTile", None, self.impl.createTile)
        self.c.provide("tileFactory.destroyTile", self.impl.setDestroyTile)
        self.c.provide("tile..position", self.impl.setTilePosition)
        # FEATURE: Tile identity.
        self.c.provide("tile..id", self.impl.setTileID, self.impl.tileID)
        # FEATURE: Game stats.
        self.c.provide("tileFactory.turnsTiles")
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        # FEATURE: Tile selection.
        del self.selection
        # FEATURE: Tile selection depiction.
        del self.selectionDepiction
        # FEATURE: Tile matching.
        del self.matching
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return TileFactory(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

