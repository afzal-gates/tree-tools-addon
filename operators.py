"""
Procedural Tree & Foliage Suite - Operators Module
Handles creation of procedural tree instances, preset loading,
scan extension setup, Pivot Painter baking, and game engine export.
"""

import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatProperty
from bpy_extras.io_utils import ExportHelper

from . import nodes_builder
from . import utils


def get_tree_modifier(obj):
    """Finds the Procedural Tree Geometry Nodes modifier on the given object."""
    if not obj or not hasattr(obj, "modifiers"):
        return None
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            if "Tree" in mod.node_group.name or "TreeSuite" in mod.name or "STT" in mod.node_group.name:
                return mod
    # Fallback to any Nodes modifier on the object
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            return mod
    return None

def apply_preset_to_modifier(mod, preset_name):
    """Applies a preset dictionary to the tree modifier via interface socket identifiers."""
    if not mod or not mod.node_group or preset_name not in utils.TREE_PRESETS:
        return
    preset_dict = utils.TREE_PRESETS[preset_name]
    socket_map = {}
    for item in mod.node_group.interface.items_tree:
        if getattr(item, 'item_type', None) == 'SOCKET' and getattr(item, 'in_out', None) == 'INPUT':
            socket_map[item.name] = item.identifier
        elif hasattr(item, 'name') and hasattr(item, 'identifier'):
            socket_map[item.name] = item.identifier

    for param_name, param_val in preset_dict.items():
        if param_name in socket_map:
            try:
                mod[socket_map[param_name]] = param_val
            except Exception:
                pass
        elif param_name in mod:
            mod[param_name] = param_val


class TREE_OT_create_tree(Operator):
    """Create a new procedural tree asset with the full foliage suite modifier"""
    bl_idname = "tree_suite.create_tree"
    bl_label = "Create Procedural Tree"
    bl_options = {'REGISTER', 'UNDO'}

    preset: EnumProperty(
        name="Preset",
        description="Starting tree archetype preset",
        items=[
            ("Oak (Deciduous)", "Oak (Deciduous)", "Spreading crown with gnarly secondary branches"),
            ("Pine (Conifer)", "Pine (Conifer)", "Tall conical trunk with drooping horizontal tiers"),
            ("Birch (Slender)", "Birch (Slender)", "Slender upright trunk with steep delicate branches"),
            ("Weeping Willow", "Weeping Willow", "Cascading curtain-like branches with hanging tips"),
            ("Stylized / Bonsai", "Stylized / Bonsai", "Artistic gnarly curves with stylized foliage clusters"),
        ],
        default="Oak (Deciduous)"
    )

    def execute(self, context):
        # Create base mesh and object
        mesh = bpy.data.meshes.new("Procedural_Tree_Mesh")
        obj = bpy.data.objects.new("Procedural_Tree", mesh)
        context.collection.objects.link(obj)

        # Select and make active
        for o in context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # Build master geometry node tree
        gn_tree = nodes_builder.build_procedural_tree_suite_master(force_rebuild=True)

        # Add modifier
        mod = obj.modifiers.new(name="TreeSuite", type='NODES')
        mod.node_group = gn_tree

        # Assign default materials
        bark_mat = utils.create_bark_material("M_Tree_Bark")
        leaf_mat = utils.create_leaf_material("M_Tree_Leaves")

        # Set materials in modifier sockets using interface identifiers
        if mod.node_group:
            for item in mod.node_group.interface.items_tree:
                if item.name == "Bark Material":
                    mod[item.identifier] = bark_mat
                elif item.name == "Leaf Material":
                    mod[item.identifier] = leaf_mat

        # Apply starting preset
        apply_preset_to_modifier(mod, self.preset)

        self.report({'INFO'}, f"Created procedural tree with '{self.preset}' preset.")
        return {'FINISHED'}


