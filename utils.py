"""
Procedural Tree & Foliage Suite - Utilities Module
Contains math helpers, procedural material generators, preset dictionaries,
Pivot Painter 2.0 baking algorithms, and export utilities.
"""

import math
import random
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler, Quaternion

# Golden angle in radians (137.507764 degrees)
GOLDEN_ANGLE = 2.399963229728653
GOLDEN_RATIO = 1.618033988749895


# ---------------------------------------------------------------------------
# Presets Dictionary
# ---------------------------------------------------------------------------
TREE_PRESETS = {
    "Oak (Deciduous)": {
        "Trunk Height": 9.5,
        "Trunk Base Radius": 0.52,
        "Trunk Tip Radius": 0.08,
        "Trunk Taper Power": 1.1,
        "Trunk Noise Scale": 0.65,
        "Trunk Noise Strength": 0.38,
        "Gravitropism": 0.05,
        "Phototropism": 0.20,
        "Roots Enable": True,
        "Root Depth": 1.8,
        "Root Spread": 4.8,
        "Root Flare Width": 0.75,
        "Primary Root Count": 6,
        "Primary Root Radius Ratio": 0.42,
        "Primary Root Angle": 102.0,
        "Primary Root Joint Flare": 0.45,
        "Primary Root Crotch Smoothness": 0.80,
        "Secondary Roots Count": 4,
        "Secondary Roots Length": 2.0,
        "Secondary Root Radius Ratio": 0.45,
        "Secondary Root Crotch Smoothness": 0.75,
        "Tertiary Roots Enable": True,
        "Tertiary Roots Count": 3,
        "Tertiary Root Crotch Smoothness": 0.70,
        "Root Gravitropism": 0.55,
        "Root Noise Strength": 0.38,
        "Mesh Resolution": 16,
        "Organic Smooth Union": False,
        "Union Voxel Size": 0.025,
        "Voxel Adaptivity": 0.08,
        "Root Seed": 50,
        "Tier 1 Enable": True,
        "Tier 1 Count": 8,
        "Tier 1 Start Factor": 0.32,
        "Tier 1 End Factor": 0.92,
        "Tier 1 Length": 4.8,
        "Tier 1 Length Falloff": 0.60,
        "Tier 1 Angle": 54.0,
        "Tier 1 Base Radius": 0.16,
        "Tier 1 Tip Radius": 0.04,
        "Tier 1 Radius Ratio": 0.46,
        "Tier 1 Joint Flare": 0.75,
        "Tier 1 Crotch Smoothness": 0.75,
        "Tier 1 Gravitropism": 0.15,
        "Tier 1 Noise Strength": 0.32,
        "Tier 2 Enable": True,
        "Tier 2 Count": 5,
        "Tier 2 Start Factor": 0.30,
        "Tier 2 End Factor": 0.90,
        "Tier 2 Length": 2.4,
        "Tier 2 Length Falloff": 0.55,
        "Tier 2 Angle": 48.0,
        "Tier 2 Base Radius": 0.045,
        "Tier 2 Tip Radius": 0.018,
        "Tier 2 Radius Ratio": 0.45,
        "Tier 2 Joint Flare": 0.65,
        "Tier 2 Crotch Smoothness": 0.75,
        "Tier 2 Gravitropism": 0.12,
        "Tier 2 Noise Strength": 0.22,
        "Tier 3 Enable": True,
        "Tier 3 Count": 4,
        "Tier 3 Start Factor": 0.35,
        "Tier 3 End Factor": 0.95,
        "Tier 3 Length": 1.1,
        "Tier 3 Length Falloff": 0.45,
        "Tier 3 Angle": 42.0,
        "Tier 3 Base Radius": 0.016,
        "Tier 3 Tip Radius": 0.005,
        "Tier 3 Radius Ratio": 0.42,
        "Tier 3 Joint Flare": 0.55,
        "Tier 3 Crotch Smoothness": 0.70,
        "Leaves Enable": True,
        "Leaf Mode": 0,
        "Leaves Count per Branch": 8,
        "Leaves Start Factor": 0.45,
        "Leaf Scale": 0.25,
        "Leaf Pitch": 35.0,
        "Leaf Roll": 25.0,
        "Sun Alignment": 0.45,
        "Wind Speed": 1.4,
        "Wind Strength": 0.22,
        "Tree Age": 180.0,
        "Aging Features Enable": True,
        "Bark Fissure Depth": 0.035,
        "Bark Fissure Scale": 1.0,
        "Trunk Fluting": 0.40,
        "Burl Gnarliness": 0.35,
        "Cavities Enable": True,
        "Cavity Scale": 0.38,
        "Cavity Height": 1.6,
    },
    "Pine (Conifer)": {
        "Trunk Height": 16.0,
        "Trunk Base Radius": 0.38,
        "Trunk Tip Radius": 0.025,
        "Trunk Taper Power": 1.4,
        "Trunk Noise Scale": 1.2,
        "Trunk Noise Strength": 0.10,
        "Gravitropism": -0.05,
        "Phototropism": 0.05,
        "Roots Enable": True,
        "Root Depth": 1.4,
        "Root Spread": 3.8,
        "Root Flare Width": 0.50,
        "Primary Root Count": 5,
        "Primary Root Radius Ratio": 0.50,
        "Primary Root Angle": 112.0,
        "Primary Root Joint Flare": 0.70,
        "Secondary Roots Count": 3,
        "Secondary Roots Length": 1.5,
        "Secondary Root Radius Ratio": 0.42,
        "Tertiary Roots Enable": False,
        "Tertiary Roots Count": 2,
        "Root Gravitropism": 0.35,
        "Root Noise Strength": 0.25,
        "Root Seed": 55,
        "Tier 1 Enable": True,
        "Tier 1 Count": 26,
        "Tier 1 Start Factor": 0.18,
        "Tier 1 End Factor": 0.98,
        "Tier 1 Length": 4.2,
        "Tier 1 Length Falloff": 0.82,
        "Tier 1 Angle": 78.0,
        "Tier 1 Base Radius": 0.09,
        "Tier 1 Tip Radius": 0.02,
        "Tier 1 Radius Ratio": 0.42,
        "Tier 1 Joint Flare": 0.60,
        "Tier 1 Gravitropism": 0.28,
        "Tier 1 Noise Strength": 0.12,
        "Tier 2 Enable": True,
        "Tier 2 Count": 7,
        "Tier 2 Start Factor": 0.25,
        "Tier 2 End Factor": 0.90,
        "Tier 2 Length": 1.1,
        "Tier 2 Length Falloff": 0.5,
        "Tier 2 Angle": 62.0,
        "Tier 2 Base Radius": 0.022,
        "Tier 2 Tip Radius": 0.008,
        "Tier 2 Radius Ratio": 0.42,
        "Tier 2 Joint Flare": 0.55,
        "Tier 2 Gravitropism": 0.15,
        "Tier 2 Noise Strength": 0.10,
        "Tier 3 Enable": False,
        "Leaves Enable": True,
        "Leaf Mode": 1,
        "Leaves Count per Branch": 16,
        "Leaves Start Factor": 0.2,
        "Leaf Scale": 0.18,
        "Leaf Pitch": 45.0,
        "Leaf Roll": 45.0,
        "Sun Alignment": 0.2,
        "Wind Speed": 1.8,
        "Wind Strength": 0.18,
        "Tree Age": 90.0,
        "Aging Features Enable": True,
        "Bark Fissure Depth": 0.025,
        "Bark Fissure Scale": 1.8,
        "Trunk Fluting": 0.15,
        "Burl Gnarliness": 0.10,
        "Cavities Enable": False,
        "Cavity Scale": 0.20,
        "Cavity Height": 1.5,
    },
    "Birch (Slender)": {
        "Trunk Height": 13.0,
        "Trunk Base Radius": 0.25,
        "Trunk Tip Radius": 0.03,
        "Trunk Taper Power": 0.9,
        "Trunk Noise Scale": 0.5,
        "Trunk Noise Strength": 0.30,
        "Gravitropism": -0.15,
        "Phototropism": 0.25,
        "Roots Enable": True,
        "Root Depth": 1.1,
        "Root Spread": 3.2,
        "Root Flare Width": 0.45,
        "Primary Root Count": 5,
        "Primary Root Radius Ratio": 0.48,
        "Primary Root Angle": 110.0,
        "Primary Root Joint Flare": 0.60,
        "Secondary Roots Count": 3,
        "Secondary Roots Length": 1.3,
        "Secondary Root Radius Ratio": 0.42,
        "Tertiary Roots Enable": True,
        "Tertiary Roots Count": 2,
        "Root Gravitropism": 0.30,
        "Root Noise Strength": 0.30,
        "Root Seed": 60,
        "Tier 1 Enable": True,
        "Tier 1 Count": 11,
        "Tier 1 Start Factor": 0.35,
        "Tier 1 End Factor": 0.96,
        "Tier 1 Length": 4.0,
        "Tier 1 Length Falloff": 0.65,
        "Tier 1 Angle": 42.0,
        "Tier 1 Base Radius": 0.07,
        "Tier 1 Tip Radius": 0.02,
        "Tier 1 Radius Ratio": 0.45,
        "Tier 1 Joint Flare": 0.55,
        "Tier 1 Gravitropism": -0.08,
        "Tier 1 Noise Strength": 0.22,
        "Tier 2 Enable": True,
        "Tier 2 Count": 9,
        "Tier 2 Start Factor": 0.25,
        "Tier 2 End Factor": 0.92,
        "Tier 2 Length": 1.8,
        "Tier 2 Length Falloff": 0.5,
        "Tier 2 Angle": 40.0,
        "Tier 2 Base Radius": 0.025,
        "Tier 2 Tip Radius": 0.010,
        "Tier 2 Radius Ratio": 0.45,
        "Tier 2 Joint Flare": 0.50,
        "Tier 2 Gravitropism": 0.02,
        "Tier 2 Noise Strength": 0.18,
        "Tier 3 Enable": True,
        "Tier 3 Count": 6,
        "Tier 3 Start Factor": 0.4,
        "Tier 3 End Factor": 0.95,
        "Tier 3 Length": 0.85,
        "Tier 3 Length Falloff": 0.4,
        "Tier 3 Angle": 38.0,
        "Tier 3 Base Radius": 0.012,
        "Tier 3 Tip Radius": 0.004,
        "Tier 3 Radius Ratio": 0.42,
        "Tier 3 Joint Flare": 0.50,
        "Leaves Enable": True,
        "Leaf Mode": 0,
        "Leaves Count per Branch": 8,
        "Leaves Start Factor": 0.35,
        "Leaf Scale": 0.20,
        "Leaf Pitch": 30.0,
        "Leaf Roll": 30.0,
        "Sun Alignment": 0.5,
        "Wind Speed": 2.2,
        "Wind Strength": 0.30,
        "Tree Age": 45.0,
        "Aging Features Enable": True,
        "Bark Fissure Depth": 0.008,
        "Bark Fissure Scale": 0.5,
        "Trunk Fluting": 0.05,
        "Burl Gnarliness": 0.05,
        "Cavities Enable": False,
        "Cavity Scale": 0.15,
        "Cavity Height": 1.2,
    },
    "Weeping Willow": {
        "Trunk Height": 7.5,
        "Trunk Base Radius": 0.55,
        "Trunk Tip Radius": 0.12,
        "Trunk Taper Power": 0.85,
        "Trunk Noise Scale": 0.45,
        "Trunk Noise Strength": 0.50,
        "Gravitropism": 0.10,
        "Phototropism": 0.15,
        "Roots Enable": True,
        "Root Depth": 1.6,
        "Root Spread": 5.2,
        "Root Flare Width": 0.80,
        "Primary Root Count": 7,
        "Primary Root Radius Ratio": 0.58,
        "Primary Root Angle": 122.0,
        "Primary Root Joint Flare": 0.90,
        "Secondary Roots Count": 5,
        "Secondary Roots Length": 2.2,
        "Secondary Root Radius Ratio": 0.48,
        "Tertiary Roots Enable": True,
        "Tertiary Roots Count": 4,
        "Root Gravitropism": 0.50,
        "Root Noise Strength": 0.42,
        "Root Seed": 65,
        "Tier 1 Enable": True,
        "Tier 1 Count": 7,
        "Tier 1 Start Factor": 0.2,
        "Tier 1 End Factor": 0.9,
        "Tier 1 Length": 5.0,
        "Tier 1 Length Falloff": 0.4,
        "Tier 1 Angle": 68.0,
        "Tier 1 Base Radius": 0.18,
        "Tier 1 Tip Radius": 0.06,
        "Tier 1 Radius Ratio": 0.50,
        "Tier 1 Joint Flare": 0.65,
        "Tier 1 Gravitropism": 0.35,
        "Tier 1 Noise Strength": 0.35,
        "Tier 2 Enable": True,
        "Tier 2 Count": 15,
        "Tier 2 Start Factor": 0.15,
        "Tier 2 End Factor": 0.95,
        "Tier 2 Length": 4.5,
        "Tier 2 Length Falloff": 0.3,
        "Tier 2 Angle": 75.0,
        "Tier 2 Base Radius": 0.05,
        "Tier 2 Tip Radius": 0.015,
        "Tier 2 Radius Ratio": 0.48,
        "Tier 2 Joint Flare": 0.60,
        "Tier 2 Gravitropism": 0.95,
        "Tier 2 Noise Strength": 0.3,
        "Tier 3 Enable": True,
        "Tier 3 Count": 14,
        "Tier 3 Start Factor": 0.2,
        "Tier 3 End Factor": 0.98,
        "Tier 3 Length": 3.2,
        "Tier 3 Length Falloff": 0.3,
        "Tier 3 Angle": 82.0,
        "Tier 3 Base Radius": 0.016,
        "Tier 3 Tip Radius": 0.005,
        "Tier 3 Radius Ratio": 0.45,
        "Tier 3 Joint Flare": 0.55,
        "Leaves Enable": True,
        "Leaf Mode": 1,
        "Leaves Count per Branch": 18,
        "Leaves Start Factor": 0.15,
        "Leaf Scale": 0.22,
        "Leaf Pitch": 15.0,
        "Leaf Roll": 45.0,
        "Sun Alignment": 0.2,
        "Wind Speed": 2.5,
        "Wind Strength": 0.38,
        "Tree Age": 120.0,
        "Aging Features Enable": True,
        "Bark Fissure Depth": 0.040,
        "Bark Fissure Scale": 1.2,
        "Trunk Fluting": 0.50,
        "Burl Gnarliness": 0.40,
        "Cavities Enable": True,
        "Cavity Scale": 0.35,
        "Cavity Height": 1.4,
    },
    "Stylized / Bonsai": {
        "Trunk Height": 5.2,
        "Trunk Base Radius": 0.45,
        "Trunk Tip Radius": 0.06,
        "Trunk Taper Power": 1.3,
        "Trunk Noise Scale": 0.35,
        "Trunk Noise Strength": 0.85,
        "Gravitropism": -0.2,
        "Phototropism": 0.35,
        "Roots Enable": True,
        "Root Depth": 1.2,
        "Root Spread": 3.0,
        "Root Flare Width": 1.10,
        "Primary Root Count": 5,
        "Primary Root Radius Ratio": 0.65,
        "Primary Root Angle": 105.0,
        "Primary Root Joint Flare": 1.10,
        "Secondary Roots Count": 3,
        "Secondary Roots Length": 1.4,
        "Secondary Root Radius Ratio": 0.50,
        "Tertiary Roots Enable": True,
        "Tertiary Roots Count": 2,
        "Root Gravitropism": 0.25,
        "Root Noise Strength": 0.65,
        "Root Seed": 70,
        "Tier 1 Enable": True,
        "Tier 1 Count": 5,
        "Tier 1 Start Factor": 0.3,
        "Tier 1 End Factor": 0.92,
        "Tier 1 Length": 3.4,
        "Tier 1 Length Falloff": 0.5,
        "Tier 1 Angle": 62.0,
        "Tier 1 Base Radius": 0.15,
        "Tier 1 Tip Radius": 0.035,
        "Tier 1 Radius Ratio": 0.55,
        "Tier 1 Joint Flare": 0.85,
        "Tier 1 Gravitropism": -0.15,
        "Tier 1 Noise Strength": 0.55,
        "Tier 2 Enable": True,
        "Tier 2 Count": 8,
        "Tier 2 Start Factor": 0.25,
        "Tier 2 End Factor": 0.9,
        "Tier 2 Length": 1.6,
        "Tier 2 Length Falloff": 0.4,
        "Tier 2 Angle": 55.0,
        "Tier 2 Base Radius": 0.04,
        "Tier 2 Tip Radius": 0.015,
        "Tier 2 Radius Ratio": 0.52,
        "Tier 2 Joint Flare": 0.80,
        "Tier 2 Gravitropism": 0.0,
        "Tier 2 Noise Strength": 0.35,
        "Tier 3 Enable": True,
        "Tier 3 Count": 6,
        "Tier 3 Start Factor": 0.35,
        "Tier 3 End Factor": 0.95,
        "Tier 3 Length": 0.7,
        "Tier 3 Length Falloff": 0.4,
        "Tier 3 Angle": 50.0,
        "Tier 3 Base Radius": 0.015,
        "Tier 3 Tip Radius": 0.005,
        "Tier 3 Radius Ratio": 0.48,
        "Tier 3 Joint Flare": 0.75,
        "Leaves Enable": True,
        "Leaf Mode": 0,
        "Leaves Count per Branch": 14,
        "Leaves Start Factor": 0.3,
        "Leaf Scale": 0.32,
        "Leaf Pitch": 40.0,
        "Leaf Roll": 30.0,
        "Sun Alignment": 0.6,
        "Wind Speed": 1.0,
        "Wind Strength": 0.15,
        "Tree Age": 400.0,
        "Aging Features Enable": True,
        "Bark Fissure Depth": 0.060,
        "Bark Fissure Scale": 0.8,
        "Trunk Fluting": 0.85,
        "Burl Gnarliness": 0.90,
        "Cavities Enable": True,
        "Cavity Scale": 0.45,
        "Cavity Height": 1.0,
    },
    "Ancient Hollow Oak (600y)": {
        "Trunk Height": 8.5,
        "Trunk Base Radius": 0.95,
        "Trunk Tip Radius": 0.14,
        "Trunk Taper Power": 0.85,
        "Trunk Noise Scale": 0.45,
        "Trunk Noise Strength": 0.65,
        "Gravitropism": 0.12,
        "Phototropism": 0.18,
        "Roots Enable": True,
        "Root Depth": 2.2,
        "Root Spread": 6.5,
        "Root Flare Width": 1.25,
        "Primary Root Count": 8,
        "Primary Root Radius Ratio": 0.52,
        "Primary Root Angle": 100.0,
        "Primary Root Joint Flare": 0.85,
        "Primary Root Crotch Smoothness": 0.85,
        "Secondary Roots Count": 5,
        "Secondary Roots Length": 2.6,
        "Secondary Root Radius Ratio": 0.48,
        "Secondary Root Crotch Smoothness": 0.80,
        "Tertiary Roots Enable": True,
        "Tertiary Roots Count": 4,
        "Tertiary Root Crotch Smoothness": 0.75,
        "Root Gravitropism": 0.60,
        "Root Noise Strength": 0.45,
        "Mesh Resolution": 16,
        "Organic Smooth Union": True,
        "Union Voxel Size": 0.025,
        "Voxel Adaptivity": 0.08,
        "Root Seed": 108,
        "Tier 1 Enable": True,
        "Tier 1 Count": 9,
        "Tier 1 Start Factor": 0.28,
        "Tier 1 End Factor": 0.88,
        "Tier 1 Length": 5.2,
        "Tier 1 Length Falloff": 0.55,
        "Tier 1 Angle": 60.0,
        "Tier 1 Base Radius": 0.28,
        "Tier 1 Tip Radius": 0.06,
        "Tier 1 Radius Ratio": 0.48,
        "Tier 1 Joint Flare": 0.85,
        "Tier 1 Crotch Smoothness": 0.80,
        "Tier 1 Gravitropism": 0.22,
        "Tier 1 Noise Strength": 0.42,
        "Tier 2 Enable": True,
        "Tier 2 Count": 6,
        "Tier 2 Start Factor": 0.25,
        "Tier 2 End Factor": 0.90,
        "Tier 2 Length": 2.6,
        "Tier 2 Length Falloff": 0.50,
        "Tier 2 Angle": 52.0,
        "Tier 2 Base Radius": 0.065,
        "Tier 2 Tip Radius": 0.022,
        "Tier 2 Radius Ratio": 0.46,
        "Tier 2 Joint Flare": 0.75,
        "Tier 2 Crotch Smoothness": 0.78,
        "Tier 2 Gravitropism": 0.16,
        "Tier 2 Noise Strength": 0.28,
        "Tier 3 Enable": True,
        "Tier 3 Count": 4,
        "Tier 3 Start Factor": 0.35,
        "Tier 3 End Factor": 0.95,
        "Tier 3 Length": 1.2,
        "Tier 3 Length Falloff": 0.45,
        "Tier 3 Angle": 45.0,
        "Tier 3 Base Radius": 0.020,
        "Tier 3 Tip Radius": 0.006,
        "Tier 3 Radius Ratio": 0.44,
        "Tier 3 Joint Flare": 0.65,
        "Tier 3 Crotch Smoothness": 0.72,
        "Leaves Enable": True,
        "Leaf Mode": 0,
        "Leaves Count per Branch": 6,
        "Leaves Start Factor": 0.50,
        "Leaf Scale": 0.26,
        "Leaf Pitch": 35.0,
        "Leaf Roll": 25.0,
        "Sun Alignment": 0.45,
        "Wind Speed": 1.2,
        "Wind Strength": 0.18,
        "Tree Age": 600.0,
        "Aging Features Enable": True,
        "Bark Fissure Depth": 0.065,
        "Bark Fissure Scale": 0.9,
        "Trunk Fluting": 0.75,
        "Burl Gnarliness": 0.65,
        "Cavities Enable": True,
        "Cavity Scale": 0.35,
        "Cavity Height": 1.7,
    },
}


