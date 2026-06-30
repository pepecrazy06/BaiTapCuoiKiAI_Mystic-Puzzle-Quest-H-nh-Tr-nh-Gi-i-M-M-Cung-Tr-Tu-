import tkinter as tk
from collections import deque
import random

GOAL_STATE = (
    1, 2, 3,
    4, 5, 6,
    7, 8, 0
)


class Node:
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action


def is_goal(state):
    return state == GOAL_STATE


# CÁCH 1: CHILD-NODE
def child_node(problem_state, node, action):
    state = list(node.state)
    zero_index = node.state.index(0)

    row = zero_index // 3
    col = zero_index % 3

    if action == "Up":
        new_row, new_col = row - 1, col
    elif action == "Down":
        new_row, new_col = row + 1, col
    elif action == "Left":
        new_row, new_col = row, col - 1
    elif action == "Right":
        new_row, new_col = row, col + 1
    else:
        return None

    if 0 <= new_row < 3 and 0 <= new_col < 3:
        new_index = new_row * 3 + new_col
        state[zero_index], state[new_index] = state[new_index], state[zero_index]
        return Node(tuple(state), node, action)

    return None


def bfs_child_node(start_state):
    node = Node(start_state)

    if is_goal(node.state):
        return node

    frontier = deque()
    frontier.append(node)

    reached = set()
    reached.add(start_state)

    actions = ["Up", "Down", "Left", "Right"]

    while frontier:
        node = frontier.popleft()

        for action in actions:
            child = child_node(start_state, node, action)

            if child is not None:
                s = child.state

                if s not in reached:
                    if is_goal(s):
                        return child

                    reached.add(s)
                    frontier.append(child)

    return None



# CÁCH 2: EXPAND
def expand(node):
    children = []

    state = node.state
    zero_index = state.index(0)

    row = zero_index // 3
    col = zero_index % 3

    moves = [
        ("Up", -1, 0),
        ("Down", 1, 0),
        ("Left", 0, -1),
        ("Right", 0, 1)
    ]

    for action, dr, dc in moves:
        new_row = row + dr
        new_col = col + dc

        if 0 <= new_row < 3 and 0 <= new_col < 3:
            new_index = new_row * 3 + new_col
            new_state = list(state)

            new_state[zero_index], new_state[new_index] = new_state[new_index], new_state[zero_index]

            child = Node(tuple(new_state), node, action)
            children.append(child)

    return children


def bfs_expand(start_state):
    node = Node(start_state)

    if is_goal(node.state):
        return node

    frontier = deque()
    frontier.append(node)

    reached = set()
    reached.add(start_state)

    while frontier:
        node = frontier.popleft()

        for child in expand(node):
            s = child.state

            if is_goal(s):
                return child

            if s not in reached:
                reached.add(s)
                frontier.append(child)

    return None


def get_solution_path(node):
    path = []

    while node is not None:
        path.append(node)
        node = node.parent

    path.reverse()
    return path


def generate_random_state():
    state = list(GOAL_STATE)

    for _ in range(50):
        zero_index = state.index(0)

        row = zero_index // 3
        col = zero_index % 3

        possible_moves = []

        moves = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1)
        ]

        for dr, dc in moves:
            new_row = row + dr
            new_col = col + dc

            if 0 <= new_row < 3 and 0 <= new_col < 3:
                new_index = new_row * 3 + new_col
                possible_moves.append(new_index)

        new_index = random.choice(possible_moves)
        state[zero_index], state[new_index] = state[new_index], state[zero_index]

    return tuple(state)


