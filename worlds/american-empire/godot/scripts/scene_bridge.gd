extends Node3D
## AE Scene Bridge: real verified simulation snapshot -> schematic Godot 4 3D.
## No archived film footage, faces, Drive media or claims of geographic accuracy.

var record: Dictionary = {}
var camera: Camera3D
var frame_number: int = 0
var orbit_enabled: bool = false

func _ready() -> void:
    var path := "res://data/scene_contract.json"
    if not FileAccess.file_exists(path):
        push_error("AE_SCENE_FAIL missing source-bound contract")
        get_tree().quit(3)
        return
    var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (raw is Dictionary):
        push_error("AE_SCENE_FAIL invalid scene contract JSON")
        get_tree().quit(4)
        return
    record = raw
    if not _valid_contract():
        push_error("AE_SCENE_FAIL scene contract validation")
        get_tree().quit(5)
        return
    _make_world()
    _make_overlay()
    orbit_enabled = OS.get_cmdline_user_args().has("--scene-proof")
    print("AE_GODOT_SCENE_READY contract=%s source=%s actor=%s place=%s year=%d" % [
        str(record["contract_sha256"]), str(record["source"]["p7_snapshot_sha256"]),
        str(record["actor"]["id"]), str(record["world"]["place_id"]), int(record["world"]["year"])
    ])

func _valid_contract() -> bool:
    if record.get("schema", "") != "american-empire.godot-scene-contract.v1":
        return false
    if record.get("authority_layer", "") != "scenario_only":
        return false
    if record.get("render_classification", "") != "technical_geometry_proof_not_approved_film":
        return false
    var p: Variant = record.get("production")
    var s: Variant = record.get("source")
    var w: Variant = record.get("world")
    var a: Variant = record.get("actor")
    if not (p is Dictionary and s is Dictionary and w is Dictionary and a is Dictionary):
        return false
    if p.get("media_refs_embedded", true) != false or p.get("no_unapproved_source_media", false) != true:
        return false
    if str(s.get("p7_snapshot_sha256", "")).length() != 64:
        return false
    if str(record.get("contract_sha256", "")).length() != 64:
        return false
    if int(w.get("year", 0)) < 2026 or int(w.get("year", 0)) > 2037:
        return false
    for key in ["service", "independence"]:
        if not w.has(key) or int(w[key]) < 0 or int(w[key]) > 100:
            return false
    if str(a.get("id", "")) == "" or str(a.get("place", "")) != str(w.get("place_id", "")):
        return false
    return true

func _material(color: Color, emission: bool = false) -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.roughness = 0.82
    if emission:
        mat.emission_enabled = true
        mat.emission = color
        mat.emission_energy_multiplier = 1.3
    return mat

func _box(pos: Vector3, dim: Vector3, tint: Color, name_hint: String) -> MeshInstance3D:
    var instance := MeshInstance3D.new()
    var mesh := BoxMesh.new()
    mesh.size = dim
    instance.mesh = mesh
    instance.name = name_hint
    instance.position = pos
    instance.material_override = _material(tint)
    add_child(instance)
    return instance