# ---------------------------------------------------------------------------
# Procedural Materials
# ---------------------------------------------------------------------------
def create_bark_material(name="M_Tree_Bark"):
    """Creates a high quality procedural tree bark shader."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    out_node = nodes.new("ShaderNodeOutputMaterial")
    out_node.location = (600, 0)

    # Principled BSDF
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

    # Texture Coordinate & Mapping (stretch vertically along Z for bark)
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)

    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    mapping.inputs["Scale"].default_value = (2.0, 2.0, 10.0)
    links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    # Noise texture for bark furrows
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-400, 100)
    noise.inputs["Scale"].default_value = 4.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.65
    noise.inputs["Distortion"].default_value = 1.2
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # Color Ramp for wood / bark tone
    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-150, 100)
    color_ramp.color_ramp.elements[0].position = 0.2
    color_ramp.color_ramp.elements[0].color = (0.09, 0.06, 0.04, 1.0) # deep bark
    color_ramp.color_ramp.elements[1].position = 0.75
    color_ramp.color_ramp.elements[1].color = (0.24, 0.18, 0.12, 1.0) # lighter wood / lichen
    links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # Bump node for tactile 3D relief
    bump = nodes.new("ShaderNodeBump")
    bump.location = (50, -150)
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.15
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    bsdf.inputs["Roughness"].default_value = 0.85
    mat.diffuse_color = (0.18, 0.11, 0.07, 1.0) # Rich dark bark in Solid viewport
    return mat


def create_leaf_material(name="M_Tree_Leaves"):
    """Creates a realistic foliage shader with translucency and subsurface scattering."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out_node = nodes.new("ShaderNodeOutputMaterial")
    out_node.location = (600, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (300, 0)
    links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])

    # Noise for leaf color variation
    noise = nodes.new("ShaderNodeTexNoise")
    noise.location = (-300, 100)
    noise.inputs["Scale"].default_value = 12.0
    noise.inputs["Detail"].default_value = 4.0

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-50, 100)
    color_ramp.color_ramp.elements[0].position = 0.15
    color_ramp.color_ramp.elements[0].color = (0.05, 0.22, 0.03, 1.0) # rich deep green
    color_ramp.color_ramp.elements[1].position = 0.85
    color_ramp.color_ramp.elements[1].color = (0.28, 0.45, 0.06, 1.0) # vibrant sunlight green
    links.new(noise.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])

    # Subsurface light transmission
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.35
    elif "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = 0.35
        
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (0.4, 0.7, 0.1)

    bsdf.inputs["Roughness"].default_value = 0.45
    mat.diffuse_color = (0.12, 0.42, 0.08, 1.0) # Vibrant green in Solid viewport
    return mat


