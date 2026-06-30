import random

ROWS = int(input("Nhập số hàng: "))
COLS = int(input("Nhập số cột: "))

MAX_STEPS = 100

matrix = []

for i in range(ROWS):
    row = []
    for j in range(COLS):
        row.append(random.randint(0, 1))
    matrix.append(row)

agent_row = random.randint(0, ROWS - 1)
agent_col = random.randint(0, COLS - 1)

state = []

for i in range(ROWS):
    row = []
    for j in range(COLS):
        row.append(matrix[i][j])
    state.append(row)

last_action = None


def print_matrix():
    for i in range(ROWS):
        for j in range(COLS):
            if i == agent_row and j == agent_col:
                print("A", end="\t")
            else:
                print(matrix[i][j], end="\t")
        print()
    print()


def has_dirty(board):
    for i in range(ROWS):
        for j in range(COLS):
            if board[i][j] == 1:
                return True
    return False


def update_state(state, action, row, col, percept):
    state[row][col] = percept

    if action == "Hút":
        state[row][col] = 0

    return state


def rule_match(state, row, col):
    if state[row][col] == 1:
        return "Hút"

    dirty_cells = []

    for i in range(ROWS):
        for j in range(COLS):
            if state[i][j] == 1:
                dirty_cells.append((i, j))

    if len(dirty_cells) == 0:
        return "STOP"

    nearest_dirty = dirty_cells[0]
    min_distance = abs(row - nearest_dirty[0]) + abs(col - nearest_dirty[1])

    for cell in dirty_cells:
        distance = abs(row - cell[0]) + abs(col - cell[1])

        if distance < min_distance:
            min_distance = distance
            nearest_dirty = cell

    target_row, target_col = nearest_dirty

    if target_row < row:
        return "UP"

    if target_row > row:
        return "DOWN"

    if target_col < col:
        return "LEFT"

    if target_col > col:
        return "RIGHT"


def do_action(action):
    global agent_row, agent_col

    if action == "Hút":
        matrix[agent_row][agent_col] = 0

    elif action == "UP":
        agent_row = agent_row - 1

    elif action == "DOWN":
        agent_row = agent_row + 1

    elif action == "LEFT":
        agent_col = agent_col - 1

    elif action == "RIGHT":
        agent_col = agent_col + 1


print("Ma trận ban đầu:")
print_matrix()

step = 0

while has_dirty(matrix) and step < MAX_STEPS:
    step = step + 1

    print("Bước:", step)
    print("Vị trí agent:", agent_row, agent_col)

    percept = matrix[agent_row][agent_col]

    state = update_state(state, last_action, agent_row, agent_col, percept)
    action = rule_match(state, agent_row, agent_col)

    print("Action:", action)

    if action == "STOP":
        break

    do_action(action)

    last_action = action

    print("Ma trận hiện tại:")
    print_matrix()


if has_dirty(matrix) == False:
    print("Tất cả các ô đã sạch. Agent dừng lại.")
else:
    print("Đã đạt số bước tối đa. Agent dừng lại.")
