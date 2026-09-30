"""
Procedural Tree & Foliage Suite - Geometry Nodes Builder Module
Programmatically creates and configures the procedural Geometry Node trees
for parametric trunks, biological tropisms, multi-tier phyllotactic branching,
scan extension photogrammetry blending, foliage instancing, and real-time attributes.
"""

import math
import bpy

# Golden angle in radians: 137.507764 degrees
GOLDEN_ANGLE = 2.399963229728653


def get_socket(node, name, is_output=False):
    """Safely retrieves a socket from node inputs or outputs by name or index."""
    sockets = node.outputs if is_output else node.inputs
    if isinstance(name, int):
        return sockets[name]
    if name in sockets:
        return sockets[name]
    name_lower = name.lower()
    for s in sockets:
        if s.name.lower() == name_lower:
            return s
    return sockets[0]


def add_interface_socket(tree, name, in_out="INPUT", socket_type="NodeSocketFloat", default_value=None, min_val=None, max_val=None):
    """Helper to add interface sockets to GeometryNodeTree (Blender 4.0+ / 4.2+ / 5.0+)."""
    socket = tree.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
    if default_value is not None and hasattr(socket, "default_value"):
        try:
            socket.default_value = default_value
        except Exception:
            pass
    if min_val is not None and hasattr(socket, "min_value"):
        socket.min_value = min_val
    if max_val is not None and hasattr(socket, "max_value"):
        socket.max_value = max_val
    return socket


def safe_set_mode(node, mode="COUNT"):
    """Safely sets mode on nodes across Blender versions."""
    if hasattr(node, "mode"):
        try:
            node.mode = mode
        except Exception:
            pass
    elif "Mode" in node.inputs:
        try:
            node.inputs["Mode"].default_value = mode.capitalize()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 1. Sub-Group: Noise Displacement
