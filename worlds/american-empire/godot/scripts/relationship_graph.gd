extends Control
## P4 schematic graph: 10 original actors and six original Stack systems.
## Graph positions are presentation-only; NOT geographic coordinates.

signal entity_chosen(entity_id: String)

var nodes: Array = []
var edges: Array = []
var selected_id: String = ""
var positions: Dictionary = {}

const BG = Color("#101c30")
const GRID = Color("#192a41")
const ACTOR_COLOR = Color("#c88c50")
const SYSTEM_COLOR = Color("#62c4cd")
const TEXT_COLOR = Color("#d8e5ed")
const HIGHLIGHT = Color("#f7deb1")

func configure(source_nodes: Array, source_edges: Array) -> void:
    nodes = source_nodes.duplicate(true)
    edges = source_edges.duplicate(true)
    selected_id = "system:S1"
    queue_redraw()

func choose_entity(entity_id: String) -> void:
    selected_id = entity_id
    queue_redraw()

func _node_positions() -> void:
    positions.clear()
    var actors: Array = []
    var systems: Array = []
    for item in nodes:
        if str(item.get("kind", "")) == "actor":
            actors.append(item)
        elif str(item.get("kind", "")) == "system":
            systems.append(item)
    var w = size.x
    var h = size.y
    for i in range(actors.size()):
        var angle = -PI / 2.0 + TAU * float(i) / max(actors.size(), 1)
        positions[str(actors[i]["id"])] = Vector2(
            w * 0.29 + cos(angle) * w * 0.22,
            h * 0.54 + sin(angle) * h * 0.33
        )
    for i in range(systems.size()):
        var angle = -PI / 2.0 + TAU * float(i) / max(systems.size(), 1)
        positions[str(systems[i]["id"])] = Vector2(
            w * 0.75 + cos(angle) * w * 0.18,
            h * 0.54 + sin(angle) * h * 0.31
        )

func _draw() -> void:
    draw_rect(Rect2(Vector2.ZERO, size), BG)
    var span: int = 32
    for x in range(0, int(size.x), span):
        draw_line(Vector2(x, 0), Vector2(x, size.y), GRID, 1.0)
    for y in range(0, int(size.y), span):
        draw_line(Vector2(0, y), Vector2(size.x, y), GRID, 1.0)
    _node_positions()
    draw_string(ThemeDB.fallback_font, Vector2(22, 33),
        "DIRECTORATE / FACTIONS", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, ACTOR_COLOR)
    draw_string(ThemeDB.fallback_font, Vector2(size.x * 0.60, 33),
        "IMPERIAL STACK", HORIZONTAL_ALIGNMENT_LEFT, -1, 17, SYSTEM_COLOR)
    draw_string(ThemeDB.fallback_font, Vector2(22, size.y - 18),
        "SCHEMATIC RELATIONSHIP GRAPH  /  NOT A GEOGRAPHIC MAP",
        HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color("#8395a9"))
    for edge in edges:
        var a: String = str(edge.get("from", ""))
        var b: String = str(edge.get("to", ""))
        if not positions.has(a) or not positions.has(b):
            continue
        var lit: bool = selected_id == a or selected_id == b
        var negative: bool = int(edge.get("strength", 0) if edge.get("strength") != null else 0) < 0
        var base: Color = Color("#b86972") if negative else Color("#59728b")
        if lit:
            base = Color("#eabf86") if not negative else Color("#ed9099")
        else:
            base.a = 0.32
        draw_line(positions[a], positions[b], base, 2.4 if lit else 1.0, true)
    for item in nodes:
        var id: String = str(item["id"])
        if not positions.has(id):
            continue
        var p: Vector2 = positions[id]
        var is_selected: bool = selected_id == id
        var col: Color = SYSTEM_COLOR if str(item["kind"]) == "system" else ACTOR_COLOR
        if is_selected:
            draw_circle(p, 25, Color(col.r, col.g, col.b, 0.19))
        draw_circle(p, 15.5 if is_selected else 12.0, col)
        draw_circle(p, 6.0, BG)
        var label: String = str(item["name"])
        if label.length() > 22:
            label = label.substr(0, 21) + "..."
        var tx: float = p.x - min(70.0, label.length() * 3.5)
        var ty: float = p.y + 33
        draw_string(ThemeDB.fallback_font, Vector2(tx, ty), label,
            HORIZONTAL_ALIGNMENT_LEFT, 150, 12, HIGHLIGHT if is_selected else TEXT_COLOR)

func _gui_input(event: InputEvent) -> void:
    if event is InputEventMouseButton:
        if event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
            var best: float = 28.0
            var chosen: String = ""
            for id in positions:
                var distance = event.position.distance_to(positions[id])
                if distance < best:
                    best = distance
                    chosen = str(id)
            if chosen != "":
                selected_id = chosen
                queue_redraw()
                entity_chosen.emit(chosen)
                accept_event()
