import tkinter as tk
from tkinter import messagebox
import heapq


GOAL_STATE = (
    1, 2, 3,
    4, 5, 6,
    7, 8, 0
)

# Chỉnh ma trận START tại đây
START_STATE = (
    1, 2, 3,
    4, 0, 6,
    7, 5, 8
)

ACTIONS = ["Left", "Right", "Up", "Down"]
STEP_COST = 1


class Node:
    def __init__(self, state, parent=None, action=None, depth=0, cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.depth = depth
        self.cost = cost  # g(n): chi phí thật từ START đến node hiện tại


def is_goal(state):
    return state == GOAL_STATE


def heuristic_misplaced(state):
    """
    h1(n): Số ô sai vị trí.
    Không tính ô trống 0.
    """
    count = 0

    for i in range(9):
        if state[i] != 0 and state[i] != GOAL_STATE[i]:
            count += 1

    return count


def heuristic_manhattan(state):
    """
    h2(n): Tổng khoảng cách Manhattan.
    Không tính ô trống 0.
    """
    total = 0

    for value in range(1, 9):
        current_index = state.index(value)
        goal_index = GOAL_STATE.index(value)

        current_row, current_col = current_index // 3, current_index % 3
        goal_row, goal_col = goal_index // 3, goal_index % 3

        total += abs(current_row - goal_row) + abs(current_col - goal_col)

    return total


def heuristic(state):
    """
    Hàm heuristic chính đang dùng cho cả A* và Heuristic Search.
    Có thể đổi sang heuristic_misplaced(state) nếu muốn dùng số ô sai vị trí.
    """
    return heuristic_manhattan(state)


def move(node, action):
    state = list(node.state)
    zero_index = node.state.index(0)

    row = zero_index // 3
    col = zero_index % 3

    if action == "Left":
        new_row, new_col = row, col - 1
    elif action == "Right":
        new_row, new_col = row, col + 1
    elif action == "Up":
        new_row, new_col = row - 1, col
    elif action == "Down":
        new_row, new_col = row + 1, col
    else:
        return None

    if 0 <= new_row < 3 and 0 <= new_col < 3:
        new_index = new_row * 3 + new_col
        state[zero_index], state[new_index] = state[new_index], state[zero_index]

        return Node(
            state=tuple(state),
            parent=node,
            action=action,
            depth=node.depth + 1,
            cost=node.cost + STEP_COST
        )

    return None


def expand(node):
    children = []

    for action in ACTIONS:
        child = move(node, action)

        if child is not None:
            children.append(child)

    return children


def get_solution_path(node):
    path = []

    while node is not None:
        path.append(node)
        node = node.parent

    path.reverse()
    return path


def matrix_to_text(state):
    text = ""

    for i in range(9):
        text += str(state[i]) + "\t"

        if (i + 1) % 3 == 0:
            text += "\n"

    return text


def frontier_to_text(frontier, mode):
    items = []

    for item in frontier:
        priority, _, node = item
        h_value = heuristic(node.state)
        g_value = node.cost
        f_value = g_value + h_value

        if mode == "ASTAR":
            items.append(f"f={priority}, g={g_value}, h={h_value}, action={node.action}")
        else:
            items.append(f"h={priority}, g={g_value}, action={node.action}")

    return str(items)


def reached_to_text(reached):
    if isinstance(reached, dict):
        return f"{len(reached)} trạng thái đã lưu chi phí tốt nhất"
    return f"{len(reached)} trạng thái đã xét"


def astar_search(start_state, max_nodes=50000):
    """
    A* Search:
    f(n) = g(n) + h(n)

    g(n): số bước đã đi từ START đến n.
    h(n): chi phí ước lượng từ n đến GOAL.
    """
    logs = []
    start_node = Node(start_state)

    logs.append("THUẬT TOÁN A* SEARCH")
    logs.append("A* chọn node trong Frontier có f(n) nhỏ nhất.")
    logs.append("Công thức: f(n) = g(n) + h(n)")
    logs.append("g(n): chi phí thật từ START đến node hiện tại.")
    logs.append("h(n): heuristic Manhattan đến GOAL.")
    logs.append("MA TRẬN BAN ĐẦU:")
    logs.append(matrix_to_text(start_node.state))

    start_g = start_node.cost
    start_h = heuristic(start_state)
    start_f = start_g + start_h

    logs.append(f"Start: g={start_g}, h={start_h}, f={start_f}")

    frontier = []
    order = 0
    heapq.heappush(frontier, (start_f, order, start_node))

    # reached lưu g(n) tốt nhất đã biết của từng trạng thái
    reached = {}
    reached[start_state] = 0

    count = 0

    while frontier:
        if count >= max_nodes:
            logs.append("Dừng vì vượt quá số node cho phép.")
            return None, logs, count

        current_f, _, node = heapq.heappop(frontier)

        # Bỏ bản ghi cũ nếu trong heap còn node có chi phí không tốt
        if node.cost > reached.get(node.state, float("inf")):
            continue

        count += 1

        g_value = node.cost
        h_value = heuristic(node.state)
        f_value = g_value + h_value

        logs.append("--------------------------------")
        logs.append("NODE ĐANG XÉT")
        logs.append(f"Action={node.action} | g(n)={g_value}, h(n)={h_value}, f(n)={f_value}, depth={node.depth}")
        logs.append(matrix_to_text(node.state))

        if is_goal(node.state):
            logs.append("Node hiện tại là GOAL.")
            return node, logs, count

        for child in expand(node):
            s = child.state
            g_new = child.cost
            h_new = heuristic(s)
            f_new = g_new + h_new

            logs.append(f"Sinh con bằng cách đi {child.action}:")
            logs.append(f"g(m)={g_new}, h(m)={h_new}, f(m)=g+h={f_new}")
            logs.append(matrix_to_text(s))

            if s not in reached or g_new < reached[s]:
                reached[s] = g_new
                order += 1
                heapq.heappush(frontier, (f_new, order, child))
                logs.append("Thêm/cập nhật m vào FRONTIER vì tìm được đường tốt hơn.")
            else:
                logs.append("Bỏ qua m vì đã có đường đi tốt hơn hoặc bằng.")

        logs.append("FRONTIER hiện tại:")
        logs.append(frontier_to_text(frontier, "ASTAR"))
        logs.append("REACHED hiện tại:")
        logs.append(reached_to_text(reached))

    logs.append("A* không tìm thấy lời giải.")
    return None, logs, count


def heuristic_search(start_state, max_nodes=50000):
    """
    Heuristic Search / Greedy Best-First Search:
    Chỉ dùng h(n) để chọn node.
    Không cộng g(n), nên chưa chắc tối ưu bằng A*.
    """
    logs = []
    start_node = Node(start_state)

    logs.append("THUẬT TOÁN HEURISTIC SEARCH")
    logs.append("Thuật toán này chọn node trong Frontier có h(n) nhỏ nhất.")
    logs.append("Khác A*: Heuristic Search chỉ xét h(n), không xét g(n).")
    logs.append("h(n): Manhattan Distance đến GOAL.")
    logs.append("MA TRẬN BAN ĐẦU:")
    logs.append(matrix_to_text(start_node.state))
    logs.append(f"h(Start) = {heuristic(start_state)}")

    frontier = []
    order = 0
    heapq.heappush(frontier, (heuristic(start_state), order, start_node))

    reached = set()
    reached.add(start_state)

    count = 0

    while frontier:
        if count >= max_nodes:
            logs.append("Dừng vì vượt quá số node cho phép.")
            return None, logs, count

        current_h, _, node = heapq.heappop(frontier)
        count += 1

        logs.append("--------------------------------")
        logs.append("NODE ĐANG XÉT")
        logs.append(f"Action={node.action} | h(n)={current_h}, g(n)={node.cost}, depth={node.depth}")
        logs.append(matrix_to_text(node.state))

        if is_goal(node.state):
            logs.append("Node hiện tại là GOAL.")
            return node, logs, count

        for child in expand(node):
            s = child.state
            child_h = heuristic(s)

            logs.append(f"Sinh con bằng cách đi {child.action}: h(m)={child_h}, g(m)={child.cost}")
            logs.append(matrix_to_text(s))

            if s not in reached:
                reached.add(s)
                order += 1
                heapq.heappush(frontier, (child_h, order, child))
                logs.append(f"Thêm m vào FRONTIER với h={child_h}.")
            else:
                logs.append("Bỏ qua m vì đã có trong FRONTIER hoặc REACHED.")

        logs.append("FRONTIER hiện tại:")
        logs.append(frontier_to_text(frontier, "HEURISTIC"))
        logs.append("REACHED hiện tại:")
        logs.append(reached_to_text(reached))

    logs.append("Heuristic Search không tìm thấy lời giải.")
    return None, logs, count


class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8 Puzzle - A* và Heuristic Search")
        self.root.geometry("980x560")
        self.root.resizable(False, False)

        self.bg = "#101820"
        self.panel = "#16232e"
        self.tile = "#243447"
        self.tile_zero = "#00adb5"
        self.text = "#eeeeee"
        self.subtext = "#b8c1cc"
        self.button = "#30475e"
        self.button_hover = "#3d5a73"

        self.root.configure(bg=self.bg)

        self.current_path = []
        self.current_index = 0
        self.current_algorithm = ""

        self.create_ui()
        self.show_state(START_STATE)
        self.write_log("Chọn A* hoặc Heuristic Search để giải bài toán.")

    def create_ui(self):
        main_frame = tk.Frame(self.root, bg=self.bg)
        main_frame.pack(fill="both", expand=True, padx=18, pady=18)

        left_frame = tk.Frame(main_frame, bg=self.panel, width=380, height=520)
        left_frame.pack(side="left", fill="y", padx=(0, 14))
        left_frame.pack_propagate(False)

        right_frame = tk.Frame(main_frame, bg=self.panel, width=550, height=520)
        right_frame.pack(side="right", fill="both", expand=True)
        right_frame.pack_propagate(False)

        title = tk.Label(
            left_frame,
            text="8 PUZZLE",
            bg=self.panel,
            fg=self.text,
            font=("Arial", 22, "bold")
        )
        title.pack(pady=(18, 8))

        self.step_label = tk.Label(
            left_frame,
            text="Bước hiện tại: 0",
            bg=self.panel,
            fg=self.subtext,
            font=("Arial", 11)
        )
        self.step_label.pack(pady=(0, 12))

        self.board_frame = tk.Frame(left_frame, bg=self.panel)
        self.board_frame.pack(pady=8)

        self.cells = []

        for i in range(9):
            cell = tk.Label(
                self.board_frame,
                text="",
                width=4,
                height=2,
                bg=self.tile,
                fg=self.text,
                font=("Arial", 24, "bold"),
                relief="flat"
            )
            cell.grid(row=i // 3, column=i % 3, padx=5, pady=5)
            self.cells.append(cell)

        button_frame = tk.Frame(left_frame, bg=self.panel)
        button_frame.pack(pady=18)

        self.btn_astar = tk.Button(
            button_frame,
            text="Giải A*",
            width=13,
            height=2,
            bg=self.button,
            fg=self.text,
            activebackground=self.button_hover,
            activeforeground=self.text,
            relief="flat",
            command=self.solve_astar
        )
        self.btn_astar.grid(row=0, column=0, padx=5, pady=5)

        self.btn_heuristic = tk.Button(
            button_frame,
            text="Giải Heuristic",
            width=13,
            height=2,
            bg=self.button,
            fg=self.text,
            activebackground=self.button_hover,
            activeforeground=self.text,
            relief="flat",
            command=self.solve_heuristic
        )
        self.btn_heuristic.grid(row=0, column=1, padx=5, pady=5)

        self.btn_next = tk.Button(
            button_frame,
            text="Next",
            width=13,
            height=2,
            bg="#1f7a5c",
            fg=self.text,
            activebackground="#24966f",
            activeforeground=self.text,
            relief="flat",
            command=self.next_step
        )
        self.btn_next.grid(row=1, column=0, padx=5, pady=5)

        self.btn_reset = tk.Button(
            button_frame,
            text="Reset",
            width=13,
            height=2,
            bg="#7a2e2e",
            fg=self.text,
            activebackground="#963838",
            activeforeground=self.text,
            relief="flat",
            command=self.reset
        )
        self.btn_reset.grid(row=1, column=1, padx=5, pady=5)

        self.info_label = tk.Label(
            left_frame,
            text="START chỉnh trong code | h(n): Manhattan",
            bg=self.panel,
            fg=self.subtext,
            font=("Arial", 11)
        )
        self.info_label.pack(pady=(8, 0))

        self.formula_label = tk.Label(
            left_frame,
            text="A*: f(n)=g(n)+h(n) | Heuristic: chọn h(n) nhỏ nhất",
            bg=self.panel,
            fg=self.subtext,
            font=("Arial", 10)
        )
        self.formula_label.pack(pady=(4, 0))

        log_title = tk.Label(
            right_frame,
            text="NỘI DUNG CHẠY THUẬT TOÁN",
            bg=self.panel,
            fg=self.text,
            font=("Arial", 15, "bold")
        )
        log_title.pack(pady=(14, 8))

        log_container = tk.Frame(right_frame, bg=self.panel)
        log_container.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.log_text = tk.Text(
            log_container,
            bg="#0b1117",
            fg=self.text,
            insertbackground=self.text,
            font=("Consolas", 10),
            wrap="word",
            relief="flat"
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_container, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")

        self.log_text.config(yscrollcommand=scrollbar.set)

    def show_state(self, state):
        for i, value in enumerate(state):
            if value == 0:
                self.cells[i].config(text="0", bg=self.tile_zero, fg="#ffffff")
            else:
                self.cells[i].config(text=str(value), bg=self.tile, fg=self.text)

    def write_log(self, content):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)

        if isinstance(content, list):
            self.log_text.insert(tk.END, "\n".join(content))
        else:
            self.log_text.insert(tk.END, content)

        self.log_text.config(state="disabled")

    def finish_solve(self, result, logs, count, algorithm):
        self.current_algorithm = algorithm
        self.current_index = 0

        if result is None:
            self.current_path = []
            logs.append("Không có đường đi để hiển thị.")
            self.write_log(logs)
            messagebox.showinfo(algorithm, f"{algorithm} không tìm thấy lời giải.")
            return

        self.current_path = get_solution_path(result)

        logs.append("================================")
        logs.append("ĐƯỜNG ĐI TỪ START ĐẾN GOAL:")

        for i, node in enumerate(self.current_path):
            g_value = node.cost
            h_value = heuristic(node.state)
            f_value = g_value + h_value

            if i == 0:
                logs.append(f"Bước {i}: START | g={g_value}, h={h_value}, f={f_value}")
            else:
                logs.append(f"Bước {i}: đi {node.action} | g={g_value}, h={h_value}, f={f_value}")

            logs.append(matrix_to_text(node.state))

        logs.append(f"Tổng số bước lời giải: {len(self.current_path) - 1}")
        logs.append(f"Tổng chi phí đường đi: {result.cost}")
        logs.append(f"Tổng số node đã xét: {count}")

        self.show_state(self.current_path[0].state)
        self.step_label.config(text="Bước hiện tại: 0")
        self.write_log(logs)

    def solve_astar(self):
        result, logs, count = astar_search(START_STATE)
        self.finish_solve(result, logs, count, "A* Search")

    def solve_heuristic(self):
        result, logs, count = heuristic_search(START_STATE)
        self.finish_solve(result, logs, count, "Heuristic Search")

    def next_step(self):
        if not self.current_path:
            messagebox.showwarning("Thông báo", "Chưa giải thuật toán.")
            return

        if self.current_index < len(self.current_path) - 1:
            self.current_index += 1
            node = self.current_path[self.current_index]

            g_value = node.cost
            h_value = heuristic(node.state)
            f_value = g_value + h_value

            self.show_state(node.state)

            self.step_label.config(
                text=f"Bước {self.current_index}: đi {node.action} | g={g_value}, h={h_value}, f={f_value}"
            )
        else:
            messagebox.showinfo("Hoàn thành", "Đã tới GOAL.")

    def reset(self):
        self.current_path = []
        self.current_index = 0
        self.current_algorithm = ""

        self.show_state(START_STATE)
        self.step_label.config(text="Bước hiện tại: 0")
        self.write_log("Đã reset về START.\nChọn A* hoặc Heuristic Search để giải lại.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()
