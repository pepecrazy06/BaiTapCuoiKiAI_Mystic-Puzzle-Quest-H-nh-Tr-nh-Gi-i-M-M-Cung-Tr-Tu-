"""
UTE Treasure Pathfinder AI - Python + HTML backend.

Chạy:
    python app.py

Mở trình duyệt:
    http://127.0.0.1:8010

Không cần cài Flask. File này dùng thư viện chuẩn của Python:
- http.server để chạy web server
- json để giao tiếp API
- search_algorithms.py để chạy BFS/DFS/IDS/UCS/Greedy/A*/Hill Climbing/Simulated Annealing
"""

from __future__ import annotations

import json
import mimetypes
import random
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from graph_data import DEFAULT_GOAL, DEFAULT_START, graph_payload
from search_algorithms import compare_all, solve

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8010





# =========================
# DUNGEON MODE - HGL02
# =========================
# Matrix 8x8 + Belief State / No Observation.
# Mỗi lần vào HGL02 sẽ sinh một dungeon session mới.
# AI không biết chính xác đang đứng ở ô nào, chỉ giữ tập belief các ô có thể.
# Map thật không được đưa toàn bộ cho frontend; frontend chỉ thấy belief thay đổi.

DUNGEON_SESSIONS: dict[str, dict] = {}

ACTIONS = ["N", "E", "S", "W"]
ACTION_DELTA = {
    "N": (-1, 0),
    "S": (1, 0),
    "W": (0, -1),
    "E": (0, 1),
}


def create_dungeon_session() -> dict:
    rng = random.Random(time.time_ns())
    session_id = uuid.uuid4().hex[:10]
    size = 8

    # Mỗi lần vào lại, exit có thể đổi góc, trap/fog đổi vị trí.
    exit_pos = rng.choice([(0, 0), (0, size - 1), (size - 1, 0), (size - 1, size - 1)])

    cells = []
    for r in range(size):
      for c in range(size):
        kind = rng.choice(["normal", "normal", "normal", "fog", "trap"])
        if (r, c) == exit_pos:
            kind = "exit"
        cells.append({"r": r, "c": c, "kind": kind})

    # No Observation: AI không biết vị trí ban đầu, nên tất cả ô đều có thể.
    initial_belief = [(r, c) for r in range(size) for c in range(size)]

    session = {
        "id": session_id,
        "created_at": time.time(),
        "size": size,
        "exit": exit_pos,
        "cells": cells,
        "initial_belief": initial_belief,
    }
    DUNGEON_SESSIONS[session_id] = session
    return session


def _move_cell(size: int, cell: tuple[int, int], action: str) -> tuple[int, int]:
    dr, dc = ACTION_DELTA[action]
    r, c = cell
    nr = max(0, min(size - 1, r + dr))
    nc = max(0, min(size - 1, c + dc))
    return (nr, nc)


def belief_step(session: dict, belief: set[tuple[int, int]], action: str) -> set[tuple[int, int]]:
    size = session["size"]
    return {_move_cell(size, cell, action) for cell in belief}


def _cell_kind(session: dict, pos: tuple[int, int]) -> str:
    if tuple(pos) == tuple(session["exit"]):
        return "exit"
    for cell in session["cells"]:
        if cell["r"] == pos[0] and cell["c"] == pos[1]:
            return cell["kind"]
    return "normal"


def belief_snapshot(session: dict, belief: set[tuple[int, int]], action: str | None = None, step: int = 0, message: str = "") -> dict:
    exit_pos = tuple(session["exit"])
    belief_cells = [
        {
            "r": r,
            "c": c,
            # Chỉ lộ kind của ô khi belief đã hội tụ; trước đó vẫn chỉ là "possible".
            "kind": "exit" if (r, c) == exit_pos and belief == {exit_pos} else "possible",
        }
        for r, c in sorted(belief)
    ]

    return {
        "step": step,
        "action": action,
        "belief": [[r, c] for r, c in sorted(belief)],
        "belief_cells": belief_cells,
        "possible_count": len(belief),
        "is_solved": belief == {exit_pos},
        "size": session["size"],
        "message": message,
    }


def observe_dungeon(session: dict) -> dict:
    belief = set(tuple(p) for p in session["initial_belief"])
    snap = belief_snapshot(
        session,
        belief,
        action=None,
        step=0,
        message="NO OBSERVATION: AI không biết chính xác đang ở ô nào trong ma trận 8x8.",
    )

    return {
        "session_id": session["id"],
        "algorithm": "belief_state_no_observation_matrix_8x8",
        "hidden_total_rooms": session["size"] * session["size"],
        **snap,
    }


def no_observation_belief_search(session: dict) -> dict:
    """
    Belief-State Search / No Observation trên ma trận 8x8.

    Trạng thái không phải là một ô đơn lẻ.
    Trạng thái là một tập belief gồm nhiều ô có thể đang đứng.

    Ví dụ:
    - Ban đầu belief = 64 ô.
    - Đi E nhiều lần: belief co lại về cột phải.
    - Đi S nhiều lần: belief co lại về hàng dưới.
    - Khi belief = {EXIT}, AI chắc chắn đã thoát.
    """
    start_time = time.time()
    size = session["size"]
    start_belief = frozenset(tuple(p) for p in session["initial_belief"])
    goal_belief = frozenset([tuple(session["exit"])])

    queue: list[frozenset[tuple[int, int]]] = [start_belief]
    parent: dict[frozenset[tuple[int, int]], tuple[frozenset[tuple[int, int]] | None, str | None]] = {
        start_belief: (None, None)
    }

    def heuristic_belief(belief: frozenset[tuple[int, int]]) -> float:
        er, ec = tuple(session["exit"])
        return sum(abs(r - er) + abs(c - ec) for r, c in belief) / max(len(belief), 1)

    found_belief = None
    expanded = 0
    max_expand = 5000

    while queue and expanded < max_expand:
        belief = queue.pop(0)
        expanded += 1

        if belief == goal_belief:
            found_belief = belief
            break

        candidates = []
        for action in ACTIONS:
            nb = frozenset(belief_step(session, set(belief), action))
            candidates.append((len(nb), heuristic_belief(nb), action, nb))
        candidates.sort()

        for _size, _h, action, nb in candidates:
            if nb not in parent:
                parent[nb] = (belief, action)
                queue.append(nb)

    if found_belief is None:
        # Fallback trực tiếp theo góc exit, vẫn đúng belief update.
        er, ec = tuple(session["exit"])
        actions = []
        actions += (["N"] * (size - 1) if er == 0 else ["S"] * (size - 1))
        actions += (["W"] * (size - 1) if ec == 0 else ["E"] * (size - 1))
    else:
        actions = []
        cur = found_belief
        while parent[cur][0] is not None:
            prev, action = parent[cur]
            actions.append(action)
            cur = prev
        actions.reverse()

    steps = []
    belief = set(start_belief)
    steps.append(belief_snapshot(
        session,
        belief,
        action=None,
        step=0,
        message="Khởi tạo belief: 64 ô đều có thể là vị trí hiện tại.",
    ))

    for i, action in enumerate(actions, start=1):
        old_count = len(belief)
        belief = belief_step(session, belief, action)
        new_count = len(belief)
        msg = f"Đi {action}: belief giảm từ {old_count} khả năng còn {new_count} khả năng."
        if belief == {tuple(session["exit"])}:
            msg += " Belief hội tụ về EXIT, AI chắc chắn đã thoát."
        steps.append(belief_snapshot(session, belief, action=action, step=i, message=msg))
        if belief == {tuple(session["exit"])}:
            break

    return {
        "success": True,
        "algorithm": "belief_state_no_observation_matrix_8x8",
        "found": belief == {tuple(session["exit"])},
        "session_id": session["id"],
        "steps": steps,
        "actions": actions,
        "nodes_expanded": expanded,
        "hidden_total_rooms": size * size,
        "final_belief": [[r, c] for r, c in sorted(belief)],
        "runtime_ms": round((time.time() - start_time) * 1000, 3),
        "explanation": (
            "Belief State / No Observation trên ma trận 8x8: AI không biết vị trí thật. "
            "AI chỉ cập nhật tập belief sau mỗi hành động N/E/S/W. "
            "Khi belief chỉ còn đúng ô EXIT, AI chắc chắn tìm được đường ra."
        ),
    }



# =========================
# AND-OR DUNGEON - M26
# =========================
# Hầm ngục bất định tại node M26.
# Route chính KHÔNG bị ép phải đi qua M26.
# Nếu một thuật toán chọn route đi ngang M26, game sẽ kích hoạt dungeon này.
# Dungeon có nhiều lối thoát, có bẫy; dính bẫy thì reset về START.

ANDOR_PROBLEM = {
    "initial_state": "M26_START",
    "goals": ["EXIT_A", "EXIT_B"],
    "rooms": {
        "M26_START": {"name": "Cổng M26", "x": 70, "y": 215, "kind": "start"},
        "HALL_A": {"name": "Hành lang trái", "x": 210, "y": 110, "kind": "normal"},
        "HALL_B": {"name": "Hành lang phải", "x": 220, "y": 315, "kind": "normal"},
        "KEY_ROOM": {"name": "Phòng chìa khóa", "x": 390, "y": 105, "kind": "key"},
        "BRIDGE_ROOM": {"name": "Cầu đá", "x": 390, "y": 315, "kind": "normal"},
        "TRAP_ROOM": {"name": "Phòng bẫy", "x": 500, "y": 225, "kind": "trap"},
        "EXIT_A": {"name": "Lối ra A", "x": 630, "y": 110, "kind": "exit"},
        "EXIT_B": {"name": "Lối ra B", "x": 630, "y": 315, "kind": "exit"},
    },
    "actions": {
        "M26_START": ["LEFT_DOOR", "RIGHT_DOOR"],
        "HALL_A": ["MAGIC_GATE", "RISKY_SHORTCUT"],
        "HALL_B": ["SAFE_TUNNEL", "CROSS_BRIDGE"],
        "KEY_ROOM": ["OPEN_EXIT_A", "SECRET_EXIT"],
        "BRIDGE_ROOM": ["OPEN_EXIT_B", "UNSTABLE_BRIDGE"],
        "TRAP_ROOM": ["RESET_TO_START"],
        "EXIT_A": [],
        "EXIT_B": [],
    },
    "results": {
        # Cửa trái có thể đi đúng HALL_A hoặc đạp bẫy reset.
        ("M26_START", "LEFT_DOOR"): ["HALL_A", "TRAP_ROOM"],
        # Cửa phải là đường an toàn hơn.
        ("M26_START", "RIGHT_DOOR"): ["HALL_B"],

        # Nhánh trái có 2 đường thoát.
        ("HALL_A", "MAGIC_GATE"): ["KEY_ROOM"],
        ("HALL_A", "RISKY_SHORTCUT"): ["EXIT_A", "TRAP_ROOM"],

        # Nhánh phải có đường an toàn và đường rủi ro.
        ("HALL_B", "SAFE_TUNNEL"): ["EXIT_B"],
        ("HALL_B", "CROSS_BRIDGE"): ["BRIDGE_ROOM", "TRAP_ROOM"],

        ("KEY_ROOM", "OPEN_EXIT_A"): ["EXIT_A"],
        ("KEY_ROOM", "SECRET_EXIT"): ["EXIT_B"],

        ("BRIDGE_ROOM", "OPEN_EXIT_B"): ["EXIT_B"],
        ("BRIDGE_ROOM", "UNSTABLE_BRIDGE"): ["EXIT_B", "TRAP_ROOM"],

        # Dính bẫy thì đi lại từ đầu.
        ("TRAP_ROOM", "RESET_TO_START"): ["M26_START"],
    },
}


def andor_goal_test(state: str) -> bool:
    return state in ANDOR_PROBLEM["goals"]


def andor_results(state: str, action: str) -> list[str]:
    return ANDOR_PROBLEM["results"].get((state, action), [])


def and_search(states: list[str], path: list[str], trace: list[dict]):
    plans = {}
    for state in states:
        plan_s = or_search(state, path, trace)
        if plan_s == "failure":
            trace.append({
                "type": "AND_FAIL",
                "state": state,
                "message": f"Nhánh kết quả {state} thất bại nên action cha không bảo đảm thành công.",
            })
            return "failure"
        plans[state] = plan_s

    trace.append({
        "type": "AND_OK",
        "states": states,
        "message": f"Tất cả kết quả {states} đều có kế hoạch xử lý.",
    })
    return plans


