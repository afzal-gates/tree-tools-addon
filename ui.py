"""
Procedural Tree & Foliage Suite - User Interface Module
Provides a comprehensive 3D Viewport N-Panel with organized, collapsible parameter
sections for parametric trunk foundation, tropisms, multi-tier branching,
scan extension photogrammetry blending, foliage, wind, and Pivot Painter 2.0 baking.
"""

import bpy
from bpy.types import Panel

from .operators import get_tree_modifier


def get_socket_identifier(mod, socket_name):
    """Finds the identifier for a given interface socket name."""
    if not mod or not mod.node_group:
        return None
    for item in mod.node_group.interface.items_tree:
        if getattr(item, 'item_type', None) == 'SOCKET' and item.name == socket_name:
            return item.identifier
        elif hasattr(item, 'name') and item.name == socket_name and hasattr(item, 'identifier'):
            return item.identifier
    return None


def draw_socket(layout, mod, socket_name, label=None, icon='NONE', slider=False):
    """Draws a modifier socket property dynamically into a layout."""
    if not mod:
        return
    identifier = get_socket_identifier(mod, socket_name)
    display_label = label if label is not None else socket_name
    
    if identifier and identifier in mod:
        row = layout.row(align=True)
        if icon != 'NONE':
            row.label(text="", icon=icon)
        row.prop(mod, f'["{identifier}"]', text=display_label, slider=slider)
    elif socket_name in mod:
        row = layout.row(align=True)
        if icon != 'NONE':
            row.label(text="", icon=icon)
        row.prop(mod, f'["{socket_name}"]', text=display_label, slider=slider)


# ---------------------------------------------------------------------------
# Base Panel Class
# ---------------------------------------------------------------------------
class TreePanelBase:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tree Tools"


# ---------------------------------------------------------------------------
# 1. Main Setup & Preset Panel
# ---------------------------------------------------------------------------
class TREE_PT_main(TreePanelBase, Panel):
    bl_idname = "TREE_PT_main"
    bl_label = "Procedural Tree Suite"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)

        col = layout.column(align=True)
        col.operator("tree_suite.create_tree", text="Create Procedural Tree", icon='OUTLINER_OB_ARMATURE')

        layout.separator()

        # Presets Box
        preset_box = layout.box()
        preset_box.label(text="Botanical Presets", icon='PRESET')
        
        row = preset_box.row(align=True)
        row.operator_menu_enum("tree_suite.apply_preset", "preset_name", text="Choose & Apply Preset", icon='COMMUNITY')

        # Active object status
        status_box = layout.box()
        if mod:
            row = status_box.row()
            row.label(text=f"Active Tree: {obj.name}", icon='CHECKMARK')
        else:
            row = status_box.row()
            row.label(text="No Procedural Tree Selected", icon='INFO')


# ---------------------------------------------------------------------------
# 2. Parametric Trunk Foundation Panel
# ---------------------------------------------------------------------------
class TREE_PT_trunk(TreePanelBase, Panel):
    bl_idname = "TREE_PT_trunk"
    bl_label = "Trunk & Curve Foundation"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Trunk Height", label="Height", icon='EMPTY_SINGLE_ARROW')
        draw_socket(col, mod, "Trunk Resolution", label="Spline Resolution")
        
        row = col.row(align=True)
        draw_socket(row, mod, "Trunk Base Radius", label="Base Radius")
        draw_socket(row, mod, "Trunk Tip Radius", label="Tip Radius")
        
        draw_socket(col, mod, "Trunk Taper Power", label="Taper Falloff", slider=True)

        layout.separator()
        noise_box = layout.box()
        noise_box.label(text="Noise & Curvature", icon='RNDCURVE')
        draw_socket(noise_box, mod, "Trunk Noise Scale", label="Noise Scale")
        draw_socket(noise_box, mod, "Trunk Noise Strength", label="Displacement")
        draw_socket(noise_box, mod, "Trunk Seed", label="Random Seed")

        layout.separator()
        guide_box = layout.box()
        guide_box.label(text="Custom Guide Curve", icon='CURVE_DATA')
        draw_socket(guide_box, mod, "Use Guide Curve", label="Enable Guide")
        draw_socket(guide_box, mod, "Guide Curve Object", label="Guide Curve")
        draw_socket(guide_box, mod, "Guide Influence", label="Guide Influence", slider=True)


