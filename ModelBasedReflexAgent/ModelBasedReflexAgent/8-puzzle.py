import random


goal = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 0]
]

actions = ["UP", "DOWN", "LEFT", "RIGHT"]



def random_state():
    nums = [1, 2, 3, 4, 5, 6, 7, 8, 0]
    random.shuffle(nums)

    return [
        nums[0:3],
        nums[3:6],
        nums[6:9]
    ]


def print_board(board):
    for row in board:
        print(row)
    print()


def find_zero(board):
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return i, j


def move(board, action):
    i, j = find_zero(board)

    if action == "UP":
        ni, nj = i - 1, j
    elif action == "DOWN":
        ni, nj = i + 1, j
    elif action == "LEFT":
        ni, nj = i, j - 1
    elif action == "RIGHT":
        ni, nj = i, j + 1

    if ni < 0 or ni > 2 or nj < 0 or nj > 2:
        return None

    new_board = [row[:] for row in board]
    new_board[i][j], new_board[ni][nj] = new_board[ni][nj], new_board[i][j]

    return new_board


def score(board):
    sai = 0

    for i in range(3):
        for j in range(3):
            if board[i][j] != 0 and board[i][j] != goal[i][j]:
                sai += 1

    return sai


def choose_best_action(board):
    best_action = None
    best_score = 999

    for action in actions:
        new_board = move(board, action)

        if new_board is not None:
            s = score(new_board)

            if s < best_score:
                best_score = s
                best_action = action

    return best_action


#main
state = random_state()

print("State ban đầu ngẫu nhiên:")
print_board(state)

step = 0
max_step = 50

while state != goal and step < max_step:
    action = choose_best_action(state)

    print("Bước", step + 1)
    print("Chọn bước tốt nhất:", action)

    state = move(state, action)
    print_board(state)

    step += 1

if state == goal:
    print("Hoàn thành!")
else:
    print("Chưa tới goal sau", max_step, "bước")