def or_search(state: str, path: list[str], trace: list[dict]):
    trace.append({
        "type": "OR",
        "state": state,
        "path": path,
        "message": f"OR node: AI đang xét {state} và được chọn hành động.",
    })

    if andor_goal_test(state):
        trace.append({
            "type": "GOAL",
            "state": state,
            "message": f"{state} là một lối ra, trả về kế hoạch rỗng.",
        })
        return []

    if state in path:
        trace.append({
            "type": "LOOP",
            "state": state,
            "message": f"Tránh lặp: {state} đã nằm trong path {path}.",
        })
        return "failure"

    for action in ANDOR_PROBLEM["actions"].get(state, []):
        result_states = andor_results(state, action)
        trace.append({
            "type": "ACTION",
            "state": state,
            "action": action,
            "results": result_states,
            "message": f"Thử action {action}. Kết quả có thể xảy ra: {result_states}.",
        })

        plan = and_search(result_states, path + [state], trace)

        if plan != "failure":
            trace.append({
                "type": "CHOOSE",
                "state": state,
                "action": action,
                "message": f"Chọn {action} tại {state} vì mọi kết quả đều có kế hoạch.",
            })
            return {"action": action, "results": plan}

    trace.append({
        "type": "OR_FAIL",
        "state": state,
        "message": f"Không có action nào tại {state} đảm bảo thoát.",
    })
    return "failure"


def andor_graph_search() -> dict:
    trace: list[dict] = []
    plan = or_search(ANDOR_PROBLEM["initial_state"], [], trace)

    edges = []
    for (state, action), results in ANDOR_PROBLEM["results"].items():
        for result in results:
            edges.append({
                "from": state,
                "to": result,
                "action": action,
                "is_trap": result == "TRAP_ROOM",
                "is_reset": state == "TRAP_ROOM" and result == "M26_START",
            })

    return {
        "success": True,
        "algorithm": "and_or_search",
        "found": plan != "failure",
        "start": ANDOR_PROBLEM["initial_state"],
        "goals": ANDOR_PROBLEM["goals"],
        "rooms": ANDOR_PROBLEM["rooms"],
        "edges": edges,
        "plan": plan,
        "trace": trace,
        "explanation": (
            "AND-OR Search tại M26: hầm ngục có nhiều lối thoát và hành động bất định. "
            "Một số hành động có thể dính bẫy; nếu vào TRAP_ROOM thì RESET_TO_START đưa về đầu. "
            "Thuật toán chỉ chọn kế hoạch nếu mọi kết quả có thể xảy ra đều xử lý được."
        ),
    }




# =========================
# DUNGEON MODE - DUN02
# =========================
# Hầm ngục dùng bản đồ ảnh thật + Backtracking + Forward Checking.
# Ý tưởng bài toán:
# - Nhân vật vào DUN02.
# - AI phải lấy chìa khóa ở ô lục giác phía dưới bên phải.
# - Chỉ sau khi có chìa khóa mới được thoát qua EXIT.
# - Có vật cản/ngõ cụt để thể hiện rõ forward checking cắt nhánh sớm.
# - Có nhánh sai để thể hiện rõ backtracking quay lui.

DUN02_SESSIONS: dict[str, dict] = {}

DUN02_MAP = {
    "image": "/static/assets/dun02_dungeon_map.png",
    "width": 1380,
    "height": 1036,
    "start": "DS",
    "key": "KEY",
    "exit": "EXIT",
    "nodes": {
        # Vào hầm ở chữ S giữa map.
        "DS":   {"label": "Start",          "x": 645,  "y": 300, "kind": "start"},

        # Khu trung tâm.
        "J1":   {"label": "Ngã ba đá",       "x": 640,  "y": 503, "kind": "junction"},

        # Nhánh trái là nhánh sai/ngõ cụt để backtracking quay lui.
        "W1":   {"label": "Sảnh tây",        "x": 436,  "y": 535, "kind": "room"},
        "W2":   {"label": "Kho đổ nát",      "x": 220,  "y": 540, "kind": "dead_end"},

        # Đường xuống chìa khóa.
        "S1":   {"label": "Trục nam",        "x": 640,  "y": 640, "kind": "corridor"},
        "S2":   {"label": "Kho phía nam",    "x": 745,  "y": 898, "kind": "room"},
        "E1":   {"label": "Hành lang đông",  "x": 880,  "y": 898, "kind": "corridor"},
        "E3":   {"label": "Phòng bàn tròn",  "x": 1080, "y": 790, "kind": "room"},
        # Chìa khóa đặt ở ô lục giác phía dưới bên phải.
        "KEY":  {"label": "Chìa khóa",       "x": 1260, "y": 914, "kind": "key"},

        # Đường từ khu đông lên exit.
        "E2":   {"label": "Đại sảnh đông",   "x": 970,  "y": 530, "kind": "junction"},
        "N1":   {"label": "Cầu thang đông",  "x": 930,  "y": 335, "kind": "corridor"},
        "N2":   {"label": "Khu giường",      "x": 945,  "y": 146, "kind": "junction"},
        "N3":   {"label": "Lối sang chữ T",  "x": 684,  "y": 148, "kind": "corridor"},
        "EXIT": {"label": "Exit",            "x": 558,  "y": 116, "kind": "exit"},

        # Vật cản/ngõ cụt cho forward checking.
        "P1":   {"label": "Thùng chắn",      "x": 1035, "y": 290, "kind": "dead_end"},
        "P2":   {"label": "Phòng khóa",      "x": 1152, "y": 118, "kind": "dead_end"},
        "T01":  {"label": "Bẫy sập",        "x": 760,  "y": 650, "kind": "trap"},
    },
    # Thứ tự cạnh cố ý: thử nhánh trái sai trước để thấy backtracking,
    # sau đó mới tìm được đường đúng qua KEY rồi quay lên EXIT.
    "edges": [
        ("DS", "J1"),

        ("J1", "W1"),
        ("W1", "W2"),

        ("J1", "S1"),
        ("S1", "S2"),
        ("S2", "E1"),

        ("E1", "E3"),
        ("E3", "KEY"),

        ("E1", "E2"),
        ("E2", "P1"),
        ("E2", "N1"),
        ("N1", "N2"),
        ("N2", "P2"),
        ("N2", "N3"),
        ("N3", "EXIT"),

        ("S1", "T01"),
    ],
    "decorations": {
        "blocked": [
            {"x": 222,  "y": 539, "label": "Đống gỗ gãy", "width": 92, "height": 46},
            {"x": 1035, "y": 292, "label": "Thùng chắn",  "width": 88, "height": 44},
            {"x": 1152, "y": 118, "label": "Phòng khóa",  "width": 92, "height": 44},
        ]
    }
}


def _dun02_adjacency() -> dict[str, list[str]]:
    adj: dict[str, list[str]] = {nid: [] for nid in DUN02_MAP["nodes"]}
    for a, b in DUN02_MAP["edges"]:
        adj[a].append(b)
        adj[b].append(a)
    return adj


DUN02_ADJ = _dun02_adjacency()






# =========================
# HGL02 BELIEF DUNGEON - CUSTOM NODE EDITOR
# =========================
# Dùng ảnh dungeon thật thay cho ma trận 8x8.
# Người dùng có thể tự đánh node/cạnh trên map.
# Belief State:
# - Trạng thái tìm kiếm không phải là 1 node, mà là tập node có thể đang đứng.
# - Nếu user đặt nhiều node kind="start", belief ban đầu gồm tất cả start đó.
# - Nếu chỉ có 1 start, belief vẫn chạy như belief set có 1 phần tử.
# - Action là hướng di chuyển N/E/S/W. Từ mỗi node, backend tự suy ra cạnh nào thuộc hướng đó dựa trên tọa độ.
# - Nếu tại một node không có cạnh theo hướng action, kết quả là đứng yên.
# - Goal khi belief hội tụ về đúng EXIT.

HGL02_SESSIONS: dict[str, dict] = {}

