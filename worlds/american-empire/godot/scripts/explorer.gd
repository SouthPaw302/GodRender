extends Control
## Godot 4 P4 World Explorer: source-backed graph + clearly labeled P3 scenarios.
## All inputs are read-only, verified Python exports from P1/P2/P3.

const GraphView = preload("res://scripts/relationship_graph.gd")
const INK = Color("#e2edf3")
const MUTED = Color("#9eb5c6")
const GOLD = Color("#dbb174")
const TEAL = Color("#65ced1")
const DARK = Color("#101827")
const PANEL = Color("#14243a")
const YEAR_MIN = 2026
const YEAR_MAX = 2037

var bundle: Dictionary = {}
var selected_year: int = 2027
var scenario_index: int = 0
var selected_entity: String = "system:S1"
var graph: Control
var year_text: Label
var phase_title: Label
var phase_body: Label
var scenario_select: OptionButton
var time_slider: HSlider
var inspector: RichTextLabel
var metric_labels: Array = []
var metric_bars: Array = []
var metrics_note: Label
var footnote: Label
var proof_cycle: bool = false
var proof_frames: int = 0

func _ready() -> void:
    var path = "res://data/world_bundle.json"
    if not FileAccess.file_exists(path):
        push_error("P4 World Explorer requires a generated verified world_bundle.json. Run tools/build_explorer_bundle.py.")
        get_tree().quit(3)
        return
    var loaded = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not (loaded is Dictionary):
        push_error("P4 input is not valid JSON object")
        get_tree().quit(4)
        return
    bundle = loaded
    if not _valid_bundle():
        push_error("P4 world-bundle authority or structural validation failed")
        get_tree().quit(5)
        return
    set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    _build_view()
    _apply_state()
    proof_cycle = OS.get_cmdline_user_args().has("--proof-cycle")
    print("AMERICAN EMPIRE P4 READY: 16 nodes, %d edges, 12 years, %d scenarios" % [
        bundle["edges"].size(), bundle["scenarios"].size()])
    print("P4 SOURCE: %s" % str(bundle["source"]["world_graph_sha256"]))

func _valid_bundle() -> bool:
    if bundle.get("schema", "") != "american-empire.godot-explorer-bundle.v1":
        return false
    if bundle.get("sources_read_only", false) != true:
        return false
    if int(bundle.get("year_min", -1)) != YEAR_MIN or int(bundle.get("year_max", -1)) != YEAR_MAX:
        return false
    if not (bundle.get("nodes", null) is Array) or bundle["nodes"].size() != 16:
        return false
    if not (bundle.get("people", null) is Array) or bundle["people"].size() != 5:
        return false
    if not (bundle.get("edges", null) is Array):
        return false
    if not (bundle.get("years", null) is Array) or bundle["years"].size() != 12:
        return false
    if not (bundle.get("scenarios", null) is Array) or bundle["scenarios"].size() != 3:
        return false
    if not (bundle.get("source", null) is Dictionary):
        return false
    if str(bundle["source"].get("matrix_blob_sha1", "")) != "575e8c1b20bc6e9bf5c61ac32e32536256abcab0":
        return false
    for i in range(12):
        if int(bundle["years"][i].get("year", -1)) != YEAR_MIN + i:
            return false
    for case in bundle["scenarios"]:
        if str(case.get("authority_layer", "")) != "scenario_only":
            return false
        if case.get("snapshots", []).size() != 12:
            return false
        if str(case.get("source_world_sha256", "")) != str(bundle["source"]["world_graph_sha256"]):
            return false
        for i in range(12):
            if int(case["snapshots"][i].get("year", -1)) != YEAR_MIN + i:
                return false
    return true

func _label(value: String, font_size: int = 16, color: Color = INK) -> Label:
    var result = Label.new()
    result.text = value
    result.add_theme_font_size_override("font_size", font_size)
    result.add_theme_color_override("font_color", color)
    result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    return result

func _panel(color: Color = PANEL) -> PanelContainer:
    var result = PanelContainer.new()
    var style = StyleBoxFlat.new()
    style.bg_color = color
    style.set_corner_radius_all(9)
    style.content_margin_left = 16
    style.content_margin_right = 16
    style.content_margin_top = 13
    style.content_margin_bottom = 13
    result.add_theme_stylebox_override("panel", style)
    return result

func _button(value: String, callback: Callable) -> Button:
    var b = Button.new()
    b.text = value
    b.custom_minimum_size = Vector2(50, 40)
    b.pressed.connect(callback)
    return b

