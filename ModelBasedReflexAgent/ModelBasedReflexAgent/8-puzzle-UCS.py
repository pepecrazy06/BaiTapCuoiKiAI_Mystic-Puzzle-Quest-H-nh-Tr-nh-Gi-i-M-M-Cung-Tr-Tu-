import heapq

# 1. Trạng thái bắt đầu và đích
START_STATE = ((1, 2, 3),
               (4, 0, 6),
               (7, 5, 8))

GOAL_STATE = ((1, 2, 3),
              (4, 5, 6),
              (7, 8, 0))

GOAL_POSITIONS = {
    1: (0, 0), 2: (0, 1), 3: (0, 2),
    4: (1, 0), 5: (1, 1), 6: (1, 2),
    7: (2, 0), 8: (2, 1), 0: (2, 2)
}

def print_state(state):
    for row in state:
        print(" ".join(str(val) if val != 0 else "_" for val in row))
    print("-" * 10)

def get_heuristic(state):
    h = 0
    for r in range(3):
        for c in range(3):
            val = state[r][c]
            if val != 0: # Không tính ô trống
                target_r, target_c = GOAL_POSITIONS[val]
                distance = abs(r - target_r) + abs(c - target_c)
                h += distance * val # LUẬT MỚI: Nhân khoảng cách với giá trị ô
    return h

def get_neighbors(state):
    """Tìm các nước đi hợp lệ và trả về (Trạng_thái_mới, Chi_phí_bước_đi)"""
    neighbors = []
    # Tìm tọa độ của ô trống (0)
    for r in range(3):
        for c in range(3):
            if state[r][c] == 0:
                zero_r, zero_c = r, c
                break
                
    # 4 hướng di chuyển: Lên, Xuống, Trái, Phải
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    for dr, dc in directions:
        new_r, new_c = zero_r + dr, zero_c + dc
        
        if 0 <= new_r < 3 and 0 <= new_c < 3:
            new_state = [list(row) for row in state]
            
            moved_value = new_state[new_r][new_c]
            
            new_state[zero_r][zero_c], new_state[new_r][new_c] = new_state[new_r][new_c], new_state[zero_r][zero_c]
            
            final_state = tuple(tuple(row) for row in new_state)
            
            neighbors.append((final_state, moved_value))
            
    return neighbors

def a_star_search(start, goal):
    frontier = []
    tie_breaker = 0
    
    h_start = get_heuristic(start)
    heapq.heappush(frontier, (h_start, tie_breaker, 0, start, [start]))
    
    visited_g = {start: 0}
    
    nodes_expanded = 0 
    
    while frontier:
        f, _, g, current_state, path = heapq.heappop(frontier)
        nodes_expanded += 1
        
        if current_state == goal:
            return path, g, nodes_expanded
            
        for next_state, move_cost in get_neighbors(current_state):
            new_g = g + move_cost
            
            if next_state not in visited_g or new_g < visited_g[next_state]:
                visited_g[next_state] = new_g
                new_f = new_g + get_heuristic(next_state)
                new_path = path + [next_state]
                
                tie_breaker += 1
                heapq.heappush(frontier, (new_f, tie_breaker, new_g, next_state, new_path))
                
    return None, 0, nodes_expanded 

print("Đang giải bài toán bằng A*...")
path, total_cost, nodes_expanded = a_star_search(START_STATE, GOAL_STATE)

if path:
    print(f"✅ TÌM THẤY ĐÍCH! Tổng chi phí tối ưu (g): {total_cost}")
    print(f"🔍 Số trạng thái đã mở rộng (Nodes expanded): {nodes_expanded}")
    print(f"👣 Số bước di chuyển: {len(path) - 1}\n")
    
    print("CHI TIẾT ĐƯỜNG ĐI:")
    for step, state in enumerate(path):
        print(f"Bước {step}:")
        print_state(state)
else:
    print("Không tìm thấy đường đi.")