func _make_world() -> void:
    var w: Dictionary = record["world"]
    var service: float = float(w["service"]) / 100.0
    var independence: float = float(w["independence"]) / 100.0
    var sky := WorldEnvironment.new()
    sky.name = "TechnicalSky"
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.095, 0.16, 0.235)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.58, 0.68, 0.80)
    env.ambient_light_energy = 0.85
    sky.environment = env
    add_child(sky)
    var sun := DirectionalLight3D.new()
    sun.name = "SourceNeutralLighting"
    sun.rotation_degrees = Vector3(-47, 29, -16)
    sun.light_energy = 1.8
    add_child(sun)

    _box(Vector3(0, -0.18, 0), Vector3(72, 0.3, 72), Color(0.14, 0.23, 0.27), "SchematicGround")
    _box(Vector3(0, -0.01, 0), Vector3(6, 0.05, 70), Color(0.065, 0.11, 0.16), "AxisRoadNorth")
    _box(Vector3(0, 0.01, 0), Vector3(70, 0.05, 6), Color(0.065, 0.11, 0.16), "AxisRoadEast")

    var rng := RandomNumberGenerator.new()
    rng.seed = int(record["production"]["scene_seed"])
    for xi in range(-3, 4):
        for zi in range(-3, 4):
            if xi == 0 or zi == 0:
                continue
            var tall: float = 3.2 + rng.randf_range(0.0, 3.0) + service * rng.randf_range(0.5, 6.5)
            var base := Vector3(float(xi) * 8.4, tall / 2.0, float(zi) * 8.4)
            var tint := Color(0.28 + 0.25 * service, 0.32 + 0.12 * independence, 0.40 + 0.14 * service)
            _box(base, Vector3(5.4, tall, 5.1), tint, "HypotheticalBlock_%s_%s" % [xi, zi])
            if rng.randf() < service:
                _box(base + Vector3(0, tall/2.0+0.12, 0), Vector3(4.5, 0.2, 3.9), Color(0.65, 0.73, 0.78), "Roof_%s_%s" % [xi, zi])

    # Character location marker, NOT an approved face, costume or cinematic model.
    var agent := MeshInstance3D.new()
    var body := CapsuleMesh.new()
    body.radius = 0.68
    body.height = 2.6
    agent.mesh = body
    agent.name = "SimulationActorMarker"
    agent.position = Vector3(0, 1.3, 0)
    agent.material_override = _material(Color(0.9, 0.68, 0.34), true)
    add_child(agent)
    for i in range(16):
        var angle: float = TAU * float(i) / 16.0
        _box(Vector3(cos(angle) * 2.15, 0.06, sin(angle) * 2.15),
             Vector3(0.38, 0.12, 0.38), Color(0.17, 0.70, 0.70), "ActorRing_%d" % i)

    camera = Camera3D.new()
    camera.name = "GodRenderSceneCamera"
    camera.current = true
    camera.fov = 49.0
    camera.far = 260.0
    add_child(camera)
    _set_camera(0.0)

func _set_camera(angle: float) -> void:
    if camera == null:
        return
    camera.position = Vector3(43 * cos(angle), 34.0, 43 * sin(angle))
    camera.look_at(Vector3(0, 1.0, 0), Vector3.UP)

func _make_overlay() -> void:
    var overlay := CanvasLayer.new()
    overlay.name = "ScenarioAuthorityOverlay"
    add_child(overlay)
    var base := PanelContainer.new()
    base.position = Vector2(27, 26)
    base.custom_minimum_size = Vector2(470, 138)
    overlay.add_child(base)
    var vb := VBoxContainer.new()
    vb.add_theme_constant_override("separation", 8)
    base.add_child(vb)
    var title := Label.new()
    title.text = "THE AMERICAN EMPIRE  /  GODRENDER 3D PROOF"
    title.add_theme_font_size_override("font_size", 18)
    vb.add_child(title)
    var location := Label.new()
    location.text = "%s   /   %d   /   %s" % [
        str(record["world"]["display_name"]), int(record["world"]["year"]),
        str(record["actor"]["id"]).to_upper()
    ]
    location.add_theme_font_size_override("font_size", 23)
    vb.add_child(location)
    var indices := Label.new()
    indices.text = "MODEL service %d/100 | autonomy %d/100 | action %s" % [
        int(record["world"]["service"]), int(record["world"]["independence"]),
        str(record["actor"]["last_action"])
    ]
    vb.add_child(indices)
    var caveat := Label.new()
    caveat.text = "SCHEMATIC / SCENARIO ONLY / NOT A FILM RECONSTRUCTION"
    caveat.add_theme_font_size_override("font_size", 13)
    vb.add_child(caveat)

func _process(_delta: float) -> void:
    if not orbit_enabled:
        return
    frame_number += 1
    _set_camera(-0.80 + float(frame_number) * 0.021)
    if frame_number == 2 or frame_number == 24 or frame_number == 44:
        print("AE_SCENE_CAMERA_PROOF frame=%d source=%s" % [
            frame_number, str(record["source"]["p7_snapshot_sha256"]).substr(0, 16)
        ])
