GOAL_STATE = (
    1, 2, 3,
    4, 5, 6,
    7, 8, 0
)

ACTIONS = ["Left", "Right", "Up", "Down"]  # L R U D


class Node:
    def __init__(self, state, parent=None, action=None):
        self.state = state
        self.parent = parent
        self.action = action


def print_matrix(state):
    for i in range(9):
        print(state[i], end="\t")
        if (i + 1) % 3 == 0:
            print()
    print()


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
        return Node(tuple(state), node, action)

    return None


def expand(node):
    children = []

    print("Sinh node con theo thứ tự L R U D:")

    for action in ACTIONS:
        child = move(node, action)

        if child is not None:
            children.append(child)
            print(f"\nĐi {action}:")
            print_matrix(child.state)

    return children


def dfs(start_state):
    start_node = Node(start_state)

    print("MA TRẬN BAN ĐẦU:")
    print_matrix(start_node.state)

    zero_index = start_state.index(0)
    row = zero_index // 3
    col = zero_index % 3

    print(f"Vị trí số 0 ban đầu: ({row}, {col})")

    if is_goal(start_node.state):
        print("START đã là GOAL")
        return start_node

    frontier = []
    frontier.append(start_node)

    reached = set()
    reached.add(start_state)

    while frontier:
        node = frontier.pop()

        print("--------------------------------")
        print("Lấy ma trận ra khỏi stack để xét:")
        print_matrix(node.state)

        if is_goal(node.state):
            print("Ma trận này bằng GOAL")
            return node

        children = expand(node)

        for child in children:
            s = child.state

            if is_goal(s):
                print(f"Ma trận sau khi đi {child.action} bằng GOAL")
                return child

            frontier_states = [n.state for n in frontier]

            if s not in reached and s not in frontier_states:
                reached.add(s)
                frontier.append(child)
                print(f"Thêm ma trận đi {child.action} vào stack")
            else:
                print(f"Ma trận đi {child.action} đã có trong reached hoặc stack nên bỏ qua")

        print("Stack hiện tại:")
        print([n.action for n in frontier])
        print("Vì stack LIFO nên ma trận thêm sau được lấy ra trước.")

    return None


def get_solution_path(node):
    path = []

    while node is not None:
        path.append(node)
        node = node.parent

    path.reverse()
    return path


start_state = (
    1, 2, 3,
    4, 0, 6,
    7, 5, 8
)

result = dfs(start_state)

print("================================")

if result is None:
    print("DFS không tìm thấy lời giải")
else:
    path = get_solution_path(result)

    print("ĐƯỜNG ĐI TỪ START ĐẾN GOAL:")

    for i, node in enumerate(path):
        if i == 0:
            print(f"Bước {i}: START")
        else:
            print(f"Bước {i}: đi {node.action}")

        print_matrix(node.state)

    print(f"Tổng số bước: {len(path) - 1}")