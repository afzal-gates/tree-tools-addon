"""
Procedural Tree & Foliage Suite
Blender Add-on for procedural botanical generation, biological tropisms,
multi-tier phyllotactic branching, photogrammetry scan extension, and
Pivot Painter 2.0 real-time game engine pipeline export.
"""

bl_info = {
    "name": "Procedural Tree & Foliage Suite",
    "author": "Technical Artist & Pipeline Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Tree Tools",
    "description": "Procedural tree & foliage generator with biological tropisms and Pivot Painter 2.0 export",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import importlib

if "operators" in locals():
    importlib.reload(operators)
if "ui" in locals():
    importlib.reload(ui)
if "nodes_builder" in locals():
    importlib.reload(nodes_builder)
if "utils" in locals():
    importlib.reload(utils)

from . import operators
from . import ui
from . import nodes_builder
from . import utils


def register():
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()


if __name__ == "__main__":
    register()
