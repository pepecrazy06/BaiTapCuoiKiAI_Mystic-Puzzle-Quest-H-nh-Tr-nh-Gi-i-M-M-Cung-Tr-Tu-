import time
from collections import deque

def get_node_id(index):
    """Hàm hỗ trợ tạo tên Node dạng A, B, C... Z, AA, AB..."""
    res = ""
    while index >= 0:
        res = chr(65 + (index % 26)) + res
        index = index // 26 - 1
    return res

class Node:
    def __init__(self, state, parent=None, action="", cost=0, node_id=""):
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost
        self.node_id = node_id

class PuzzleSolver:
    def __init__(self):
        self.moves = {'U': -3, 'D': 3, 'L': -1, 'R': 1}

    def get_neighbors(self, state):
        neighbors = []
        idx = state.index(0)
        row, col = divmod(idx, 3)

        for action, move in self.moves.items():
            if (action == 'U' and row > 0) or \
               (action == 'D' and row < 2) or \
               (action == 'L' and col > 0) or \
               (action == 'R' and col < 2):
                new_state = list(state)
                new_state[idx], new_state[idx + move] = new_state[idx + move], new_state[idx]
                neighbors.append((tuple(new_state), action))
        return neighbors

    def solve(self, start_state, goal_state, algorithm="BFS"):
        start_time = time.time()
        goal_tuple = tuple(goal_state)
        
        node_counter = 0
        def next_id():
            nonlocal node_counter
            res = get_node_id(node_counter)
            node_counter += 1
            return res

        start_node = Node(tuple(start_state), node_id=next_id())
        frontier = deque([start_node]) if algorithm == "BFS" else [start_node]
        reached_set = {start_node.state}
        reached_list = [start_node.state] # Lưu dạng list để giữ thứ tự cho UI
        
        history_logs = [] # Lưu toàn bộ quá trình duyệt

        while frontier:
            current_node = frontier.popleft() if algorithm == "BFS" else frontier.pop()
            
            # Nếu là đích, ghi log dòng cuối cùng và kết thúc
            if current_node.state == goal_tuple:
                history_logs.append({
                    "node": current_node,
                    "frontier_added": [{"is_goal": True, "state": current_node.state, "id": current_node.node_id, "parent_id": current_node.parent.node_id if current_node.parent else "", "action": "", "cost": current_node.cost}],
                    "reached": list(reached_list)
                })
                return {"success": True, "history": history_logs, "time": round((time.time() - start_time) * 1000, 2)}

            # Nếu chưa phải đích, sinh các con
            frontier_snapshot = []
            for next_state, action in self.get_neighbors(current_node.state):
                if next_state not in reached_set:
                    reached_set.add(next_state)
                    reached_list.append(next_state)
                    
                    child_node = Node(next_state, current_node, action, current_node.cost + 1, next_id())
                    frontier.append(child_node)
                    
                    is_goal = (next_state == goal_tuple)
                    frontier_snapshot.append({
                        "state": next_state, "parent_id": current_node.node_id,
                        "action": action, "cost": child_node.cost, 
                        "id": child_node.node_id, "is_goal": is_goal
                    })

            # Lưu vào lịch sử
            history_logs.append({
                "node": current_node,
                "frontier_added": frontier_snapshot,
                "reached": list(reached_list)
            })

        return {"success": False, "history": history_logs, "time": round((time.time() - start_time) * 1000, 2)}