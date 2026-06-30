import tkinter as tk
from tkinter import messagebox
from collections import deque


GOAL_STATE = (
    1, 2, 3,
    4, 5, 6,
    7, 8, 0
)

START_STATE = (
    1, 2, 3,
    4, 0, 6,
    7, 5, 8
)

ACTIONS = ["Left", "Right", "Up", "Down"]



class Node:
    def __init__(self, state, parent=None, action=None, depth=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.depth = depth


def is_goal(state):
    return state == GOAL_STATE


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
            depth=node.depth + 1
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
        value = state[i]

        if value == 0:
            text += "0\t"
        else:
            text += str(value) + "\t"

        if (i + 1) % 3 == 0:
            text += "\n"

    return text



def dfs(start_state, max_nodes=50000):
    logs = []
    start_node = Node(start_state)

    logs.append("THUẬT TOÁN DFS")
    logs.append("MA TRẬN BAN ĐẦU:")
    logs.append(matrix_to_text(start_node.state))

    if is_goal(start_node.state):
        logs.append("START đã là GOAL")
        return start_node, logs, 0

    frontier = []
    frontier.append(start_node)

    reached = set()
    reached.add(start_state)

    count = 0

    while frontier:
        if count >= max_nodes:
            logs.append("Dừng vì vượt quá số node cho phép.")
            return None, logs, count

        node = frontier.pop()
        count += 1

        logs.append("--------------------------------")
        logs.append(f"Lấy node ra khỏi stack để xét, độ sâu = {node.depth}")
        logs.append(matrix_to_text(node.state))

        for child in expand(node):
            s = child.state

            logs.append(f"Sinh con bằng cách đi {child.action}:")
            logs.append(matrix_to_text(s))

            if is_goal(s):
                logs.append(f"Node con đi {child.action} là GOAL.")
                return child, logs, count

            frontier_states = [n.state for n in frontier]

            if s not in reached and s not in frontier_states:
                reached.add(s)
                frontier.append(child)
                logs.append(f"Thêm node đi {child.action} vào stack.")
            else:
                logs.append(f"Node đi {child.action} đã có trong reached hoặc stack nên bỏ qua.")

        logs.append("Stack hiện tại:")
        logs.append(str([n.action for n in frontier]))
        logs.append("Vì stack là LIFO nên node thêm sau sẽ được xét trước.")

    logs.append("DFS không tìm thấy lời giải.")
    return None, logs, count



def depth_limited_search(node, limit, path_states, logs, counter):
    counter[0] += 1

    logs.append("--------------------------------")
    logs.append(f"Đang xét node ở độ sâu {node.depth}, giới hạn = {limit}")
    logs.append(matrix_to_text(node.state))

    if is_goal(node.state):
        logs.append("Node hiện tại là GOAL.")
        return node

    if node.depth == limit:
        logs.append("Đã đạt giới hạn độ sâu, không mở rộng node này.")
        return None

    for child in expand(node):
        s = child.state

        logs.append(f"Sinh con bằng cách đi {child.action}:")
        logs.append(matrix_to_text(s))

        if s not in path_states:
            path_states.add(s)

            result = depth_limited_search(
                child,
                limit,
                path_states,
                logs,
                counter
            )

            if result is not None:
                return result

            path_states.remove(s)
        else:
            logs.append("Node này bị lặp trên đường đi hiện tại nên bỏ qua.")

    return None


def ids(start_state, max_depth=30):
    logs = []
    logs.append("THUẬT TOÁN IDS")
    logs.append("IDS = lặp DFS theo từng giới hạn độ sâu.")
    logs.append("MA TRẬN BAN ĐẦU:")
    logs.append(matrix_to_text(start_state))

    total_count = 0

    for limit in range(max_depth + 1):
        logs.append("================================")
        logs.append(f"BẮT ĐẦU DLS VỚI GIỚI HẠN ĐỘ SÂU = {limit}")

        start_node = Node(start_state)
        path_states = set()
        path_states.add(start_state)

        counter = [0]

        result = depth_limited_search(
            start_node,
            limit,
            path_states,
            logs,
            counter
        )

        total_count += counter[0]

        if result is not None:
            logs.append("================================")
            logs.append(f"IDS tìm thấy GOAL ở giới hạn độ sâu = {limit}")
            return result, logs, total_count

    logs.append("IDS không tìm thấy lời giải trong giới hạn đã cho.")
    return None, logs, total_count



class PuzzleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("8 Puzzle - DFS và IDS")
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
        self.write_log("Chọn DFS hoặc IDS để giải bài toán.")

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
            font=("Arial", 12)
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

        self.btn_dfs = tk.Button(
            button_frame,
            text="Giải DFS",
            width=11,
            height=2,
            bg=self.button,
            fg=self.text,
            activebackground=self.button_hover,
            activeforeground=self.text,
            relief="flat",
            command=self.solve_dfs
        )
        self.btn_dfs.grid(row=0, column=0, padx=5, pady=5)

        self.btn_ids = tk.Button(
            button_frame,
            text="Giải IDS",
            width=11,
            height=2,
            bg=self.button,
            fg=self.text,
            activebackground=self.button_hover,
            activeforeground=self.text,
            relief="flat",
            command=self.solve_ids
        )
        self.btn_ids.grid(row=0, column=1, padx=5, pady=5)

        self.btn_next = tk.Button(
            button_frame,
            text="Next",
            width=11,
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
            width=11,
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
            text="START được chỉnh trong code",
            bg=self.panel,
            fg=self.subtext,
            font=("Arial", 11)
        )
        self.info_label.pack(pady=(8, 0))

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
                self.cells[i].config(
                    text="0",
                    bg=self.tile_zero,
                    fg="#ffffff"
                )
            else:
                self.cells[i].config(
                    text=str(value),
                    bg=self.tile,
                    fg=self.text
                )

    def write_log(self, content):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)

        if isinstance(content, list):
            self.log_text.insert(tk.END, "\n".join(content))
        else:
            self.log_text.insert(tk.END, content)

        self.log_text.config(state="disabled")

    def solve_dfs(self):
        result, logs, count = dfs(START_STATE)

        self.current_algorithm = "DFS"
        self.current_index = 0

        if result is None:
            self.current_path = []
            logs.append("Không có đường đi để hiển thị.")
            self.write_log(logs)
            messagebox.showinfo("DFS", "DFS không tìm thấy lời giải.")
            return

        self.current_path = get_solution_path(result)

        logs.append("================================")
        logs.append("ĐƯỜNG ĐI TỪ START ĐẾN GOAL:")

        for i, node in enumerate(self.current_path):
            if i == 0:
                logs.append(f"Bước {i}: START")
            else:
                logs.append(f"Bước {i}: đi {node.action}")

            logs.append(matrix_to_text(node.state))

        logs.append(f"Tổng số bước lời giải: {len(self.current_path) - 1}")
        logs.append(f"Tổng số node đã xét: {count}")

        self.show_state(self.current_path[0].state)
        self.step_label.config(text="Bước hiện tại: 0")
        self.write_log(logs)

    def solve_ids(self):
        result, logs, count = ids(START_STATE, max_depth=30)

        self.current_algorithm = "IDS"
        self.current_index = 0

        if result is None:
            self.current_path = []
            logs.append("Không có đường đi để hiển thị.")
            self.write_log(logs)
            messagebox.showinfo("IDS", "IDS không tìm thấy lời giải trong giới hạn.")
            return

        self.current_path = get_solution_path(result)

        logs.append("================================")
        logs.append("ĐƯỜNG ĐI TỪ START ĐẾN GOAL:")

        for i, node in enumerate(self.current_path):
            if i == 0:
                logs.append(f"Bước {i}: START")
            else:
                logs.append(f"Bước {i}: đi {node.action}")

            logs.append(matrix_to_text(node.state))

        logs.append(f"Tổng số bước lời giải: {len(self.current_path) - 1}")
        logs.append(f"Tổng số node đã xét qua các lần lặp: {count}")

        self.show_state(self.current_path[0].state)
        self.step_label.config(text="Bước hiện tại: 0")
        self.write_log(logs)

    def next_step(self):
        if not self.current_path:
            messagebox.showwarning("Thông báo", "Chưa giải thuật toán.")
            return

        if self.current_index < len(self.current_path) - 1:
            self.current_index += 1
            node = self.current_path[self.current_index]

            self.show_state(node.state)

            self.step_label.config(
                text=f"Bước hiện tại: {self.current_index} - Đi {node.action}"
            )
        else:
            messagebox.showinfo("Hoàn thành", "Đã tới GOAL.")

    def reset(self):
        self.current_path = []
        self.current_index = 0
        self.current_algorithm = ""

        self.show_state(START_STATE)
        self.step_label.config(text="Bước hiện tại: 0")
        self.write_log("Đã reset về START.\nChọn DFS hoặc IDS để giải lại.")




if __name__ == "__main__":
    root = tk.Tk()
    app = PuzzleApp(root)
    root.mainloop()