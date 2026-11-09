# File formats of GnuSolar, one module per format.
#
# The model (model/*) knows nothing about files, it only converts itself to
# plain data and back (ModelNode.toDict / fromDict). The modules here turn
# that plain data into files and back. They do not use Qt.
#
#   pvp.py   the native GnuSolar project file (plant.pvp)