HGL02_DEFAULT_MAP = {'image': '/static/assets/hgl02_belief_dungeon_map.png',
 'width': 1920,
 'height': 768,
 'start': 'H01',
 'exit': 'H58',
 'nodes': {'H01': {'label': 'Start H01', 'x': 396.8, 'y': 386.9, 'kind': 'start'},
           'H02': {'label': 'H02', 'x': 496.7, 'y': 353.1, 'kind': 'normal'},
           'H03': {'label': 'H03', 'x': 505.1, 'y': 270.2, 'kind': 'normal'},
           'H04': {'label': 'H04', 'x': 515.3, 'y': 182.2, 'kind': 'normal'},
           'H05': {'label': 'H05', 'x': 523.7, 'y': 119.6, 'kind': 'normal'},
           'H06': {'label': 'H06', 'x': 613.4, 'y': 104.3, 'kind': 'normal'},
           'H07': {'label': 'H07', 'x': 721.7, 'y': 109.4, 'kind': 'normal'},
           'H08': {'label': 'H08', 'x': 823.3, 'y': 109.4, 'kind': 'normal'},
           'H09': {'label': 'H09', 'x': 924.8, 'y': 112.8, 'kind': 'normal'},
           'H10': {'label': 'H10', 'x': 926.5, 'y': 178.8, 'kind': 'normal'},
           'H11': {'label': 'H11', 'x': 1006, 'y': 116.2, 'kind': 'normal'},
           'H12': {'label': 'H12', 'x': 1088.9, 'y': 109.4, 'kind': 'normal'},
           'H13': {'label': 'H13', 'x': 1007.7, 'y': 170.3, 'kind': 'normal'},
           'H14': {'label': 'H14', 'x': 924.8, 'y': 238, 'kind': 'normal'},
           'H15': {'label': 'H15', 'x': 1007.7, 'y': 238, 'kind': 'normal'},
           'H16': {'label': 'H16', 'x': 923.1, 'y': 290.5, 'kind': 'normal'},
           'H17': {'label': 'H17', 'x': 836.8, 'y': 290.5, 'kind': 'normal'},
           'H18': {'label': 'H18', 'x': 840.2, 'y': 222.8, 'kind': 'normal'},
           'H19': {'label': 'H19', 'x': 840.2, 'y': 158.5, 'kind': 'normal'},
           'H20': {'label': 'H20', 'x': 757.3, 'y': 161.9, 'kind': 'normal'},
           'H21': {'label': 'H21', 'x': 755.6, 'y': 224.5, 'kind': 'normal'},
           'H22': {'label': 'H22', 'x': 752.2, 'y': 285.4, 'kind': 'normal'},
           'H23': {'label': 'H23', 'x': 689.6, 'y': 292.2, 'kind': 'normal'},
           'H24': {'label': 'H24', 'x': 618.5, 'y': 288.8, 'kind': 'normal'},
           'H25': {'label': 'H25', 'x': 574.5, 'y': 280.3, 'kind': 'normal'},
           'H26': {'label': 'H26', 'x': 584.7, 'y': 217.7, 'kind': 'normal'},
           'H27': {'label': 'H27', 'x': 586.4, 'y': 163.6, 'kind': 'normal'},
           'H28': {'label': 'H28', 'x': 677.7, 'y': 168.6, 'kind': 'normal'},
           'H29': {'label': 'H29', 'x': 674.4, 'y': 214.3, 'kind': 'normal'},
           'H30': {'label': 'H30', 'x': 579.6, 'y': 346.3, 'kind': 'normal'},
           'H31': {'label': 'H31', 'x': 657.4, 'y': 353.1, 'kind': 'normal'},
           'H32': {'label': 'H32', 'x': 745.4, 'y': 353.1, 'kind': 'normal'},
           'H33': {'label': 'H33', 'x': 745.4, 'y': 415.7, 'kind': 'normal'},
           'H34': {'label': 'H34', 'x': 843.6, 'y': 349.7, 'kind': 'normal'},
           'H35': {'label': 'H35', 'x': 921.4, 'y': 356.5, 'kind': 'normal'},
           'H36': {'label': 'H36', 'x': 916.3, 'y': 415.7, 'kind': 'normal'},
           'H37': {'label': 'H37', 'x': 833.4, 'y': 424.2, 'kind': 'normal'},
           'H38': {'label': 'H38', 'x': 831.7, 'y': 483.4, 'kind': 'normal'},
           'H39': {'label': 'H39', 'x': 831.7, 'y': 556.2, 'kind': 'normal'},
           'H40': {'label': 'H40', 'x': 830, 'y': 628.9, 'kind': 'normal'},
           'H41': {'label': 'H41', 'x': 1009.4, 'y': 293.9, 'kind': 'normal'},
           'H42': {'label': 'H42', 'x': 1090.6, 'y': 295.5, 'kind': 'normal'},
           'H43': {'label': 'H43', 'x': 1087.3, 'y': 349.7, 'kind': 'normal'},
           'H44': {'label': 'H44', 'x': 1087.3, 'y': 408.9, 'kind': 'normal'},
           'H45': {'label': 'H45', 'x': 1168.5, 'y': 432.6, 'kind': 'normal'},
           'H46': {'label': 'H46', 'x': 1171.9, 'y': 486.8, 'kind': 'normal'},
           'H47': {'label': 'H47', 'x': 1256.5, 'y': 422.5, 'kind': 'normal'},
           'H48': {'label': 'H48', 'x': 1332.6, 'y': 420.8, 'kind': 'normal'},
           'H49': {'label': 'H49', 'x': 1344.5, 'y': 353.1, 'kind': 'normal'},
           'H50': {'label': 'H50', 'x': 1264.9, 'y': 356.5, 'kind': 'normal'},
           'H51': {'label': 'H51', 'x': 1180.3, 'y': 353.1, 'kind': 'normal'},
           'H52': {'label': 'H52', 'x': 1176.9, 'y': 287.1, 'kind': 'normal'},
           'H53': {'label': 'H53', 'x': 1261.6, 'y': 285.4, 'kind': 'normal'},
           'H54': {'label': 'H54', 'x': 1325.9, 'y': 290.5, 'kind': 'normal'},
           'H55': {'label': 'H55', 'x': 1429.1, 'y': 285.4, 'kind': 'normal'},
           'H56': {'label': 'H56', 'x': 1432.5, 'y': 356.5, 'kind': 'normal'},
           'H57': {'label': 'H57', 'x': 1512, 'y': 354.8, 'kind': 'normal'},
           'H58': {'label': 'Exit H58', 'x': 1591.5, 'y': 359.9, 'kind': 'exit'},
           'H59': {'label': 'H59', 'x': 1425.7, 'y': 214.3, 'kind': 'normal'},
           'H60': {'label': 'H60', 'x': 1418.9, 'y': 150, 'kind': 'normal'},
           'H61': {'label': 'H61', 'x': 1398.6, 'y': 102.6, 'kind': 'normal'},
           'H62': {'label': 'H62', 'x': 1330.9, 'y': 109.4, 'kind': 'normal'},
           'H63': {'label': 'H63', 'x': 1332.6, 'y': 168.6, 'kind': 'normal'},
           'H64': {'label': 'H64', 'x': 1337.7, 'y': 221.1, 'kind': 'normal'},
           'H65': {'label': 'H65', 'x': 1253.1, 'y': 224.5, 'kind': 'normal'},
           'H66': {'label': 'H66', 'x': 1239.6, 'y': 143.2, 'kind': 'normal'},
           'H67': {'label': 'H67', 'x': 1236.2, 'y': 97.6, 'kind': 'normal'},
           'H68': {'label': 'H68', 'x': 1165.1, 'y': 102.6, 'kind': 'normal'},
           'H69': {'label': 'H69', 'x': 923.1, 'y': 627.2, 'kind': 'normal'},
           'H70': {'label': 'H70', 'x': 1006, 'y': 628.9, 'kind': 'normal'},
           'H71': {'label': 'H71', 'x': 1011.1, 'y': 562.9, 'kind': 'normal'},
           'H72': {'label': 'H72', 'x': 1087.3, 'y': 559.5, 'kind': 'normal'},
           'H73': {'label': 'H73', 'x': 1099.1, 'y': 627.2, 'kind': 'normal'},
           'H74': {'label': 'H74', 'x': 1187.1, 'y': 628.9, 'kind': 'normal'},
           'H75': {'label': 'H75', 'x': 1182, 'y': 556.2, 'kind': 'normal'},
           'H76': {'label': 'H76', 'x': 1266.6, 'y': 559.5, 'kind': 'normal'},
           'H77': {'label': 'H77', 'x': 1371.6, 'y': 557.8, 'kind': 'normal'},
           'H78': {'label': 'H78', 'x': 1361.4, 'y': 496.9, 'kind': 'normal'},
           'H79': {'label': 'H79', 'x': 1280.2, 'y': 488.5, 'kind': 'normal'},
           'H80': {'label': 'H80', 'x': 1446, 'y': 498.6, 'kind': 'normal'},
           'H81': {'label': 'H81', 'x': 1444.3, 'y': 419.1, 'kind': 'normal'},
           'H82': {'label': 'H82', 'x': 1459.5, 'y': 566.3, 'kind': 'normal'},
           'H83': {'label': 'H83', 'x': 1459.5, 'y': 623.8, 'kind': 'normal'},
           'H84': {'label': 'H84', 'x': 1371.6, 'y': 628.9, 'kind': 'normal'},
           'H85': {'label': 'H85', 'x': 1290.3, 'y': 625.5, 'kind': 'normal'},
           'H86': {'label': 'H86', 'x': 748.8, 'y': 630.6, 'kind': 'normal'},
           'H87': {'label': 'H87', 'x': 654, 'y': 627.2, 'kind': 'normal'},
           'H88': {'label': 'H88', 'x': 561, 'y': 627.2, 'kind': 'normal'},
           'H89': {'label': 'H89', 'x': 478.1, 'y': 630.6, 'kind': 'normal'},
           'H90': {'label': 'H90', 'x': 473, 'y': 549.4, 'kind': 'normal'},
           'H91': {'label': 'H91', 'x': 484.8, 'y': 488.5, 'kind': 'normal'},
           'H92': {'label': 'H92', 'x': 576.2, 'y': 495.2, 'kind': 'normal'},
           'H93': {'label': 'H93', 'x': 584.7, 'y': 432.6, 'kind': 'normal'},
           'H94': {'label': 'H94', 'x': 660.8, 'y': 434.3, 'kind': 'normal'},
           'H95': {'label': 'H95', 'x': 655.7, 'y': 505.4, 'kind': 'normal'},
           'H96': {'label': 'H96', 'x': 652.4, 'y': 566.3, 'kind': 'normal'},
           'H97': {'label': 'H97', 'x': 559.3, 'y': 557.8, 'kind': 'normal'},
           'H98': {'label': 'H98', 'x': 748.8, 'y': 561.2, 'kind': 'normal'},
           'H99': {'label': 'H99', 'x': 745.4, 'y': 495.2, 'kind': 'normal'},
           'H100': {'label': 'H100', 'x': 498.4, 'y': 417.4, 'kind': 'normal'},
           'H101': {'label': 'H101', 'x': 1083.9, 'y': 486.8, 'kind': 'normal'},
           'H102': {'label': 'H102', 'x': 1012.8, 'y': 488.5, 'kind': 'normal'},
           'H103': {'label': 'H103', 'x': 923.1, 'y': 495.2, 'kind': 'normal'},
           'H104': {'label': 'H104', 'x': 919.7, 'y': 556.2, 'kind': 'normal'},
           'H105': {'label': 'H105', 'x': 1007.7, 'y': 422.5, 'kind': 'normal'},
           'H106': {'label': 'H106', 'x': 1007.7, 'y': 359.9, 'kind': 'normal'}},
 'edges': [['H01', 'H02'],
           ['H03', 'H02'],
           ['H04', 'H03'],
           ['H05', 'H04'],
           ['H06', 'H05'],
           ['H07', 'H06'],
           ['H08', 'H07'],
           ['H09', 'H08'],
           ['H09', 'H11'],
           ['H12', 'H11'],
           ['H13', 'H11'],
           ['H13', 'H10'],
           ['H09', 'H10'],
           ['H14', 'H10'],
           ['H16', 'H14'],
           ['H17', 'H16'],
           ['H18', 'H17'],
           ['H19', 'H18'],
           ['H19', 'H20'],
           ['H20', 'H21'],
           ['H21', 'H22'],
           ['H22', 'H23'],
           ['H23', 'H24'],
           ['H24', 'H25'],
           ['H25', 'H26'],
           ['H26', 'H27'],
           ['H27', 'H28'],
           ['H28', 'H29'],
           ['H25', 'H30'],
           ['H30', 'H31'],
           ['H31', 'H32'],
           ['H32', 'H33'],
           ['H32', 'H34'],
           ['H34', 'H35'],
           ['H35', 'H36'],
           ['H36', 'H37'],
           ['H37', 'H38'],
           ['H38', 'H39'],
           ['H39', 'H40'],
           ['H68', 'H67'],
           ['H67', 'H66'],
           ['H66', 'H65'],
           ['H65', 'H64'],
           ['H64', 'H63'],
           ['H63', 'H62'],
           ['H62', 'H61'],
           ['H61', 'H60'],
           ['H60', 'H59'],
           ['H59', 'H55'],
           ['H55', 'H54'],
           ['H54', 'H53'],
           ['H55', 'H56'],
           ['H56', 'H81'],
           ['H81', 'H80'],
           ['H80', 'H82'],
           ['H82', 'H83'],
           ['H83', 'H84'],
           ['H84', 'H85'],
           ['H80', 'H78'],
           ['H78', 'H77'],
           ['H78', 'H79'],
           ['H77', 'H76'],
           ['H53', 'H52'],
           ['H52', 'H51'],
           ['H14', 'H15'],
           ['H15', 'H41'],
           ['H41', 'H42'],
           ['H42', 'H43'],
           ['H43', 'H44'],
           ['H44', 'H45'],
           ['H45', 'H46'],
           ['H45', 'H47'],
           ['H47', 'H48'],
           ['H51', 'H50'],
           ['H50', 'H49'],
           ['H49', 'H48'],
           ['H76', 'H75'],
           ['H75', 'H74'],
           ['H104', 'H103'],
           ['H103', 'H102'],
           ['H102', 'H105'],
           ['H105', 'H106'],
           ['H102', 'H101'],
           ['H101', 'H72'],
           ['H73', 'H72'],
           ['H74', 'H73'],
           ['H72', 'H71'],
           ['H71', 'H70'],
           ['H70', 'H69'],
           ['H69', 'H40'],
           ['H99', 'H98'],
           ['H98', 'H96'],
           ['H96', 'H97'],
           ['H96', 'H95'],
           ['H95', 'H94'],
           ['H94', 'H93'],
           ['H93', 'H92'],
           ['H93', 'H100'],
           ['H92', 'H91'],
           ['H91', 'H90'],
           ['H90', 'H89'],
           ['H89', 'H88'],
           ['H88', 'H87'],
           ['H87', 'H86'],
           ['H86', 'H40'],
           ['H56', 'H57'],
           ['H57', 'H58']],
 'decorations': {'blocked': []}}


def solve_hgl02_andor_search(session: dict) -> dict:
    """
    AND-OR Search cho HGL02.
    State = node hiện tại trong hầm ngục.
    Goal = H58.
    Action = chọn đi sang một node kề.
    Vì map node hiện tại là graph rõ ràng, mỗi action có một kết quả chính là node được chọn.
    Cấu trúc OR_SEARCH / AND_SEARCH vẫn được giữ đúng dạng thuật toán AND-OR.
    """
    start_time = time.time()
    dungeon_map = session["map"]
    nodes = dungeon_map["nodes"]
    edges = dungeon_map["edges"]
    start_state = dungeon_map.get("start", "H01")
    goal_state = "H58"

    adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for a, b in edges:
        if a in nodes and b in nodes:
            adj[a].append(b)
            adj[b].append(a)

    # Sắp xếp láng giềng theo khoảng cách Manhattan tới goal để plan gọn hơn.
    gx = nodes[goal_state]["x"]
    gy = nodes[goal_state]["y"]

    def h(nid: str) -> float:
        n = nodes[nid]
        return abs(n["x"] - gx) + abs(n["y"] - gy)

    for nid in adj:
        adj[nid].sort(key=h)

    trace: list[dict] = []

    def goal_test(state: str) -> bool:
        return state == goal_state

    def actions(state: str) -> list[str]:
        return [f"GO_{nb}" for nb in adj.get(state, [])]

    def results(state: str, action: str) -> list[str]:
        # Deterministic result, but represented as a set/list for AND-OR.
        return [action.removeprefix("GO_")]

    def and_search(states: list[str], path: list[str]):
        plans = {}
        for s in states:
            plan_s = or_search(s, path)
            if plan_s == "failure":
                trace.append({
                    "type": "and_fail",
                    "state": s,
                    "path": path[:],
                    "message": f"AND_SEARCH thất bại tại {s}; một kết quả của action không có lời giải."
                })
                return "failure"
            plans[s] = plan_s
        return plans

    def or_search(state: str, path: list[str]):
        trace.append({
            "type": "or",
            "state": state,
            "path": path[:],
            "message": f"OR_SEARCH xét state {state}."
        })

        if goal_test(state):
            trace.append({
                "type": "goal",
                "state": state,
                "path": path[:],
                "message": f"{state} là goal H58, trả về kế hoạch rỗng."
            })
            return []

        if state in path:
            trace.append({
                "type": "loop",
                "state": state,
                "path": path[:],
                "message": f"Phát hiện lặp tại {state}, trả về failure."
            })
            return "failure"

        for action in actions(state):
            result_states = results(state, action)
            trace.append({
                "type": "try_action",
                "state": state,
                "action": action,
                "results": result_states,
                "path": path[:],
                "message": f"Thử action {action}; result_states = {result_states}."
            })
            plan = and_search(result_states, path + [state])
            if plan != "failure":
                return {"action": action, "results": plan}

        trace.append({
            "type": "or_fail",
            "state": state,
            "path": path[:],
            "message": f"Không còn action hợp lệ từ {state}, trả về failure."
        })
        return "failure"

    plan = or_search(start_state, [])

    def extract_path(plan_obj, current: str) -> list[str]:
        path = [current]
        seen = set()
        while isinstance(plan_obj, dict) and plan_obj.get("action") and current not in seen:
            seen.add(current)
            nxt = plan_obj["action"].removeprefix("GO_")
            path.append(nxt)
            plan_obj = plan_obj.get("results", {}).get(nxt)
            current = nxt
        return path

    path_nodes = extract_path(plan, start_state) if plan != "failure" else []
    path_edges = []
    for a, b in zip(path_nodes, path_nodes[1:]):
        path_edges.append({"from": a, "to": b})

    steps = []
    for idx, nid in enumerate(path_nodes):
        steps.append({
            "step": idx,
            "node": nid,
            "x": nodes[nid]["x"],
            "y": nodes[nid]["y"],
            "is_goal": nid == goal_state,
            "message": "Bắt đầu tại H01." if idx == 0 else f"Nhân vật di chuyển tới {nid}."
        })

    return {
        "success": True,
        "algorithm": "and_or_search_hgl02",
        "session_id": session["id"],
        "found": plan != "failure" and path_nodes and path_nodes[-1] == goal_state,
        "start": start_state,
        "goal": goal_state,
        "path_nodes": path_nodes,
        "path_edges": path_edges,
        "steps": steps,
        "plan": plan,
        "trace": trace,
        "nodes_expanded": sum(1 for t in trace if t["type"] == "or"),
        "runtime_ms": round((time.time() - start_time) * 1000, 3),
        "map": dungeon_map,
        "explanation": (
            "HGL02 dùng AND-OR Search. OR_SEARCH chọn action tại node hiện tại; "
            "AND_SEARCH kiểm tra mọi result_state của action. Goal mới là H58."
        ),
    }