# ---------------------------------------------------------------------------
# Real-Time Pipeline & Pivot Painter 2.0 Baking
# ---------------------------------------------------------------------------
def bake_pivot_painter_data(tree_obj, create_baked_copy=True):
    """
    Evaluates tree geometry and bakes Unreal Engine / Unity Pivot Painter 2.0
    compatible data into custom Color Attributes and UV Channels.
    
    Data channels produced:
    1. Color Attribute 'PP_Hierarchy_Wind':
       - Red: Local branch wind weight (0.0 at branch base, 1.0 at branch tip)
       - Green: Global tree height wind weight (0.0 at roots, 1.0 at canopy top)
       - Blue: Normalized hierarchy depth (0=Trunk, 0.25=Primary, 0.5=Secondary, 0.75=Twigs, 1.0=Leaves)
       - Alpha: Random phase per island (0.0 to 1.0) for desynchronized flutter
    2. Color Attribute 'PP_ParentPivot':
       - RGB: Normalized / encoded parent pivot coordinate
    3. UV Channel 'PP_BranchPivot':
       - U = Branch Pivot X, V = Branch Pivot Y
    4. UV Channel 'PP_ParentPivot':
       - U = Parent Pivot X, V = Parent Pivot Y
    5. UV Channel 'PP_Pivots_Z':
       - U = Branch Pivot Z, V = Parent Pivot Z
    """
    if not tree_obj or tree_obj.type != 'MESH':
        raise ValueError("Active object must be a valid mesh with tree geometry.")

    context = bpy.context
    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = tree_obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()

    target_obj = tree_obj
    if create_baked_copy:
        baked_mesh = eval_mesh.copy()
        target_obj = bpy.data.objects.new(f"{tree_obj.name}_PivotPainter_Baked", baked_mesh)
        target_obj.matrix_world = tree_obj.matrix_world.copy()
        context.collection.objects.link(target_obj)
        context.view_layer.objects.active = target_obj
        target_obj.select_set(True)
    else:
        # replace mesh data in place
        tree_obj.modifiers.clear()
        tree_obj.data = eval_mesh.copy()
        target_obj = tree_obj

    mesh = target_obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    total_verts = len(bm.verts)
    if total_verts == 0:
        bm.free()
        eval_obj.to_mesh_clear()
        return target_obj

    # Calculate overall mesh bounding box
    min_z = min(v.co.z for v in bm.verts)
    max_z = max(v.co.z for v in bm.verts)
    height_span = max(0.001, max_z - min_z)

    # Check for procedural geometry node attributes if present
    has_tier_attr = "pp_tier" in mesh.attributes
    has_pivot_attr = "pp_pivot" in mesh.attributes
    has_parent_pivot_attr = "pp_parent_pivot" in mesh.attributes
    has_wind_weight_attr = "pp_wind_weight" in mesh.attributes

    # Read pre-computed attributes if present
    tier_data = None
    pivot_data = None
    parent_pivot_data = None
    wind_weight_data = None

    if has_tier_attr:
        tier_data = [d.value for d in mesh.attributes["pp_tier"].data]
    if has_pivot_attr:
        pivot_data = [Vector(d.vector) for d in mesh.attributes["pp_pivot"].data]
    if has_parent_pivot_attr:
        parent_pivot_data = [Vector(d.vector) for d in mesh.attributes["pp_parent_pivot"].data]
    if has_wind_weight_attr:
        wind_weight_data = [d.value for d in mesh.attributes["pp_wind_weight"].data]

    # Topological island analysis using BMesh for disconnected foliage / branches
    # Group vertices by connected components
    visited = set()
    islands = []
    for vert in bm.verts:
        if vert.index in visited:
            continue
        island_verts = []
        stack = [vert]
        visited.add(vert.index)
        while stack:
            curr = stack.pop()
            island_verts.append(curr)
            for edge in curr.link_edges:
                other = edge.other_vert(curr)
                if other.index not in visited:
                    visited.add(other.index)
                    stack.append(other)
        islands.append(island_verts)

    # Prepare custom Color Attributes
    color_attrs = mesh.color_attributes
    for attr_name in ["PP_Hierarchy_Wind", "PP_ParentPivot"]:
        if attr_name in color_attrs:
            color_attrs.remove(color_attrs[attr_name])

    wind_layer = color_attrs.new(name="PP_Hierarchy_Wind", type='FLOAT_COLOR', domain='POINT')
    pivot_layer = color_attrs.new(name="PP_ParentPivot", type='FLOAT_COLOR', domain='POINT')

    # Prepare custom UV Layers for precision vector baking
    uv_layers = mesh.uv_layers
    uv_branch_pivot = uv_layers.get("UV_BranchPivot") or uv_layers.new(name="UV_BranchPivot")
    uv_parent_pivot = uv_layers.get("UV_ParentPivot") or uv_layers.new(name="UV_ParentPivot")
    uv_pivots_z = uv_layers.get("UV_Pivots_Z") or uv_layers.new(name="UV_Pivots_Z")

    # Vertex buffers for colors
    wind_colors = [(0.0, 0.0, 0.0, 1.0)] * total_verts
    parent_pivot_colors = [(0.0, 0.0, 0.0, 1.0)] * total_verts
    vert_branch_pivots = [Vector((0, 0, 0))] * total_verts
    vert_parent_pivots = [Vector((0, 0, 0))] * total_verts

    for island_idx, island_verts in enumerate(islands):
        rand_phase = random.random()
        
        # Calculate local island bounds and lowest point (approx local pivot)
        island_min_z = min(v.co.z for v in island_verts)
        lowest_vert = min(island_verts, key=lambda v: v.co.z)
        local_pivot = lowest_vert.co.copy()
        
        # Approximate parent pivot: lowest point projected down or towards origin
        parent_pivot = local_pivot.copy()
        parent_pivot.z = max(0.0, parent_pivot.z - 1.5)
        
        island_max_dist = max(0.001, max((v.co - local_pivot).length for v in island_verts))

        for v in island_verts:
            idx = v.index
            
            # 1. Hierarchy depth
            if tier_data and idx < len(tier_data):
                tier_val = float(tier_data[idx])
            else:
                # Estimate tier based on relative elevation and island size
                rel_z = (v.co.z - min_z) / height_span
                tier_val = 0.0 if len(island_verts) > total_verts * 0.4 else (2.0 if len(island_verts) < 16 else 1.0)
            
            norm_hierarchy = min(1.0, tier_val / 4.0)

            # 2. Local branch wind weight (0 at pivot, 1 at tip)
            if wind_weight_data and idx < len(wind_weight_data):
                local_wind = float(wind_weight_data[idx])
            else:
                local_wind = (v.co - local_pivot).length / island_max_dist
            local_wind = max(0.0, min(1.0, local_wind))

            # 3. Global height wind weight
            global_wind = max(0.0, min(1.0, (v.co.z - min_z) / height_span))

            # 4. Pivots
            if pivot_data and idx < len(pivot_data):
                b_piv = pivot_data[idx]
            else:
                b_piv = local_pivot

            if parent_pivot_data and idx < len(parent_pivot_data):
                p_piv = parent_pivot_data[idx]
            else:
                p_piv = parent_pivot

            vert_branch_pivots[idx] = b_piv
            vert_parent_pivots[idx] = p_piv

            # Pack Color Attributes
            wind_colors[idx] = (local_wind, global_wind, norm_hierarchy, rand_phase)
            parent_pivot_colors[idx] = (p_piv.x, p_piv.y, p_piv.z, 1.0)

    # Write colors to attributes
    for idx, col in enumerate(wind_colors):
        wind_layer.data[idx].color = col
        pivot_layer.data[idx].color = parent_pivot_colors[idx]

    # Write UV coordinates for loops/corners
    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v_idx = mesh.loops[loop_idx].vertex_index
            b_piv = vert_branch_pivots[v_idx]
            p_piv = vert_parent_pivots[v_idx]
            
            uv_branch_pivot.data[loop_idx].uv = (b_piv.x, b_piv.y)
            uv_parent_pivot.data[loop_idx].uv = (p_piv.x, p_piv.y)
            uv_pivots_z.data[loop_idx].uv = (b_piv.z, p_piv.z)

    bm.free()
    eval_obj.to_mesh_clear()
    mesh.update()

    return target_obj


# ---------------------------------------------------------------------------
# FBX Export Helper
# ---------------------------------------------------------------------------
def export_tree_fbx(tree_obj, filepath):
    """Exports the specified tree object to FBX format ready for UE / Unity."""
    context = bpy.context
    prev_active = context.view_layer.objects.active
    prev_selected = [o for o in context.selected_objects]

    # Deselect all and select only tree_obj
    for o in context.selected_objects:
        o.select_set(False)
    tree_obj.select_set(True)
    context.view_layer.objects.active = tree_obj

    try:
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_NONE',
            axis_forward='-Z',
            axis_up='Y',
            mesh_smooth_type='FACE',
            colors_type='FLOAT',
            prioritize_active_color=True,
            bake_anim=False
        )
    finally:
        # Restore selection
        for o in prev_selected:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if prev_active and prev_active.name in bpy.data.objects:
            context.view_layer.objects.active = prev_active