class TREE_OT_apply_preset(Operator):
    """Apply a botanical preset to the active procedural tree"""
    bl_idname = "tree_suite.apply_preset"
    bl_label = "Apply Preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name: EnumProperty(
        name="Preset",
        items=[
            ("Oak (Deciduous)", "Oak (Deciduous)", "Spreading crown with gnarly secondary branches"),
            ("Pine (Conifer)", "Pine (Conifer)", "Tall conical trunk with drooping horizontal tiers"),
            ("Birch (Slender)", "Birch (Slender)", "Slender upright trunk with steep delicate branches"),
            ("Weeping Willow", "Weeping Willow", "Cascading curtain-like branches with hanging tips"),
            ("Stylized / Bonsai", "Stylized / Bonsai", "Artistic gnarly curves with stylized foliage clusters"),
        ],
        default="Oak (Deciduous)"
    )

    @classmethod
    def poll(cls, context):
        return get_tree_modifier(context.active_object) is not None

    def execute(self, context):
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            self.report({'WARNING'}, "No active tree modifier found.")
            return {'CANCELLED'}

        apply_preset_to_modifier(mod, self.preset_name)
        self.report({'INFO'}, f"Applied preset '{self.preset_name}'.")
        return {'FINISHED'}


class TREE_OT_bake_pivot_painter(Operator):
    """Bake Unreal Engine & Unity Pivot Painter 2.0 attributes into vertex colors and UV channels"""
    bl_idname = "tree_suite.bake_pivot_painter"
    bl_label = "Bake Pivot Painter Data"
    bl_options = {'REGISTER', 'UNDO'}

    create_copy: BoolProperty(
        name="Create Baked Copy",
        description="Create a separate baked mesh copy instead of replacing in place",
        default=True
    )

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        try:
            baked_obj = utils.bake_pivot_painter_data(obj, create_baked_copy=self.create_copy)
            self.report({'INFO'}, f"Successfully baked Pivot Painter 2.0 data to '{baked_obj.name}'.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to bake Pivot Painter data: {str(e)}")
            return {'CANCELLED'}


class TREE_OT_export_fbx(Operator, ExportHelper):
    """Export tree to FBX format with vertex colors, UVs, and Pivot Painter data for UE / Unity"""
    bl_idname = "tree_suite.export_fbx"
    bl_label = "Export Game-Ready FBX"

    filename_ext = ".fbx"
    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

    auto_bake_pivots: BoolProperty(
        name="Auto-Bake Pivot Painter",
        description="Automatically bake Pivot Painter 2.0 channels prior to export",
        default=True
    )

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a valid tree mesh object.")
            return {'CANCELLED'}

        export_target = obj
        temp_copy = None

        try:
            if self.auto_bake_pivots:
                temp_copy = utils.bake_pivot_painter_data(obj, create_baked_copy=True)
                export_target = temp_copy

            utils.export_tree_fbx(export_target, self.filepath)
            self.report({'INFO'}, f"Exported game-ready tree to {os.path.basename(self.filepath)}.")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"FBX export failed: {str(e)}")
            return {'CANCELLED'}
        finally:
            if temp_copy and temp_copy != obj:
                # Cleanup temporary bake object
                bpy.data.objects.remove(temp_copy, do_unlink=True)


class TREE_OT_add_sun_target(Operator):
    """Spawn an empty object designated as the Sun Target for phototropism guidance"""
    bl_idname = "tree_suite.add_sun_target"
    bl_label = "Add Sun Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sun_empty = bpy.data.objects.new("Tree_Sun_Target", None)
        sun_empty.empty_display_type = 'SPHERE'
        sun_empty.empty_display_size = 1.0
        sun_empty.location = (5.0, 5.0, 15.0)
        context.collection.objects.link(sun_empty)

        # If a tree object is active, assign sun object to modifier
        active_obj = context.active_object
        mod = get_tree_modifier(active_obj)
        if mod and "Sun Object" in mod:
            mod["Sun Object"] = sun_empty

        self.report({'INFO'}, f"Created Sun Target '{sun_empty.name}' and linked to active tree.")
        return {'FINISHED'}


class STT_OT_create_tree_alias(Operator):
    """Alias for 'Create Base Tree' button in Simple Tree Tools panel"""
    bl_idname = "stt.create_tree"
    bl_label = "Create Base Tree"
    bl_description = "Spawns a procedural tree generator object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return bpy.ops.tree_suite.create_tree(preset="Oak (Deciduous)")


classes = (
    TREE_OT_create_tree,
    TREE_OT_apply_preset,
    TREE_OT_bake_pivot_painter,
    TREE_OT_export_fbx,
    TREE_OT_add_sun_target,
    STT_OT_create_tree_alias,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