def create_hgl02_session() -> dict:
    session_id = uuid.uuid4().hex[:10]
    session = {
        "id": session_id,
        "created_at": time.time(),
        "map": HGL02_DEFAULT_MAP,
    }
    HGL02_SESSIONS[session_id] = session
    return session


def hgl02_payload(session: dict) -> dict:
    return {
        "session_id": session["id"],
        "map": session["map"],
        "explanation": (
            "HGL02 dùng Belief State trên map hầm ngục tự đánh node. "
            "Người dùng có thể đặt node/cạnh, rồi backend tìm chuỗi hành động N/E/S/W làm belief hội tụ về EXIT."
        ),
    }


def _hgl02_build_adj(custom_map: dict) -> dict[str, list[str]]:
    nodes = custom_map.get("nodes", {})
    adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for edge in custom_map.get("edges", []):
        if len(edge) != 2:
            continue
        a, b = edge
        if a in nodes and b in nodes:
            if b not in adj[a]:
                adj[a].append(b)
            if a not in adj[b]:
                adj[b].append(a)
    return adj


def _hgl02_direction(src: dict, dst: dict) -> str:
    dx = dst["x"] - src["x"]
    dy = dst["y"] - src["y"]
    if abs(dx) >= abs(dy):
        return "E" if dx >= 0 else "W"
    return "S" if dy >= 0 else "N"


def _hgl02_direction_table(custom_map: dict) -> dict[str, dict[str, str]]:
    nodes = custom_map.get("nodes", {})
    adj = _hgl02_build_adj(custom_map)
    table: dict[str, dict[str, str]] = {}

    for node_id, n in nodes.items():
        table[node_id] = {}
        buckets: dict[str, list[tuple[float, str]]] = {"N": [], "E": [], "S": [], "W": []}

        for nb in adj.get(node_id, []):
            nb_node = nodes[nb]
            if nb_node.get("kind") == "blocked":
                continue
            d = _hgl02_direction(n, nb_node)
            dist = ((n["x"] - nb_node["x"]) ** 2 + (n["y"] - nb_node["y"]) ** 2) ** 0.5
            buckets[d].append((dist, nb))

        for d, items in buckets.items():
            if items:
                items.sort()
                table[node_id][d] = items[0][1]

    return table


def solve_hgl02_belief_custom(custom_map: dict, session_id: str = "hgl02-custom") -> dict:
    start_time = time.time()
    nodes = custom_map.get("nodes", {})
    edges = custom_map.get("edges", [])
    exit_id = custom_map.get("exit") or "HE"

    if not nodes or exit_id not in nodes:
        return {"success": False, "error": "Map HGL02 cần có node Exit."}

    start_nodes = [
        nid for nid, n in nodes.items()
        if n.get("kind") == "start" and n.get("kind") != "blocked"
    ]
    if not start_nodes:
        start_id = custom_map.get("start")
        if start_id in nodes:
            start_nodes = [start_id]

    if not start_nodes:
        return {"success": False, "error": "Map HGL02 cần ít nhất 1 node Start."}

    blocked = {nid for nid, n in nodes.items() if n.get("kind") == "blocked"}
    start_belief = frozenset(nid for nid in start_nodes if nid not in blocked)
    goal_belief = frozenset([exit_id])
    table = _hgl02_direction_table(custom_map)
    actions = ["N", "E", "S", "W"]

    def step_belief(belief: frozenset[str], action: str) -> frozenset[str]:
        result = []
        for s in belief:
            if s in blocked:
                continue
            nxt = table.get(s, {}).get(action, s)
            if nxt in blocked:
                nxt = s
            result.append(nxt)
        return frozenset(sorted(set(result)))

    def heuristic(belief: frozenset[str]) -> float:
        ex = nodes[exit_id]["x"]
        ey = nodes[exit_id]["y"]
        total = 0.0
        for nid in belief:
            n = nodes[nid]
            total += abs(n["x"] - ex) + abs(n["y"] - ey)
        return total / max(len(belief), 1)

    # BFS/A* nhẹ trên không gian belief.
    from heapq import heappop, heappush

    pq = []
    counter = 0
    heappush(pq, (heuristic(start_belief), 0, counter, start_belief))
    parent: dict[frozenset[str], tuple[frozenset[str] | None, str | None]] = {
        start_belief: (None, None)
    }
    best_cost = {start_belief: 0}
    expanded = 0
    found = None
    max_expand = 2000

    while pq and expanded < max_expand:
        _prio, cost, _c, belief = heappop(pq)
        expanded += 1

        if belief == goal_belief:
            found = belief
            break

        for action in actions:
            nb = step_belief(belief, action)
            if not nb:
                continue
            nc = cost + 1
            if nb not in best_cost or nc < best_cost[nb]:
                best_cost[nb] = nc
                parent[nb] = (belief, action)
                counter += 1
                heappush(pq, (nc + heuristic(nb), nc, counter, nb))

    action_plan: list[str] = []
    if found is not None:
        cur = found
        while parent[cur][0] is not None:
            prev, action = parent[cur]
            action_plan.append(action)
            cur = prev
        action_plan.reverse()

    steps = []
    belief = start_belief
    steps.append({
        "step": 0,
        "action": None,
        "belief": list(belief),
        "belief_nodes": {nid: nodes[nid] for nid in belief},
        "possible_count": len(belief),
        "message": f"Khởi tạo belief tại các Start: {', '.join(belief)}.",
        "is_solved": belief == goal_belief,
    })

    for i, action in enumerate(action_plan, start=1):
        old = belief
        belief = step_belief(belief, action)
        steps.append({
            "step": i,
            "action": action,
            "belief": list(belief),
            "belief_nodes": {nid: nodes[nid] for nid in belief},
            "possible_count": len(belief),
            "message": f"Thực hiện action {action}: belief từ {{{', '.join(old)}}} → {{{', '.join(belief)}}}.",
            "is_solved": belief == goal_belief,
        })

    result_map = {
        "image": custom_map.get("image", "/static/assets/hgl02_belief_dungeon_map.png"),
        "width": custom_map.get("width", 1920),
        "height": custom_map.get("height", 768),
        "start": custom_map.get("start") or (start_nodes[0] if start_nodes else None),
        "exit": exit_id,
        "nodes": nodes,
        "edges": edges,
        "decorations": custom_map.get("decorations", {"blocked": []}),
        "custom": custom_map.get("custom", True),
        "direction_table": table,
    }

    return {
        "success": True,
        "algorithm": "belief_state_custom_hgl02",
        "session_id": session_id,
        "found": belief == goal_belief,
        "start_belief": list(start_belief),
        "exit": exit_id,
        "actions": action_plan,
        "steps": steps,
        "nodes_expanded": expanded,
        "runtime_ms": round((time.time() - start_time) * 1000, 3),
        "map": result_map,
        "explanation": (
            "Belief State trên map HGL02 tự đánh node. Belief là tập các node có thể đang đứng. "
            "Mỗi action N/E/S/W cập nhật đồng thời tất cả khả năng trong belief. "
            "Khi belief còn đúng EXIT, AI chắc chắn thoát hầm ngục."
        ),
    }



# =========================
# DUN02 DUNGEON - BACKTRACKING + FORWARD CHECKING
# =========================
# DUN02 dùng ảnh hầm ngục riêng và thuật toán Backtracking + Forward Checking.
# Luật: phải lấy KEY trước rồi mới được đi tới EXIT.

