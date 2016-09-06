
from pymjin2 import *

LAYOUT_PARSER_PREFIX_DEPTH   = "d"
LAYOUT_PARSER_PREFIX_HEIGHT  = "h"
# We use KMahjongg layout format.
LAYOUT_PARSER_PREFIX_VERSION = "kmahjongg-layout-v"
LAYOUT_PARSER_PREFIX_WIDTH   = "w"
# List of supported layout format versions.
LAYOUT_PARSER_VERSIONS = ["1.0",
                          "1.1"]

class LayoutParserImpl(object):
    def __init__(self, c):
        self.c = c
        # FEATURE: error reporting.
        self.lastError = None
    def __del__(self):
        self.c = None
    # FEATURE: error reporting.
    def error(self, key):
        return ((self.lastError) if self.lastError else ())
    def parseFieldLines(self, lines, fieldID, width, height):
        for h in xrange(0, height - 1):
            for w in xrange(0, width - 1):
                if ((lines[h][w]         == "1") and
                    (lines[h][w + 1]     == "2") and
                    (lines[h + 1][w]     == "4") and
                    (lines[h + 1][w + 1] == "3")):
                    # Save tile position.
                    self.positions.append(str(fieldID))
                    self.positions.append(str(h))
                    self.positions.append(str(w))
    def parseLines(self, lines):
        # Field default dimensions.
        width  = 32
        height = 16
        depth  = 0
        # Field buffer.
        fieldID = 0
        fieldLineID = 0
        fieldLines  = []
        self.positions = []
        # FEATURE: error reporting.
        self.lastError = None
        # Parse the file.
        for ln in lines:
            sln = ln.strip()
            # Ignore comments.
            if (ln.startswith("#")):
                continue
            # Format version.
            elif (ln.startswith(LAYOUT_PARSER_PREFIX_VERSION)):
                version = sln.split(LAYOUT_PARSER_PREFIX_VERSION)[1]
                # Make sure version is supported.
                if (version not in LAYOUT_PARSER_VERSIONS):
                    # FEATURE: error reporting.
                    error = ("KMahjongg layout version '{0}' "
                             "is unsupported").format(version)
                    self.reportError(error)
                    return
            # 1.1: depth.
            elif (ln.startswith(LAYOUT_PARSER_PREFIX_DEPTH)):
                d = sln.split(LAYOUT_PARSER_PREFIX_DEPTH)[1]
                depth = int(d)
            # 1.1: height.
            elif (ln.startswith(LAYOUT_PARSER_PREFIX_HEIGHT)):
                h = sln.split(LAYOUT_PARSER_PREFIX_HEIGHT)[1]
                height = int(h)
            # 1.1: width.
            elif (ln.startswith(LAYOUT_PARSER_PREFIX_WIDTH)):
                w = sln.split(LAYOUT_PARSER_PREFIX_WIDTH)[1]
                width = int(w)
            # Field line.
            else:
                # Accumulate lines to have a complete field for current depth.
                fieldLines.append(sln)
                fieldLineID = fieldLineID + 1
                # Process complete field.
                if (fieldLineID >= height):
                    self.parseFieldLines(fieldLines, fieldID, width, height)
                    fieldID = fieldID + 1
                    # Reset buffer.
                    fieldLines = []
                    fieldLineID = 0
        # FEATURE: error reporting.
        # Make sure number of positions (positions / 3) is even ( positions / 3 / 2).
        if ((len(self.positions) % 6) != 0):
            self.reportError("KMahjongg layout has invalid number of tiles")
    # FEATURE: error reporting.
    def reportError(self, error):
        self.lastError = error
        self.c.set("error.last", error)
    def setParseFileName(self, key, value):
        fileName = value[0]
        with open(fileName, "r") as f:
            lns = f.readlines()
        self.parseLines(lns)
    def tilePositions(self, key):
        return self.positions

class LayoutParser(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "LayoutParser")
        self.impl = LayoutParserImpl(self.c)
        self.c.setConst("SCENE", sceneName)
        # FEATURE: error reporting.
        self.c.provide("layout.error", None, self.impl.error)
        self.c.provide("layout.parseFileName", self.impl.setParseFileName)
        self.c.provide("layout.positions", None, self.impl.tilePositions)
    def __del__(self):
        # Tear down.
        self.c.clear()
        # Destroy.
        del self.impl
        del self.c

def SCRIPT_CREATE(sceneName, nodeName, env):
    return LayoutParser(sceneName, nodeName, env)

def SCRIPT_DESTROY(instance):
    del instance

