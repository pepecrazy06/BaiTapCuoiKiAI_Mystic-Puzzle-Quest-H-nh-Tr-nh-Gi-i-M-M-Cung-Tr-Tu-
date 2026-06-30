import tkinter as tk
from tkinter import messagebox


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

# Thứ tự sinh trạng thái lân cận.
# Simple Hill Climbing sẽ xét theo đúng thứ tự này và lấy trạng thái tốt hơn đầu tiên.
ACTIONS = ["Left", "Right", "Up", "Down"]
STEP_COST = 1


class Node:
    def __init__(self, state, parent=None, action=None, depth=0, cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.depth = depth
        self.cost = cost


def is_goal(state):
    return state == GOAL_STATE


def heuristic_manhattan(state):
    """
    h(n): Tổng khoảng cách Manhattan từ trạng thái hiện tại tới GOAL.
    Không tính ô trống 0.

    Với mỗi ô số k:
    Manhattan = |dòng hiện tại - dòng đích| + |cột hiện tại - cột đích|
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


def simple_hill_climbing_manhattan(start_state, max_steps=1000):
    """
    Simple Hill Climbing + Manhattan:
    - Dùng h(n) = Manhattan Distance.
    - Vì Manhattan là khoảng cách tới đích nên h càng nhỏ càng tốt.
    - Xét lân cận lần lượt theo ACTIONS.
    - Gặp trạng thái đầu tiên có h nhỏ hơn current thì chuyển ngay sang trạng thái đó.
    - Nếu không có trạng thái nào tốt hơn thì dừng ở cực trị cục bộ.
    """
    logs = []
    current = Node(start_state)
    count = 0

    logs.append("THUẬT TOÁN SIMPLE HILL CLIMBING + MANHATTAN")
    logs.append("Quy ước: h(n) = tổng khoảng cách Manhattan, h càng nhỏ càng tốt.")
    logs.append("Simple Hill Climbing: xét lân cận lần lượt, gặp trạng thái tốt hơn đầu tiên thì đi ngay.")
    logs.append("Thứ tự xét: " + " -> ".join(ACTIONS))
    logs.append("MA TRẬN BAN ĐẦU:")
    logs.append(matrix_to_text(current.state))
    logs.append(f"h(Start) = {heuristic(current.state)}")

    while count < max_steps:
        count += 1
        current_h = heuristic(current.state)

        logs.append("--------------------------------")
        logs.append(f"BƯỚC {count}")
        logs.append(f"CURRENT_STATE | h={current_h}, depth={current.depth}")
        logs.append(matrix_to_text(current.state))

        if is_goal(current.state):
            logs.append("Current_State là GOAL. Dừng thuật toán.")
            return current, logs, count, True

        moved = False
        neighbors = expand(current)

        logs.append("Sinh và xét lần lượt các trạng thái lân cận:")

        for child in neighbors:
            child_h = heuristic(child.state)
            logs.append(f"Next_State đi {child.action}: h={child_h}")
            logs.append(matrix_to_text(child.state))

            if child_h < current_h:
                logs.append(f"Vì h(Next_State)={child_h} < h(Current_State)={current_h} nên chọn trạng thái này.")
                current = child
                moved = True
                break
            else:
                logs.append(f"Không chọn vì h(Next_State)={child_h} không nhỏ hơn h(Current_State)={current_h}.")

        if not moved:
            logs.append("Không tồn tại trạng thái lân cận nào tốt hơn.")
            logs.append("Dừng vì đã đạt cực trị cục bộ / không leo tiếp được.")
            return current, logs, count, is_goal(current.state)

    logs.append("Dừng vì vượt quá số bước cho phép.")
    return current, logs, count, is_goal(current.state)


def steepest_ascent_hill_climbing_manhattan(start_state, max_steps=1000):
    """
    Leo đồi dốc nhất / Steepest-Ascent Hill Climbing + Manhattan:
    - Dùng h(n) = Manhattan Distance.
    - Sinh toàn bộ lân cận.
    - Chọn trạng thái có h nhỏ nhất trong các lân cận.
    - Chỉ chuyển nếu h tốt nhất nhỏ hơn h hiện tại.
    - Nếu không có trạng thái tốt hơn thì dừng.
    """
    logs = []
    current = Node(start_state)
    count = 0

    logs.append("THUẬT TOÁN LEO ĐỒI DỐC NHẤT + MANHATTAN")
    logs.append("Quy ước: h(n) = tổng khoảng cách Manhattan, h càng nhỏ càng tốt.")
    logs.append("Leo đồi dốc nhất: sinh toàn bộ lân cận rồi chọn trạng thái có h nhỏ nhất.")
    logs.append("MA TRẬN BAN ĐẦU:")
    logs.append(matrix_to_text(current.state))
    logs.append(f"h(Start) = {heuristic(current.state)}")

    while count < max_steps:
        count += 1
        current_h = heuristic(current.state)

        logs.append("--------------------------------")
        logs.append(f"BƯỚC {count}")
        logs.append(f"CURRENT_STATE | h={current_h}, depth={current.depth}")
        logs.append(matrix_to_text(current.state))

        if is_goal(current.state):
            logs.append("Current_State là GOAL. Dừng thuật toán.")
            return current, logs, count, True

        neighbors = expand(current)
        best_child = None
        best_h = float("inf")

        logs.append("Sinh toàn bộ trạng thái lân cận:")

        for child in neighbors:
            child_h = heuristic(child.state)
            logs.append(f"Next_State đi {child.action}: h={child_h}")
            logs.append(matrix_to_text(child.state))

            if child_h < best_h:
                best_h = child_h
                best_child = child

        logs.append(f"Trạng thái lân cận tốt nhất có h={best_h}.")

        if best_child is not None and best_h < current_h:
            logs.append(f"Vì h(Best_Next)={best_h} < h(Current_State)={current_h} nên chuyển sang Best_Next.")
            current = best_child
        else:
            logs.append("Không có trạng thái lân cận nào tốt hơn Current_State.")
            logs.append("Dừng vì đã đạt cực trị cục bộ / không leo tiếp được.")
            return current, logs, count, is_goal(current.state)

    logs.append("Dừng vì vượt quá số bước cho phép.")
    return current, logs, count, is_goal(current.state)


class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8 Puzzle - Simple Hill Climbing Manhattan")
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
        self.write_log("Chọn Simple Hill Manhattan hoặc Leo đồi dốc nhất để chạy bài toán.")

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

        self.btn_simple = tk.Button(
            button_frame,
            text="Simple Hill\nManhattan",
            width=13,
            height=2,
            bg=self.button,
            fg=self.text,
            activebackground=self.button_hover,
            activeforeground=self.text,
            relief="flat",
            command=self.solve_simple_hill
        )
        self.btn_simple.grid(row=0, column=0, padx=5, pady=5)

        self.btn_steepest = tk.Button(
            button_frame,
            text="Leo đồi\ndốc nhất",
            width=13,
            height=2,
            bg=self.button,
            fg=self.text,
            activebackground=self.button_hover,
            activeforeground=self.text,
            relief="flat",
            command=self.solve_steepest
        )
        self.btn_steepest.grid(row=0, column=1, padx=5, pady=5)

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
            text="Hill Climbing: chọn trạng thái có h nhỏ hơn hiện tại",
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

    def finish_solve(self, result, logs, count, algorithm, reached_goal):
        self.current_algorithm = algorithm
        self.current_index = 0
        self.current_path = get_solution_path(result) if result is not None else []

        logs.append("================================")
        logs.append("ĐƯỜNG ĐI THUẬT TOÁN ĐÃ CHỌN:")

        for i, node in enumerate(self.current_path):
            h_value = heuristic(node.state)

            if i == 0:
                logs.append(f"Bước {i}: START | h={h_value}")
            else:
                logs.append(f"Bước {i}: đi {node.action} | h={h_value}")

            logs.append(matrix_to_text(node.state))

        logs.append(f"Tổng số bước đã đi: {len(self.current_path) - 1}")
        logs.append(f"Tổng số vòng lặp đã xét: {count}")
        logs.append(f"Kết quả cuối cùng có phải GOAL không: {'Có' if reached_goal else 'Không'}")

        if self.current_path:
            self.show_state(self.current_path[0].state)
            self.step_label.config(text="Bước hiện tại: 0")

        self.write_log(logs)

        if reached_goal:
            messagebox.showinfo(algorithm, f"{algorithm} đã tìm thấy GOAL.")
        else:
            messagebox.showinfo(algorithm, f"{algorithm} dừng ở cực trị cục bộ, chưa chắc tới GOAL.")

    def solve_simple_hill(self):
        result, logs, count, reached_goal = simple_hill_climbing_manhattan(START_STATE)
        self.finish_solve(result, logs, count, "Simple Hill Climbing Manhattan", reached_goal)

    def solve_steepest(self):
        result, logs, count, reached_goal = steepest_ascent_hill_climbing_manhattan(START_STATE)
        self.finish_solve(result, logs, count, "Leo đồi dốc nhất Manhattan", reached_goal)

    def next_step(self):
        if not self.current_path:
            messagebox.showwarning("Thông báo", "Chưa chạy thuật toán.")
            return

        if self.current_index < len(self.current_path) - 1:
            self.current_index += 1
            node = self.current_path[self.current_index]
            h_value = heuristic(node.state)

            self.show_state(node.state)
            self.step_label.config(
                text=f"Bước {self.current_index}: đi {node.action} | h={h_value}"
            )
        else:
            if is_goal(self.current_path[-1].state):
                messagebox.showinfo("Hoàn thành", "Đã tới GOAL.")
            else:
                messagebox.showinfo("Dừng", "Đã tới trạng thái dừng của Hill Climbing.")

    def reset(self):
        self.current_path = []
        self.current_index = 0
        self.current_algorithm = ""

        self.show_state(START_STATE)
        self.step_label.config(text="Bước hiện tại: 0")
        self.write_log("Đã reset về START.\nChọn Simple Hill Manhattan hoặc Leo đồi dốc nhất để chạy lại.")


if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()