func _build_view() -> void:
    var backdrop = ColorRect.new()
    backdrop.color = DARK
    backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    add_child(backdrop)
    var outer = MarginContainer.new()
    outer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    outer.add_theme_constant_override("margin_left", 22)
    outer.add_theme_constant_override("margin_right", 22)
    outer.add_theme_constant_override("margin_top", 18)
    outer.add_theme_constant_override("margin_bottom", 15)
    add_child(outer)
    var frame = VBoxContainer.new()
    frame.add_theme_constant_override("separation", 12)
    outer.add_child(frame)

    var header = HBoxContainer.new()
    frame.add_child(header)
    var heading = VBoxContainer.new()
    heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    header.add_child(heading)
    heading.add_child(_label("THE AMERICAN EMPIRE", 30, GOLD))
    heading.add_child(_label("THE QUIET ACCESSION  /  P4 WORLD EXPLORER", 15, MUTED))
    var authority = _label("ORIGINAL CANON   |   P3 NUMBERS ARE HYPOTHETICAL", 14, TEAL)
    header.add_child(authority)

    var controls = _panel(Color("#1c3145"))
    frame.add_child(controls)
    var toolbar = HBoxContainer.new()
    toolbar.add_theme_constant_override("separation", 12)
    controls.add_child(toolbar)
    toolbar.add_child(_button("<", _move_year.bind(-1)))
    year_text = _label("2027", 26, GOLD)
    year_text.custom_minimum_size.x = 82
    toolbar.add_child(year_text)
    toolbar.add_child(_button(">", _move_year.bind(1)))
    time_slider = HSlider.new()
    time_slider.min_value = YEAR_MIN
    time_slider.max_value = YEAR_MAX
    time_slider.step = 1
    time_slider.value = selected_year
    time_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    time_slider.custom_minimum_size.x = 240
    time_slider.value_changed.connect(_on_time_slide)
    toolbar.add_child(time_slider)
    toolbar.add_child(_label("SCENARIO", 13, MUTED))
    scenario_select = OptionButton.new()
    scenario_select.custom_minimum_size.x = 220
    for item in bundle["scenarios"]:
        scenario_select.add_item(str(item["name"]))
    scenario_select.selected = 0
    scenario_select.item_selected.connect(_on_scenario_selected)
    toolbar.add_child(scenario_select)

    var phase_card = _panel()
    frame.add_child(phase_card)
    var phase_row = VBoxContainer.new()
    phase_card.add_child(phase_row)
    phase_title = _label("", 23, GOLD)
    phase_row.add_child(phase_title)
    phase_body = _label("", 15, INK)
    phase_row.add_child(phase_body)

    var body = HBoxContainer.new()
    body.size_flags_vertical = Control.SIZE_EXPAND_FILL
    body.add_theme_constant_override("separation", 12)
    frame.add_child(body)

    var visual_card = _panel(Color("#101c30"))
    visual_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    visual_card.size_flags_vertical = Control.SIZE_EXPAND_FILL
    body.add_child(visual_card)
    graph = GraphView.new()
    graph.custom_minimum_size = Vector2(610, 425)
    graph.size_flags_horizontal = Control.SIZE_EXPAND_FILL
    graph.size_flags_vertical = Control.SIZE_EXPAND_FILL
    graph.configure(bundle["nodes"], bundle["edges"])
    graph.entity_chosen.connect(_on_graph_entity)
    visual_card.add_child(graph)

    var sidebar = VBoxContainer.new()
    sidebar.custom_minimum_size.x = 380
    sidebar.size_flags_vertical = Control.SIZE_EXPAND_FILL
    sidebar.add_theme_constant_override("separation", 8)
    body.add_child(sidebar)
    sidebar.add_child(_label("WORLD STATE  /  MODEL ASSUMPTIONS", 16, TEAL))
    for item in bundle["variables"]:
        var row = HBoxContainer.new()
        row.add_theme_constant_override("separation", 7)
        sidebar.add_child(row)
        var label = _label(str(item["name"]), 13, INK)
        label.custom_minimum_size.x = 172
        row.add_child(label)
        var bar = ProgressBar.new()
        bar.min_value = 0
        bar.max_value = 100
        bar.show_percentage = false
        bar.custom_minimum_size = Vector2(130, 17)
        bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        row.add_child(bar)
        var value = _label("0", 14, GOLD)
        value.custom_minimum_size.x = 27
        row.add_child(value)
        metric_labels.append(value)
        metric_bars.append(bar)
    metrics_note = _label("", 12, MUTED)
    sidebar.add_child(metrics_note)
    sidebar.add_child(_label("INSPECT FACTIONS, SYSTEMS OR PEOPLE", 15, TEAL))
    var person_chooser = OptionButton.new()
    person_chooser.add_item("Select a viewpoint character...")
    for p in bundle["people"]:
        person_chooser.add_item(str(p["name"]))
    person_chooser.item_selected.connect(_on_person_selected)
    sidebar.add_child(person_chooser)
    var inspect_panel = _panel(Color("#1b2939"))
    inspect_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
    sidebar.add_child(inspect_panel)
    inspector = RichTextLabel.new()
    inspector.bbcode_enabled = false
    inspector.scroll_active = true
    inspector.fit_content = false
    inspector.custom_minimum_size.y = 150
    inspector.size_flags_vertical = Control.SIZE_EXPAND_FILL
    inspector.add_theme_font_size_override("normal_font_size", 14)
    inspector.add_theme_color_override("default_color", INK)
    inspect_panel.add_child(inspector)

    footnote = _label("", 13, MUTED)
    frame.add_child(footnote)