DUN02_DEFAULT_MAP = {
    "image": "/static/assets/dun02_dungeon_map.png",
    "width": 1600,
    "height": 1200,
    "start": "DS",
    "key": "KEY",
    "exit": "EXIT",
    "nodes": {
        "U01": {
                "label": "Hành lang",
                "x": 198.6,
                "y": 655.9,
                "x_percent": 12.41,
                "y_percent": 54.66,
                "kind": "corridor"
        },
        "DS": {
                "label": "Start",
                "x": 201.5,
                "y": 654.9,
                "x_percent": 12.59,
                "y_percent": 54.57,
                "kind": "start"
        },
        "KEY": {
                "label": "KEY",
                "x": 1414.8,
                "y": 1047.7,
                "x_percent": 88.42,
                "y_percent": 87.31,
                "kind": "key"
        },
        "U02": {
                "label": "Hành lang",
                "x": 293.4,
                "y": 638.8,
                "x_percent": 18.34,
                "y_percent": 53.23,
                "kind": "corridor"
        },
        "U03": {
                "label": "Ngã ba",
                "x": 373.6,
                "y": 636.4,
                "x_percent": 23.35,
                "y_percent": 53.03,
                "kind": "junction"
        },
        "U04": {
                "label": "Hành lang",
                "x": 373.6,
                "y": 694.7,
                "x_percent": 23.35,
                "y_percent": 57.89,
                "kind": "corridor"
        },
        "U05": {
                "label": "Hành lang",
                "x": 445,
                "y": 633.5,
                "x_percent": 27.81,
                "y_percent": 52.79,
                "kind": "corridor"
        },
        "U06": {
                "label": "Hành lang",
                "x": 376.5,
                "y": 560.6,
                "x_percent": 23.53,
                "y_percent": 46.72,
                "kind": "corridor"
        },
        "U07": {
                "label": "Hành lang",
                "x": 376.5,
                "y": 481.8,
                "x_percent": 23.53,
                "y_percent": 40.15,
                "kind": "corridor"
        },
        "U08": {
                "label": "Hành lang",
                "x": 389.6,
                "y": 385.6,
                "x_percent": 24.35,
                "y_percent": 32.13,
                "kind": "corridor"
        },
        "U09": {
                "label": "Hành lang",
                "x": 388.2,
                "y": 287.9,
                "x_percent": 24.26,
                "y_percent": 23.99,
                "kind": "corridor"
        },
        "U10": {
                "label": "Hành lang",
                "x": 380.9,
                "y": 217.9,
                "x_percent": 23.81,
                "y_percent": 18.16,
                "kind": "corridor"
        },
        "U11": {
                "label": "Hành lang",
                "x": 452.3,
                "y": 212.5,
                "x_percent": 28.27,
                "y_percent": 17.71,
                "kind": "corridor"
        },
        "U12": {
                "label": "Hành lang",
                "x": 525.3,
                "y": 214,
                "x_percent": 32.83,
                "y_percent": 17.83,
                "kind": "corridor"
        },
        "U13": {
                "label": "Hành lang",
                "x": 618.6,
                "y": 212.5,
                "x_percent": 38.66,
                "y_percent": 17.71,
                "kind": "corridor"
        },
        "U14": {
                "label": "Hành lang",
                "x": 706.1,
                "y": 212.5,
                "x_percent": 44.13,
                "y_percent": 17.71,
                "kind": "corridor"
        },
        "U15": {
                "label": "Hành lang",
                "x": 780.5,
                "y": 214,
                "x_percent": 48.78,
                "y_percent": 17.83,
                "kind": "corridor"
        },
        "U16": {
                "label": "Hành lang",
                "x": 865,
                "y": 215.4,
                "x_percent": 54.06,
                "y_percent": 17.95,
                "kind": "corridor"
        },
        "U17": {
                "label": "Hành lang",
                "x": 946.7,
                "y": 218.4,
                "x_percent": 59.17,
                "y_percent": 18.2,
                "kind": "corridor"
        },
        "U18": {
                "label": "Hành lang",
                "x": 1031.3,
                "y": 215.4,
                "x_percent": 64.46,
                "y_percent": 17.95,
                "kind": "corridor"
        },
        "U19": {
                "label": "Hành lang",
                "x": 1127.5,
                "y": 206.7,
                "x_percent": 70.47,
                "y_percent": 17.22,
                "kind": "corridor"
        },
        "U20": {
                "label": "Hành lang",
                "x": 1082.3,
                "y": 284,
                "x_percent": 67.64,
                "y_percent": 23.67,
                "kind": "corridor"
        },
        "U21": {
                "label": "Hành lang",
                "x": 1086.7,
                "y": 379.7,
                "x_percent": 67.92,
                "y_percent": 31.64,
                "kind": "corridor"
        },
        "U22": {
                "label": "Hành lang",
                "x": 518,
                "y": 639.3,
                "x_percent": 32.38,
                "y_percent": 53.27,
                "kind": "corridor"
        },
        "U23": {
                "label": "Hành lang",
                "x": 606.9,
                "y": 649.5,
                "x_percent": 37.93,
                "y_percent": 54.13,
                "kind": "corridor"
        },
        "U24": {
                "label": "Hành lang",
                "x": 376.5,
                "y": 769.1,
                "x_percent": 23.53,
                "y_percent": 64.09,
                "kind": "corridor"
        },
        "U25": {
                "label": "Hành lang",
                "x": 378,
                "y": 869.7,
                "x_percent": 23.63,
                "y_percent": 72.47,
                "kind": "corridor"
        },
        "U26": {
                "label": "Hành lang",
                "x": 376.5,
                "y": 955.8,
                "x_percent": 23.53,
                "y_percent": 79.65,
                "kind": "corridor"
        },
        "U27": {
                "label": "Hành lang",
                "x": 382.3,
                "y": 1038.9,
                "x_percent": 23.89,
                "y_percent": 86.58,
                "kind": "corridor"
        },
        "U28": {
                "label": "Hành lang",
                "x": 459.6,
                "y": 1038.9,
                "x_percent": 28.73,
                "y_percent": 86.58,
                "kind": "corridor"
        },
        "U29": {
                "label": "Hành lang",
                "x": 536.9,
                "y": 1038.9,
                "x_percent": 33.56,
                "y_percent": 86.58,
                "kind": "corridor"
        },
        "U30": {
                "label": "Hành lang",
                "x": 628.8,
                "y": 1021.4,
                "x_percent": 39.3,
                "y_percent": 85.12,
                "kind": "corridor"
        },
        "U31": {
                "label": "Hành lang",
                "x": 691.5,
                "y": 1018.5,
                "x_percent": 43.22,
                "y_percent": 84.88,
                "kind": "corridor"
        },
        "U32": {
                "label": "Hành lang",
                "x": 770.3,
                "y": 1021.4,
                "x_percent": 48.14,
                "y_percent": 85.12,
                "kind": "corridor"
        },
        "U33": {
                "label": "Hành lang",
                "x": 843.2,
                "y": 1047.7,
                "x_percent": 52.7,
                "y_percent": 87.31,
                "kind": "corridor"
        },
        "U34": {
                "label": "Hành lang",
                "x": 926.3,
                "y": 1053.5,
                "x_percent": 57.89,
                "y_percent": 87.79,
                "kind": "corridor"
        },
        "U35": {
                "label": "Hành lang",
                "x": 1015.2,
                "y": 1056.4,
                "x_percent": 63.45,
                "y_percent": 88.03,
                "kind": "corridor"
        },
        "U36": {
                "label": "Hành lang",
                "x": 1378.4,
                "y": 1046.2,
                "x_percent": 86.15,
                "y_percent": 87.18,
                "kind": "corridor"
        },
        "U37": {
                "label": "Hành lang",
                "x": 1277.7,
                "y": 1046.2,
                "x_percent": 79.86,
                "y_percent": 87.18,
                "kind": "corridor"
        },
        "U38": {
                "label": "Hành lang",
                "x": 1158.2,
                "y": 1053.5,
                "x_percent": 72.39,
                "y_percent": 87.79,
                "kind": "corridor"
        },
        "U39": {
                "label": "Ngã ba",
                "x": 1083.8,
                "y": 1050.6,
                "x_percent": 67.74,
                "y_percent": 87.55,
                "kind": "junction"
        },
        "U40": {
                "label": "Hành lang",
                "x": 1078,
                "y": 952.9,
                "x_percent": 67.38,
                "y_percent": 79.41,
                "kind": "corridor"
        },
        "U41": {
                "label": "Hành lang",
                "x": 704.6,
                "y": 645.2,
                "x_percent": 44.04,
                "y_percent": 53.77,
                "kind": "corridor"
        },
        "U42": {
                "label": "Hành lang",
                "x": 824.2,
                "y": 636.4,
                "x_percent": 51.51,
                "y_percent": 53.03,
                "kind": "corridor"
        },
        "U43": {
                "label": "Hành lang",
                "x": 921.9,
                "y": 633.5,
                "x_percent": 57.62,
                "y_percent": 52.79,
                "kind": "corridor"
        },
        "U44": {
                "label": "Hành lang",
                "x": 1059,
                "y": 637.9,
                "x_percent": 66.19,
                "y_percent": 53.16,
                "kind": "corridor"
        },
        "U45": {
                "label": "Hành lang",
                "x": 1158.2,
                "y": 629.1,
                "x_percent": 72.39,
                "y_percent": 52.42,
                "kind": "corridor"
        },
        "U46": {
                "label": "Hành lang",
                "x": 1276.3,
                "y": 623.3,
                "x_percent": 79.77,
                "y_percent": 51.94,
                "kind": "corridor"
        },
        "U47": {
                "label": "Hành lang",
                "x": 1091.1,
                "y": 436.6,
                "x_percent": 68.19,
                "y_percent": 36.38,
                "kind": "corridor"
        },
        "U48": {
                "label": "Hành lang",
                "x": 1088.2,
                "y": 521.2,
                "x_percent": 68.01,
                "y_percent": 43.43,
                "kind": "corridor"
        },
        "U49": {
                "label": "Hành lang",
                "x": 1072.1,
                "y": 742.9,
                "x_percent": 67.01,
                "y_percent": 61.91,
                "kind": "corridor"
        },
        "U50": {
                "label": "Hành lang",
                "x": 1072.1,
                "y": 831.8,
                "x_percent": 67.01,
                "y_percent": 69.32,
                "kind": "corridor"
        },
        "EXIT": {
                "label": "Exit",
                "x": 149,
                "y": 645.2,
                "x_percent": 9.31,
                "y_percent": 53.77,
                "kind": "exit"
        },
        "U51": {
                "label": "Bẫy",
                "x": 1353.6,
                "y": 620.4,
                "x_percent": 84.6,
                "y_percent": 51.7,
                "kind": "trap"
        }
},
    "edges": [
        ("DS", "EXIT"),
        ("DS", "U01"),
        ("DS", "U02"),
        ("U02", "U03"),
        ("U03", "U05"),
        ("U03", "U06"),
        ("U03", "U04"),
        ("U05", "U22"),
        ("U22", "U23"),
        ("U23", "U41"),
        ("U41", "U42"),
        ("U42", "U43"),
        ("U43", "U44"),
        ("U44", "U45"),
        ("U45", "U46"),
        ("U46", "U51"),
        ("U44", "U48"),
        ("U48", "U47"),
        ("U47", "U21"),
        ("U21", "U20"),
        ("U20", "U19"),
        ("U44", "U49"),
        ("U49", "U50"),
        ("U50", "U40"),
        ("U40", "U39"),
        ("U06", "U07"),
        ("U07", "U08"),
        ("U08", "U09"),
        ("U09", "U10"),
        ("U10", "U11"),
        ("U11", "U12"),
        ("U12", "U13"),
        ("U13", "U14"),
        ("U14", "U15"),
        ("U15", "U16"),
        ("U16", "U17"),
        ("U17", "U18"),
        ("U18", "U19"),
        ("U04", "U24"),
        ("U24", "U25"),
        ("U25", "U26"),
        ("U26", "U27"),
        ("U27", "U28"),
        ("U28", "U29"),
        ("U29", "U30"),
        ("U30", "U31"),
        ("U31", "U32"),
        ("U32", "U33"),
        ("U33", "U34"),
        ("U34", "U35"),
        ("U35", "U39"),
        ("U39", "U38"),
        ("U38", "U37"),
        ("U37", "U36"),
        ("U36", "KEY")
    ],
    "decorations": {"blocked": []},
}


def create_dun02_session() -> dict:
    session_id = uuid.uuid4().hex[:10]
    session = {
        "id": session_id,
        "created_at": time.time(),
        "map": DUN02_DEFAULT_MAP,
    }
    DUN02_SESSIONS[session_id] = session
    return session


def dun02_payload(session: dict) -> dict:
    return {
        "session_id": session["id"],
        "map": session["map"],
        "explanation": (
            "DUN02 dùng Backtracking + Forward Checking. "
            "AI phải lấy KEY trước, sau đó mới được đi đến EXIT."
        ),
    }


def _dun02_build_adj(dungeon_map: dict) -> dict[str, list[str]]:
    nodes = dungeon_map.get("nodes", {})
    adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for a, b in dungeon_map.get("edges", []):
        if a in nodes and b in nodes:
            adj[a].append(b)
            adj[b].append(a)
    return adj


def solve_dun02_backtracking_fc(session: dict) -> dict:
    start_time = time.time()
    dungeon_map = session["map"]
    nodes = dungeon_map["nodes"]
    adj = _dun02_build_adj(dungeon_map)

    start = dungeon_map.get("start", "DS")
    key_node = dungeon_map.get("key", "KEY")
    exit_node = dungeon_map.get("exit", "EXIT")

    trace: list[dict] = []
    visited_order: list[str] = []
    solution_path: list[str] = []
    nodes_expanded = 0

    def state(node_id: str, has_key: bool) -> tuple[str, bool]:
        return (node_id, has_key)

    def remaining_goal(has_key: bool) -> str:
        return exit_node if has_key else key_node

    def preview_next_candidates(node_id: str, has_key: bool, path_states: set[tuple[str, bool]]) -> list[str]:
        preview = []
        for nb in adj.get(node_id, []):
            kind = nodes.get(nb, {}).get("kind", "normal")
            next_has_key = has_key or nb == key_node
            st = state(nb, next_has_key)

            if kind in {"blocked", "trap"}:
                continue
            if nb == exit_node and not next_has_key:
                continue
            if st in path_states:
                continue

            preview.append(nb)
        return preview

    def candidates(node_id: str, has_key: bool, path_states: set[tuple[str, bool]], depth: int) -> list[str]:
        out = []
        target = remaining_goal(has_key)

        for nb in adj.get(node_id, []):
            kind = nodes.get(nb, {}).get("kind", "normal")
            next_has_key = has_key or nb == key_node
            st = state(nb, next_has_key)

            if kind == "blocked":
                trace.append({
                    "type": "prune",
                    "node": node_id,
                    "candidate": nb,
                    "depth": depth,
                    "reason": f"Forward checking bỏ {nb} vì đây là vật cản.",
                })
                continue

            if kind == "trap":
                trace.append({
                    "type": "prune",
                    "node": node_id,
                    "candidate": nb,
                    "depth": depth,
                    "reason": f"Forward checking bỏ {nb} vì đây là bẫy.",
                })
                continue

            if nb == exit_node and not next_has_key:
                trace.append({
                    "type": "prune",
                    "node": node_id,
                    "candidate": nb,
                    "depth": depth,
                    "reason": "Forward checking bỏ EXIT vì chưa lấy KEY.",
                })
                continue

            if st in path_states:
                trace.append({
                    "type": "prune",
                    "node": node_id,
                    "candidate": nb,
                    "depth": depth,
                    "reason": "Forward checking bỏ trạng thái lặp trên nhánh hiện tại.",
                })
                continue

            preview = preview_next_candidates(nb, next_has_key, path_states | {st})
            terminal_ok = (nb == key_node and not has_key) or (nb == exit_node and next_has_key)

            if not preview and not terminal_ok:
                trace.append({
                    "type": "prune",
                    "node": node_id,
                    "candidate": nb,
                    "depth": depth,
                    "reason": f"Forward checking bỏ {nb} vì đi vào đây không còn nước hợp lệ để tới {target}.",
                })
                continue

            out.append(nb)

        return out

    def dfs(current: str, has_key: bool, path: list[str], path_states: set[tuple[str, bool]], depth: int) -> bool:
        nonlocal nodes_expanded, solution_path
        nodes_expanded += 1
        visited_order.append(current)

        trace.append({
            "type": "visit",
            "node": current,
            "depth": depth,
            "has_key": has_key,
            "message": f"Đang xét node {current}. {'Đã có KEY.' if has_key else 'Chưa có KEY.'}",
        })

        if current == key_node and not has_key:
            has_key = True
            path_states = set(path_states)
            path_states.add(state(current, True))
            trace.append({
                "type": "pickup_key",
                "node": current,
                "depth": depth,
                "has_key": True,
                "message": "Đã lấy KEY. Từ bây giờ EXIT mới hợp lệ.",
            })

        if current == exit_node and has_key:
            solution_path = path.copy()
            trace.append({
                "type": "success",
                "node": current,
                "depth": depth,
                "has_key": True,
                "message": "Thoát DUN02 thành công sau khi đã lấy KEY.",
            })
            return True

        cand = candidates(current, has_key, path_states, depth)
        if not cand:
            trace.append({
                "type": "backtrack",
                "node": current,
                "depth": depth,
                "has_key": has_key,
                "message": f"Không còn lựa chọn hợp lệ tại {current} → quay lui.",
            })
            return False

        for nb in cand:
            next_has_key = has_key or nb == key_node
            trace.append({
                "type": "choose",
                "node": current,
                "candidate": nb,
                "depth": depth,
                "has_key": has_key,
                "message": f"Backtracking chọn thử nhánh {nb} từ {current}.",
            })

            next_states = set(path_states)
            next_states.add(state(nb, next_has_key))

            if dfs(nb, next_has_key, path + [nb], next_states, depth + 1):
                return True

            trace.append({
                "type": "return",
                "node": current,
                "candidate": nb,
                "depth": depth,
                "has_key": has_key,
                "message": f"Nhánh {nb} thất bại → quay lui về {current}.",
            })

        trace.append({
            "type": "backtrack",
            "node": current,
            "depth": depth,
            "has_key": has_key,
            "message": f"Đã thử hết lựa chọn từ {current} → backtrack.",
        })
        return False

    found = dfs(start, False, [start], {state(start, False)}, 0)

    path_edges = [{"from": a, "to": b} for a, b in zip(solution_path, solution_path[1:])]

    return {
        "success": True,
        "algorithm": "backtracking_forward_checking_dun02",
        "session_id": session["id"],
        "found": found,
        "start": start,
        "key": key_node,
        "exit": exit_node,
        "path_nodes": solution_path,
        "path_edges": path_edges,
        "visited_order": visited_order,
        "trace": trace,
        "nodes_expanded": nodes_expanded,
        "runtime_ms": round((time.time() - start_time) * 1000, 3),
        "map": dungeon_map,
        "explanation": (
            "DUN02 dùng Backtracking + Forward Checking: thử từng nhánh, "
            "cắt bẫy/vật cản/EXIT khi chưa có KEY, rồi quay lui nếu nhánh sai."
        ),
    }





