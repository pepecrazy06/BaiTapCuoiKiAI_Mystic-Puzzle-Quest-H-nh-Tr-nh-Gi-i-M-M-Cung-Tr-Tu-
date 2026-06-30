import tkinter as tk
from tkinter import ttk, messagebox
from solver import PuzzleSolver

# Định nghĩa bảng màu Dark Theme theo mẫu
BG_MAIN = "#12151e"
BG_PANEL = "#1a1e29"
BG_TILE = "#2a3142"
BG_TILE_EMPTY = "#12151e"
FG_TEXT = "#e2e8f0"
FG_DIM = "#94a3b8"
BTN_BLUE = "#3b82f6"
BTN_DARK = "#272e3f"
BORDER = "#334155"

class PuzzleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("8-Puzzle AI Search")
        # Áp dụng kích thước tổng thể mới
        self.root.geometry("980x620")
        self.root.configure(bg=BG_MAIN)
        
        self.solver = PuzzleSolver()
        self.history = []
        self.current_step = 0
        self.is_playing = False
        
        # Trạng thái mặc định
        self.start_state = [1, 2, 3, 4, 0, 6, 7, 5, 8]
        self.goal_state = [1, 2, 3, 4, 5, 6, 7, 8, 0]
        
        self.setup_ui()
        self.draw_main_board(self.start_state)

    def setup_ui(self):
        # --- TOP SECTION (Ma trận & Thông tin) ---
        top_frame = tk.Frame(self.root, bg=BG_MAIN)
        top_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 1. Khung Ma trận bên trái
        board_container = tk.Frame(top_frame, bg=BG_MAIN, highlightbackground=BORDER, highlightthickness=1)
        board_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(board_container, text="8 Puzzle Search", bg=BG_MAIN, fg=FG_DIM, font=("Arial", 10)).pack(anchor="nw", padx=10, pady=10)
        
        self.board_frame = tk.Frame(board_container, bg=BG_MAIN)
        self.board_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # ÁP DỤNG CÁCH KHỞI TẠO MA TRẬN MỚI BẰNG VÒNG LẶP RANGE(9)
        self.main_tiles = []
        for i in range(9):
            row_idx = i // 3
            col_idx = i % 3
            
            cell = tk.Label(
                self.board_frame, 
                text="", 
                width=4, 
                height=2, 
                font=("Segoe UI", 22, "bold"),
                bg=BG_TILE, 
                fg="white"
            )
            
            cell.grid(
                row=row_idx, 
                column=col_idx, 
                padx=6, 
                pady=6, 
                ipadx=10, 
                ipady=10
            )
            
            self.main_tiles.append(cell)

        # 2. Khung Thông tin bên phải
        info_container = tk.Frame(top_frame, bg=BG_MAIN, width=400)
        info_container.pack(side=tk.RIGHT, fill=tk.Y)
        info_container.pack_propagate(False) # Cố định chiều rộng
        
        # 2.1 Panel Trạng thái
        status_panel = tk.Frame(info_container, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
        status_panel.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(status_panel, text="🔵 TRẠNG THÁI", bg=BG_PANEL, fg=BTN_BLUE, font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=15)
        tk.Label(status_panel, text="Có thể chỉnh trạng thái ban đầu và đích trực tiếp.\nChọn thuật toán rồi nhấn Run để chạy.", bg=BG_PANEL, fg=FG_DIM, justify=tk.LEFT).pack(anchor="w", padx=15, pady=(0, 15))
        
        self.lbl_algo = self.create_status_row(status_panel, "Thuật toán:", "Chưa chọn")
        self.lbl_step = self.create_status_row(status_panel, "Bước hiện tại:", "-")
        self.lbl_empty = self.create_status_row(status_panel, "Vị trí ô trống:", "-")
        self.lbl_action = self.create_status_row(status_panel, "Hành động:", "-")
        self.lbl_result = self.create_status_row(status_panel, "Kết quả:", "Chưa chạy", fg_val="#facc15")
        tk.Frame(status_panel, bg=BG_PANEL, height=10).pack()

        # 2.2 Panel Nhật ký
        log_panel = tk.Frame(info_container, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
        log_panel.pack(fill=tk.BOTH, expand=True)
        
        log_header = tk.Frame(log_panel, bg=BG_PANEL)
        log_header.pack(fill=tk.X, padx=15, pady=15)
        tk.Label(log_header, text="🗎 NHẬT KÝ", bg=BG_PANEL, fg=FG_TEXT, font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        btn_details = tk.Button(log_header, text="Xem chi tiết quá trình ➝", bg=BG_PANEL, fg="white", bd=0, cursor="hand2", command=self.open_details_window, font=("Arial", 10, "bold"))
        btn_details.pack(side=tk.RIGHT)
        
        self.txt_log = tk.Text(log_panel, bg="#12151e", fg=FG_DIM, bd=0, font=("Arial", 10), padx=10, pady=10)
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        self.txt_log.insert(tk.END, "Nhật ký sẽ hiển thị ở đây.\nBạn có thể xem chi tiết quá trình tìm kiếm bằng nút bên trên.")
        self.txt_log.config(state=tk.DISABLED)

        # --- BOTTOM SECTION (Điều khiển) ---
        bottom_frame = tk.Frame(self.root, bg=BG_MAIN, highlightbackground=BORDER, highlightthickness=1)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=(0, 20), ipady=10)
        
        # 1. Chọn Thuật toán
        algo_frame = tk.Frame(bottom_frame, bg=BG_MAIN)
        algo_frame.pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(algo_frame, text="Chọn thuật toán:", bg=BG_MAIN, fg=FG_TEXT).pack(anchor="w", pady=(0, 5))
        self.algo_cb = ttk.Combobox(algo_frame, values=["BFS", "DFS"], state="readonly", width=25)
        self.algo_cb.current(0)
        self.algo_cb.pack()

        # 2. Cụm phím Điều khiển (Giữa)
        ctrl_frame = tk.Frame(bottom_frame, bg=BG_PANEL, highlightbackground=BORDER, highlightthickness=1)
        ctrl_frame.pack(side=tk.LEFT, padx=50, pady=10)
        
        self.btn_run = tk.Button(ctrl_frame, text="▶ Run", bg=BTN_BLUE, fg="white", width=15, bd=0, font=("Arial", 10, "bold"), command=self.solve_puzzle)
        self.btn_run.pack(fill=tk.X, pady=1)
        
        self.btn_next = tk.Button(ctrl_frame, text="➝ Next Step", bg=BTN_DARK, fg="white", width=15, bd=0, command=self.step_next)
        self.btn_next.pack(fill=tk.X, pady=1)
        
        self.btn_prev = tk.Button(ctrl_frame, text="← Quay lại", bg=BTN_DARK, fg="white", width=15, bd=0, command=self.step_prev)
        self.btn_prev.pack(fill=tk.X, pady=1)
        
        self.btn_auto = tk.Button(ctrl_frame, text="↻ Tự động", bg=BTN_DARK, fg="white", width=15, bd=0, command=self.play_auto)
        self.btn_auto.pack(fill=tk.X, pady=1)
        
        self.btn_reset = tk.Button(ctrl_frame, text="⟲ Reset", bg=BTN_DARK, fg="white", width=15, bd=0, command=self.reset_board)
        self.btn_reset.pack(fill=tk.X, pady=1)

        # 3. Chọn Trạng thái (Phải)
        setup_frame = tk.Frame(bottom_frame, bg=BG_MAIN)
        setup_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        top_setup = tk.Frame(setup_frame, bg=BG_MAIN)
        top_setup.pack(fill=tk.X, pady=(0, 5))
        tk.Label(top_setup, text="Chọn trạng thái:", bg=BG_MAIN, fg=FG_TEXT).pack(side=tk.LEFT)
        self.state_type_cb = ttk.Combobox(top_setup, values=["Trạng thái ban đầu", "Trạng thái đích"], state="readonly", width=18)
        self.state_type_cb.current(0)
        self.state_type_cb.pack(side=tk.LEFT, padx=10)
        self.state_type_cb.bind("<<ComboboxSelected>>", self.load_state_to_inputs)

        grid_setup = tk.Frame(setup_frame, bg=BG_MAIN)
        grid_setup.pack(fill=tk.X)
        
        self.state_inputs = []
        for i in range(3):
            for j in range(3):
                ent = tk.Entry(grid_setup, width=3, bg=BG_TILE, fg="white", bd=0, font=("Arial", 12), justify="center")
                ent.grid(row=i, column=j, padx=2, pady=2)
                self.state_inputs.append(ent)
                
        self.load_state_to_inputs()
        
        tk.Button(setup_frame, text="✓ Xác nhận cập nhật", bg=BTN_BLUE, fg="white", bd=0, font=("Arial", 10, "bold"), command=self.save_state_inputs).pack(fill=tk.X, pady=(10, 0))

    def create_status_row(self, parent, label_text, val_text, fg_val=FG_TEXT):
        row = tk.Frame(parent, bg=BG_PANEL)
        row.pack(fill=tk.X, padx=15, pady=3)
        tk.Label(row, text=label_text, bg=BG_PANEL, fg=FG_DIM).pack(side=tk.LEFT)
        lbl_val = tk.Label(row, text=val_text, bg=BG_PANEL, fg=fg_val, font=("Arial", 10, "bold"))
        lbl_val.pack(side=tk.RIGHT)
        return lbl_val

    # --- LOGIC GIAO DIỆN ---
    def load_state_to_inputs(self, event=None):
        state = self.start_state if self.state_type_cb.current() == 0 else self.goal_state
        for i, val in enumerate(state):
            self.state_inputs[i].delete(0, tk.END)
            self.state_inputs[i].insert(0, str(val))

    def save_state_inputs(self):
        try:
            new_state = [int(ent.get()) for ent in self.state_inputs]
            if len(set(new_state)) != 9 or max(new_state) > 8 or min(new_state) < 0:
                raise ValueError
        except:
            messagebox.showerror("Lỗi", "Vui lòng nhập đủ các số từ 0 đến 8 (không trùng lặp).")
            return
            
        if self.state_type_cb.current() == 0:
            self.start_state = new_state
            self.draw_main_board(self.start_state)
            self.log_msg("Đã cập nhật trạng thái Ban Đầu.")
        else:
            self.goal_state = new_state
            self.log_msg("Đã cập nhật trạng thái Đích.")

    def log_msg(self, msg):
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.insert(tk.END, "\n> " + msg)
        self.txt_log.see(tk.END)
        self.txt_log.config(state=tk.DISABLED)

    def draw_main_board(self, state):
        # ĐÃ CẬP NHẬT: Vòng lặp duyệt mảng 1 chiều thay vì 2 chiều
        for i in range(9):
            val = state[i]
            bg_c = BG_TILE_EMPTY if val == 0 else BG_TILE
            self.main_tiles[i].config(text=str(val) if val != 0 else "", bg=bg_c)

        # Cập nhật tọa độ ô trống
        idx = state.index(0)
        row, col = divmod(idx, 3)
        self.lbl_empty.config(text=f"({row}, {col})")

    # --- LOGIC CHẠY THUẬT TOÁN ---
    def solve_puzzle(self):
        self.log_msg(f"Đang chạy thuật toán {self.algo_cb.get()}...")
        self.lbl_algo.config(text=self.algo_cb.get())
        self.lbl_result.config(text="Đang xử lý...", fg="#facc15")
        self.root.update()
        
        result = self.solver.solve(self.start_state, self.goal_state, self.algo_cb.get())
        
        if result["success"]:
            self.history = result["history"]
            self.current_step = 0
            self.lbl_result.config(text=f"Thành công ({result['time']} ms)", fg="#22c55e")
            self.log_msg(f"Tìm thấy đường đi! Tổng số Node duyệt: {len(self.history)}")
            self.update_status_panel()
        else:
            self.lbl_result.config(text="Thất bại", fg="#ef4444")
            self.log_msg("Không tìm thấy đường đi khả thi!")

    def update_status_panel(self):
        if not self.history: return
        step_data = self.history[self.current_step]
        self.lbl_step.config(text=f"{self.current_step + 1} / {len(self.history)}")
        self.lbl_action.config(text=step_data['node'].action if step_data['node'].action else "Start")
        self.draw_main_board(step_data['node'].state)

    def step_next(self):
        if self.history and self.current_step < len(self.history) - 1:
            self.current_step += 1
            self.update_status_panel()

    def step_prev(self):
        if self.history and self.current_step > 0:
            self.current_step -= 1
            self.update_status_panel()

    def play_auto(self):
        if not self.history: return
        if self.is_playing:
            self.is_playing = False
            self.btn_auto.config(text="↻ Tự động")
        else:
            self.is_playing = True
            self.btn_auto.config(text="⏸ Dừng")
            self._auto_loop()

    def _auto_loop(self):
        if self.is_playing and self.current_step < len(self.history) - 1:
            self.step_next()
            self.root.after(500, self._auto_loop)
        else:
            self.is_playing = False
            self.btn_auto.config(text="↻ Tự động")

    def reset_board(self):
        self.is_playing = False
        self.btn_auto.config(text="↻ Tự động")
        self.history = []
        self.current_step = 0
        self.draw_main_board(self.start_state)
        self.lbl_result.config(text="Chưa chạy", fg="#facc15")
        self.lbl_step.config(text="-")
        self.lbl_action.config(text="-")
        self.txt_log.config(state=tk.NORMAL)
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.insert(tk.END, "Nhật ký sẽ hiển thị ở đây.\nBạn có thể xem chi tiết quá trình tìm kiếm bằng nút bên trên.")
        self.txt_log.config(state=tk.DISABLED)

 # --- CỬA SỔ CHI TIẾT (BẢNG TRỰC QUAN GIỐNG 100% ẢNH MẪU) ---
    def open_details_window(self):
        if not self.history:
            messagebox.showinfo("Thông báo", "Vui lòng chạy thuật toán để sinh dữ liệu nhật ký trước!")
            return
            
        top = tk.Toplevel(self.root)
        top.title("Chi tiết quá trình (Node, Frontier, Reached)")
        top.geometry("1280x750") 
        top.configure(bg="#f8fafc") # Nền xám nhạt giống ảnh mẫu
        
        COL1_W = 100
        COL2_W = 460
        
        # Header (Đậm hơn một chút để phân biệt)
        header_frame = tk.Frame(top, bg="#cbd5e1", pady=8)
        header_frame.pack(fill=tk.X)
        
        h1 = tk.Frame(header_frame, width=COL1_W, bg="#cbd5e1")
        h1.pack(side=tk.LEFT, fill=tk.Y)
        h1.pack_propagate(False)
        tk.Label(h1, text="Node", bg="#cbd5e1", font=("Segoe UI", 10, "bold"), fg="#334155").pack(anchor="w", padx=15)

        h2 = tk.Frame(header_frame, width=COL2_W, bg="#cbd5e1")
        h2.pack(side=tk.LEFT, fill=tk.Y)
        h2.pack_propagate(False)
        tk.Label(h2, text="Frontier", bg="#cbd5e1", font=("Segoe UI", 10, "bold"), fg="#334155").pack(anchor="w", padx=10)

        h3 = tk.Frame(header_frame, bg="#cbd5e1")
        h3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(h3, text="Reached", bg="#cbd5e1", font=("Segoe UI", 10, "bold"), fg="#334155").pack(anchor="w", padx=10)

        # Canvas Cuộn
        canvas = tk.Canvas(top, bg="#f8fafc", highlightthickness=0)
        scrollbar = tk.Scrollbar(top, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f8fafc")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def draw_mini_board(parent, state):
            # Khung viền mỏng màu xám bao quanh ma trận con
            frame = tk.Frame(parent, bg="#94a3b8", bd=1)
            for i in range(3):
                for j in range(3):
                    val = state[i * 3 + j]
                    # Màu ô trống tối (đậm), ô có số màu xám sáng
                    bg_c = "#1e293b" if val == 0 else "#e2e8f0"
                    fg_c = "#1e293b" if val == 0 else "#0f172a"
                    # Ép kích thước gọn lại (width=2) giống hệt ảnh mẫu
                    tk.Label(frame, text=str(val) if val != 0 else "", width=2, height=1, font=("Arial", 7, "bold"), bg=bg_c, fg=fg_c).grid(row=i, column=j, padx=1, pady=1)
            return frame

        # Vẽ Dữ liệu
        for step_data in self.history:
            # Tạo hiệu ứng đường kẻ ngang phân cách giữa các Node (Bằng cách lồng Frame)
            row_wrapper = tk.Frame(scrollable_frame, bg="#cbd5e1") 
            row_wrapper.pack(fill=tk.X, pady=(0, 1)) # Đường kẻ dưới dày 1px
            
            row_frame = tk.Frame(row_wrapper, bg="#f1f5f9") # Màu nền của từng dòng
            row_frame.pack(fill=tk.X, padx=0, pady=(0, 1))

            # Cột 1: Node
            col1 = tk.Frame(row_frame, width=COL1_W, bg="#f1f5f9")
            col1.pack(side=tk.LEFT, fill=tk.Y)
            col1.pack_propagate(False)
            
            c1_inner = tk.Frame(col1, bg="#f1f5f9")
            c1_inner.pack(padx=15, pady=10, anchor="nw")
            
            node_lbl = f"Node {step_data['node'].node_id}"
            tk.Label(c1_inner, text=node_lbl, bg="#f1f5f9", font=("Segoe UI", 9, "bold"), fg="#2563eb").pack(anchor="w", pady=(0, 5))
            draw_mini_board(c1_inner, step_data['node'].state).pack(anchor="w")

            # Cột 2: Frontier
            col2 = tk.Frame(row_frame, width=COL2_W, bg="#f1f5f9")
            col2.pack(side=tk.LEFT, fill=tk.Y)
            col2.pack_propagate(False)
            
            c2_inner = tk.Frame(col2, bg="#f1f5f9")
            c2_inner.pack(padx=10, pady=10, anchor="nw")
            
            for item in step_data['frontier_added']:
                f_row = tk.Frame(c2_inner, bg="#f1f5f9")
                f_row.pack(anchor="w", pady=4) 
                
                # Dấu ngoặc nhọn mở
                tk.Label(f_row, text="{ ", bg="#f1f5f9", font=("Consolas", 11, "bold"), fg="#334155").pack(side=tk.LEFT)
                
                # Ma trận con
                draw_mini_board(f_row, item['state']).pack(side=tk.LEFT, padx=5)
                
                # Phần thông tin Parent, Action, Cost và Node trỏ tới
                action = item['action'] if item['action'] else " "
                parent = item['parent_id'] if item['parent_id'] else " "
                info_txt = f" ,  {parent}  ,  {action}  ,  {item['cost']}  }}  \u279D  Node {item['id']}"
                
                if item['is_goal']: info_txt += " \u2605" # Thêm icon ngôi sao nếu là Goal
                color = "#16a34a" if item['is_goal'] else "#334155"
                
                tk.Label(f_row, text=info_txt, bg="#f1f5f9", font=("Consolas", 9, "bold"), fg=color).pack(side=tk.LEFT)

            # Cột 3: Reached
            col3 = tk.Frame(row_frame, bg="#f1f5f9")
            col3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            c3_inner = tk.Frame(col3, bg="#f1f5f9")
            c3_inner.pack(padx=10, pady=10, anchor="nw")
            
            for idx, r_state in enumerate(step_data['reached']):
                mb = draw_mini_board(c3_inner, r_state)
                # Cho 6 ma trận nằm ngang 1 hàng (vì đã thu nhỏ ma trận)
                mb.grid(row=idx // 6, column=idx % 6, padx=3, pady=3)