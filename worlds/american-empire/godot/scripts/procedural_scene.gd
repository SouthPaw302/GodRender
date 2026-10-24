extends "res://scripts/scene_bridge.gd"
## Source-bound procedural interpretation of the same validated P9 contract.
## Synthetic terrain only. Does not replace the existing schematic 3D proof.

var terrain_record: Dictionary = {}

func _point(row: int, col: int) -> Vector3:
    var n: int = int(terrain_record["grid"])
    var h: Array = terrain_record["heights_dm"]
    var elevation: float = (float(h[row][col]) - float(terrain_record["sea_level_dm"])) * 0.012
    return Vector3((float(col) / float(n - 1) - 0.5) * 72.0, elevation,
                   (float(row) / float(n - 1) - 0.5) * 72.0)

func _triangle(tool: SurfaceTool, a: Vector3, b: Vector3, c: Vector3) -> void:
    tool.add_vertex(a)
    tool.add_vertex(b)
    tool.add_vertex(c)

func _make_world() -> void:
    var path := "res://data/procedural_geometry.json"
    if not FileAccess.file_exists(path):
        push_error("AE_PROCEDURAL_FAIL geometry JSON absent")
        get_tree().quit(8)
        return
    var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (parsed is Dictionary):
        push_error("AE_PROCEDURAL_FAIL invalid geometry")
        get_tree().quit(9)
        return
    terrain_record = parsed
    var grid: int = int(terrain_record.get("grid", 0))
    if terrain_record.get("schema", "") != "american-empire.procedural-geometry.v1" or grid != 64 or        terrain_record.get("authority_layer", "") != "scenario_only" or        terrain_record.get("real_geography", true) != false or        terrain_record.get("no_private_media", false) != true or        terrain_record.get("source_scene_contract_sha256", "") != record["contract_sha256"] or        terrain_record.get("source_p7_snapshot_sha256", "") != record["source"]["p7_snapshot_sha256"] or        terrain_record.get("place_id", "") != record["world"]["place_id"] or        int(terrain_record.get("year", -1)) != int(record["world"]["year"]):
        push_error("AE_PROCEDURAL_FAIL geometry and verified P7 source disagree")
        get_tree().quit(10)
        return
    var heights: Variant = terrain_record.get("heights_dm")
    if not (heights is Array) or heights.size() != grid:
        push_error("AE_PROCEDURAL_FAIL malformed height grid")
        get_tree().quit(11)
        return
    for line in heights:
        if not (line is Array) or line.size() != grid:
            push_error("AE_PROCEDURAL_FAIL uneven height grid")
            get_tree().quit(12)
            return

    var sky := WorldEnvironment.new()
    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    environment.background_color = Color(0.11, 0.19, 0.28)
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color(0.65, 0.73, 0.81)
    sky.environment = environment
    add_child(sky)
    var sunlight := DirectionalLight3D.new()
    sunlight.rotation_degrees = Vector3(-48, 26, 0)
    sunlight.light_energy = 1.55
    add_child(sunlight)

    var ground := SurfaceTool.new()
    ground.begin(Mesh.PRIMITIVE_TRIANGLES)
    for r in range(grid - 1):
        for c in range(grid - 1):
            var a := _point(r, c)
            var b := _point(r, c + 1)
            var d := _point(r + 1, c)
            var e := _point(r + 1, c + 1)
            _triangle(ground, a, d, b)
            _triangle(ground, b, d, e)
    ground.generate_normals()
    var surface := MeshInstance3D.new()
    surface.name = "SourceBoundSyntheticTerrain"
    surface.mesh = ground.commit()
    surface.material_override = _material(Color(0.29, 0.42, 0.30))
    add_child(surface)

    _box(Vector3(0, -1.0, 0), Vector3(72.0, 1.95, 72.0),
         Color(0.12, 0.27, 0.38), "MathematicalSeaLevel")

    for entry in terrain_record.get("roads", []):
        var points: Array = entry["cells"]
        var road := SurfaceTool.new()
        road.begin(Mesh.PRIMITIVE_TRIANGLES)
        for i in range(points.size() - 1):
            var p: Array = points[i]
            var q: Array = points[i + 1]
            var from := _point(int(p[0]), int(p[1])) + Vector3.UP * .09
            var to := _point(int(q[0]), int(q[1])) + Vector3.UP * .09
            var direction := to - from
            var side := Vector3(-direction.z, 0, direction.x).normalized() * .17
            _triangle(road, from - side, to - side, from + side)
            _triangle(road, from + side, to - side, to + side)
        var strip := MeshInstance3D.new()
        strip.mesh = road.commit()
        strip.material_override = _material(Color(0.80, 0.67, 0.47))
        strip.name = "SlopeAwareRoad_" + str(entry["from"]) + "_" + str(entry["to"])
        add_child(strip)

    for cell in terrain_record.get("river_cells", []):
        if int(cell[0]) % 2 != 0:
            continue
        var p := _point(int(cell[0]), int(cell[1]))
        _box(p + Vector3.UP * .12, Vector3(.49, .07, .49),
             Color(0.23, 0.60, 0.74), "D8Drainage")

    var locations: Array = terrain_record.get("settlements", [])
    for site in locations:
        var r: int = int(site["row"])
        var c: int = int(site["col"])
        var origin := _point(r, c)
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dz == 0:
                    continue
                var height := 1.0 + float((abs(dx * 7 + dz * 5 + r + c) % 4))
                _box(origin + Vector3(float(dx) * 1.55, height / 2, float(dz) * 1.55),
                     Vector3(1.15, height, 1.15),
                     Color(0.61, 0.60, 0.48), "SyntheticBuilding_" + str(site["id"]))

    if locations.size() > 0 and bool(record["actor"]["present_in_scene"]):
        var location: Dictionary = locations[0]
        var center := _point(int(location["row"]), int(location["col"]))
        _box(center + Vector3.UP * 1.1, Vector3(.6, 2.2, .6),
             Color(0.94, 0.64, 0.23), "ScenarioOnlyActorMarker")

    camera = Camera3D.new()
    camera.name = "GodRenderProceduralCamera"
    camera.current = true
    camera.fov = 49.0
    camera.far = 260.0
    add_child(camera)
    _set_camera(0.0)
    print("AE_PROCEDURAL_SCENE_READY geometry=%s source=%s towns=%d" % [
        str(terrain_record["geometry_sha256"]),
        str(terrain_record["source_p7_snapshot_sha256"]),
        locations.size()
    ])