# =========================
# FB04 BELIEF DUNGEON - USER NODE EDITOR + BFS
# =========================
# Hầm ngục sân bóng tại node FB04.
# Thuật toán chỉ áp dụng riêng cho FB04: Belief State + BFS.
# Mặc định map KHÔNG có node. Người dùng tự click đặt node/cạnh trong UI.

FB04_SESSIONS: dict[str, dict] = {}

FB04_EMPTY_MAP = {
    "image": "/static/assets/fb04_belief_dungeon_map.png",
    "width": 2048,
    "height": 1536,
    "start": "B01",
    "exit": "B55",
    "nodes": {'B01': {'label': 'Start / Belief', 'x': 281.8, 'y': 934.2, 'x_percent': 13.76, 'y_percent': 60.82, 'kind': 'start'}, 'B02': {'label': 'Hành lang', 'x': 406.4, 'y': 862.5, 'x_percent': 19.84, 'y_percent': 56.15, 'kind': 'corridor'}, 'B03': {'label': 'Hành lang', 'x': 533, 'y': 787.3, 'x_percent': 26.03, 'y_percent': 51.26, 'kind': 'corridor'}, 'B04': {'label': 'Hành lang', 'x': 651.6, 'y': 712.2, 'x_percent': 31.82, 'y_percent': 46.37, 'kind': 'corridor'}, 'B05': {'label': 'Hành lang', 'x': 780.2, 'y': 648.9, 'x_percent': 38.1, 'y_percent': 42.25, 'kind': 'corridor'}, 'B06': {'label': 'Hành lang', 'x': 916.7, 'y': 583.6, 'x_percent': 44.76, 'y_percent': 37.99, 'kind': 'corridor'}, 'B07': {'label': 'Hành lang', 'x': 1025.5, 'y': 512.4, 'x_percent': 50.07, 'y_percent': 33.36, 'kind': 'corridor'}, 'B08': {'label': 'Hành lang', 'x': 400.4, 'y': 1002.9, 'x_percent': 19.55, 'y_percent': 65.29, 'kind': 'corridor'}, 'B09': {'label': 'Hành lang', 'x': 531, 'y': 933.7, 'x_percent': 25.93, 'y_percent': 60.79, 'kind': 'corridor'}, 'B10': {'label': 'Hành lang', 'x': 647.7, 'y': 856.6, 'x_percent': 31.63, 'y_percent': 55.77, 'kind': 'corridor'}, 'B11': {'label': 'Hành lang', 'x': 770.3, 'y': 785.3, 'x_percent': 37.61, 'y_percent': 51.13, 'kind': 'corridor'}, 'B12': {'label': 'Hành lang', 'x': 893, 'y': 722.1, 'x_percent': 43.6, 'y_percent': 47.01, 'kind': 'corridor'}, 'B13': {'label': 'Hành lang', 'x': 1021.5, 'y': 644.9, 'x_percent': 49.88, 'y_percent': 41.99, 'kind': 'corridor'}, 'B14': {'label': 'Hành lang', 'x': 1136.3, 'y': 577.7, 'x_percent': 55.48, 'y_percent': 37.61, 'kind': 'corridor'}, 'B15': {'label': 'Hành lang', 'x': 521.1, 'y': 1073.1, 'x_percent': 25.44, 'y_percent': 69.86, 'kind': 'corridor'}, 'B16': {'label': 'Hành lang', 'x': 645.7, 'y': 998, 'x_percent': 31.53, 'y_percent': 64.97, 'kind': 'corridor'}, 'B17': {'label': 'Hành lang', 'x': 768.4, 'y': 936.7, 'x_percent': 37.52, 'y_percent': 60.98, 'kind': 'corridor'}, 'B18': {'label': 'Hành lang', 'x': 891, 'y': 859.5, 'x_percent': 43.51, 'y_percent': 55.96, 'kind': 'corridor'}, 'B19': {'label': 'Hành lang', 'x': 1023.5, 'y': 792.3, 'x_percent': 49.98, 'y_percent': 51.58, 'kind': 'corridor'}, 'B20': {'label': 'Hành lang', 'x': 1148.1, 'y': 717.1, 'x_percent': 56.06, 'y_percent': 46.69, 'kind': 'corridor'}, 'B21': {'label': 'Hành lang', 'x': 1268.8, 'y': 651.8, 'x_percent': 61.95, 'y_percent': 42.43, 'kind': 'corridor'}, 'B22': {'label': 'Hành lang', 'x': 643.7, 'y': 1144.4, 'x_percent': 31.43, 'y_percent': 74.51, 'kind': 'corridor'}, 'B23': {'label': 'Hành lang', 'x': 766.4, 'y': 1071.2, 'x_percent': 37.42, 'y_percent': 69.74, 'kind': 'corridor'}, 'B24': {'label': 'Hành lang', 'x': 896.9, 'y': 1000, 'x_percent': 43.79, 'y_percent': 65.1, 'kind': 'corridor'}, 'B25': {'label': 'Start / Belief', 'x': 1017.6, 'y': 930.7, 'x_percent': 49.69, 'y_percent': 60.59, 'kind': 'start'}, 'B26': {'label': 'Hành lang', 'x': 1140.2, 'y': 859.5, 'x_percent': 55.67, 'y_percent': 55.96, 'kind': 'corridor'}, 'B27': {'label': 'Hành lang', 'x': 1262.9, 'y': 788.3, 'x_percent': 61.67, 'y_percent': 51.32, 'kind': 'corridor'}, 'B28': {'label': 'Hành lang', 'x': 1379.6, 'y': 717.1, 'x_percent': 67.36, 'y_percent': 46.69, 'kind': 'corridor'}, 'B29': {'label': 'Hành lang', 'x': 762.4, 'y': 1221.5, 'x_percent': 37.23, 'y_percent': 79.52, 'kind': 'corridor'}, 'B30': {'label': 'Hành lang', 'x': 887, 'y': 1148.3, 'x_percent': 43.31, 'y_percent': 74.76, 'kind': 'corridor'}, 'B31': {'label': 'Hành lang', 'x': 1017.6, 'y': 1073.1, 'x_percent': 49.69, 'y_percent': 69.86, 'kind': 'corridor'}, 'B32': {'label': 'Hành lang', 'x': 1130.3, 'y': 1000, 'x_percent': 55.19, 'y_percent': 65.1, 'kind': 'corridor'}, 'B33': {'label': 'Hành lang', 'x': 1254.9, 'y': 930.7, 'x_percent': 61.27, 'y_percent': 60.59, 'kind': 'corridor'}, 'B34': {'label': 'Hành lang', 'x': 1377.6, 'y': 859.5, 'x_percent': 67.27, 'y_percent': 55.96, 'kind': 'corridor'}, 'B35': {'label': 'Hành lang', 'x': 1502.2, 'y': 792.3, 'x_percent': 73.35, 'y_percent': 51.58, 'kind': 'corridor'}, 'B36': {'label': 'Hành lang', 'x': 877.1, 'y': 1290.7, 'x_percent': 42.83, 'y_percent': 84.03, 'kind': 'corridor'}, 'B37': {'label': 'Hành lang', 'x': 1013.6, 'y': 1209.6, 'x_percent': 49.49, 'y_percent': 78.75, 'kind': 'corridor'}, 'B38': {'label': 'Start / Belief', 'x': 1136.3, 'y': 1140.4, 'x_percent': 55.48, 'y_percent': 74.24, 'kind': 'start'}, 'B39': {'label': 'Hành lang', 'x': 1254.9, 'y': 1073.1, 'x_percent': 61.27, 'y_percent': 69.86, 'kind': 'corridor'}, 'B40': {'label': 'Hành lang', 'x': 1379.6, 'y': 1001.9, 'x_percent': 67.36, 'y_percent': 65.23, 'kind': 'corridor'}, 'B41': {'label': 'Hành lang', 'x': 1502.2, 'y': 930.7, 'x_percent': 73.35, 'y_percent': 60.59, 'kind': 'corridor'}, 'B42': {'label': 'Hành lang', 'x': 1628.8, 'y': 859.5, 'x_percent': 79.53, 'y_percent': 55.96, 'kind': 'corridor'}, 'B43': {'label': 'Hành lang', 'x': 1003.7, 'y': 1360, 'x_percent': 49.01, 'y_percent': 88.54, 'kind': 'corridor'}, 'B44': {'label': 'Hành lang', 'x': 1132.3, 'y': 1286.8, 'x_percent': 55.29, 'y_percent': 83.78, 'kind': 'corridor'}, 'B45': {'label': 'Hành lang', 'x': 1254.9, 'y': 1215.6, 'x_percent': 61.27, 'y_percent': 79.14, 'kind': 'corridor'}, 'B46': {'label': 'Hành lang', 'x': 1391.4, 'y': 1144.4, 'x_percent': 67.94, 'y_percent': 74.51, 'kind': 'corridor'}, 'B47': {'label': 'Hành lang', 'x': 1506.1, 'y': 1077.1, 'x_percent': 73.54, 'y_percent': 70.12, 'kind': 'corridor'}, 'B48': {'label': 'Hành lang', 'x': 1618.9, 'y': 1000, 'x_percent': 79.05, 'y_percent': 65.1, 'kind': 'corridor'}, 'B49': {'label': 'Hành lang', 'x': 1749.4, 'y': 926.8, 'x_percent': 85.42, 'y_percent': 60.34, 'kind': 'corridor'}, 'B51': {'label': 'Hành lang', 'x': 1379.6, 'y': 576.2, 'x_percent': 67.36, 'y_percent': 37.51, 'kind': 'corridor'}, 'B52': {'label': 'Hành lang', 'x': 1506.1, 'y': 656.3, 'x_percent': 73.54, 'y_percent': 42.73, 'kind': 'corridor'}, 'B53': {'label': 'Hành lang', 'x': 1498.2, 'y': 460.5, 'x_percent': 73.15, 'y_percent': 29.98, 'kind': 'corridor'}, 'B54': {'label': 'Hành lang', 'x': 1593.2, 'y': 513.9, 'x_percent': 77.79, 'y_percent': 33.46, 'kind': 'corridor'}, 'B55': {'label': 'Exit', 'x': 1670.3, 'y': 373.4, 'x_percent': 81.56, 'y_percent': 24.31, 'kind': 'exit'}},
    "edges": [['B01', 'B02'], ['B02', 'B03'], ['B03', 'B04'], ['B04', 'B05'], ['B05', 'B06'], ['B06', 'B07'], ['B07', 'B14'], ['B14', 'B21'], ['B21', 'B28'], ['B28', 'B51'], ['B51', 'B52'], ['B52', 'B53'], ['B53', 'B54'], ['B54', 'B55'], ['B08', 'B09'], ['B09', 'B10'], ['B10', 'B11'], ['B11', 'B12'], ['B12', 'B13'], ['B13', 'B14'], ['B15', 'B16'], ['B16', 'B17'], ['B17', 'B18'], ['B18', 'B19'], ['B19', 'B20'], ['B20', 'B21'], ['B22', 'B23'], ['B23', 'B24'], ['B24', 'B25'], ['B25', 'B26'], ['B26', 'B27'], ['B27', 'B28'], ['B29', 'B30'], ['B30', 'B31'], ['B31', 'B32'], ['B32', 'B33'], ['B33', 'B34'], ['B34', 'B35'], ['B35', 'B28'], ['B36', 'B37'], ['B37', 'B38'], ['B38', 'B39'], ['B39', 'B40'], ['B40', 'B41'], ['B41', 'B42'], ['B42', 'B51'], ['B43', 'B44'], ['B44', 'B45'], ['B45', 'B46'], ['B46', 'B47'], ['B47', 'B48'], ['B48', 'B49'], ['B49', 'B42'], ['B01', 'B08'], ['B08', 'B15'], ['B15', 'B22'], ['B02', 'B09'], ['B09', 'B16'], ['B16', 'B23'], ['B23', 'B29'], ['B03', 'B10'], ['B10', 'B17'], ['B17', 'B24'], ['B24', 'B30'], ['B30', 'B36'], ['B04', 'B11'], ['B11', 'B18'], ['B18', 'B25'], ['B25', 'B31'], ['B31', 'B37'], ['B37', 'B43'], ['B05', 'B12'], ['B12', 'B19'], ['B19', 'B26'], ['B26', 'B32'], ['B32', 'B38'], ['B38', 'B44'], ['B06', 'B13'], ['B13', 'B20'], ['B20', 'B27'], ['B27', 'B33'], ['B33', 'B39'], ['B39', 'B45'], ['B28', 'B34'], ['B34', 'B40'], ['B40', 'B46'], ['B35', 'B41'], ['B41', 'B47'], ['B42', 'B48']],
    "transitions": {'B01': {'RIGHT': 'B02'}, 'B02': {'RIGHT': 'B03'}, 'B03': {'RIGHT': 'B04'}, 'B04': {'RIGHT': 'B05'}, 'B05': {'RIGHT': 'B06'}, 'B06': {'RIGHT': 'B07'}, 'B07': {'RIGHT': 'B14'}, 'B14': {'RIGHT': 'B21'}, 'B21': {'RIGHT': 'B28'}, 'B28': {'RIGHT': 'B51'}, 'B51': {'RIGHT': 'B52'}, 'B52': {'RIGHT': 'B53'}, 'B53': {'RIGHT': 'B54'}, 'B54': {'RIGHT': 'B55'}, 'B25': {'RIGHT': 'B26'}, 'B26': {'RIGHT': 'B27'}, 'B27': {'RIGHT': 'B28'}, 'B38': {'RIGHT': 'B39'}, 'B39': {'RIGHT': 'B40'}, 'B40': {'RIGHT': 'B41'}, 'B41': {'RIGHT': 'B42'}, 'B42': {'RIGHT': 'B51'}, 'B55': {'RIGHT': 'B55', 'UP': 'B55', 'DOWN': 'B55', 'LEFT': 'B55'}},
    "required_route": ["B51", "B52", "B53", "B54", "B55"],
    "display_route": ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B14", "B21", "B28", "B51", "B52", "B53", "B54", "B55"],
    "decorations": {"blocked": []},
    "custom": False,
}


