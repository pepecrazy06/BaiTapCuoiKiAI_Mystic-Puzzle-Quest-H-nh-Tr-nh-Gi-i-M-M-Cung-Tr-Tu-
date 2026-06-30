import random

ROWS = int(input("Nhập số hàng: "))
COLS = int(input("Nhập số cột: "))

MAX_STEPS = 100


def create_goal():
    numbers = list(range(1, ROWS * COLS))
    numbers.append("A")

    goal = []
    index = 0

    for i in range(ROWS):
        row = []
        for j in range(COLS):
            row.append(numbers[index])
            index += 1
        goal.append(tuple(row))

    return tuple(goal)


def create_random_matrix():
    numbers = list(range(1, ROWS * COLS))
    numbers.append("A")
    random.shuffle(numbers)

    matrix = []
    index = 0

    for i in range(ROWS):
        row = []
        for j in range(COLS):
            row.append(numbers[index])
            index += 1
        matrix.append(tuple(row))

    return tuple(matrix)


def print_matrix(matrix):
    for row in matrix:
        for value in row:
            print(value, end="\t")
        print()
    print()


def find_A(matrix):
    for i in range(ROWS):
        for j in range(COLS):
            if matrix[i][j] == "A":
                return i, j


def heuristic(matrix, goal):
    sai = 0

    for i in range(ROWS):
        for j in range(COLS):
            if matrix[i][j] != goal[i][j]:
                sai += 1

    return sai


def get_neighbors(matrix):
    neighbors = []

    row, col = find_A(matrix)

    moves = [
        (-1, 0, "đi lên"),
        (1, 0, "đi xuống"),
        (0, -1, "đi sang trái"),
        (0, 1, "đi sang phải")
    ]

    for dr, dc, action in moves:
        new_row = row + dr
        new_col = col + dc

        if 0 <= new_row < ROWS and 0 <= new_col < COLS:
            temp = [list(r) for r in matrix]

            temp[row][col], temp[new_row][new_col] = temp[new_row][new_col], temp[row][col]

            new_matrix = tuple(tuple(r) for r in temp)

            neighbors.append((new_matrix, action))

    return neighbors


def SIMPLE_REFLEX_AGENT(current, goal, visited):
    neighbors = get_neighbors(current)

    best_matrix = None
    best_action = None
    best_score = 999999

    for next_matrix, action in neighbors:
        score = heuristic(next_matrix, goal)

        if next_matrix not in visited and score < best_score:
            best_score = score
            best_matrix = next_matrix
            best_action = action

    # Nếu các hướng đều đã đi rồi, chọn ngẫu nhiên 1 hướng để vẫn tiếp tục
    if best_matrix is None:
        best_matrix, best_action = random.choice(neighbors)

    return best_matrix, best_action


GOAL = create_goal()
current = create_random_matrix()

visited = set()
visited.add(current)

print("\nMa trận ban đầu:")
print_matrix(current)

print("Ma trận đích:")
print_matrix(GOAL)

step = 0

while current != GOAL and step < MAX_STEPS:
    step += 1

    current, action = SIMPLE_REFLEX_AGENT(current, GOAL, visited)
    visited.add(current)

    print("Bước", step)
    print("Hành động:", action)
    print("Số ô sai vị trí:", heuristic(current, GOAL))
    print_matrix(current)


if current == GOAL:
    print("Hoàn thành! Ma trận đã được sắp xếp đúng.")
else:
    print("Agent đã đi quá", MAX_STEPS, "bước nhưng chưa sắp xếp được.")