class PuzzleUI:
    def __init__(self, root):
        self.root = root
        self.root.title("8 Puzzle BFS")

        self.start_state = generate_random_state()

        self.solution_child = []
        self.solution_expand = []

        self.solution_path = []
        self.current_step = 0
        self.selected_method = None

        self.title_label = tk.Label(
            root,
            text="8 Puzzle - Breadth First Search",
            font=("Arial", 18, "bold")
        )
        self.title_label.pack(pady=10)

        self.frame = tk.Frame(root)
        self.frame.pack()

        self.buttons = []

        for i in range(9):
            btn = tk.Label(
                self.frame,
                text="",
                width=6,
                height=3,
                font=("Arial", 24, "bold"),
                borderwidth=2,
                relief="solid"
            )
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)
            self.buttons.append(btn)

        self.info_label = tk.Label(
            root,
            text="Ma trận được tạo ngẫu nhiên.\nNhấn So sánh BFS để xem 2 cách.",
            font=("Arial", 12),
            justify="left",
            wraplength=420
        )
        self.info_label.pack(pady=10)

        self.compare_button = tk.Button(
            root,
            text="So sánh BFS",
            font=("Arial", 12),
            command=self.compare_bfs
        )
        self.compare_button.pack(pady=3)

        self.child_button = tk.Button(
            root,
            text="Chọn BFS CHILD-NODE",
            font=("Arial", 12),
            command=self.choose_child,
            state="disabled"
        )
        self.child_button.pack(pady=3)

        self.expand_button = tk.Button(
            root,
            text="Chọn BFS EXPAND",
            font=("Arial", 12),
            command=self.choose_expand,
            state="disabled"
        )
        self.expand_button.pack(pady=3)

        self.next_button = tk.Button(
            root,
            text="Next Step",
            font=("Arial", 12),
            command=self.next_step,
            state="disabled"
        )
        self.next_button.pack(pady=3)

        self.random_button = tk.Button(
            root,
            text="Random Matrix",
            font=("Arial", 12),
            command=self.random_matrix
        )
        self.random_button.pack(pady=3)

        self.reset_button = tk.Button(
            root,
            text="Reset",
            font=("Arial", 12),
            command=self.reset
        )
        self.reset_button.pack(pady=3)

        self.display_state(self.start_state)

    def display_state(self, state):
        for i in range(9):
            value = state[i]

            if value == 0:
                self.buttons[i].config(text="", bg="lightgray")
            else:
                self.buttons[i].config(text=str(value), bg="white")

    def compare_bfs(self):
        result_child = bfs_child_node(self.start_state)
        result_expand = bfs_expand(self.start_state)

        if result_child is None or result_expand is None:
            self.info_label.config(text="Không tìm thấy lời giải")
            return

        self.solution_child = get_solution_path(result_child)
        self.solution_expand = get_solution_path(result_expand)

        steps_child = len(self.solution_child) - 1
        steps_expand = len(self.solution_expand) - 1

        self.info_label.config(
            text=f"So sánh kết quả:\n"
                 f"Cách 1 - BFS CHILD-NODE: {steps_child} bước\n"
                 f"Cách 2 - BFS EXPAND: {steps_expand} bước\n\n"
                 f"Hãy chọn 1 cách để xem từng bước."
        )

        self.child_button.config(state="normal")
        self.expand_button.config(state="normal")
        self.next_button.config(state="disabled")

    def choose_child(self):
        self.solution_path = self.solution_child
        self.current_step = 0
        self.selected_method = "BFS CHILD-NODE"

        self.display_state(self.solution_path[0].state)

        self.info_label.config(
            text=f"Đã chọn {self.selected_method}\n"
                 f"Số bước: {len(self.solution_path) - 1}\n"
                 f"Nhấn Next Step để xem từng bước."
        )

        self.next_button.config(state="normal")

    def choose_expand(self):
        self.solution_path = self.solution_expand
        self.current_step = 0
        self.selected_method = "BFS EXPAND"

        self.display_state(self.solution_path[0].state)

        self.info_label.config(
            text=f"Đã chọn {self.selected_method}\n"
                 f"Số bước: {len(self.solution_path) - 1}\n"
                 f"Nhấn Next Step để xem từng bước."
        )

        self.next_button.config(state="normal")

    def next_step(self):
        if self.current_step < len(self.solution_path):
            node = self.solution_path[self.current_step]
            self.display_state(node.state)

            if self.current_step == 0:
                zero_index = node.state.index(0)

                row = zero_index // 3
                col = zero_index % 3

                self.info_label.config(
                    text=f"{self.selected_method}\n"
                         f"Bước {self.current_step}: Start\n"
                         f"Vị trí ô trống hiện tại: ({row}, {col})"
                )

            else:
                prev_node = self.solution_path[self.current_step - 1]
                current_node = self.solution_path[self.current_step]

                prev_zero_index = prev_node.state.index(0)
                current_zero_index = current_node.state.index(0)

                prev_row = prev_zero_index // 3
                prev_col = prev_zero_index % 3

                current_row = current_zero_index // 3
                current_col = current_zero_index % 3

                self.info_label.config(
                    text=f"{self.selected_method}\n"
                         f"Bước {self.current_step}\n"
                         f"Vị trí hiện tại: ({prev_row}, {prev_col})\n"
                         f"Đi: {current_node.action}\n"
                         f"Vị trí sau khi đi: ({current_row}, {current_col})"
                )

            self.current_step += 1

        else:
            self.info_label.config(text="Đã đến trạng thái Goal")
            self.next_button.config(state="disabled")

    def random_matrix(self):
        self.start_state = generate_random_state()

        self.solution_child = []
        self.solution_expand = []
        self.solution_path = []
        self.current_step = 0
        self.selected_method = None

        self.display_state(self.start_state)

        self.info_label.config(
            text="Đã tạo ma trận ngẫu nhiên mới.\nNhấn So sánh BFS để xem 2 cách."
        )

        self.child_button.config(state="disabled")
        self.expand_button.config(state="disabled")
        self.next_button.config(state="disabled")

    def reset(self):
        self.solution_path = []
        self.current_step = 0
        self.selected_method = None

        self.display_state(self.start_state)

        self.info_label.config(
            text="Đã reset về ma trận ban đầu.\nNhấn So sánh BFS để xem 2 cách."
        )

        self.next_button.config(state="disabled")


root = tk.Tk()
app = PuzzleUI(root)
root.mainloop()