def create_fb04_session() -> dict:
    session_id = uuid.uuid4().hex[:10]
    start_nodes = [
        nid for nid, n in FB04_EMPTY_MAP.get("nodes", {}).items()
        if n.get("kind") == "start"
    ]
    actual_start = random.choice(start_nodes) if start_nodes else FB04_EMPTY_MAP.get("start")
    session = {
        "id": session_id,
        "created_at": time.time(),
        "map": FB04_EMPTY_MAP,
        "actual_start": actual_start,
    }
    FB04_SESSIONS[session_id] = session
    return session


def fb04_payload(session: dict) -> dict:
    return {
        "session_id": session["id"],
        "map": session["map"],
        "belief": [nid for nid, n in session["map"].get("nodes", {}).items() if n.get("kind") == "start"],
        "actual_start": session.get("actual_start"),
        "explanation": (
            "FB04 dùng Belief State + BFS trên map node đã cố định. "
            "Belief ban đầu gồm B01, B25, B38 và route bắt buộc đi qua B51 → B52 → B53 → B54 → B55."
        ),
    }


def _fb04_build_adj(dungeon_map: dict) -> dict[str, list[str]]:
    nodes = dungeon_map.get("nodes", {})
    adj: dict[str, list[str]] = {nid: [] for nid in nodes}
    for edge in dungeon_map.get("edges", []):
        if len(edge) != 2:
            continue
        a, b = edge
        if a in nodes and b in nodes:
            if nodes[a].get("kind") == "blocked" or nodes[b].get("kind") == "blocked":
                continue
            if b not in adj[a]:
                adj[a].append(b)
            if a not in adj[b]:
                adj[b].append(a)
    return adj


def _fb04_direction(src: dict, dst: dict) -> str:
    dx = dst["x"] - src["x"]
    dy = dst["y"] - src["y"]
    if abs(dx) >= abs(dy):
        return "RIGHT" if dx >= 0 else "LEFT"
    return "DOWN" if dy >= 0 else "UP"


def _fb04_direction_table(dungeon_map: dict) -> dict[str, dict[str, str]]:
    nodes = dungeon_map.get("nodes", {})
    adj = _fb04_build_adj(dungeon_map)
    table: dict[str, dict[str, str]] = {}

    for node_id, n in nodes.items():
        table[node_id] = {}
        buckets: dict[str, list[tuple[float, str]]] = {"UP": [], "RIGHT": [], "DOWN": [], "LEFT": []}

        for nb in adj.get(node_id, []):
            nb_node = nodes[nb]
            if nb_node.get("kind") == "blocked":
                continue
            d = _fb04_direction(n, nb_node)
            dist = ((n["x"] - nb_node["x"]) ** 2 + (n["y"] - nb_node["y"]) ** 2) ** 0.5
            buckets[d].append((dist, nb))

        for d, items in buckets.items():
            if items:
                items.sort()
                table[node_id][d] = items[0][1]

    return table


def solve_fb04_belief_bfs(custom_map: dict, session_id: str = "fb04-custom", actual_start: str | None = None) -> dict:
    start_time = time.time()
    dungeon_map = custom_map or FB04_EMPTY_MAP
    nodes = dungeon_map.get("nodes", {})
    edges = dungeon_map.get("edges", [])
    exit_id = dungeon_map.get("exit")

    if not nodes:
        return {
            "success": False,
            "error": "Map FB04 chưa có node. Hãy bật chỉnh node và click lên map để thêm node.",
        }

    if not exit_id or exit_id not in nodes:
        return {
            "success": False,
            "error": "Map FB04 cần có node Exit.",
        }

    start_nodes = [
        nid for nid, n in nodes.items()
        if n.get("kind") == "start" and n.get("kind") != "blocked"
    ]

    if not start_nodes:
        start_id = dungeon_map.get("start")
        if start_id in nodes:
            start_nodes = [start_id]

    if not start_nodes:
        return {
            "success": False,
            "error": "Map FB04 cần ít nhất 1 node Start.",
        }

    if actual_start not in start_nodes:
        actual_start = start_nodes[0]

    blocked = {nid for nid, n in nodes.items() if n.get("kind") == "blocked"}
    start_belief = frozenset(nid for nid in start_nodes if nid not in blocked)
    goal_belief = frozenset([exit_id])
    # Chạy thật FB04 dùng transition thiết kế sẵn, không suy cạnh theo hình học.
    # Như vậy route không thể nhảy thẳng lên Goal; mọi nhánh phải đi qua
    # B51 -> B52 -> B53 -> B54 -> B55.
    table: dict[str, dict[str, str]] = {nid: {} for nid in nodes}
    manual_transitions = dungeon_map.get("transitions", {})
    for src, action_map in manual_transitions.items():
        table.setdefault(src, {})
        for action, dst in action_map.items():
            if src in nodes and dst in nodes:
                table[src][action] = dst

    actions = ["RIGHT", "UP", "DOWN", "LEFT"]

    def step_belief(belief: frozenset[str], action: str) -> frozenset[str]:
        result = []
        for s in belief:
            if s in blocked:
                continue
            nxt = table.get(s, {}).get(action, s)
            if nxt in blocked:
                nxt = s
            result.append(nxt)
        return frozenset(sorted(set(result)))

    from collections import deque

    queue = deque([start_belief])
    parent: dict[frozenset[str], tuple[frozenset[str] | None, str | None]] = {
        start_belief: (None, None)
    }

    trace: list[dict] = []
    expanded = 0
    found = None
    max_expand = 5000

    while queue and expanded < max_expand:
        belief = queue.popleft()
        expanded += 1
        trace.append({
            "type": "expand",
            "belief": list(belief),
            "possible_count": len(belief),
            "message": "BFS mở rộng belief {" + ", ".join(belief) + "}.",
        })

        if belief == goal_belief:
            found = belief
            break

        for action in actions:
            nb = step_belief(belief, action)
            trace.append({
                "type": "try_action",
                "action": action,
                "from_belief": list(belief),
                "to_belief": list(nb),
                "possible_count": len(nb),
                "message": "Thử action " + action + ": belief chuyển thành {" + ", ".join(nb) + "}.",
            })
            if nb not in parent:
                parent[nb] = (belief, action)
                queue.append(nb)

    action_plan: list[str] = []
    if found is not None:
        cur = found
        while parent[cur][0] is not None:
            prev, action = parent[cur]
            action_plan.append(action)
            cur = prev
        action_plan.reverse()

    steps = []
    belief = start_belief
    steps.append({
        "step": 0,
        "action": None,
        "belief": list(belief),
        "possible_count": len(belief),
        "is_solved": belief == goal_belief,
        "message": "Khởi tạo belief gồm {" + ", ".join(belief) + "}.",
    })

    for i, action in enumerate(action_plan, start=1):
        old = belief
        belief = step_belief(belief, action)
        steps.append({
            "step": i,
            "action": action,
            "belief": list(belief),
            "possible_count": len(belief),
            "is_solved": belief == goal_belief,
            "message": "BFS chọn " + action + ": belief {" + ", ".join(old) + "} → {" + ", ".join(belief) + "}.",
        })

    # Đường vẽ minh họa tổng thể.
    path_nodes = dungeon_map.get("display_route") or []
    if not path_nodes:
        for step in steps:
            b = step["belief"]
            path_nodes.append(b[0] if b else exit_id)

    # Đường đi thực tế của 1 nhân vật thật, xuất phát ngẫu nhiên từ 1 Start.
    actual_path = [actual_start]
    current_actual = actual_start
    for action in action_plan:
        current_actual = table.get(current_actual, {}).get(action, current_actual)
        actual_path.append(current_actual)

    result_map = {
        "image": dungeon_map.get("image", "/static/assets/fb04_belief_dungeon_map.png"),
        "width": dungeon_map.get("width", 2048),
        "height": dungeon_map.get("height", 1536),
        "start": dungeon_map.get("start") or (start_nodes[0] if start_nodes else None),
        "exit": exit_id,
        "nodes": nodes,
        "edges": edges,
        "decorations": dungeon_map.get("decorations", {"blocked": []}),
        "custom": True,
        "direction_table": table,
    }

    return {
        "success": True,
        "algorithm": "belief_state_bfs_fb04",
        "session_id": session_id,
        "found": belief == goal_belief,
        "start_belief": list(start_belief),
        "exit": exit_id,
        "actual_start": actual_start,
        "actual_path": actual_path,
        "actions": action_plan,
        "steps": steps,
        "path_nodes": path_nodes,
        "required_route": dungeon_map.get("required_route", []),
        "passed_required_route": all(x in path_nodes for x in dungeon_map.get("required_route", [])),
        "nodes_expanded": expanded,
        "runtime_ms": round((time.time() - start_time) * 1000, 3),
        "map": result_map,
        "trace": trace[:140],
        "explanation": (
            "FB04 dùng Belief State + BFS. BFS duyệt trên không gian belief và đảm bảo tìm ra lời giải nếu map hữu hạn có chuỗi action làm belief hội tụ về Exit."
        ),
    }



# =========================
# FINAL BOSS - DRAGON MINIMAX TACTICAL PUZZLE
# =========================
# Mini-game cuối: 4x4 tactical puzzle.
# Knight = MAX: đi tới ô rồng.
# Dragon = MIN: dùng Minimax để chọn ô phun lửa chặn đường.
# Mỗi lượt: Knight đi 1 ô kề cạnh -> nếu chưa thắng, Dragon phun lửa đốt 1 ô.

BOSS_SESSIONS: dict[str, dict] = {}

BOSS_SIZE = 5
BOSS_MAX_TURNS = 18
BOSS_MINIMAX_DEPTH = 2

# Đường chính để demo có thể thắng boss.
# Rồng không được đốt trực tiếp tuyến này, nhưng vẫn dùng Minimax để đốt các ô khác nhằm gây áp lực.
BOSS_PROTECTED_PATH = {(4, 2), (3, 2), (2, 2), (1, 2), (0, 2)}


def _boss_neighbors(pos: tuple[int, int]) -> list[tuple[int, int]]:
    r, c = pos
    result = []
    for dr, dc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOSS_SIZE and 0 <= nc < BOSS_SIZE:
            result.append((nr, nc))
    return result


def _boss_pos_to_id(pos: tuple[int, int]) -> str:
    return f"{pos[0]}-{pos[1]}"


def _boss_id_to_pos(cell_id: str) -> tuple[int, int]:
    r, c = cell_id.split("-")
    return int(r), int(c)