# ---------------------------------------------------------------------------
def build_noise_displace_group(force_rebuild=False):
    """Builds reusable 4D noise vector displacement node group."""
    name = "Tree_Sub_NoiseDisplace"
    if not force_rebuild and name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name], do_unlink=True)

    tree = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    tree.interface.clear()

    # Sockets
    add_interface_socket(tree, "Geometry", "INPUT", "NodeSocketGeometry")
    add_interface_socket(tree, "Scale", "INPUT", "NodeSocketFloat", default_value=0.8, min_val=0.01, max_val=20.0)
    add_interface_socket(tree, "Strength", "INPUT", "NodeSocketFloat", default_value=0.35, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Anchor Power", "INPUT", "NodeSocketFloat", default_value=1.5, min_val=0.5, max_val=4.0)
    add_interface_socket(tree, "Seed", "INPUT", "NodeSocketFloat", default_value=0.0)
    add_interface_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    links = tree.links

    in_node = nodes.new("NodeGroupInput")
    in_node.location = (-600, 0)
    out_node = nodes.new("NodeGroupOutput")
    out_node.location = (600, 0)

    # Spline parameter for anchoring root
    spline_param = nodes.new("GeometryNodeSplineParameter")
    spline_param.location = (-400, -100)

    power_node = nodes.new("ShaderNodeMath")
    power_node.operation = "POWER"
    power_node.location = (-200, -100)
    links.new(spline_param.outputs["Factor"], power_node.inputs[0])
    links.new(in_node.outputs["Anchor Power"], power_node.inputs[1])

    # 4D Noise
    pos_node = nodes.new("GeometryNodeInputPosition")
    pos_node.location = (-400, 200)

    noise_node = nodes.new("ShaderNodeTexNoise")
    noise_node.noise_dimensions = "4D"
    noise_node.location = (-200, 200)
    links.new(pos_node.outputs["Position"], noise_node.inputs["Vector"])
    links.new(in_node.outputs["Scale"], noise_node.inputs["Scale"])
    links.new(in_node.outputs["Seed"], noise_node.inputs["W"])

    # Center noise (-0.5)
    sub_node = nodes.new("ShaderNodeVectorMath")
    sub_node.operation = "SUBTRACT"
    sub_node.inputs[1].default_value = (0.5, 0.5, 0.5)
    sub_node.location = (50, 200)
    links.new(noise_node.outputs["Color"], sub_node.inputs[0])

    # Scale by Strength
    scale_str = nodes.new("ShaderNodeVectorMath")
    scale_str.operation = "SCALE"
    scale_str.location = (250, 200)
    links.new(sub_node.outputs["Vector"], scale_str.inputs["Vector"])
    links.new(in_node.outputs["Strength"], scale_str.inputs["Scale"])

    # Scale by Anchor Factor
    scale_fac = nodes.new("ShaderNodeVectorMath")
    scale_fac.operation = "SCALE"
    scale_fac.location = (400, 100)
    links.new(scale_str.outputs["Vector"], scale_fac.inputs["Vector"])
    links.new(power_node.outputs["Value"], scale_fac.inputs["Scale"])

    # Set Position
    set_pos = nodes.new("GeometryNodeSetPosition")
    set_pos.location = (450, -50)
    links.new(in_node.outputs["Geometry"], set_pos.inputs["Geometry"])
    links.new(scale_fac.outputs["Vector"], set_pos.inputs["Offset"])

    links.new(set_pos.outputs["Geometry"], out_node.inputs["Geometry"])
    return tree


# ---------------------------------------------------------------------------
# 2. Sub-Group: Biological Tropisms (Gravitropism, Phototropism, Thigmotropism)
# ---------------------------------------------------------------------------
def build_tropisms_group(force_rebuild=False):
    """Builds biological tropism calculation group."""
    name = "Tree_Sub_Tropisms"
    if not force_rebuild and name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name], do_unlink=True)

    tree = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    tree.interface.clear()

    # Sockets
    add_interface_socket(tree, "Geometry", "INPUT", "NodeSocketGeometry")
    add_interface_socket(tree, "Gravitropism", "INPUT", "NodeSocketFloat", default_value=-0.15, min_val=-2.0, max_val=2.0)
    add_interface_socket(tree, "Phototropism", "INPUT", "NodeSocketFloat", default_value=0.2, min_val=-2.0, max_val=2.0)
    add_interface_socket(tree, "Sun Vector", "INPUT", "NodeSocketVector", default_value=(5.0, 5.0, 15.0))
    add_interface_socket(tree, "Sun Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Thigmotropism", "INPUT", "NodeSocketFloat", default_value=0.0, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Obstacle Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Obstacle Distance", "INPUT", "NodeSocketFloat", default_value=1.5, min_val=0.1, max_val=20.0)
    add_interface_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    links = tree.links

    in_node = nodes.new("NodeGroupInput")
    in_node.location = (-900, 0)
    out_node = nodes.new("NodeGroupOutput")
    out_node.location = (900, 0)

    pos_node = nodes.new("GeometryNodeInputPosition")
    pos_node.location = (-700, 200)

    spline_param = nodes.new("GeometryNodeSplineParameter")
    spline_param.location = (-700, 50)

    fac_pow = nodes.new("ShaderNodeMath")
    fac_pow.operation = "POWER"
    fac_pow.inputs[1].default_value = 1.3
    fac_pow.location = (-500, 50)
    links.new(spline_param.outputs["Factor"], fac_pow.inputs[0])

    # --- Gravitropism ---
    # Vector (0, 0, -1) * Gravitropism * Factor
    grav_vec = nodes.new("ShaderNodeVectorMath")
    grav_vec.operation = "SCALE"
    grav_vec.inputs["Vector"].default_value = (0.0, 0.0, -1.0)
    grav_vec.location = (-300, 300)
    links.new(in_node.outputs["Gravitropism"], grav_vec.inputs["Scale"])

    grav_scaled = nodes.new("ShaderNodeVectorMath")
    grav_scaled.operation = "SCALE"
    grav_scaled.location = (-100, 300)
    links.new(grav_vec.outputs["Vector"], grav_scaled.inputs["Vector"])
    links.new(fac_pow.outputs["Value"], grav_scaled.inputs["Scale"])

    # --- Phototropism ---
    # Pull toward Sun Position
    sun_info = nodes.new("GeometryNodeObjectInfo")
    sun_info.transform_space = "RELATIVE"
    sun_info.location = (-700, -200)
    links.new(in_node.outputs["Sun Object"], sun_info.inputs["Object"])

    # Select between Sun Object location or Sun Vector
    dir_to_sun = nodes.new("ShaderNodeVectorMath")
    dir_to_sun.operation = "SUBTRACT"
    dir_to_sun.location = (-400, -150)
    links.new(in_node.outputs["Sun Vector"], dir_to_sun.inputs[0])
    links.new(pos_node.outputs["Position"], dir_to_sun.inputs[1])

    norm_sun = nodes.new("ShaderNodeVectorMath")
    norm_sun.operation = "NORMALIZE"
    norm_sun.location = (-200, -150)
    links.new(dir_to_sun.outputs["Vector"], norm_sun.inputs["Vector"])

    photo_scale = nodes.new("ShaderNodeVectorMath")
    photo_scale.operation = "SCALE"
    photo_scale.location = (0, -150)
    links.new(norm_sun.outputs["Vector"], photo_scale.inputs["Vector"])
    links.new(in_node.outputs["Phototropism"], photo_scale.inputs["Scale"])

    photo_factored = nodes.new("ShaderNodeVectorMath")
    photo_factored.operation = "SCALE"
    photo_factored.location = (200, -150)
    links.new(photo_scale.outputs["Vector"], photo_factored.inputs["Vector"])
    links.new(fac_pow.outputs["Value"], photo_factored.inputs["Scale"])

    # --- Thigmotropism (Obstacle Avoidance) ---
    obs_info = nodes.new("GeometryNodeObjectInfo")
    obs_info.transform_space = "RELATIVE"
    obs_info.location = (-700, -500)
    links.new(in_node.outputs["Obstacle Object"], obs_info.inputs["Object"])

    prox_node = nodes.new("GeometryNodeProximity")
    prox_node.target_element = "FACES"
    prox_node.location = (-400, -450)
    links.new(obs_info.outputs["Geometry"], prox_node.inputs["Geometry"])
    links.new(pos_node.outputs["Position"], prox_node.inputs["Sample Position"])

    # Push away vector = Point - Hit Position
    push_dir = nodes.new("ShaderNodeVectorMath")
    push_dir.operation = "SUBTRACT"
    push_dir.location = (-150, -450)
    links.new(pos_node.outputs["Position"], push_dir.inputs[0])
    links.new(prox_node.outputs["Position"], push_dir.inputs[1])

    norm_push = nodes.new("ShaderNodeVectorMath")
    norm_push.operation = "NORMALIZE"
    norm_push.location = (50, -450)
    links.new(push_dir.outputs["Vector"], norm_push.inputs["Vector"])

    # Avoidance falloff: max(0.0, 1.0 - (dist / obs_dist))
    div_dist = nodes.new("ShaderNodeMath")
    div_dist.operation = "DIVIDE"
    div_dist.location = (-150, -650)
    links.new(prox_node.outputs["Distance"], div_dist.inputs[0])
    links.new(in_node.outputs["Obstacle Distance"], div_dist.inputs[1])

    inv_dist = nodes.new("ShaderNodeMath")
    inv_dist.operation = "SUBTRACT"
    inv_dist.inputs[0].default_value = 1.0
    inv_dist.location = (50, -650)
    links.new(div_dist.outputs["Value"], inv_dist.inputs[1])

    max_dist = nodes.new("ShaderNodeMath")
    max_dist.operation = "MAXIMUM"
    max_dist.inputs[1].default_value = 0.0
    max_dist.location = (250, -650)
    links.new(inv_dist.outputs["Value"], max_dist.inputs[0])

    push_mag = nodes.new("ShaderNodeMath")
    push_mag.operation = "MULTIPLY"
    push_mag.location = (450, -650)
    links.new(max_dist.outputs["Value"], push_mag.inputs[0])
    links.new(in_node.outputs["Thigmotropism"], push_mag.inputs[1])

    push_vector = nodes.new("ShaderNodeVectorMath")
    push_vector.operation = "SCALE"
    push_vector.location = (300, -450)
    links.new(norm_push.outputs["Vector"], push_vector.inputs["Vector"])
    links.new(push_mag.outputs["Value"], push_vector.inputs["Scale"])

    # --- Sum Total Displacements ---
    sum1 = nodes.new("ShaderNodeVectorMath")
    sum1.operation = "ADD"
    sum1.location = (450, 100)
    links.new(grav_scaled.outputs["Vector"], sum1.inputs[0])
    links.new(photo_factored.outputs["Vector"], sum1.inputs[1])

    sum2 = nodes.new("ShaderNodeVectorMath")
    sum2.operation = "ADD"
    sum2.location = (650, 0)
    links.new(sum1.outputs["Vector"], sum2.inputs[0])
    links.new(push_vector.outputs["Vector"], sum2.inputs[1])

    set_pos = nodes.new("GeometryNodeSetPosition")
    set_pos.location = (750, 200)
    links.new(in_node.outputs["Geometry"], set_pos.inputs["Geometry"])
    links.new(sum2.outputs["Vector"], set_pos.inputs["Offset"])

    links.new(set_pos.outputs["Geometry"], out_node.inputs["Geometry"])
    return tree


# ---------------------------------------------------------------------------
# 3. Sub-Group: Hierarchical Branch Tier (Phyllotaxis & Spline Foundation)
# ---------------------------------------------------------------------------
def build_branch_tier_group(force_rebuild=False):
    """Builds multi-tier phyllotactic branching generator with hierarchical diameter and smooth joint collar flare."""
    name = "Tree_Sub_Branch_Tier"
    if name in bpy.data.node_groups:
        if force_rebuild:
            bpy.data.node_groups.remove(bpy.data.node_groups[name], do_unlink=True)
        else:
            grp = bpy.data.node_groups[name]
            socket_names = [item.name for item in grp.interface.items_tree if getattr(item, 'in_out', None) == 'INPUT']
            if "Radius Ratio" in socket_names and "Joint Flare" in socket_names and "Length Falloff" in socket_names:
                return grp
            bpy.data.node_groups.remove(grp, do_unlink=True)

    tree = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    tree.interface.clear()

    # Sockets
    add_interface_socket(tree, "Parent Curves", "INPUT", "NodeSocketGeometry")
    add_interface_socket(tree, "Branch Count", "INPUT", "NodeSocketInt", default_value=12, min_val=0, max_val=100)
    add_interface_socket(tree, "Start Factor", "INPUT", "NodeSocketFloat", default_value=0.25, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "End Factor", "INPUT", "NodeSocketFloat", default_value=0.95, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Branch Length", "INPUT", "NodeSocketFloat", default_value=3.5, min_val=0.1, max_val=30.0)
    add_interface_socket(tree, "Length Falloff", "INPUT", "NodeSocketFloat", default_value=0.55, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Branch Angle", "INPUT", "NodeSocketFloat", default_value=55.0, min_val=0.0, max_val=180.0)
    add_interface_socket(tree, "Base Radius", "INPUT", "NodeSocketFloat", default_value=0.08, min_val=0.001, max_val=1.0)
    add_interface_socket(tree, "Tip Radius", "INPUT", "NodeSocketFloat", default_value=0.015, min_val=0.001, max_val=0.5)
    add_interface_socket(tree, "Radius Ratio", "INPUT", "NodeSocketFloat", default_value=0.48, min_val=0.05, max_val=0.95)
    add_interface_socket(tree, "Joint Flare", "INPUT", "NodeSocketFloat", default_value=0.65, min_val=0.0, max_val=2.0)
    add_interface_socket(tree, "Phyllotaxis Angle", "INPUT", "NodeSocketFloat", default_value=137.5, min_val=0.0, max_val=360.0)
    add_interface_socket(tree, "Gravitropism", "INPUT", "NodeSocketFloat", default_value=0.1, min_val=-2.0, max_val=2.0)
    add_interface_socket(tree, "Noise Strength", "INPUT", "NodeSocketFloat", default_value=0.25, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Resolution", "INPUT", "NodeSocketInt", default_value=16, min_val=4, max_val=64)
    add_interface_socket(tree, "Tier Index", "INPUT", "NodeSocketInt", default_value=1)
    add_interface_socket(tree, "Seed", "INPUT", "NodeSocketInt", default_value=10)

    add_interface_socket(tree, "Child Curves", "OUTPUT", "NodeSocketGeometry")
    add_interface_socket(tree, "Spawn Points", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    links = tree.links

    in_node = nodes.new("NodeGroupInput")
    in_node.location = (-1400, 0)
    out_node = nodes.new("NodeGroupOutput")
    out_node.location = (2500, 0)

    # Convert degrees to radians for angles
    deg_to_rad = nodes.new("ShaderNodeMath")
    deg_to_rad.operation = "RADIANS"
    deg_to_rad.location = (-1000, -200)
    links.new(in_node.outputs["Branch Angle"], deg_to_rad.inputs[0])

    phyl_rad = nodes.new("ShaderNodeMath")
    phyl_rad.operation = "RADIANS"
    phyl_rad.location = (-1000, -350)
    links.new(in_node.outputs["Phyllotaxis Angle"], phyl_rad.inputs[0])

    # Trim parent curve between Start Factor and End Factor so trunk base is bare
    trim_parent = nodes.new("GeometryNodeTrimCurve")
    trim_parent.location = (-1150, 200)
    links.new(in_node.outputs["Parent Curves"], trim_parent.inputs["Curve"])
    links.new(in_node.outputs["Start Factor"], trim_parent.inputs[2])
    links.new(in_node.outputs["End Factor"], trim_parent.inputs[3])

    # Stamp parent_radius and parent_factor onto trimmed curve before sampling points
    rad_in_parent = nodes.new("GeometryNodeInputRadius")
    rad_in_parent.location = (-1150, 50)
    store_parent_r = nodes.new("GeometryNodeStoreNamedAttribute")
    store_parent_r.data_type = "FLOAT"
    store_parent_r.domain = "POINT"
    store_parent_r.inputs["Name"].default_value = "parent_radius"
    store_parent_r.location = (-950, 150)
    links.new(trim_parent.outputs["Curve"], store_parent_r.inputs["Geometry"])
    links.new(rad_in_parent.outputs["Radius"], store_parent_r.inputs["Value"])

    param_parent = nodes.new("GeometryNodeSplineParameter")
    param_parent.location = (-1150, -50)
    store_parent_f = nodes.new("GeometryNodeStoreNamedAttribute")
    store_parent_f.data_type = "FLOAT"
    store_parent_f.domain = "POINT"
    store_parent_f.inputs["Name"].default_value = "parent_factor"
    store_parent_f.location = (-800, 150)
    links.new(store_parent_r.outputs["Geometry"], store_parent_f.inputs["Geometry"])
    links.new(param_parent.outputs["Factor"], store_parent_f.inputs["Value"])

    # Sample points on trimmed parent curve (Curve to Points)
    c2p = nodes.new("GeometryNodeCurveToPoints")
    safe_set_mode(c2p, "COUNT")
    c2p.location = (-600, 200)
    links.new(store_parent_f.outputs["Geometry"], c2p.inputs["Curve"])
    links.new(in_node.outputs["Branch Count"], c2p.inputs["Count"])

    # Hierarchical Length Scaling along parent curve:
    # Lower branches are full length, upper branches become shorter
    pt_pfac = nodes.new("GeometryNodeInputNamedAttribute")
    pt_pfac.data_type = "FLOAT"
    pt_pfac.inputs["Name"].default_value = "parent_factor"
    pt_pfac.location = (-400, 450)

    mul_l_fall = nodes.new("ShaderNodeMath")
    mul_l_fall.operation = "MULTIPLY"
    mul_l_fall.location = (-250, 450)
    links.new(pt_pfac.outputs["Attribute"], mul_l_fall.inputs[0])
    links.new(in_node.outputs["Length Falloff"], mul_l_fall.inputs[1])

    sub_l_fall = nodes.new("ShaderNodeMath")
    sub_l_fall.operation = "SUBTRACT"
    sub_l_fall.inputs[0].default_value = 1.0
    sub_l_fall.location = (-100, 450)
    links.new(mul_l_fall.outputs["Value"], sub_l_fall.inputs[1])

    max_l_fall = nodes.new("ShaderNodeMath")
    max_l_fall.operation = "MAXIMUM"
    max_l_fall.inputs[1].default_value = 0.2
    max_l_fall.location = (50, 450)
    links.new(sub_l_fall.outputs["Value"], max_l_fall.inputs[0])

    eff_len = nodes.new("ShaderNodeMath")
    eff_len.operation = "MULTIPLY"
    eff_len.location = (200, 450)
    links.new(in_node.outputs["Branch Length"], eff_len.inputs[0])
    links.new(max_l_fall.outputs["Value"], eff_len.inputs[1])

    # Read Index for phyllotactic rotation
    idx_node = nodes.new("GeometryNodeInputIndex")
    idx_node.location = (-900, -400)

    # Rotation around Z (tangent): index * golden_angle + seed
    mult_phyl = nodes.new("ShaderNodeMath")
    mult_phyl.operation = "MULTIPLY"
    mult_phyl.location = (-700, -350)
    links.new(idx_node.outputs["Index"], mult_phyl.inputs[0])
    links.new(phyl_rad.outputs["Value"], mult_phyl.inputs[1])

    add_seed = nodes.new("ShaderNodeMath")
    add_seed.operation = "ADD"
    add_seed.location = (-500, -350)
    links.new(mult_phyl.outputs["Value"], add_seed.inputs[0])
    links.new(in_node.outputs["Seed"], add_seed.inputs[1])

    # Euler Rotation 1: Phyllotactic spin around Local Z axis (tangent)
    rot_spin = nodes.new("FunctionNodeRotateEuler")
    rot_spin.rotation_type = "AXIS_ANGLE"
    rot_spin.space = "LOCAL"
    rot_spin.inputs["Axis"].default_value = (0.0, 0.0, 1.0)
    rot_spin.location = (-300, 0)
    links.new(c2p.outputs["Rotation"], rot_spin.inputs["Rotation"])
    links.new(add_seed.outputs["Value"], rot_spin.inputs["Angle"])

    # Euler Rotation 2: Branch tilt outward around Local X axis
    rot_tilt = nodes.new("FunctionNodeRotateEuler")
    rot_tilt.rotation_type = "AXIS_ANGLE"
    rot_tilt.space = "LOCAL"
    rot_tilt.inputs["Axis"].default_value = (1.0, 0.0, 0.0)
    rot_tilt.location = (-100, 0)
    links.new(rot_spin.outputs["Rotation"], rot_tilt.inputs["Rotation"])
    links.new(deg_to_rad.outputs["Value"], rot_tilt.inputs["Angle"])

    # Store parent pivot on spawn points
    pos_spawn = nodes.new("GeometryNodeInputPosition")
    pos_spawn.location = (-600, 50)

    store_parent_pivot = nodes.new("GeometryNodeStoreNamedAttribute")
    store_parent_pivot.data_type = "FLOAT_VECTOR"
    store_parent_pivot.domain = "POINT"
    store_parent_pivot.inputs["Name"].default_value = "pp_parent_pivot"
    store_parent_pivot.location = (-400, 200)
    links.new(c2p.outputs["Points"], store_parent_pivot.inputs["Geometry"])
    links.new(pos_spawn.outputs["Position"], store_parent_pivot.inputs["Value"])

    # Base curve line primitive (pointing along Z axis, length 1.0)
    curve_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    curve_line.inputs["Start"].default_value = (0.0, 0.0, 0.0)
    curve_line.inputs["End"].default_value = (0.0, 0.0, 1.0)
    curve_line.location = (-100, 600)

    # Scale vector for instance: Branch Length along Z modulated by position
    combine_scale = nodes.new("ShaderNodeCombineXYZ")
    combine_scale.inputs["X"].default_value = 1.0
    combine_scale.inputs["Y"].default_value = 1.0
    combine_scale.location = (350, 450)
    links.new(eff_len.outputs["Value"], combine_scale.inputs["Z"])

    # Instance child curves on parent points
    instance_node = nodes.new("GeometryNodeInstanceOnPoints")
    instance_node.location = (150, 150)
    links.new(store_parent_pivot.outputs["Geometry"], instance_node.inputs["Points"])
    links.new(curve_line.outputs["Curve"], instance_node.inputs["Instance"])
    links.new(rot_tilt.outputs["Rotation"], instance_node.inputs["Rotation"])
    links.new(combine_scale.outputs["Vector"], instance_node.inputs["Scale"])

    # Realize Instances to convert back into editable curve splines
    realize_node = nodes.new("GeometryNodeRealizeInstances")
    realize_node.location = (350, 150)
    links.new(instance_node.outputs["Instances"], realize_node.inputs["Geometry"])

    # Resample child curves
    resample_node = nodes.new("GeometryNodeResampleCurve")
    safe_set_mode(resample_node, "COUNT")
    resample_node.location = (550, 150)
    links.new(realize_node.outputs["Geometry"], resample_node.inputs["Curve"])
    links.new(in_node.outputs["Resolution"], resample_node.inputs["Count"])

    # Spline parameter for child curve radius taper & wind weight
    spline_param = nodes.new("GeometryNodeSplineParameter")
    spline_param.location = (550, -100)

    # --- Hierarchical Radius Calculation ---
    # Read parent_radius and parent_factor inherited from parent curve
    read_prad = nodes.new("GeometryNodeInputNamedAttribute")
    read_prad.data_type = "FLOAT"
    read_prad.inputs["Name"].default_value = "parent_radius"
    read_prad.location = (550, -250)

    read_pfac = nodes.new("GeometryNodeInputNamedAttribute")
    read_pfac.data_type = "FLOAT"
    read_pfac.inputs["Name"].default_value = "parent_factor"
    read_pfac.location = (550, -400)

    # Base radius = parent_radius * Radius Ratio * (1.0 - 0.45 * parent_factor)
    mul_r_ratio = nodes.new("ShaderNodeMath")
    mul_r_ratio.operation = "MULTIPLY"
    mul_r_ratio.location = (750, -250)
    links.new(read_prad.outputs["Attribute"], mul_r_ratio.inputs[0])
    links.new(in_node.outputs["Radius Ratio"], mul_r_ratio.inputs[1])

    mul_pf_fall = nodes.new("ShaderNodeMath")
    mul_pf_fall.operation = "MULTIPLY"
    mul_pf_fall.inputs[0].default_value = 0.45
    mul_pf_fall.location = (750, -400)
    links.new(read_pfac.outputs["Attribute"], mul_pf_fall.inputs[1])

    sub_pf_fall = nodes.new("ShaderNodeMath")
    sub_pf_fall.operation = "SUBTRACT"
    sub_pf_fall.inputs[0].default_value = 1.0
    sub_pf_fall.location = (900, -400)
    links.new(mul_pf_fall.outputs["Value"], sub_pf_fall.inputs[1])

    mul_hier_base = nodes.new("ShaderNodeMath")
    mul_hier_base.operation = "MULTIPLY"
    mul_hier_base.location = (1050, -250)
    links.new(mul_r_ratio.outputs["Value"], mul_hier_base.inputs[0])
    links.new(sub_pf_fall.outputs["Value"], mul_hier_base.inputs[1])

    clamp_hier_base = nodes.new("ShaderNodeMath")
    clamp_hier_base.operation = "MAXIMUM"
    clamp_hier_base.inputs[1].default_value = 0.003
    clamp_hier_base.location = (1200, -250)
    links.new(mul_hier_base.outputs["Value"], clamp_hier_base.inputs[0])

    # Switch to fallback Base Radius if parent_radius is not present
    sw_base_r = nodes.new("GeometryNodeSwitch")
    sw_base_r.input_type = "FLOAT"
    sw_base_r.location = (1350, -250)
    links.new(read_prad.outputs["Exists"], sw_base_r.inputs["Switch"])
    links.new(in_node.outputs["Base Radius"], sw_base_r.inputs["False"])
    links.new(clamp_hier_base.outputs["Value"], sw_base_r.inputs["True"])

    # Tip radius: effective_base_r * 0.18 (clamped to >= 0.002)
    mul_tip_r = nodes.new("ShaderNodeMath")
    mul_tip_r.operation = "MULTIPLY"
    mul_tip_r.inputs[1].default_value = 0.18
    mul_tip_r.location = (1500, -350)
    links.new(sw_base_r.outputs["Output"], mul_tip_r.inputs[0])

    clamp_tip_r = nodes.new("ShaderNodeMath")
    clamp_tip_r.operation = "MAXIMUM"
    clamp_tip_r.inputs[1].default_value = 0.002
    clamp_tip_r.location = (1650, -350)
    links.new(mul_tip_r.outputs["Value"], clamp_tip_r.inputs[0])

    # Linear Taper along child branch: base_r * (1 - s) + tip_r * s
    inv_s = nodes.new("ShaderNodeMath")
    inv_s.operation = "SUBTRACT"
    inv_s.inputs[0].default_value = 1.0
    inv_s.location = (1500, -100)
    links.new(spline_param.outputs["Factor"], inv_s.inputs[1])

    mul_taper_base = nodes.new("ShaderNodeMath")
    mul_taper_base.operation = "MULTIPLY"
    mul_taper_base.location = (1650, -100)
    links.new(inv_s.outputs["Value"], mul_taper_base.inputs[0])
    links.new(sw_base_r.outputs["Output"], mul_taper_base.inputs[1])

    mul_taper_tip = nodes.new("ShaderNodeMath")
    mul_taper_tip.operation = "MULTIPLY"
    mul_taper_tip.location = (1650, -220)
    links.new(spline_param.outputs["Factor"], mul_taper_tip.inputs[0])
    links.new(clamp_tip_r.outputs["Value"], mul_taper_tip.inputs[1])

    taper_sum = nodes.new("ShaderNodeMath")
    taper_sum.operation = "ADD"
    taper_sum.location = (1800, -150)
    links.new(mul_taper_base.outputs["Value"], taper_sum.inputs[0])
    links.new(mul_taper_tip.outputs["Value"], taper_sum.inputs[1])

    # --- Joint Collar Flare (Smooth Trunk-to-Branch Connection) ---
    # Collar falloff over first 22% of branch length: max(0.0, 1.0 - (s / 0.22))^2
    div_s_flare = nodes.new("ShaderNodeMath")
    div_s_flare.operation = "DIVIDE"
    div_s_flare.inputs[1].default_value = 0.22
    div_s_flare.location = (1500, 80)
    links.new(spline_param.outputs["Factor"], div_s_flare.inputs[0])

    sub_flare_f = nodes.new("ShaderNodeMath")
    sub_flare_f.operation = "SUBTRACT"
    sub_flare_f.inputs[0].default_value = 1.0
    sub_flare_f.location = (1650, 80)
    links.new(div_s_flare.outputs["Value"], sub_flare_f.inputs[1])

    max_flare_f = nodes.new("ShaderNodeMath")
    max_flare_f.operation = "MAXIMUM"
    max_flare_f.inputs[1].default_value = 0.0
    max_flare_f.location = (1800, 80)
    links.new(sub_flare_f.outputs["Value"], max_flare_f.inputs[0])

    pow_flare_f = nodes.new("ShaderNodeMath")
    pow_flare_f.operation = "POWER"
    pow_flare_f.inputs[1].default_value = 2.0
    pow_flare_f.location = (1950, 80)
    links.new(max_flare_f.outputs["Value"], pow_flare_f.inputs[0])

    # Flare amplitude: max(0.0, parent_radius - effective_base_r) * Joint Flare
    sub_r_diff = nodes.new("ShaderNodeMath")
    sub_r_diff.operation = "SUBTRACT"
    sub_r_diff.location = (1650, 200)
    links.new(read_prad.outputs["Attribute"], sub_r_diff.inputs[0])
    links.new(sw_base_r.outputs["Output"], sub_r_diff.inputs[1])

    max_r_diff = nodes.new("ShaderNodeMath")
    max_r_diff.operation = "MAXIMUM"
    max_r_diff.inputs[1].default_value = 0.0
    max_r_diff.location = (1800, 200)
    links.new(sub_r_diff.outputs["Value"], max_r_diff.inputs[0])

    mul_flare_amp = nodes.new("ShaderNodeMath")
    mul_flare_amp.operation = "MULTIPLY"
    mul_flare_amp.location = (1950, 200)
    links.new(max_r_diff.outputs["Value"], mul_flare_amp.inputs[0])
    links.new(in_node.outputs["Joint Flare"], mul_flare_amp.inputs[1])

    mul_flare_boost = nodes.new("ShaderNodeMath")
    mul_flare_boost.operation = "MULTIPLY"
    mul_flare_boost.location = (2100, 140)
    links.new(pow_flare_f.outputs["Value"], mul_flare_boost.inputs[0])
    links.new(mul_flare_amp.outputs["Value"], mul_flare_boost.inputs[1])

    # Total final radius = taper_sum + collar_boost
    rad_final = nodes.new("ShaderNodeMath")
    rad_final.operation = "ADD"
    rad_final.location = (2250, 0)
    links.new(taper_sum.outputs["Value"], rad_final.inputs[0])
    links.new(mul_flare_boost.outputs["Value"], rad_final.inputs[1])

    # Set Curve Radius
    set_radius = nodes.new("GeometryNodeSetCurveRadius")
    set_radius.location = (800, 150)
    links.new(resample_node.outputs["Curve"], set_radius.inputs["Curve"])
    links.new(rad_final.outputs["Value"], set_radius.inputs["Radius"])

    # Apply Noise Displacement Sub-Group
    noise_sub = build_noise_displace_group()
    noise_group_node = nodes.new("GeometryNodeGroup")
    noise_group_node.node_tree = noise_sub
    noise_group_node.location = (1000, 150)
    links.new(set_radius.outputs["Curve"], noise_group_node.inputs["Geometry"])
    links.new(in_node.outputs["Noise Strength"], noise_group_node.inputs["Strength"])

    # Gravitropism droop / arch along branch curve:
    # Displacement Z = -1.0 * Gravitropism * (Factor ^ 1.4)
    fac_pow = nodes.new("ShaderNodeMath")
    fac_pow.operation = "POWER"
    fac_pow.inputs[1].default_value = 1.4
    fac_pow.location = (850, -300)
    links.new(spline_param.outputs["Factor"], fac_pow.inputs[0])

    grav_mul1 = nodes.new("ShaderNodeMath")
    grav_mul1.operation = "MULTIPLY"
    grav_mul1.location = (1000, -300)
    links.new(fac_pow.outputs["Value"], grav_mul1.inputs[0])
    links.new(in_node.outputs["Gravitropism"], grav_mul1.inputs[1])

    grav_mul2 = nodes.new("ShaderNodeMath")
    grav_mul2.operation = "MULTIPLY"
    grav_mul2.inputs[1].default_value = -1.0
    grav_mul2.location = (1150, -300)
    links.new(grav_mul1.outputs["Value"], grav_mul2.inputs[0])

    grav_offset = nodes.new("ShaderNodeCombineXYZ")
    grav_offset.inputs["X"].default_value = 0.0
    grav_offset.inputs["Y"].default_value = 0.0
    grav_offset.location = (1300, -300)
    links.new(grav_mul2.outputs["Value"], grav_offset.inputs["Z"])

    set_grav = nodes.new("GeometryNodeSetPosition")
    set_grav.location = (1150, 150)
    links.new(noise_group_node.outputs["Geometry"], set_grav.inputs["Geometry"])
    links.new(grav_offset.outputs["Vector"], set_grav.inputs["Offset"])

    # Store Procedural Attributes for Pivot Painter 2.0
    # 1. Tier Index
    store_tier = nodes.new("GeometryNodeStoreNamedAttribute")
    store_tier.data_type = "INT"
    store_tier.domain = "POINT"
    store_tier.inputs["Name"].default_value = "pp_tier"
    store_tier.location = (1350, 150)
    links.new(set_grav.outputs["Geometry"], store_tier.inputs["Geometry"])
    links.new(in_node.outputs["Tier Index"], store_tier.inputs["Value"])

    # 2. Local Wind Weight (Curve Factor)
    store_wind = nodes.new("GeometryNodeStoreNamedAttribute")
    store_wind.data_type = "FLOAT"
    store_wind.domain = "POINT"
    store_wind.inputs["Name"].default_value = "pp_wind_weight"
    store_wind.location = (1400, 150)
    links.new(store_tier.outputs["Geometry"], store_wind.inputs["Geometry"])
    links.new(spline_param.outputs["Factor"], store_wind.inputs["Value"])

    # 3. Store evaluated radius and factor on child curve for recursive propagation to next tier!
    store_for_child_r = nodes.new("GeometryNodeStoreNamedAttribute")
    store_for_child_r.data_type = "FLOAT"
    store_for_child_r.domain = "POINT"
    store_for_child_r.inputs["Name"].default_value = "parent_radius"
    store_for_child_r.location = (1600, 150)
    links.new(store_wind.outputs["Geometry"], store_for_child_r.inputs["Geometry"])
    links.new(rad_final.outputs["Value"], store_for_child_r.inputs["Value"])

    store_for_child_f = nodes.new("GeometryNodeStoreNamedAttribute")
    store_for_child_f.data_type = "FLOAT"
    store_for_child_f.domain = "POINT"
    store_for_child_f.inputs["Name"].default_value = "parent_factor"
    store_for_child_f.location = (1800, 150)
    links.new(store_for_child_r.outputs["Geometry"], store_for_child_f.inputs["Geometry"])
    links.new(spline_param.outputs["Factor"], store_for_child_f.inputs["Value"])

    links.new(store_for_child_f.outputs["Geometry"], out_node.inputs["Child Curves"])
    links.new(store_parent_pivot.outputs["Geometry"], out_node.inputs["Spawn Points"])

    return tree


# ---------------------------------------------------------------------------
# 4. Sub-Group: Leaves & Foliage Instancer
# ---------------------------------------------------------------------------
def build_foliage_generator_group(force_rebuild=False):
    """Builds foliage instancing node group supporting procedural diamonds, cards, and custom meshes."""
    name = "Tree_Sub_Foliage_Generator"
    if not force_rebuild and name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name], do_unlink=True)

    tree = bpy.data.node_groups.new(name=name, type="GeometryNodeTree")
    tree.interface.clear()

    # Sockets
    add_interface_socket(tree, "Twig Curves", "INPUT", "NodeSocketGeometry")
    add_interface_socket(tree, "Leaf Mode", "INPUT", "NodeSocketInt", default_value=0) # 0: Diamond, 1: Card, 2: Custom
    add_interface_socket(tree, "Custom Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Count per Branch", "INPUT", "NodeSocketInt", default_value=10, min_val=1, max_val=60)
    add_interface_socket(tree, "Start Factor", "INPUT", "NodeSocketFloat", default_value=0.4, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Leaf Scale", "INPUT", "NodeSocketFloat", default_value=0.25, min_val=0.01, max_val=3.0)
    add_interface_socket(tree, "Pitch Angle", "INPUT", "NodeSocketFloat", default_value=35.0, min_val=-180.0, max_val=180.0)
    add_interface_socket(tree, "Roll Angle", "INPUT", "NodeSocketFloat", default_value=25.0, min_val=-180.0, max_val=180.0)
    add_interface_socket(tree, "Sun Alignment", "INPUT", "NodeSocketFloat", default_value=0.45, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Sun Vector", "INPUT", "NodeSocketVector", default_value=(5.0, 5.0, 15.0))
    add_interface_socket(tree, "Seed", "INPUT", "NodeSocketInt", default_value=42)

    add_interface_socket(tree, "Foliage Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    links = tree.links

    in_node = nodes.new("NodeGroupInput")
    in_node.location = (-1100, 0)
    out_node = nodes.new("NodeGroupOutput")
    out_node.location = (1500, 0)

    # Trim twig curves so foliage only sprouts near the tips
    trim_twigs = nodes.new("GeometryNodeTrimCurve")
    trim_twigs.location = (-1050, 200)
    links.new(in_node.outputs["Twig Curves"], trim_twigs.inputs["Curve"])
    links.new(in_node.outputs["Start Factor"], trim_twigs.inputs[2])

    # Sample points on trimmed twigs
    c2p = nodes.new("GeometryNodeCurveToPoints")
    safe_set_mode(c2p, "COUNT")
    c2p.location = (-850, 200)
    links.new(trim_twigs.outputs["Curve"], c2p.inputs["Curve"])
    links.new(in_node.outputs["Count per Branch"], c2p.inputs["Count"])

    # Rotation adjustments: Pitch & Roll
    deg_pitch = nodes.new("ShaderNodeMath")
    deg_pitch.operation = "RADIANS"
    deg_pitch.location = (-650, 0)
    links.new(in_node.outputs["Pitch Angle"], deg_pitch.inputs[0])

    deg_roll = nodes.new("ShaderNodeMath")
    deg_roll.operation = "RADIANS"
    deg_roll.location = (-650, -150)
    links.new(in_node.outputs["Roll Angle"], deg_roll.inputs[0])

    rot_pitch = nodes.new("FunctionNodeRotateEuler")
    rot_pitch.rotation_type = "AXIS_ANGLE"
    rot_pitch.space = "LOCAL"
    rot_pitch.inputs["Axis"].default_value = (1.0, 0.0, 0.0)
    rot_pitch.location = (-450, 100)
    links.new(c2p.outputs["Rotation"], rot_pitch.inputs["Rotation"])
    links.new(deg_pitch.outputs["Value"], rot_pitch.inputs["Angle"])

    rot_roll = nodes.new("FunctionNodeRotateEuler")
    rot_roll.rotation_type = "AXIS_ANGLE"
    rot_roll.space = "LOCAL"
    rot_roll.inputs["Axis"].default_value = (0.0, 1.0, 0.0)
    rot_roll.location = (-250, 100)
    links.new(rot_pitch.outputs["Rotation"], rot_roll.inputs["Rotation"])
    links.new(deg_roll.outputs["Value"], rot_roll.inputs["Angle"])

    # Sun Alignment via AlignEulerToVector
    align_sun = nodes.new("FunctionNodeAlignEulerToVector")
    align_sun.axis = "Z"
    align_sun.location = (-50, 100)
    links.new(rot_roll.outputs["Rotation"], align_sun.inputs["Rotation"])
    links.new(in_node.outputs["Sun Alignment"], align_sun.inputs["Factor"])
    links.new(in_node.outputs["Sun Vector"], align_sun.inputs["Vector"])

    # Procedural Leaf Geometry Options (botanical scale in meters):
    # 1. Procedural 3D Diamond Leaf Mesh (MeshGrid with slight curve)
    grid_leaf = nodes.new("GeometryNodeMeshGrid")
    grid_leaf.inputs["Size X"].default_value = 0.12
    grid_leaf.inputs["Size Y"].default_value = 0.22
    grid_leaf.inputs["Vertices X"].default_value = 3
    grid_leaf.inputs["Vertices Y"].default_value = 4
    grid_leaf.location = (-600, -400)

    # Offset grid so pivot is at base of petiole (0, 0, 0)
    offset_leaf = nodes.new("GeometryNodeSetPosition")
    offset_leaf.inputs["Offset"].default_value = (0.0, 0.11, 0.0)
    offset_leaf.location = (-400, -400)
    links.new(grid_leaf.outputs["Mesh"], offset_leaf.inputs["Geometry"])

    # 2. Card Cutout (flat quad)
    card_leaf = nodes.new("GeometryNodeMeshGrid")
    card_leaf.inputs["Size X"].default_value = 0.14
    card_leaf.inputs["Size Y"].default_value = 0.24
    card_leaf.inputs["Vertices X"].default_value = 2
    card_leaf.inputs["Vertices Y"].default_value = 2
    card_leaf.location = (-600, -600)

    offset_card = nodes.new("GeometryNodeSetPosition")
    offset_card.inputs["Offset"].default_value = (0.0, 0.12, 0.0)
    offset_card.location = (-400, -600)
    links.new(card_leaf.outputs["Mesh"], offset_card.inputs["Geometry"])

    # 3. Custom Object Info
    custom_obj_info = nodes.new("GeometryNodeObjectInfo")
    custom_obj_info.transform_space = "RELATIVE"
    custom_obj_info.location = (-400, -800)
    links.new(in_node.outputs["Custom Object"], custom_obj_info.inputs["Object"])

    # Switch between Card vs Diamond
    switch_card = nodes.new("GeometryNodeSwitch")
    switch_card.input_type = "GEOMETRY"
    switch_card.location = (-150, -450)
    # If Leaf Mode == 1, switch to card
    comp_mode1 = nodes.new("ShaderNodeMath")
    comp_mode1.operation = "COMPARE"
    comp_mode1.inputs[1].default_value = 1.0
    comp_mode1.inputs[2].default_value = 0.1
    comp_mode1.location = (-350, -300)
    links.new(in_node.outputs["Leaf Mode"], comp_mode1.inputs[0])
    links.new(comp_mode1.outputs["Value"], switch_card.inputs["Switch"])
    links.new(offset_leaf.outputs["Geometry"], switch_card.inputs["False"])
    links.new(offset_card.outputs["Geometry"], switch_card.inputs["True"])

    # Switch between (Card/Diamond) vs Custom Object
    switch_custom = nodes.new("GeometryNodeSwitch")
    switch_custom.input_type = "GEOMETRY"
    switch_custom.location = (50, -500)
    comp_mode2 = nodes.new("ShaderNodeMath")
    comp_mode2.operation = "GREATER_THAN"
    comp_mode2.inputs[1].default_value = 1.5
    comp_mode2.location = (-150, -700)
    links.new(in_node.outputs["Leaf Mode"], comp_mode2.inputs[0])
    links.new(comp_mode2.outputs["Value"], switch_custom.inputs["Switch"])
    links.new(switch_card.outputs["Output"], switch_custom.inputs["False"])
    links.new(custom_obj_info.outputs["Geometry"], switch_custom.inputs["True"])

    # Random scale variation for leaves
    rand_scale = nodes.new("FunctionNodeRandomValue")
    rand_scale.data_type = "FLOAT"
    rand_scale.inputs["Min"].default_value = 0.8
    rand_scale.inputs["Max"].default_value = 1.2
    rand_scale.location = (-50, 300)

    mult_scale = nodes.new("ShaderNodeMath")
    mult_scale.operation = "MULTIPLY"
    mult_scale.location = (150, 300)
    links.new(in_node.outputs["Leaf Scale"], mult_scale.inputs[0])
    links.new(rand_scale.outputs["Value"], mult_scale.inputs[1])

    scale_vec = nodes.new("ShaderNodeCombineXYZ")
    scale_vec.location = (300, 300)
    links.new(mult_scale.outputs["Value"], scale_vec.inputs["X"])
    links.new(mult_scale.outputs["Value"], scale_vec.inputs["Y"])
    links.new(mult_scale.outputs["Value"], scale_vec.inputs["Z"])

    # Instance foliage on twig points
    inst_node = nodes.new("GeometryNodeInstanceOnPoints")
    inst_node.location = (300, 100)
    links.new(c2p.outputs["Points"], inst_node.inputs["Points"])
    links.new(switch_custom.outputs["Output"], inst_node.inputs["Instance"])
    links.new(align_sun.outputs["Rotation"], inst_node.inputs["Rotation"])
    links.new(scale_vec.outputs["Vector"], inst_node.inputs["Scale"])

    # Realize foliage instances
    realize_leaves = nodes.new("GeometryNodeRealizeInstances")
    realize_leaves.location = (500, 100)
    links.new(inst_node.outputs["Instances"], realize_leaves.inputs["Geometry"])

    # Store Pivot Painter Attributes for leaves
    store_leaf_tier = nodes.new("GeometryNodeStoreNamedAttribute")
    store_leaf_tier.data_type = "INT"
    store_leaf_tier.domain = "POINT"
    store_leaf_tier.inputs["Name"].default_value = "pp_tier"
    store_leaf_tier.inputs["Value"].default_value = 4 # Leaves = Tier 4
    store_leaf_tier.location = (700, 100)
    links.new(realize_leaves.outputs["Geometry"], store_leaf_tier.inputs["Geometry"])

    store_leaf_wind = nodes.new("GeometryNodeStoreNamedAttribute")
    store_leaf_wind.data_type = "FLOAT"
    store_leaf_wind.domain = "POINT"
    store_leaf_wind.inputs["Name"].default_value = "pp_wind_weight"
    store_leaf_wind.inputs["Value"].default_value = 1.0
    store_leaf_wind.location = (900, 100)
    links.new(store_leaf_tier.outputs["Geometry"], store_leaf_wind.inputs["Geometry"])

    links.new(store_leaf_wind.outputs["Geometry"], out_node.inputs["Foliage Geometry"])
    return tree


# ---------------------------------------------------------------------------
# 5. Master Geometry Node Tree: Procedural Tree & Foliage Suite
# ---------------------------------------------------------------------------
def build_procedural_tree_suite_master(force_rebuild=False):
    """Builds the comprehensive master tree modifier node graph."""
    master_name = "Procedural_Tree_Suite"

    # Ensure all sub-groups exist and have up-to-date sockets
    noise_sub = build_noise_displace_group(force_rebuild=force_rebuild)
    trop_sub = build_tropisms_group(force_rebuild=force_rebuild)
    branch_tier_sub = build_branch_tier_group(force_rebuild=force_rebuild)
    foliage_sub = build_foliage_generator_group(force_rebuild=force_rebuild)

    if not force_rebuild and master_name in bpy.data.node_groups:
        cached_tree = bpy.data.node_groups[master_name]
        socket_names = [item.name for item in cached_tree.interface.items_tree if getattr(item, 'in_out', None) == 'INPUT']
        if "Tier 1 Radius Ratio" in socket_names and "Tier 1 Joint Flare" in socket_names:
            # Verify CurveToMesh Scale is connected
            c2m_nodes = [n for n in cached_tree.nodes if n.type == 'CURVE_TO_MESH']
            if c2m_nodes:
                c2m = c2m_nodes[0]
                if len(c2m.inputs["Scale"].links) == 0:
                    rad_nodes = [n for n in cached_tree.nodes if n.type == 'INPUT_RADIUS']
                    rad = rad_nodes[0] if rad_nodes else cached_tree.nodes.new("GeometryNodeInputRadius")
                    cached_tree.links.new(rad.outputs["Radius"], c2m.inputs["Scale"])
                c2m.inputs["Fill Caps"].default_value = True
            return cached_tree
        bpy.data.node_groups.remove(cached_tree, do_unlink=True)
    elif master_name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[master_name], do_unlink=True)

    tree = bpy.data.node_groups.new(name=master_name, type="GeometryNodeTree")
    tree.interface.clear()

    # Define all interface sockets
    # Category 1: Trunk & Foundation
    add_interface_socket(tree, "Trunk Height", "INPUT", "NodeSocketFloat", default_value=10.0, min_val=0.5, max_val=100.0)
    add_interface_socket(tree, "Trunk Resolution", "INPUT", "NodeSocketInt", default_value=32, min_val=4, max_val=256)
    add_interface_socket(tree, "Trunk Base Radius", "INPUT", "NodeSocketFloat", default_value=0.45, min_val=0.01, max_val=5.0)
    add_interface_socket(tree, "Trunk Tip Radius", "INPUT", "NodeSocketFloat", default_value=0.06, min_val=0.001, max_val=2.0)
    add_interface_socket(tree, "Trunk Taper Power", "INPUT", "NodeSocketFloat", default_value=1.1, min_val=0.1, max_val=5.0)
    add_interface_socket(tree, "Trunk Noise Scale", "INPUT", "NodeSocketFloat", default_value=0.6, min_val=0.01, max_val=20.0)
    add_interface_socket(tree, "Trunk Noise Strength", "INPUT", "NodeSocketFloat", default_value=0.4, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Trunk Seed", "INPUT", "NodeSocketInt", default_value=1)
    add_interface_socket(tree, "Use Guide Curve", "INPUT", "NodeSocketBool", default_value=False)
    add_interface_socket(tree, "Guide Curve Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Guide Influence", "INPUT", "NodeSocketFloat", default_value=0.8, min_val=0.0, max_val=1.0)

    # Category 2: Biological Tropisms
    add_interface_socket(tree, "Gravitropism", "INPUT", "NodeSocketFloat", default_value=-0.1, min_val=-2.0, max_val=2.0)
    add_interface_socket(tree, "Phototropism", "INPUT", "NodeSocketFloat", default_value=0.15, min_val=-2.0, max_val=2.0)
    add_interface_socket(tree, "Sun Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Sun Vector", "INPUT", "NodeSocketVector", default_value=(5.0, 5.0, 15.0))
    add_interface_socket(tree, "Thigmotropism", "INPUT", "NodeSocketFloat", default_value=0.0, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Obstacle Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Obstacle Avoidance Dist", "INPUT", "NodeSocketFloat", default_value=1.5, min_val=0.1, max_val=20.0)

    # Category 3: Primary Branches (Tier 1)
    add_interface_socket(tree, "Tier 1 Enable", "INPUT", "NodeSocketBool", default_value=True)
    add_interface_socket(tree, "Tier 1 Count", "INPUT", "NodeSocketInt", default_value=7, min_val=0, max_val=100)
    add_interface_socket(tree, "Tier 1 Start Factor", "INPUT", "NodeSocketFloat", default_value=0.32, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 1 End Factor", "INPUT", "NodeSocketFloat", default_value=0.92, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 1 Length", "INPUT", "NodeSocketFloat", default_value=4.8, min_val=0.1, max_val=50.0)
    add_interface_socket(tree, "Tier 1 Length Falloff", "INPUT", "NodeSocketFloat", default_value=0.55, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 1 Angle", "INPUT", "NodeSocketFloat", default_value=55.0, min_val=0.0, max_val=180.0)
    add_interface_socket(tree, "Tier 1 Base Radius", "INPUT", "NodeSocketFloat", default_value=0.14, min_val=0.001, max_val=2.0)
    add_interface_socket(tree, "Tier 1 Tip Radius", "INPUT", "NodeSocketFloat", default_value=0.035, min_val=0.001, max_val=1.0)
    add_interface_socket(tree, "Tier 1 Radius Ratio", "INPUT", "NodeSocketFloat", default_value=0.48, min_val=0.05, max_val=0.95)
    add_interface_socket(tree, "Tier 1 Joint Flare", "INPUT", "NodeSocketFloat", default_value=0.65, min_val=0.0, max_val=2.0)
    add_interface_socket(tree, "Tier 1 Phyllotaxis Angle", "INPUT", "NodeSocketFloat", default_value=137.5, min_val=0.0, max_val=360.0)
    add_interface_socket(tree, "Tier 1 Gravitropism", "INPUT", "NodeSocketFloat", default_value=0.15, min_val=-2.0, max_val=2.0)
    add_interface_socket(tree, "Tier 1 Noise Strength", "INPUT", "NodeSocketFloat", default_value=0.25, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Tier 1 Seed", "INPUT", "NodeSocketInt", default_value=10)

    # Category 4: Secondary Branches (Tier 2)
    add_interface_socket(tree, "Tier 2 Enable", "INPUT", "NodeSocketBool", default_value=True)
    add_interface_socket(tree, "Tier 2 Count", "INPUT", "NodeSocketInt", default_value=5, min_val=0, max_val=100)
    add_interface_socket(tree, "Tier 2 Start Factor", "INPUT", "NodeSocketFloat", default_value=0.35, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 2 End Factor", "INPUT", "NodeSocketFloat", default_value=0.90, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 2 Length", "INPUT", "NodeSocketFloat", default_value=2.2, min_val=0.1, max_val=25.0)
    add_interface_socket(tree, "Tier 2 Length Falloff", "INPUT", "NodeSocketFloat", default_value=0.5, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 2 Angle", "INPUT", "NodeSocketFloat", default_value=48.0, min_val=0.0, max_val=180.0)
    add_interface_socket(tree, "Tier 2 Base Radius", "INPUT", "NodeSocketFloat", default_value=0.035, min_val=0.001, max_val=1.0)
    add_interface_socket(tree, "Tier 2 Tip Radius", "INPUT", "NodeSocketFloat", default_value=0.012, min_val=0.001, max_val=0.5)
    add_interface_socket(tree, "Tier 2 Radius Ratio", "INPUT", "NodeSocketFloat", default_value=0.48, min_val=0.05, max_val=0.95)
    add_interface_socket(tree, "Tier 2 Joint Flare", "INPUT", "NodeSocketFloat", default_value=0.65, min_val=0.0, max_val=2.0)
    add_interface_socket(tree, "Tier 2 Phyllotaxis Angle", "INPUT", "NodeSocketFloat", default_value=137.5, min_val=0.0, max_val=360.0)
    add_interface_socket(tree, "Tier 2 Gravitropism", "INPUT", "NodeSocketFloat", default_value=0.10, min_val=-2.0, max_val=2.0)
    add_interface_socket(tree, "Tier 2 Noise Strength", "INPUT", "NodeSocketFloat", default_value=0.20, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Tier 2 Seed", "INPUT", "NodeSocketInt", default_value=20)

    # Category 5: Twigs (Tier 3)
    add_interface_socket(tree, "Tier 3 Enable", "INPUT", "NodeSocketBool", default_value=True)
    add_interface_socket(tree, "Tier 3 Count", "INPUT", "NodeSocketInt", default_value=4, min_val=0, max_val=80)
    add_interface_socket(tree, "Tier 3 Start Factor", "INPUT", "NodeSocketFloat", default_value=0.40, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 3 End Factor", "INPUT", "NodeSocketFloat", default_value=0.95, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 3 Length", "INPUT", "NodeSocketFloat", default_value=0.9, min_val=0.05, max_val=10.0)
    add_interface_socket(tree, "Tier 3 Length Falloff", "INPUT", "NodeSocketFloat", default_value=0.4, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Tier 3 Angle", "INPUT", "NodeSocketFloat", default_value=42.0, min_val=0.0, max_val=180.0)
    add_interface_socket(tree, "Tier 3 Base Radius", "INPUT", "NodeSocketFloat", default_value=0.012, min_val=0.001, max_val=0.5)
    add_interface_socket(tree, "Tier 3 Tip Radius", "INPUT", "NodeSocketFloat", default_value=0.004, min_val=0.001, max_val=0.2)
    add_interface_socket(tree, "Tier 3 Radius Ratio", "INPUT", "NodeSocketFloat", default_value=0.45, min_val=0.05, max_val=0.95)
    add_interface_socket(tree, "Tier 3 Joint Flare", "INPUT", "NodeSocketFloat", default_value=0.60, min_val=0.0, max_val=2.0)
    add_interface_socket(tree, "Tier 3 Seed", "INPUT", "NodeSocketInt", default_value=30)

    # Category 6: Leaves & Foliage
    add_interface_socket(tree, "Leaves Enable", "INPUT", "NodeSocketBool", default_value=True)
    add_interface_socket(tree, "Leaf Mode", "INPUT", "NodeSocketInt", default_value=0) # 0: Diamond, 1: Card, 2: Custom
    add_interface_socket(tree, "Custom Leaf Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Leaves Count per Branch", "INPUT", "NodeSocketInt", default_value=5, min_val=0, max_val=60)
    add_interface_socket(tree, "Leaves Start Factor", "INPUT", "NodeSocketFloat", default_value=0.55, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Leaf Scale", "INPUT", "NodeSocketFloat", default_value=1.0, min_val=0.01, max_val=5.0)
    add_interface_socket(tree, "Leaf Pitch", "INPUT", "NodeSocketFloat", default_value=35.0, min_val=-180.0, max_val=180.0)
    add_interface_socket(tree, "Leaf Roll", "INPUT", "NodeSocketFloat", default_value=25.0, min_val=-180.0, max_val=180.0)
    add_interface_socket(tree, "Sun Alignment", "INPUT", "NodeSocketFloat", default_value=0.4, min_val=0.0, max_val=1.0)
    add_interface_socket(tree, "Leaf Seed", "INPUT", "NodeSocketInt", default_value=100)

    # Category 7: Wind & Secondary Motion
    add_interface_socket(tree, "Wind Enable", "INPUT", "NodeSocketBool", default_value=True)
    add_interface_socket(tree, "Wind Speed", "INPUT", "NodeSocketFloat", default_value=1.5, min_val=0.0, max_val=20.0)
    add_interface_socket(tree, "Wind Strength", "INPUT", "NodeSocketFloat", default_value=0.2, min_val=0.0, max_val=5.0)
    add_interface_socket(tree, "Wind Direction", "INPUT", "NodeSocketVector", default_value=(1.0, 0.3, 0.0))

    # Category 8: Scan Extension (Photogrammetry Blending)
    add_interface_socket(tree, "Scan Enable", "INPUT", "NodeSocketBool", default_value=False)
    add_interface_socket(tree, "Scan Object", "INPUT", "NodeSocketObject")
    add_interface_socket(tree, "Scan Point Count", "INPUT", "NodeSocketInt", default_value=12, min_val=1, max_val=200)
    add_interface_socket(tree, "Scan Branch Length", "INPUT", "NodeSocketFloat", default_value=4.0, min_val=0.1, max_val=20.0)
    add_interface_socket(tree, "Scan Remesh Union", "INPUT", "NodeSocketBool", default_value=False)
    add_interface_socket(tree, "Scan Voxel Size", "INPUT", "NodeSocketFloat", default_value=0.05, min_val=0.005, max_val=0.5)
    add_interface_socket(tree, "Scan Voxel Adaptivity", "INPUT", "NodeSocketFloat", default_value=0.05, min_val=0.0, max_val=1.0)

    # Category 9: Meshing & Materials
    add_interface_socket(tree, "Mesh Resolution", "INPUT", "NodeSocketInt", default_value=12, min_val=3, max_val=64)
    add_interface_socket(tree, "Bark Material", "INPUT", "NodeSocketMaterial")
    add_interface_socket(tree, "Leaf Material", "INPUT", "NodeSocketMaterial")

    add_interface_socket(tree, "Geometry", "OUTPUT", "NodeSocketGeometry")

    nodes = tree.nodes
    links = tree.links

    in_node = nodes.new("NodeGroupInput")
    in_node.location = (-1600, 0)
    out_node = nodes.new("NodeGroupOutput")
    out_node.location = (2400, 0)

    # 1. Base Trunk Primitive
    trunk_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    trunk_line.inputs["Start"].default_value = (0.0, 0.0, 0.0)
    trunk_line.location = (-1300, 400)

    trunk_end = nodes.new("ShaderNodeCombineXYZ")
    trunk_end.inputs["X"].default_value = 0.0
    trunk_end.inputs["Y"].default_value = 0.0
    trunk_end.location = (-1450, 400)
    links.new(in_node.outputs["Trunk Height"], trunk_end.inputs["Z"])
    links.new(trunk_end.outputs["Vector"], trunk_line.inputs["End"])

    # Trunk Resample
    trunk_resample = nodes.new("GeometryNodeResampleCurve")
    safe_set_mode(trunk_resample, "COUNT")
    trunk_resample.location = (-1100, 400)
    links.new(trunk_line.outputs["Curve"], trunk_resample.inputs["Curve"])
    links.new(in_node.outputs["Trunk Resolution"], trunk_resample.inputs["Count"])

    # Trunk Noise Displacement
    noise_sub = build_noise_displace_group()
    trunk_noise = nodes.new("GeometryNodeGroup")
    trunk_noise.node_tree = noise_sub
    trunk_noise.location = (-900, 400)
    links.new(trunk_resample.outputs["Curve"], trunk_noise.inputs["Geometry"])
    links.new(in_node.outputs["Trunk Noise Scale"], trunk_noise.inputs["Scale"])
    links.new(in_node.outputs["Trunk Noise Strength"], trunk_noise.inputs["Strength"])

    # Trunk Tropisms
    trop_sub = build_tropisms_group()
    trunk_trop = nodes.new("GeometryNodeGroup")
    trunk_trop.node_tree = trop_sub
    trunk_trop.location = (-700, 400)
    links.new(trunk_noise.outputs["Geometry"], trunk_trop.inputs["Geometry"])
    links.new(in_node.outputs["Gravitropism"], trunk_trop.inputs["Gravitropism"])
    links.new(in_node.outputs["Phototropism"], trunk_trop.inputs["Phototropism"])
    links.new(in_node.outputs["Sun Object"], trunk_trop.inputs["Sun Object"])
    links.new(in_node.outputs["Sun Vector"], trunk_trop.inputs["Sun Vector"])
    links.new(in_node.outputs["Thigmotropism"], trunk_trop.inputs["Thigmotropism"])
    links.new(in_node.outputs["Obstacle Object"], trunk_trop.inputs["Obstacle Object"])
    links.new(in_node.outputs["Obstacle Avoidance Dist"], trunk_trop.inputs["Obstacle Distance"])

    # Trunk Radius Taper
    trunk_param = nodes.new("GeometryNodeSplineParameter")
    trunk_param.location = (-700, 100)

    trunk_pow = nodes.new("ShaderNodeMath")
    trunk_pow.operation = "POWER"
    trunk_pow.location = (-500, 100)
    links.new(trunk_param.outputs["Factor"], trunk_pow.inputs[0])
    links.new(in_node.outputs["Trunk Taper Power"], trunk_pow.inputs[1])

    trunk_inv = nodes.new("ShaderNodeMath")
    trunk_inv.operation = "SUBTRACT"
    trunk_inv.inputs[0].default_value = 1.0
    trunk_inv.location = (-350, 100)
    links.new(trunk_pow.outputs["Value"], trunk_inv.inputs[1])

    trunk_r_base = nodes.new("ShaderNodeMath")
    trunk_r_base.operation = "MULTIPLY"
    trunk_r_base.location = (-200, 150)
    links.new(trunk_inv.outputs["Value"], trunk_r_base.inputs[0])
    links.new(in_node.outputs["Trunk Base Radius"], trunk_r_base.inputs[1])

    trunk_r_tip = nodes.new("ShaderNodeMath")
    trunk_r_tip.operation = "MULTIPLY"
    trunk_r_tip.location = (-200, 0)
    links.new(trunk_pow.outputs["Value"], trunk_r_tip.inputs[0])
    links.new(in_node.outputs["Trunk Tip Radius"], trunk_r_tip.inputs[1])

    trunk_rad = nodes.new("ShaderNodeMath")
    trunk_rad.operation = "ADD"
    trunk_rad.location = (-50, 100)
    links.new(trunk_r_base.outputs["Value"], trunk_rad.inputs[0])
    links.new(trunk_r_tip.outputs["Value"], trunk_rad.inputs[1])

    trunk_set_rad = nodes.new("GeometryNodeSetCurveRadius")
    trunk_set_rad.location = (-500, 400)
    links.new(trunk_trop.outputs["Geometry"], trunk_set_rad.inputs["Curve"])
    links.new(trunk_rad.outputs["Value"], trunk_set_rad.inputs["Radius"])

    # Store Trunk Attributes (Tier = 0)
    trunk_tier = nodes.new("GeometryNodeStoreNamedAttribute")
    trunk_tier.data_type = "INT"
    trunk_tier.domain = "POINT"
    trunk_tier.inputs["Name"].default_value = "pp_tier"
    trunk_tier.inputs["Value"].default_value = 0
    trunk_tier.location = (-300, 400)
    links.new(trunk_set_rad.outputs["Curve"], trunk_tier.inputs["Geometry"])

    trunk_wind = nodes.new("GeometryNodeStoreNamedAttribute")
    trunk_wind.data_type = "FLOAT"
    trunk_wind.domain = "POINT"
    trunk_wind.inputs["Name"].default_value = "pp_wind_weight"
    trunk_wind.location = (-100, 400)
    links.new(trunk_tier.outputs["Geometry"], trunk_wind.inputs["Geometry"])
    links.new(trunk_param.outputs["Factor"], trunk_wind.inputs["Value"])

    # Stamp parent_radius and parent_factor onto trunk for Tier 1 inheritance
    trunk_prad = nodes.new("GeometryNodeStoreNamedAttribute")
    trunk_prad.data_type = "FLOAT"
    trunk_prad.domain = "POINT"
    trunk_prad.inputs["Name"].default_value = "parent_radius"
    trunk_prad.location = (50, 400)
    links.new(trunk_wind.outputs["Geometry"], trunk_prad.inputs["Geometry"])
    links.new(trunk_rad.outputs["Value"], trunk_prad.inputs["Value"])

    trunk_pfac = nodes.new("GeometryNodeStoreNamedAttribute")
    trunk_pfac.data_type = "FLOAT"
    trunk_pfac.domain = "POINT"
    trunk_pfac.inputs["Name"].default_value = "parent_factor"
    trunk_pfac.location = (200, 400)
    links.new(trunk_prad.outputs["Geometry"], trunk_pfac.inputs["Geometry"])
    links.new(trunk_param.outputs["Factor"], trunk_pfac.inputs["Value"])

    # 2. Tier 1 Branches (Primary)
    branch_tier_sub = build_branch_tier_group()

    tier1_node = nodes.new("GeometryNodeGroup")
    tier1_node.node_tree = branch_tier_sub
    tier1_node.location = (350, 400)
    links.new(trunk_pfac.outputs["Geometry"], tier1_node.inputs["Parent Curves"])
    links.new(in_node.outputs["Tier 1 Count"], tier1_node.inputs["Branch Count"])
    links.new(in_node.outputs["Tier 1 Start Factor"], tier1_node.inputs["Start Factor"])
    links.new(in_node.outputs["Tier 1 End Factor"], tier1_node.inputs["End Factor"])
    links.new(in_node.outputs["Tier 1 Length"], tier1_node.inputs["Branch Length"])
    links.new(in_node.outputs["Tier 1 Length Falloff"], tier1_node.inputs["Length Falloff"])
    links.new(in_node.outputs["Tier 1 Angle"], tier1_node.inputs["Branch Angle"])
    links.new(in_node.outputs["Tier 1 Base Radius"], tier1_node.inputs["Base Radius"])
    links.new(in_node.outputs["Tier 1 Tip Radius"], tier1_node.inputs["Tip Radius"])
    links.new(in_node.outputs["Tier 1 Radius Ratio"], tier1_node.inputs["Radius Ratio"])
    links.new(in_node.outputs["Tier 1 Joint Flare"], tier1_node.inputs["Joint Flare"])
    links.new(in_node.outputs["Tier 1 Phyllotaxis Angle"], tier1_node.inputs["Phyllotaxis Angle"])
    links.new(in_node.outputs["Tier 1 Gravitropism"], tier1_node.inputs["Gravitropism"])
    links.new(in_node.outputs["Tier 1 Noise Strength"], tier1_node.inputs["Noise Strength"])
    links.new(in_node.outputs["Tier 1 Seed"], tier1_node.inputs["Seed"])
    tier1_node.inputs["Tier Index"].default_value = 1

    # 3. Tier 2 Branches (Secondary)
    tier2_node = nodes.new("GeometryNodeGroup")
    tier2_node.node_tree = branch_tier_sub
    tier2_node.location = (650, 400)
    links.new(tier1_node.outputs["Child Curves"], tier2_node.inputs["Parent Curves"])
    links.new(in_node.outputs["Tier 2 Count"], tier2_node.inputs["Branch Count"])
    links.new(in_node.outputs["Tier 2 Start Factor"], tier2_node.inputs["Start Factor"])
    links.new(in_node.outputs["Tier 2 End Factor"], tier2_node.inputs["End Factor"])
    links.new(in_node.outputs["Tier 2 Length"], tier2_node.inputs["Branch Length"])
    links.new(in_node.outputs["Tier 2 Length Falloff"], tier2_node.inputs["Length Falloff"])
    links.new(in_node.outputs["Tier 2 Angle"], tier2_node.inputs["Branch Angle"])
    links.new(in_node.outputs["Tier 2 Base Radius"], tier2_node.inputs["Base Radius"])
    links.new(in_node.outputs["Tier 2 Tip Radius"], tier2_node.inputs["Tip Radius"])
    links.new(in_node.outputs["Tier 2 Radius Ratio"], tier2_node.inputs["Radius Ratio"])
    links.new(in_node.outputs["Tier 2 Joint Flare"], tier2_node.inputs["Joint Flare"])
    links.new(in_node.outputs["Tier 2 Phyllotaxis Angle"], tier2_node.inputs["Phyllotaxis Angle"])
    links.new(in_node.outputs["Tier 2 Gravitropism"], tier2_node.inputs["Gravitropism"])
    links.new(in_node.outputs["Tier 2 Noise Strength"], tier2_node.inputs["Noise Strength"])
    links.new(in_node.outputs["Tier 2 Seed"], tier2_node.inputs["Seed"])
    tier2_node.inputs["Tier Index"].default_value = 2

    # 4. Tier 3 Branches (Twigs)
    tier3_node = nodes.new("GeometryNodeGroup")
    tier3_node.node_tree = branch_tier_sub
    tier3_node.location = (950, 400)
    links.new(tier2_node.outputs["Child Curves"], tier3_node.inputs["Parent Curves"])
    links.new(in_node.outputs["Tier 3 Count"], tier3_node.inputs["Branch Count"])
    links.new(in_node.outputs["Tier 3 Start Factor"], tier3_node.inputs["Start Factor"])
    links.new(in_node.outputs["Tier 3 End Factor"], tier3_node.inputs["End Factor"])
    links.new(in_node.outputs["Tier 3 Length"], tier3_node.inputs["Branch Length"])
    links.new(in_node.outputs["Tier 3 Length Falloff"], tier3_node.inputs["Length Falloff"])
    links.new(in_node.outputs["Tier 3 Angle"], tier3_node.inputs["Branch Angle"])
    links.new(in_node.outputs["Tier 3 Base Radius"], tier3_node.inputs["Base Radius"])
    links.new(in_node.outputs["Tier 3 Tip Radius"], tier3_node.inputs["Tip Radius"])
    links.new(in_node.outputs["Tier 3 Radius Ratio"], tier3_node.inputs["Radius Ratio"])
    links.new(in_node.outputs["Tier 3 Joint Flare"], tier3_node.inputs["Joint Flare"])
    links.new(in_node.outputs["Tier 3 Seed"], tier3_node.inputs["Seed"])
    tier3_node.inputs["Tier Index"].default_value = 3

    # 5. Foliage Instancing
    foliage_sub = build_foliage_generator_group()
    foliage_node = nodes.new("GeometryNodeGroup")
    foliage_node.node_tree = foliage_sub
    foliage_node.location = (1250, 400)
    links.new(tier3_node.outputs["Child Curves"], foliage_node.inputs["Twig Curves"])
    links.new(in_node.outputs["Leaf Mode"], foliage_node.inputs["Leaf Mode"])
    links.new(in_node.outputs["Custom Leaf Object"], foliage_node.inputs["Custom Object"])
    links.new(in_node.outputs["Leaves Count per Branch"], foliage_node.inputs["Count per Branch"])
    links.new(in_node.outputs["Leaves Start Factor"], foliage_node.inputs["Start Factor"])
    links.new(in_node.outputs["Leaf Scale"], foliage_node.inputs["Leaf Scale"])
    links.new(in_node.outputs["Leaf Pitch"], foliage_node.inputs["Pitch Angle"])
    links.new(in_node.outputs["Leaf Roll"], foliage_node.inputs["Roll Angle"])
    links.new(in_node.outputs["Sun Alignment"], foliage_node.inputs["Sun Alignment"])
    links.new(in_node.outputs["Sun Vector"], foliage_node.inputs["Sun Vector"])
    links.new(in_node.outputs["Leaf Seed"], foliage_node.inputs["Seed"])

    # Switches for Branch Tiers
    switch_t1 = nodes.new("GeometryNodeSwitch")
    switch_t1.input_type = "GEOMETRY"
    switch_t1.location = (550, 250)
    links.new(in_node.outputs["Tier 1 Enable"], switch_t1.inputs["Switch"])
    links.new(tier1_node.outputs["Child Curves"], switch_t1.inputs["True"])

    switch_t2 = nodes.new("GeometryNodeSwitch")
    switch_t2.input_type = "GEOMETRY"
    switch_t2.location = (850, 250)
    links.new(in_node.outputs["Tier 2 Enable"], switch_t2.inputs["Switch"])
    links.new(tier2_node.outputs["Child Curves"], switch_t2.inputs["True"])

    switch_t3 = nodes.new("GeometryNodeSwitch")
    switch_t3.input_type = "GEOMETRY"
    switch_t3.location = (1150, 250)
    links.new(in_node.outputs["Tier 3 Enable"], switch_t3.inputs["Switch"])
    links.new(tier3_node.outputs["Child Curves"], switch_t3.inputs["True"])

    # Join Wood Splines (Trunk + Tier 1 + Tier 2 + Tier 3)
    join_curves = nodes.new("GeometryNodeJoinGeometry")
    join_curves.location = (1350, 150)
    links.new(trunk_pfac.outputs["Geometry"], join_curves.inputs["Geometry"])
    links.new(switch_t1.outputs["Output"], join_curves.inputs["Geometry"])
    links.new(switch_t2.outputs["Output"], join_curves.inputs["Geometry"])
    links.new(switch_t3.outputs["Output"], join_curves.inputs["Geometry"])

    # 6. Wind & Secondary Motion
    time_node = nodes.new("GeometryNodeInputSceneTime")
    time_node.location = (1100, -100)

    wind_phase = nodes.new("ShaderNodeMath")
    wind_phase.operation = "MULTIPLY"
    wind_phase.location = (1250, -100)
    links.new(time_node.outputs["Seconds"], wind_phase.inputs[0])
    links.new(in_node.outputs["Wind Speed"], wind_phase.inputs[1])

    # 4D Noise displacement for wind
    pos_wind = nodes.new("GeometryNodeInputPosition")
    pos_wind.location = (1100, -300)

    wind_noise = nodes.new("ShaderNodeTexNoise")
    wind_noise.noise_dimensions = "4D"
    wind_noise.inputs["Scale"].default_value = 0.5
    wind_noise.location = (1250, -300)
    links.new(pos_wind.outputs["Position"], wind_noise.inputs["Vector"])
    links.new(wind_phase.outputs["Value"], wind_noise.inputs["W"])

    wind_sub = nodes.new("ShaderNodeVectorMath")
    wind_sub.operation = "SUBTRACT"
    wind_sub.inputs[1].default_value = (0.5, 0.5, 0.5)
    wind_sub.location = (1450, -300)
    links.new(wind_noise.outputs["Color"], wind_sub.inputs[0])

    wind_scale_str = nodes.new("ShaderNodeVectorMath")
    wind_scale_str.operation = "SCALE"
    wind_scale_str.location = (1600, -300)
    links.new(wind_sub.outputs["Vector"], wind_scale_str.inputs["Vector"])
    links.new(in_node.outputs["Wind Strength"], wind_scale_str.inputs["Scale"])

    # Directional breeze component
    wind_dir_scaled = nodes.new("ShaderNodeVectorMath")
    wind_dir_scaled.operation = "SCALE"
    wind_dir_scaled.location = (1600, -150)
    links.new(in_node.outputs["Wind Direction"], wind_dir_scaled.inputs["Vector"])
    links.new(in_node.outputs["Wind Strength"], wind_dir_scaled.inputs["Scale"])

    wind_total_vec = nodes.new("ShaderNodeVectorMath")
    wind_total_vec.operation = "ADD"
    wind_total_vec.location = (1750, -200)
    links.new(wind_scale_str.outputs["Vector"], wind_total_vec.inputs[0])
    links.new(wind_dir_scaled.outputs["Vector"], wind_total_vec.inputs[1])

    # Apply Wind Offset to wood curves
    set_wind_wood = nodes.new("GeometryNodeSetPosition")
    set_wind_wood.location = (1350, 150)
    links.new(join_curves.outputs["Geometry"], set_wind_wood.inputs["Geometry"])
    links.new(wind_total_vec.outputs["Vector"], set_wind_wood.inputs["Offset"])

    # Switch to bypass wind if Wind Enable is False
    switch_wind = nodes.new("GeometryNodeSwitch")
    switch_wind.input_type = "GEOMETRY"
    switch_wind.location = (1550, 150)
    links.new(in_node.outputs["Wind Enable"], switch_wind.inputs["Switch"])
    links.new(join_curves.outputs["Geometry"], switch_wind.inputs["False"])
    links.new(set_wind_wood.outputs["Geometry"], switch_wind.inputs["True"])

    # 7. Curve to Mesh (Trunk & Branches)
    curve_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    curve_profile.inputs["Radius"].default_value = 1.0 # scaled by curve point radius via Scale socket!
    curve_profile.location = (1550, 0)
    links.new(in_node.outputs["Mesh Resolution"], curve_profile.inputs["Resolution"])

    # Read point radius to scale profile circle properly at each point
    rad_input = nodes.new("GeometryNodeInputRadius")
    rad_input.location = (1550, -100)

    curve_to_mesh = nodes.new("GeometryNodeCurveToMesh")
    curve_to_mesh.inputs["Fill Caps"].default_value = True # Caps ends to avoid hollow open barrels
    curve_to_mesh.location = (1750, 150)
    links.new(switch_wind.outputs["Output"], curve_to_mesh.inputs["Curve"])
    links.new(curve_profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])
    links.new(rad_input.outputs["Radius"], curve_to_mesh.inputs["Scale"])

    # Set Bark Material
    set_mat_bark = nodes.new("GeometryNodeSetMaterial")
    set_mat_bark.location = (1950, 150)
    links.new(curve_to_mesh.outputs["Mesh"], set_mat_bark.inputs["Geometry"])
    links.new(in_node.outputs["Bark Material"], set_mat_bark.inputs["Material"])

    # Set Leaf Material
    set_mat_leaf = nodes.new("GeometryNodeSetMaterial")
    set_mat_leaf.location = (1350, 400)
    links.new(foliage_node.outputs["Foliage Geometry"], set_mat_leaf.inputs["Geometry"])
    links.new(in_node.outputs["Leaf Material"], set_mat_leaf.inputs["Material"])

    # Switch leaves bypass if Leaves Enable is False
    switch_leaves = nodes.new("GeometryNodeSwitch")
    switch_leaves.input_type = "GEOMETRY"
    switch_leaves.location = (1550, 400)
    links.new(in_node.outputs["Leaves Enable"], switch_leaves.inputs["Switch"])
    links.new(set_mat_leaf.outputs["Geometry"], switch_leaves.inputs["True"])

    # Join Wood Mesh and Foliage
    join_final = nodes.new("GeometryNodeJoinGeometry")
    join_final.location = (2150, 200)
    links.new(set_mat_bark.outputs["Geometry"], join_final.inputs["Geometry"])
    links.new(switch_leaves.outputs["Output"], join_final.inputs["Geometry"])

    # Output final procedural geometry
    links.new(join_final.outputs["Geometry"], out_node.inputs["Geometry"])

    return tree
