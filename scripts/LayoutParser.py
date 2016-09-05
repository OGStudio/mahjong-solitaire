
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
    def __del__(self):
        self.c = None
    def setParseFileName(self, key, value):
        fileName = value[0]
        with open(fileName, "r") as f:
            lns = f.readlines()
        # Parse the file.
        for ln in lns:
            sln = ln.strip()
            # Ignore lines starting with "#".
            if (ln.startswith("#")):
                continue
            # Make sure version is supported.
            elif (ln.startswith(LAYOUT_PARSER_PREFIX_VERSION)):
                version = sln.split(LAYOUT_PARSER_PREFIX_VERSION)[1]
                if (version not in LAYOUT_PARSER_VERSIONS):
                    msg = "KMahjongg layout version '{0}' is unsupported".format(version)
                    self.c.set("error.last", msg)
                    # TODO: report unsuccessful parsing to the caller.
                    return
            # Ignore 1.1 only specifications.
            elif (ln.startswith(LAYOUT_PARSER_PREFIX_DEPTH) or
                  ln.startswith(LAYOUT_PARSER_PREFIX_HEIGHT) or
                  ln.startswith(LAYOUT_PARSER_PREFIX_WIDTH)):
                continue
            else:
                print "line", ln

class LayoutParser(object):
    def __init__(self, sceneName, nodeName, env):
        self.c = EnvironmentClient(env, "LayoutParser")
        self.impl = LayoutParserImpl(self.c)
        self.c.setConst("SCENE", sceneName)
        self.c.provide("layout.parseFileName", self.impl.setParseFileName)
        self.c.provide("layout.positions")
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