def _boss_shortest_distance(knight: tuple[int, int], dragon: tuple[int, int], burned: set[tuple[int, int]]) -> int | None:
    from collections import deque
    if knight in burned:
        return None
    q = deque([(knight, 0)])
    seen = {knight}
    while q:
        cur, dist = q.popleft()
        if cur == dragon:
            return dist
        for nb in _boss_neighbors(cur):
            if nb in seen or nb in burned:
                continue
            seen.add(nb)
            q.append((nb, dist + 1))
    return None


def _boss_player_moves(knight: tuple[int, int], dragon: tuple[int, int], burned: set[tuple[int, int]]) -> list[tuple[int, int]]:
    moves = [p for p in _boss_neighbors(knight) if p not in burned]
    if dragon in moves:
        return [dragon]
    # Ưu tiên các ô làm giảm khoảng cách tới rồng, để player giống đang chơi hợp lý.
    moves.sort(key=lambda p: (
        0 if p in BOSS_PROTECTED_PATH else 1,
        abs(p[0] - dragon[0]) + abs(p[1] - dragon[1])
    ))
    return moves


def _boss_dragon_fire_candidates(knight: tuple[int, int], dragon: tuple[int, int], burned: set[tuple[int, int]]) -> list[tuple[int, int]]:
    candidates = []
    for r in range(BOSS_SIZE):
        for c in range(BOSS_SIZE):
            p = (r, c)
            if p in burned or p == knight or p == dragon:
                continue

            # Cân bằng gameplay: không cho rồng đốt trực tiếp tuyến thắng chính,
            # nếu không Minimax tối ưu sẽ dồn người chơi thua quá nhanh.
            if p in BOSS_PROTECTED_PATH:
                continue

            candidates.append(p)

    # Rồng ưu tiên xét quanh đường đi của người chơi để minimax nhìn "khôn" hơn.
    candidates.sort(key=lambda p: (
        abs(p[0] - knight[0]) + abs(p[1] - knight[1]),
        abs(p[0] - dragon[0]) + abs(p[1] - dragon[1])
    ))
    return candidates[:8]


def _boss_evaluate(knight: tuple[int, int], dragon: tuple[int, int], burned: set[tuple[int, int]], turn: int) -> int:
    # Điểm càng lớn càng lợi cho Knight/MAX.
    if knight == dragon:
        return 1000 - turn * 10

    moves = _boss_player_moves(knight, dragon, burned)
    if not moves:
        return -1000 + turn * 10

    dist = _boss_shortest_distance(knight, dragon, burned)
    if dist is None:
        return -900 + turn * 8

    mobility = len(moves)
    burned_pressure = len(burned)

    # Knight thích khoảng cách ngắn và nhiều hướng đi.
    return 120 - dist * 28 + mobility * 12 - burned_pressure * 3


def _boss_minimax(knight: tuple[int, int], dragon: tuple[int, int], burned: set[tuple[int, int]],
                  depth: int, is_max: bool, turn: int, alpha: int = -10_000, beta: int = 10_000) -> tuple[int, tuple[int, int] | None]:
    if depth == 0 or knight == dragon:
        return _boss_evaluate(knight, dragon, burned, turn), None

    if is_max:
        moves = _boss_player_moves(knight, dragon, burned)
        if not moves:
            return _boss_evaluate(knight, dragon, burned, turn), None

        best_score = -10_000
        best_move = None
        for mv in moves:
            score, _ = _boss_minimax(mv, dragon, burned, depth - 1, False, turn + 1, alpha, beta)
            if score > best_score:
                best_score = score
                best_move = mv
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score, best_move

    candidates = _boss_dragon_fire_candidates(knight, dragon, burned)
    if not candidates:
        return _boss_evaluate(knight, dragon, burned, turn), None

    best_score = 10_000
    best_fire = None
    for target in candidates:
        new_burned = set(burned)
        new_burned.add(target)
        score, _ = _boss_minimax(knight, dragon, new_burned, depth - 1, True, turn + 1, alpha, beta)
        if score < best_score:
            best_score = score
            best_fire = target
        beta = min(beta, best_score)
        if beta <= alpha:
            break
    return best_score, best_fire


def create_boss_session() -> dict:
    session_id = uuid.uuid4().hex[:10]
    session = {
        "id": session_id,
        "created_at": time.time(),
        "size": BOSS_SIZE,
        "knight": (4, 2),
        "dragon": (0, 2),
        "burned": set(),
        "turn": 0,
        "status": "playing",
        "winner": None,
        "last_knight_from": None,
        "last_knight_to": None,
        "last_fire": None,
        "log": [
            "Boss cuối bắt đầu: Knight tiến vào từ cổng dưới tại E3, Dragon chờ ở A3.",
            "Rồng dùng Minimax để phun lửa chặn đường, nhưng có giới hạn độ khó để người chơi vẫn có thể thắng."
        ],
    }
    BOSS_SESSIONS[session_id] = session
    return session


def boss_payload(session: dict) -> dict:
    return {
        "success": True,
        "session_id": session["id"],
        "size": session["size"],
        "knight": _boss_pos_to_id(session["knight"]),
        "dragon": _boss_pos_to_id(session["dragon"]),
        "burned": [_boss_pos_to_id(p) for p in sorted(session["burned"])],
        "turn": session["turn"],
        "status": session["status"],
        "winner": session["winner"],
        "log": session["log"],
        "valid_moves": [_boss_pos_to_id(p) for p in _boss_player_moves(session["knight"], session["dragon"], session["burned"])],
        "last_knight_from": _boss_pos_to_id(session["last_knight_from"]) if session.get("last_knight_from") else None,
        "last_knight_to": _boss_pos_to_id(session["last_knight_to"]) if session.get("last_knight_to") else None,
        "last_fire": _boss_pos_to_id(session["last_fire"]) if session.get("last_fire") else None,
        "explanation": "Knight là MAX, Dragon là MIN. Rồng dùng Minimax để chọn ô phun lửa làm đường đi của Knight tệ nhất."
    }


def _boss_finish_if_needed(session: dict) -> bool:
    knight = session["knight"]
    dragon = session["dragon"]
    burned = session["burned"]

    if knight == dragon:
        session["status"] = "finished"
        session["winner"] = "knight"
        session["log"].append("Knight đã chạm tới Dragon. Người chơi thắng và lấy được kho báu.")
        return True

    if not _boss_player_moves(knight, dragon, burned):
        session["status"] = "finished"
        session["winner"] = "dragon"
        session["log"].append("Knight bị kẹt, không còn ô hợp lệ để đi. Dragon thắng.")
        return True

    if session["turn"] >= BOSS_MAX_TURNS:
        session["status"] = "finished"
        session["winner"] = "dragon"
        session["log"].append("Hết số lượt tối đa. Dragon giữ được kho báu.")
        return True

    return False


def boss_step(session: dict, move_id: str | None = None) -> dict:
    if session["status"] != "playing":
        return boss_payload(session)

    knight = session["knight"]
    dragon = session["dragon"]
    burned = session["burned"]

    valid = _boss_player_moves(knight, dragon, burned)
    if move_id:
        move = _boss_id_to_pos(move_id)
        if move not in valid:
            return {"success": False, "error": "Nước đi không hợp lệ hoặc ô đã bị dung nham."}
    else:
        _, move = _boss_minimax(knight, dragon, burned, BOSS_MINIMAX_DEPTH, True, session["turn"])
        if move is None:
            move = valid[0] if valid else knight

    session["last_knight_from"] = knight
    session["last_knight_to"] = move
    session["last_fire"] = None
    old_knight = knight
    session["knight"] = move
    session["turn"] += 1
    session["log"].append(f"Knight di chuyển {_boss_pos_to_id(old_knight)} → {_boss_pos_to_id(move)}.")

    if _boss_finish_if_needed(session):
        return boss_payload(session)

    knight = session["knight"]
    burned = session["burned"]

    score, fire = _boss_minimax(knight, dragon, burned, BOSS_MINIMAX_DEPTH, False, session["turn"])
    if fire is not None:
        session["burned"].add(fire)
        session["last_fire"] = fire
        session["log"].append(f"Dragon dùng Minimax phun lửa vào ô {_boss_pos_to_id(fire)}. Điểm đánh giá: {score}.")
    else:
        session["log"].append("Dragon không còn ô hợp lệ để phun lửa.")

    _boss_finish_if_needed(session)
    return boss_payload(session)


class UTEHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_error(404, "File not found")
            return

        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        raw = path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:
        path = unquote(self.path.split("?", 1)[0])
        query = parse_qs(urlparse(self.path).query)

        if path == "/api/boss/new":
            session = create_boss_session()
            self._send_json(boss_payload(session))
            return

        if path == "/api/boss/step":
            session_id = query.get("session_id", [""])[0]
            move_id = query.get("move", [""])[0] or None
            session = BOSS_SESSIONS.get(session_id)
            if not session:
                session = create_boss_session()
            self._send_json(boss_step(session, move_id))
            return


        if path == "/":
            self._send_file(ROOT / "templates" / "index.html")
            return

        if path == "/api/graph":
            self._send_json(graph_payload())
            return

        if path == "/api/dungeon/new":
            session = create_dungeon_session()
            self._send_json({
                "success": True,
                "message": "Đã sinh hầm ngục sương mù mới. Map ẩn đã thay đổi.",
                "observation": observe_dungeon(session),
            })
            return

        if path == "/api/hgl02/new":
            session = create_hgl02_session()
            self._send_json({
                "success": True,
                "message": "Đã vào HGL02. Đây là map hầm ngục Belief State có thể tự đánh node.",
                **hgl02_payload(session),
            })
            return

        if path == "/api/fb04/new":
            session = create_fb04_session()
            self._send_json({
                "success": True,
                "message": "Đã vào FB04. Đây là hầm ngục Belief State + BFS tự đánh node.",
                **fb04_payload(session),
            })
            return

        if path == "/api/dun02/new":
            session = create_dun02_session()
            self._send_json({
                "success": True,
                "message": "Đã vào DUN02. Đây là hầm ngục Backtracking + Forward Checking.",
                **dun02_payload(session),
            })
            return

        if path == "/api/hgl02/andor_solve":
            session_id = self.path.split("session_id=", 1)[1].split("&", 1)[0] if "session_id=" in self.path else ""
            session = HGL02_SESSIONS.get(session_id) if session_id else create_hgl02_session()
            self._send_json(solve_hgl02_andor_search(session))
            return

        if path == "/api/andor/solve":
            self._send_json(andor_graph_search())
            return

        if path.startswith("/static/"):
            safe_path = path.lstrip("/")
            file_path = (ROOT / safe_path).resolve()
            static_root = (ROOT / "static").resolve()
            if static_root not in file_path.parents and file_path != static_root:
                self.send_error(403, "Forbidden")
                return
            self._send_file(file_path)
            return

        self.send_error(404, "Not found")

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0]
        data = self._read_json_body()

        if path == "/api/solve":
            result = solve(
                algorithm=data.get("algorithm", "astar"),
                start=data.get("start", DEFAULT_START),
                goal=data.get("goal", DEFAULT_GOAL),
                mode=data.get("mode", "distance"),
                beam_width=int(data.get("beam_width", 2)),
                depth_limit=int(data.get("depth_limit", 80)),
            )
            self._send_json(result)
            return

        if path == "/api/compare":
            results = compare_all(
                mode=data.get("mode", "distance"),
                beam_width=int(data.get("beam_width", 2)),
                depth_limit=int(data.get("depth_limit", 80)),
            )
            self._send_json({"success": True, "results": results})
            return

        if path == "/api/dungeon/solve":
            session_id = data.get("session_id")
            session = DUNGEON_SESSIONS.get(session_id)
            if not session:
                self._send_json({"success": False, "error": "Dungeon session không tồn tại. Hãy vào hầm ngục lại để sinh map mới."}, status=404)
                return

            self._send_json(no_observation_belief_search(session))
            return

        if path == "/api/fb04/solve":
            custom_map = data.get("map", {})
            session_id = data.get("session_id", "fb04-custom")
            actual_start = data.get("actual_start")
            self._send_json(solve_fb04_belief_bfs(custom_map, session_id, actual_start))
            return

        if path == "/api/dun02/solve":
            session_id = data.get("session_id")
            session = DUN02_SESSIONS.get(session_id)
            if not session:
                session = create_dun02_session()
            self._send_json(solve_dun02_backtracking_fc(session))
            return

        if path == "/api/dun02/solve_custom":
            custom_map = data.get("map", {})
            session_id = data.get("session_id", "dun02-custom")
            session = {
                "id": session_id,
                "created_at": time.time(),
                "map": custom_map,
            }
            self._send_json(solve_dun02_backtracking_fc(session))
            return

        if path == "/api/hgl02/solve_custom":
            custom_map = data.get("map", {})
            session_id = data.get("session_id", "hgl02-custom")
            self._send_json(solve_hgl02_belief_custom(custom_map, session_id=session_id))
            return

            self._send_json(solve_dun02_backtracking_fc(session))
            return

        self.send_error(404, "Not found")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), UTEHandler)
    print(f"UTE Treasure Pathfinder is running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
