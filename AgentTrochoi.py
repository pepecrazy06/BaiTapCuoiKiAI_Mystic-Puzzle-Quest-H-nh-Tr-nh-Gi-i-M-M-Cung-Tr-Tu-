import random

# ==========================================
# SIMPLE REFLEX AGENT
# ==========================================

ROWS = int(input("Nhập số hàng: "))
COLS = int(input("Nhập số cột: "))

# ==========================================
# TẠO MA TRẬN RANDOM
# ==========================================

matrix = []

for i in range(ROWS):

    row = []

    for j in range(COLS):
        row.append(random.randint(1, 8))

    matrix.append(row)


# ==========================================
# IN MA TRẬN
# ==========================================

def print_matrix(matrix):

    for row in matrix:

        for value in row:
            print(value, end="\t")

        print()


# ==========================================
# INTERPRET-INPUT(percept)
# percept -> state
# ==========================================

def INTERPRET_INPUT(percept):

    state = percept

    return state


# ==========================================
# RULE-MATCH(state, rules)
# ==========================================

def RULE_MATCH(state, target_pos):

    current_row, current_col = state
    target_row, target_col = target_pos

    # ======================================
    # TẬP LUẬT
    # ======================================

    if target_row < current_row:

        rule = {
            "STATE": state,
            "ACTION": "đi lên"
        }

    elif target_row > current_row:

        rule = {
            "STATE": state,
            "ACTION": "đi xuống"
        }

    elif target_col < current_col:

        rule = {
            "STATE": state,
            "ACTION": "đi sang trái"
        }

    elif target_col > current_col:

        rule = {
            "STATE": state,
            "ACTION": "đi sang phải"
        }

    else:

        rule = {
            "STATE": state,
            "ACTION": "dừng lại"
        }

    return rule


# ==========================================
# function SIMPLE-REFLEX-AGENT(percept)
# returns action
# ==========================================

def SIMPLE_REFLEX_AGENT(percept, target_pos):

    # state <- INTERPRET-INPUT(percept)
    state = INTERPRET_INPUT(percept)

    # rule <- RULE-MATCH(state, rules)
    rule = RULE_MATCH(state, target_pos)

    # action <- rule.ACTION
    action = rule["ACTION"]

    # return action
    return action


# ==========================================
# DI CHUYỂN AGENT
# ==========================================

def move_agent(matrix, current_pos, action):

    row, col = current_pos

    new_row = row
    new_col = col

    if action == "đi lên":
        new_row -= 1

    elif action == "đi xuống":
        new_row += 1

    elif action == "đi sang trái":
        new_col -= 1

    elif action == "đi sang phải":
        new_col += 1

    elif action == "dừng lại":
        return current_pos

    # Hoán đổi vị trí
    matrix[row][col], matrix[new_row][new_col] = \
        matrix[new_row][new_col], matrix[row][col]

    return (new_row, new_col)


# ==========================================
# MAIN
# ==========================================

print("\nMa trận ban đầu:\n")
print_matrix(matrix)

# Random vị trí hiện tại của agent
current_row = random.randint(0, ROWS - 1)
current_col = random.randint(0, COLS - 1)

current_pos = (current_row, current_col)

# Đánh dấu agent
matrix[current_row][current_col] = "A"

print("\nVị trí hiện tại của agent:", current_pos)

print("\nMa trận có agent:\n")
print_matrix(matrix)

# Nhập vị trí muốn đến
target_row = int(input("\nNhập hàng muốn đến: "))
target_col = int(input("Nhập cột muốn đến: "))

target_pos = (target_row, target_col)

print("\nAgent bắt đầu di chuyển...\n")

# ==========================================
# AGENT HOẠT ĐỘNG
# ==========================================

while current_pos != target_pos:

    percept = current_pos

    action = SIMPLE_REFLEX_AGENT(percept, target_pos)

    print("Percept:", percept)
    print("Action:", action)

    current_pos = move_agent(matrix, current_pos, action)

    print("\nMa trận sau khi di chuyển:\n")
    print_matrix(matrix)
    print()

print("Agent đã tới đích:", target_pos)