# ---------------------------------------------------------------------------
# 2.5 Subterranean Root System Panel
# ---------------------------------------------------------------------------
class TREE_PT_roots(TreePanelBase, Panel):
    bl_idname = "TREE_PT_roots"
    bl_label = "Subterranean Root System"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        box_crown = layout.box()
        box_crown.label(text="Root Crown & Buttress Flare", icon='MOD_FLUIDSIM')
        draw_socket(box_crown, mod, "Roots Enable", label="Enable Root System")
        draw_socket(box_crown, mod, "Root Depth", label="Root Crown Depth (m)", icon='ARROW_LEFTRIGHT')
        draw_socket(box_crown, mod, "Root Spread", label="Radial Spread (m)", icon='FULLSCREEN_ENTER')
        draw_socket(box_crown, mod, "Root Flare Width", label="Buttress Flare Expansion", slider=True)

        box_p = layout.box()
        box_p.label(text="Primary Structural Roots", icon='PARTICLE_POINT')
        draw_socket(box_p, mod, "Primary Root Count", label="Root Count")
        draw_socket(box_p, mod, "Primary Root Radius Ratio", label="Thickness Ratio", slider=True)
        draw_socket(box_p, mod, "Primary Root Angle", label="Downward Angle (°)")
        draw_socket(box_p, mod, "Primary Root Joint Flare", label="Buttress Joint Flare", slider=True)
        draw_socket(box_p, mod, "Primary Root Crotch Smoothness", label="Crotch Curve Tangency", slider=True)

        box_s = layout.box()
        box_s.label(text="Secondary Roots", icon='CURVE_BEZCIRCLE')
        draw_socket(box_s, mod, "Secondary Roots Count", label="Roots per Primary")
        draw_socket(box_s, mod, "Secondary Roots Length", label="Length (m)")
        draw_socket(box_s, mod, "Secondary Root Radius Ratio", label="Parent Thickness Ratio", slider=True)
        draw_socket(box_s, mod, "Secondary Root Crotch Smoothness", label="Crotch Curve Tangency", slider=True)

        box_t = layout.box()
        box_t.label(text="Tertiary Fine Rootlets", icon='GP_DOTS')
        draw_socket(box_t, mod, "Tertiary Roots Enable", label="Enable Fine Rootlets")
        draw_socket(box_t, mod, "Tertiary Roots Count", label="Rootlet Count")
        draw_socket(box_t, mod, "Tertiary Root Crotch Smoothness", label="Crotch Curve Tangency", slider=True)

        box_soil = layout.box()
        box_soil.label(text="Soil Resistance & Geotropism", icon='FORCE_GRAV')
        draw_socket(box_soil, mod, "Root Gravitropism", label="Downward Plunge (Gravitropism)", slider=True)
        draw_socket(box_soil, mod, "Root Noise Strength", label="Soil Impedance Tortuosity", slider=True)
        draw_socket(box_soil, mod, "Root Seed", label="Root Seed")


# ---------------------------------------------------------------------------
# 3. Biological Tropisms & Environmental Growth Panel
# ---------------------------------------------------------------------------
class TREE_PT_tropisms(TreePanelBase, Panel):
    bl_idname = "TREE_PT_tropisms"
    bl_label = "Biological Tropisms & Obstacles"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        
        # Gravitropism
        grav_box = layout.box()
        grav_box.label(text="Gravitropism (Gravity / Anti-Gravity)", icon='FORCE_GRAVITY')
        draw_socket(grav_box, mod, "Gravitropism", label="Gravity Pull (-Up / +Down)", slider=True)

        # Phototropism
        photo_box = layout.box()
        photo_box.label(text="Phototropism (Sun Seeking)", icon='LIGHT_SUN')
        draw_socket(photo_box, mod, "Phototropism", label="Sun Pull Strength", slider=True)
        draw_socket(photo_box, mod, "Sun Object", label="Sun Object")
        draw_socket(photo_box, mod, "Sun Vector", label="Sun Direction")
        photo_box.operator("tree_suite.add_sun_target", text="Spawn Sun Target Empty", icon='EMPTY_DATA')

        # Thigmotropism / Obstacle Avoidance
        obs_box = layout.box()
        obs_box.label(text="Thigmotropism (Obstacle Avoidance)", icon='MOD_PHYSICS')
        draw_socket(obs_box, mod, "Thigmotropism", label="Avoidance Force", slider=True)
        draw_socket(obs_box, mod, "Obstacle Object", label="Obstacle Collision Mesh")
        draw_socket(obs_box, mod, "Obstacle Avoidance Dist", label="Avoidance Radius")