func _move_year(amount: int) -> void:
    _set_year(selected_year + amount)

func _set_year(value: int) -> void:
    selected_year = clampi(value, YEAR_MIN, YEAR_MAX)
    if time_slider != null:
        time_slider.set_value_no_signal(selected_year)
    _apply_state()

func _on_time_slide(value: float) -> void:
    _set_year(int(value))

func _on_scenario_selected(index: int) -> void:
    scenario_index = clampi(index, 0, bundle["scenarios"].size() - 1)
    _apply_state()

func _on_person_selected(index: int) -> void:
    if index <= 0:
        return
    selected_entity = str(bundle["people"][index - 1]["id"])
    selected_entity = "person:" + selected_entity
    graph.choose_entity("")
    _update_inspector()

func _on_graph_entity(entity_id: String) -> void:
    selected_entity = entity_id
    _update_inspector()

func _apply_state() -> void:
    if bundle.is_empty() or year_text == null:
        return
    var phase: Dictionary = bundle["years"][selected_year - YEAR_MIN]
    var scenario: Dictionary = bundle["scenarios"][scenario_index]
    var snapshot: Dictionary = scenario["snapshots"][selected_year - YEAR_MIN]
    year_text.text = str(selected_year)
    phase_title.text = "%d  /  %s" % [selected_year, str(phase["title"])]
    phase_body.text = str(phase["summary"])
    for i in range(bundle["variables"].size()):
        var name: String = str(bundle["variables"][i]["attributes"]["id"])
        var value: int = int(snapshot["state"][name])
        metric_bars[i].value = value
        metric_labels[i].text = str(value)
    metrics_note.text = "Accession pressure proxy: %s  |  Dependency gap: %s" % [
        str(snapshot["indicators"]["accession_pressure_raw"]),
        str(snapshot["indicators"]["dependency_gap"])
    ]
    footnote.text = "SCHEMATIC: ORIGINAL FACTION/STACK RELATIONSHIPS  |  YEAR: CANON TITLE  |  NUMERIC STATE: %s (SCENARIO ONLY)" % str(scenario["name"]).to_upper()
    _update_inspector()
    print("AE_P4_VIEW year=%d scenario=%s snapshot=%s" % [
        selected_year, str(scenario["id"]), str(snapshot["snapshot_sha256"]).substr(0, 12)
    ])

func _update_inspector() -> void:
    if inspector == null:
        return
    var entity: Dictionary = {}
    for node in bundle["nodes"]:
        if str(node["id"]) == selected_entity:
            entity = node
            break
    if entity.is_empty():
        for person in bundle["people"]:
            if "person:" + str(person["id"]) == selected_entity:
                entity = person
                break
    if entity.is_empty():
        inspector.text = "Select a source-backed institution or Stack system."
        return
    var attrs: Dictionary = entity["attributes"]
    var text: String = str(entity["name"]).to_upper() + "\n"
    text += "KIND: " + str(entity["kind"]) + " | ESTABLISHED MATRIX ENTITY\n\n"
    for field in ["type", "domain", "role", "goal", "fear", "benefit", "control_surface",
                  "function", "knows", "does_not_know", "dramatic_question"]:
        if attrs.has(field):
            text += field.replace("_", " ").capitalize() + ": " + str(attrs[field]) + "\n\n"
    var linked: Array = []
    for edge in bundle["edges"]:
        if str(edge["from"]) == selected_entity or str(edge["to"]) == selected_entity:
            linked.append(str(edge["label"]) + " (" + str(edge["from"]) + " -> " + str(edge["to"]) + ")")
    if linked.size() > 0:
        text += "CANON / STACK LINKS\n"
        for label in linked:
            text += " - " + label + "\n"
    var source: Dictionary = entity["source"]
    text += "\nSOURCE: " + str(source["path"]) + str(source["json_pointer"])
    text += "\nGit object: " + str(source["git_blob_sha1"])
    inspector.text = text

func _process(_delta: float) -> void:
    if not proof_cycle:
        return
    proof_frames += 1
    if proof_frames == 14:
        _set_year(2029)
    elif proof_frames == 27:
        scenario_select.select(1)
        _on_scenario_selected(1)
    elif proof_frames == 40:
        _set_year(2033)