# ---------------------------------------------------------------------------
# 4. Primary Branches (Tier 1) Panel
# ---------------------------------------------------------------------------
class TREE_PT_branch_t1(TreePanelBase, Panel):
    bl_idname = "TREE_PT_branch_t1"
    bl_label = "Primary Branches (Tier 1)"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Tier 1 Enable", label="Enable Primary Branches", icon='CHECKBOX_HLT')
        draw_socket(col, mod, "Tier 1 Count", label="Branch Count")
        
        row_range = col.row(align=True)
        draw_socket(row_range, mod, "Tier 1 Start Factor", label="Start Height", slider=True)
        draw_socket(row_range, mod, "Tier 1 End Factor", label="End Height", slider=True)

        row_len = col.row(align=True)
        draw_socket(row_len, mod, "Tier 1 Length", label="Length")
        draw_socket(row_len, mod, "Tier 1 Length Falloff", label="Taper Falloff", slider=True)

        draw_socket(col, mod, "Tier 1 Angle", label="Branch Outward Angle (°)", slider=True)

        row_rad = col.row(align=True)
        draw_socket(row_rad, mod, "Tier 1 Base Radius", label="Base Radius")
        draw_socket(row_rad, mod, "Tier 1 Tip Radius", label="Tip Radius")

        row_hier1 = col.row(align=True)
        draw_socket(row_hier1, mod, "Tier 1 Radius Ratio", label="Parent Thickness Ratio", slider=True)
        draw_socket(row_hier1, mod, "Tier 1 Joint Flare", label="Joint Collar Flare", slider=True)
        draw_socket(col, mod, "Tier 1 Crotch Smoothness", label="Crotch Curve Tangency", slider=True)

        draw_socket(col, mod, "Tier 1 Phyllotaxis Angle", label="Phyllotaxis Spiral (°)", slider=True)
        draw_socket(col, mod, "Tier 1 Gravitropism", label="Branch Droop", slider=True)
        draw_socket(col, mod, "Tier 1 Noise Strength", label="Branch Noise")
        draw_socket(col, mod, "Tier 1 Seed", label="Seed")


# ---------------------------------------------------------------------------
# 5. Secondary Branches (Tier 2) Panel
# ---------------------------------------------------------------------------
class TREE_PT_branch_t2(TreePanelBase, Panel):
    bl_idname = "TREE_PT_branch_t2"
    bl_label = "Secondary Branches (Tier 2)"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Tier 2 Enable", label="Enable Secondary Branches", icon='CHECKBOX_HLT')
        draw_socket(col, mod, "Tier 2 Count", label="Count per Branch")

        row_range = col.row(align=True)
        draw_socket(row_range, mod, "Tier 2 Start Factor", label="Start Range", slider=True)
        draw_socket(row_range, mod, "Tier 2 End Factor", label="End Range", slider=True)

        row_len = col.row(align=True)
        draw_socket(row_len, mod, "Tier 2 Length", label="Length")
        draw_socket(row_len, mod, "Tier 2 Length Falloff", label="Falloff", slider=True)

        draw_socket(col, mod, "Tier 2 Angle", label="Branch Angle (°)", slider=True)

        row_rad = col.row(align=True)
        draw_socket(row_rad, mod, "Tier 2 Base Radius", label="Base Radius")
        draw_socket(row_rad, mod, "Tier 2 Tip Radius", label="Tip Radius")

        row_hier2 = col.row(align=True)
        draw_socket(row_hier2, mod, "Tier 2 Radius Ratio", label="Parent Thickness Ratio", slider=True)
        draw_socket(row_hier2, mod, "Tier 2 Joint Flare", label="Joint Collar Flare", slider=True)
        draw_socket(col, mod, "Tier 2 Crotch Smoothness", label="Crotch Curve Tangency", slider=True)

        draw_socket(col, mod, "Tier 2 Phyllotaxis Angle", label="Phyllotaxis Angle (°)", slider=True)
        draw_socket(col, mod, "Tier 2 Gravitropism", label="Droop", slider=True)
        draw_socket(col, mod, "Tier 2 Noise Strength", label="Noise")
        draw_socket(col, mod, "Tier 2 Seed", label="Seed")


# ---------------------------------------------------------------------------
# 6. Twigs (Tier 3) Panel
# ---------------------------------------------------------------------------
class TREE_PT_branch_t3(TreePanelBase, Panel):
    bl_idname = "TREE_PT_branch_t3"
    bl_label = "Twigs (Tier 3)"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Tier 3 Enable", label="Enable Twigs", icon='CHECKBOX_HLT')
        draw_socket(col, mod, "Tier 3 Count", label="Twig Count")

        row_range = col.row(align=True)
        draw_socket(row_range, mod, "Tier 3 Start Factor", label="Start Range", slider=True)
        draw_socket(row_range, mod, "Tier 3 End Factor", label="End Range", slider=True)

        row_len = col.row(align=True)
        draw_socket(row_len, mod, "Tier 3 Length", label="Twig Length")
        draw_socket(row_len, mod, "Tier 3 Length Falloff", label="Length Falloff", slider=True)

        draw_socket(col, mod, "Tier 3 Angle", label="Twig Angle (°)", slider=True)

        row_rad = col.row(align=True)
        draw_socket(row_rad, mod, "Tier 3 Base Radius", label="Base Radius")
        draw_socket(row_rad, mod, "Tier 3 Tip Radius", label="Tip Radius")

        row_hier3 = col.row(align=True)
        draw_socket(row_hier3, mod, "Tier 3 Radius Ratio", label="Parent Thickness Ratio", slider=True)
        draw_socket(row_hier3, mod, "Tier 3 Joint Flare", label="Joint Collar Flare", slider=True)
        draw_socket(col, mod, "Tier 3 Crotch Smoothness", label="Crotch Curve Tangency", slider=True)

        draw_socket(col, mod, "Tier 3 Seed", label="Seed")


# ---------------------------------------------------------------------------
# 7. Scan Extension Module (Photogrammetry Blending)
# ---------------------------------------------------------------------------
class TREE_PT_scan(TreePanelBase, Panel):
    bl_idname = "TREE_PT_scan"
    bl_label = "Scan Extension (Photogrammetry)"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Scan Enable", label="Enable Scan Extension", icon='CHECKBOX_HLT')
        draw_socket(col, mod, "Scan Object", label="3D Scanned Trunk Mesh")
        draw_socket(col, mod, "Scan Point Count", label="Spawn Point Count")
        draw_socket(col, mod, "Scan Branch Length", label="Extension Branch Length")

        layout.separator()
        remesh_box = layout.box()
        remesh_box.label(text="Volumetric Remesh Weld", icon='MESH_DATA')
        draw_socket(remesh_box, mod, "Scan Remesh Union", label="Enable Volumetric Weld")
        draw_socket(remesh_box, mod, "Scan Voxel Size", label="Voxel Size")
        draw_socket(remesh_box, mod, "Scan Voxel Adaptivity", label="Adaptivity", slider=True)


# ---------------------------------------------------------------------------
# 8. Leaves & Foliage Instancing Panel
# ---------------------------------------------------------------------------
class TREE_PT_leaves(TreePanelBase, Panel):
    bl_idname = "TREE_PT_leaves"
    bl_label = "Leaves & Foliage Instancing"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Leaves Enable", label="Enable Leaves", icon='CHECKBOX_HLT')
        
        mode_box = layout.box()
        mode_box.label(text="Leaf Topology Mode", icon='MESH_PLANE')
        draw_socket(mode_box, mod, "Leaf Mode", label="Mode (0:3D Diamond, 1:Card, 2:Custom)")
        draw_socket(mode_box, mod, "Custom Leaf Object", label="Custom Leaf Asset")

        col.separator()
        draw_socket(col, mod, "Leaves Count per Branch", label="Foliage Density")
        draw_socket(col, mod, "Leaves Start Factor", label="Twig Start Range", slider=True)
        draw_socket(col, mod, "Leaf Scale", label="Leaf Scale")

        row_rot = col.row(align=True)
        draw_socket(row_rot, mod, "Leaf Pitch", label="Pitch (°)", slider=True)
        draw_socket(row_rot, mod, "Leaf Roll", label="Roll (°)", slider=True)

        draw_socket(col, mod, "Sun Alignment", label="Sun Orientation Bias", slider=True)
        draw_socket(col, mod, "Leaf Seed", label="Foliage Seed")


# ---------------------------------------------------------------------------
# 9. Wind & Secondary Motion Panel
# ---------------------------------------------------------------------------
class TREE_PT_wind(TreePanelBase, Panel):
    bl_idname = "TREE_PT_wind"
    bl_label = "Wind & Secondary Motion"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Wind Enable", label="Enable Wind Animation", icon='FORCE_WIND')
        draw_socket(col, mod, "Wind Speed", label="Wind Speed", icon='TIME')
        draw_socket(col, mod, "Wind Strength", label="Strength / Amplitude")
        draw_socket(col, mod, "Wind Direction", label="Wind Vector Direction")


# ---------------------------------------------------------------------------
# 10. Meshing & Organic Remesh Union Panel
# ---------------------------------------------------------------------------
class TREE_PT_meshing(TreePanelBase, Panel):
    bl_idname = "TREE_PT_meshing"
    bl_label = "Meshing & Organic Union"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        mod = get_tree_modifier(obj)
        if not mod:
            layout.label(text="Select a tree to view controls", icon='RESTRICT_SELECT_ON')
            return

        col = layout.column(align=True)
        draw_socket(col, mod, "Mesh Resolution", label="Spline Radial Resolution")

        box_union = layout.box()
        box_union.label(text="Organic Remesh Union (SDF)", icon='MOD_REMESH')
        draw_socket(box_union, mod, "Organic Smooth Union", label="Enable Smooth Union (VDB)", icon='CHECKBOX_HLT')
        draw_socket(box_union, mod, "Union Voxel Size", label="Voxel Size (m)")
        draw_socket(box_union, mod, "Voxel Adaptivity", label="Adaptivity Decimation", slider=True)

        box_mat = layout.box()
        box_mat.label(text="Materials", icon='MATERIAL')
        draw_socket(box_mat, mod, "Bark Material", label="Bark Material")
        draw_socket(box_mat, mod, "Leaf Material", label="Leaf Material")


# ---------------------------------------------------------------------------
# 11. Real-Time Pipeline & Pivot Painter 2.0 Export Panel
# ---------------------------------------------------------------------------
class TREE_PT_pipeline(TreePanelBase, Panel):
    bl_idname = "TREE_PT_pipeline"
    bl_label = "Real-Time Pipeline & Pivot Painter"
    bl_parent_id = "TREE_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        col = layout.column(align=True)
        
        info_box = layout.box()
        info_box.label(text="Pivot Painter 2.0 Channels:", icon='EXPORT')
        col_text = info_box.column(align=True)
        col_text.label(text="• PP_Hierarchy_Wind (Color Attrib)")
        col_text.label(text="• PP_ParentPivot (Color Attrib)")
        col_text.label(text="• UV_BranchPivot & UV_ParentPivot")

        layout.separator()
        col.operator("tree_suite.bake_pivot_painter", text="Bake Pivot Painter Data", icon='RENDER_STILL')
        col.operator("tree_suite.export_fbx", text="Export Game-Ready FBX", icon='EXPORT')


classes = (
    TREE_PT_main,
    TREE_PT_trunk,
    TREE_PT_roots,
    TREE_PT_tropisms,
    TREE_PT_branch_t1,
    TREE_PT_branch_t2,
    TREE_PT_branch_t3,
    TREE_PT_scan,
    TREE_PT_leaves,
    TREE_PT_wind,
    TREE_PT_meshing,
    TREE_PT_pipeline,
)


def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass


def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
