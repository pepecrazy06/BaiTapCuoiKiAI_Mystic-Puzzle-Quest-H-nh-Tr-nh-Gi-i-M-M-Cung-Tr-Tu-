# UTE Treasure Pathfinder AI — Python + HTML Version

Bản này đã chuyển từ JavaScript-only sang **Python + HTML**.

## Cấu trúc

```text
ute_treasure_pathfinder_python_html/
├── app.py
├── graph_data.py
├── search_algorithms.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── assets/
    │   └── ute_fantasy_map.png
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## Vai trò từng phần

- `app.py`: Python web server, cung cấp API cho frontend.
- `graph_data.py`: định nghĩa map, node, edge, waypoint và rule vật cản.
- `search_algorithms.py`: cài đặt BFS, DFS, IDS, UCS, Greedy, A*, Beam Search bằng Python.
- `templates/index.html`: giao diện HTML.
- `static/js/app.js`: chỉ xử lý giao diện, vẽ map, gọi API Python.
- `static/css/style.css`: giao diện game.

## Cách chạy

Không cần cài Flask. Chỉ cần Python 3.10+.

```bash
python app.py
```

Sau đó mở:

```text
http://127.0.0.1:8000
```

## Luật di chuyển

- Nhân vật chỉ đi qua node.
- Không đi xuyên qua nhà.
- Không đi xuyên qua tường.
- Không đi xuyên qua hồ.
- Không đi xuyên qua rừng.
- Gặp vật cản phải đi vòng theo hành lang hoặc node hợp lệ.

## Công cụ đánh node

Trong giao diện có mục **Công cụ đánh node**:

1. Bấm **Bật lấy tọa độ**.
2. Click vào đường đi trên map.
3. Copy tọa độ `x, y`.
4. Thêm node tạm lên map.
5. Xuất code node để dán vào `graph_data.py`.


## Cập nhật bản blank-coords

- Đã xóa tình trạng trùng Start/Goal do code tự vẽ khi chưa có tọa độ.
- Trong `graph_data.py` chỉ còn:
  - `S` là Start
  - `GOAL` là Goal
- Tọa độ `x`, `y` của Start/Goal đang để `None`.
- Bạn tự bật công cụ lấy tọa độ trên giao diện rồi điền lại vào `graph_data.py`.
- `EDGE_DATA` đang để trống để bạn tự nối node sau khi đánh node xong.

Ví dụ sau khi lấy tọa độ:

```python
NODES = {
    "S": {"name": "KTX D - Start", "x": 817.7, "y": 127.2, "kind": "start"},
    "GOAL": {"name": "Khối A.1 - Goal", "x": 742, "y": 792, "kind": "goal"},
    "N1": {"name": "Lối đi 1", "x": 700, "y": 250},
}

EDGE_DATA = [
    ("S", "N1"),
    ("N1", "GOAL"),
]
```


## Cập nhật map

- Đã thay ảnh nền map bằng ảnh mới bạn vừa gửi.
- Hiện tại **chưa đặt node nào cả** trên map.
- `graph_data.py` đang ở trạng thái template trống để bạn tự lấy tọa độ rồi thêm node sau.
- Khi mở app, map sẽ hiện đúng ảnh mới nhưng chưa có node/start/goal hiển thị cho đến khi bạn điền tọa độ.


## Cập nhật ảnh nền lần 2

- Đã thay ảnh nền bằng ảnh mới nhất bạn vừa gửi.
- Vẫn giữ trạng thái **chưa đặt node nào cả**.
- Vẫn chưa hiển thị Start/Goal trên map cho đến khi bạn tự điền tọa độ trong `graph_data.py`.


## Cập nhật autosave tọa độ

- Mỗi lần bật **Bật lấy tọa độ** và click lên map, tọa độ sẽ tự lưu vào `localStorage`.
- Không cần bấm copy từng điểm nữa.
- Trên map chỉ hiện mã `P01`, `P02`, ... để đỡ rối.
- Bấm **Xuất toàn bộ tọa độ đã click** để lấy lại toàn bộ danh sách.
- Bấm **Xóa lịch sử click** nếu muốn đánh lại từ đầu.


## Cập nhật halfmap_precise_runnable

- Đã nhập bộ tọa độ chính xác 1/2 map bạn vừa gửi.
- Đã đặt:
  - `S`: Start tại `(826.2, 170.5)`
  - `GOAL`: Goal tại `(729.7, 828.5)`
- Đã nối `EDGE_DATA` sơ bộ theo các tuyến:
  - tuyến chính từ Start xuống Goal,
  - tuyến cổng chính,
  - tuyến hầm ngục/khu E,
  - tuyến đài phun nước/khoa máy,
  - tuyến nhánh phải gần A4.
- Bản này chạy được thuật toán trước, sau đó có thể đánh thêm 1/2 map còn lại và nối thêm cạnh.
- Tổng node: 96
- Tổng cạnh: 101


## Hotfix hiển thị node/player/goal

- Đổi port chạy sang `8010` để tránh trình duyệt/server cũ ở port 8000.
- Mở đúng link: `http://127.0.0.1:8010`
- Node được làm lớn và sáng hơn.
- Khi tải graph sẽ hiện dòng `Đã tải graph: ... node / ... cạnh`.
- Nếu vẫn không thấy node, bấm `Ctrl + F5`.


## Cập nhật fullmap_runnable

- Đã thêm toàn bộ tọa độ phần còn lại bạn vừa gửi.
- Đã nối thêm `EDGE_DATA` sơ bộ cho các tuyến:
  - khu hầm ngục lớn / A.1 sang Khối G,
  - khu xưởng phải,
  - tuyến sân bóng / dịch vụ,
  - tuyến phòng thí nghiệm / căn tin,
  - hành lang thư viện - HSSV - y tế,
  - tuyến KTX phải.
- Tổng node hiện tại: 205
- Tổng cạnh hiện tại: 228
- Bản này vẫn chạy ở port `8010`.


## Bản cập nhật mới
- Thêm 2 node mới: `(1063.7, 462)` và `(1124, 469.9)`.
- Tắt và gỡ chức năng lấy tọa độ bằng click trên map.
- Node có chú thích/hàm tên chứa `hầm ngục` sẽ hiển thị màu tím.
- Goal có thêm icon kho báu.
- Nhân vật pixel được vẽ lại đẹp hơn.


## Cập nhật goal_gate_v3

- Thêm node mới `GATE_MID` tại `(775, 845.6)`.
- Muốn tới `GOAL`, nhân vật bắt buộc phải đi qua 1 trong 3 node:
  - `GATE_MID`: `(775, 845.6)`
  - `B09`: `(723.7, 864.6)`
  - `G04`: `(683.8, 835.3)`
- Đã xóa các cạnh nối thẳng vào `GOAL` từ những node khác.
- Ba node cổng vào Goal được tô màu vàng để dễ nhận biết.


## Cập nhật SA v4

- Thêm thuật toán `SA` / `Simulated Annealing` vào map chính.
- SA chạy trên graph node của map:
  - current state = node hiện tại
  - next state = node hàng xóm ngẫu nhiên
  - nếu tốt hơn thì nhận
  - nếu xấu hơn vẫn có thể nhận theo xác suất `exp(-Δ / T)`
  - nhiệt độ giảm dần `T = alpha * T`
- Giao diện đã có thêm nút `SA`.
- Bảng so sánh thuật toán đã có thêm dòng `SA`.


## Cập nhật Dungeon Mode v5

- Thêm **Hầm ngục sương mù tại node HGL02**.
- Mỗi lần bấm **Vào hầm ngục HGL02** hoặc **Sinh map hầm ngục mới**, backend sẽ sinh một dungeon graph ẩn mới.
- Frontend không nhận toàn bộ map hầm ngục.
- AI chỉ được quan sát:
  - phòng hiện tại,
  - các phòng kề bên có thể đi tiếp.
- Thuật toán dùng trong hầm ngục: **Online DFS**.
- AI vừa đi vừa khám phá, hết đường mới thì quay lui.
- Map hiển thị theo kiểu fog-of-war: chỉ hiện các phòng/cạnh đã khám phá.


## Cập nhật belief_dungeon_v6

- Khi route chính đi ngang qua node `HGL02`, game tự động mở hầm ngục sương mù.
- Mỗi lần vào hầm ngục, backend sinh một map ẩn mới.
- Trong hầm ngục, AI dùng **Belief State / No Observation**, không dùng Online DFS nữa.
- AI không biết chính xác đang ở phòng nào và không thấy toàn bộ bản đồ.
- AI giữ một tập niềm tin `belief` gồm các phòng có thể đang đứng.
- Sau mỗi hành động `N/E/S/W`, belief được cập nhật.
- Khi belief hội tụ về `{D_EXIT}`, AI chắc chắn đã tìm được lối ra.
- Sau khi thoát dungeon, nhân vật tiếp tục route chính về Goal.


## Cập nhật belief_dungeon_v6 - HGL02 tự kích hoạt

- Route A* về Goal đã được chỉnh để đi ngang qua `HGL02`.
- Khi nhân vật tới `HGL02`, game tự động mở hầm ngục sương mù.
- Mỗi lần vào hầm ngục, backend sinh một map ẩn mới.
- Trong hầm ngục, AI dùng **Belief State / No Observation**:
  - Không biết chắc đang ở phòng nào.
  - Không thấy toàn bộ map.
  - Chỉ giữ tập niềm tin `belief`.
  - Sau mỗi hành động `N/E/S/W`, belief được cập nhật.
  - Khi belief hội tụ về `{D_EXIT}`, AI chắc chắn đã thoát.
- Sau khi thoát hầm ngục, nhân vật tiếp tục route chính về Goal.


## Cập nhật dungeon_matrix8_v7

- Đã bỏ 2 khung `Dungeon Mode` bị lặp trên giao diện chính.
- Hầm ngục chỉ hiện dưới dạng overlay khi route đi ngang node `HGL02`.
- Map hầm ngục đổi sang ma trận **8×8**.
- Mỗi lần vào HGL02, backend sinh một session/map ẩn mới.
- AI dùng **Belief State / No Observation**:
  - Ban đầu belief = 64 ô.
  - AI không biết chính xác đang ở ô nào.
  - Sau mỗi hành động N/E/S/W, belief co lại.
  - Khi belief hội tụ về EXIT, AI thoát hầm ngục.


## Cập nhật andor_optional_m26_v9

- Không ép route A* phải đi qua `M26` nữa.
- Nếu thuật toán nào chọn route đi qua `M26`, game mới kích hoạt hầm ngục AND-OR.
- Hầm ngục M26 có nhiều lối thoát:
  - `EXIT_A`
  - `EXIT_B`
- Hầm ngục có bẫy:
  - nếu rơi vào `TRAP_ROOM`, hành động `RESET_TO_START` đưa nhân vật về `M26_START`.
- AND-OR Search sẽ chọn kế hoạch điều kiện đảm bảo xử lý mọi kết quả có thể xảy ra.
- Hầm ngục HGL02 8×8 vẫn tự đóng sau khi belief hội tụ và thoát thành công.


## Cập nhật v10

- Thêm node mới `N_DUN_LINK` tại `(391.4, 799.5)`.
- Node này được nối với `C10` và `DUN03` để hỗ trợ đường đi khu hầm ngục bên trái.
- Sửa rule màu tím:
  - Chỉ 3 node sau có màu tím: `DUN02`, `HGL02`, `FB04`.
  - Các node khác dù tên có chữ "hầm ngục" cũng không tự động tím nữa.


## Cập nhật purple_required_v11

- Quy định rule mới: rương ở `GOAL` chỉ mở nếu route đã đi qua đủ 3 node tím:
  - `DUN02`
  - `HGL02`
  - `FB04`
- Hiện tại chưa cần đưa map hầm ngục đầy đủ vào các node tím.
- Các node tím tạm thời đóng vai trò như 3 chìa khóa / 3 cổng điều kiện.
- Khi route đi qua node tím, node đó sẽ đổi sang màu vàng để báo đã kích hoạt.
- Nếu tới Goal mà thiếu node tím, rương hiện `LOCKED` và không chạy hiệu ứng mở kho báu.


## Cập nhật purple_multigoal_v12

- Sửa đúng bài toán chính:
  - Không còn tìm thẳng `S -> GOAL`.
  - Thuật toán phải tìm route: `S -> đi qua đủ DUN02, HGL02, FB04 -> GOAL`.
- Vì có 3 node tím, backend thử tất cả thứ tự checkpoint và chọn route có tổng chi phí tốt nhất.
- Mỗi đoạn giữa 2 checkpoint vẫn dùng đúng thuật toán người chơi chọn:
  - BFS / DFS / IDS / UCS / Greedy / A* / Beam / SA.
- Khi đi qua node tím, node đổi sang màu vàng.
- Chỉ khi đã qua đủ 3 node tím và quay về `GOAL`, rương mới mở.


## Cập nhật DUN02 Backtracking + Forward Checking

- Thêm hầm ngục mới tại node `DUN02`.
- Khi nhân vật đi ngang `DUN02`, game tự chuyển sang map hầm ngục riêng bằng ảnh dungeon được cung cấp.
- Trong DUN02:
  - Start là `DS`.
  - Chìa khóa đặt tại `KEY`, ở ô lục giác phía dưới bên phải.
  - EXIT chỉ hợp lệ sau khi AI đã lấy chìa khóa.
  - Có các nhánh vật cản/ngõ cụt như `W2`, `P1`, `P2`.
- Thuật toán dùng: **Backtracking + Forward Checking**.
  - Backtracking: thử nhánh, nếu sai thì quay lui.
  - Forward checking: cắt sớm nhánh ngõ cụt, trạng thái lặp, hoặc EXIT khi chưa có chìa khóa.
- Sau khi thoát DUN02, overlay tự đóng và nhân vật tiếp tục route chính tới node tím khác rồi tới Goal.

### API mới

- `GET /api/dun02/new`
- `POST /api/dun02/solve`


## Cập nhật DUN02 Node Editor v13

- Trong overlay DUN02 có thêm chế độ **tự đánh node**.
- Các chức năng mới:
  - Bật/tắt đánh node.
  - Click trực tiếp lên map hầm ngục để thêm node.
  - Chọn loại node: thường, Start, Key, Exit, vật cản, ngõ cụt.
  - Chọn 2 node rồi bấm nối cạnh.
  - Xóa node mẫu để tự vẽ map từ đầu.
  - Undo node.
  - Xuất code nodes/edges.
  - Chạy Backtracking + Forward Checking trên map tự đánh.
- Backend có API mới:
  - `POST /api/dun02/solve_custom`


## Cập nhật HGL02 Belief Editor v14

- Bỏ hầm ngục HGL02 dạng ma trận 8x8.
- Thay bằng ảnh map hầm ngục mới: `static/assets/hgl02_belief_dungeon_map.png`.
- Có thể click trực tiếp node `HGL02` trên map chính để mở hầm ngục.
- Khi route chính đi ngang `HGL02`, hầm ngục cũng tự mở như trước.
- Trong HGL02 có chế độ tự đánh node:
  - Bật/tắt đánh node.
  - Click lên map để thêm node.
  - Chọn loại node: thường, Start, Exit, vật cản, ngõ cụt.
  - Chọn 2 node rồi nối cạnh.
  - Xóa node mẫu / Undo node / Xuất code.
  - Chạy Belief State trên map tự đánh.
- Belief State:
  - Belief ban đầu gồm tất cả node loại `start`.
  - Action là `N/E/S/W`.
  - Backend tự suy ra hướng đi từ tọa độ các cạnh bạn nối.
  - Khi belief còn đúng Exit, AI thoát hầm ngục.


## Cập nhật HGL02 blank editor v15

- HGL02 không còn node mẫu.
- Khi click vào node `HGL02` hoặc route đi ngang `HGL02`, overlay chỉ mở map hầm ngục trống.
- Không tự chạy Belief State khi mới vào HGL02.
- Người dùng tự đánh node/cạnh trước:
  - đặt Start,
  - đặt Exit,
  - đặt node thường/vật cản/ngõ cụt,
  - nối cạnh.
- Sau khi tự đánh xong mới bấm **Chạy Belief State**.


## Cập nhật v16
- DUN02 nay hoạt động tương tự HGL02: click node tím DUN02 để mở hầm ngục trống và tự đánh node.
- Có thêm các loại node cho DUN02: Start, Key, Exit, Node thường, Vật cản, Ngõ cụt, Bẫy, Ngã ba/Ngã tư, Hành lang, Checkpoint.
- Forward checking sẽ prune vật cản, bẫy, EXIT khi chưa có key, trạng thái lặp và nhánh không còn nước đi hợp lệ.


## Cập nhật v17 - HGL02 fixed nodes

- Đã đưa toàn bộ tọa độ HGL02 từ file người dùng cung cấp vào code.
- HGL02 dùng map cố định:
  - `H01` là node bắt đầu.
  - `H56` là node kết thúc.
  - Tổng cộng 106 node và 107 cạnh.
- Đã xóa phần chỉnh sửa node ở HGL02 khỏi giao diện.
- HGL02 chỉ còn nút:
  - `Chạy Belief State HGL02`
  - `Làm mới hiển thị`
- DUN02 vẫn giữ chế độ tự đánh node và các loại node phục vụ Backtracking + Forward Checking.


## Cập nhật v18 - HGL02 AND-OR Search

- HGL02 đổi từ Belief State sang **AND-OR Search**.
- Start trong hầm ngục: `H01`.
- Goal mới trong hầm ngục: `H58` thay vì `H56`.
- Đã ẩn node kỹ thuật và đường nối trong hầm ngục HGL02.
- Nhân vật xuất hiện trong hầm ngục và di chuyển theo node do AND-OR Search tìm được.
- DUN02 vẫn giữ chế độ edit node cho Backtracking + Forward Checking.


## Cập nhật v19

- Đã thay ảnh map hầm ngục **HGL02** bằng ảnh mới người dùng cung cấp.
- Đã giữ HGL02 ở chế độ **AND-OR Search**, goal vẫn là **H58**.
- Đã chỉnh lại **DUN02 editor** để dễ tự thêm node hơn: mở sẵn chế độ edit, có hướng dẫn click trực tiếp lên map, hỗ trợ click/pointerdown để tạo node, và xuất code tự copy vào clipboard khi có thể.
- DUN02 vẫn dùng logic **Backtracking + Forward Checking** cho map tự đánh.



## Ghi chú bản này

Đã xóa toàn bộ hầm ngục riêng của DUN02. DUN02 chỉ còn là node trên map chính, không mở popup và không chạy thuật toán hầm ngục riêng.



## DUN02 dungeon

DUN02 đã được đổi sang ảnh hầm ngục mới `static/assets/dun02_dungeon_map.png`.
Thuật toán trong DUN02 là **Backtracking + Forward Checking**:
- Start: `DS`
- Key: `KEY`
- Exit: `EXIT`
- Forward Checking cắt bẫy, vật cản, EXIT khi chưa có KEY và trạng thái lặp.



## DUN02 v20

DUN02 đã được sửa theo 3 yêu cầu:
- Hiện node và cạnh trên ảnh để thấy đường đi của nhân vật.
- Popup DUN02 tự fit theo màn hình.
- Có chế độ chỉnh đường đi: bật chỉnh node, thêm node, nối 2 node, chạy theo map đang chỉnh và xuất code.


## DUN02 v24 - Fixed coordinates + Backtracking Forward Checking

DUN02 đã xóa chế độ chỉnh node thủ công trong UI.
Map DUN02 đã cố định theo tọa độ người dùng gửi:
- Số node: 54
- Số cạnh: 55
- Start: DS
- Key: KEY
- Exit: EXIT
- Trap: U51

Thuật toán Backtracking + Forward Checking đã được mở lại cho DUN02.


## Sửa FB04 Belief State + BFS Editor

- Đã sửa đúng node hầm ngục sân bóng là `FB04`, không phải `FB03`.
- `PURPLE_REQUIRED_NODES = ["DUN02", "HGL02", "FB04"]`.
- Hầm ngục FB04 dùng ảnh `static/assets/fb04_belief_dungeon_map.png`.
- FB04 không có node mẫu cố định.
- Khi vào FB04, người dùng tự đánh node:
  - đặt nhiều Start để tạo belief ban đầu,
  - đặt Exit,
  - nối cạnh,
  - chạy Belief State + BFS.
- BFS chỉ áp dụng trong hầm ngục FB04, không ảnh hưởng HGL02/DUN02.


## Hotfix FB04 editor v26

- Thêm hiển thị node đang chọn.
- Thêm nút đặt node đã chọn làm Start.
- Thêm nút đặt node đã chọn làm Exit.
- Thêm nút đổi node đã chọn về Hành lang.
- Ô export giờ hiển thị rõ danh sách tọa độ đã đặt trước phần code.


## v27 FB04 panel force visible

Sửa lỗi panel FB04 không hiện dù code đã thêm:
- ép hiển thị #fb04EditPanel khi overlay có class fb04-mode,
- thêm toggle trực tiếp trong setDungeonOverlayMode(),
- thêm nút Start/Exit/Hành lang và danh sách tọa độ đã đặt.

## v28 FB04 fixed Belief BFS

- Đã đưa bộ node FB04 người dùng đánh vào code, xóa B50.
- Start belief: B01, B25, B38.
- Exit: B55.
- Thiết kế route bắt buộc đi qua B51 -> B52 -> B53 -> B54 -> B55.
- Khi chạy thật, node kỹ thuật được ẩn bằng dấu ? và hiệu ứng sương mù.
- FB04 chạy bằng Belief State + BFS.


## v29 FB04 Belief BFS - Cách 2

- Mỗi lần vào FB04, hệ thống chọn ngẫu nhiên 1 Start thật trong tập belief.
- Tập belief ban đầu vẫn gồm nhiều Start, nên thuật toán vẫn là Belief State + BFS.
- Khi chạy thật:
  - không hiện dấu `?`,
  - thay bằng hiệu ứng sương mù,
  - chỉ có 1 nhân vật thật di chuyển theo đường đi tương ứng với Start thật được chọn.


## v33 FB04 way2 run-only UI
- Giữ cách 2: random 1 Start thật trong 3 Start của FB04.
- Bỏ toàn bộ nút / panel chỉnh belief không cần thiết.
- Chỉ chừa lại nút **Chạy thuật toán hầm ngục** giống 2 hầm ngục trước.


## v34 FB04 fix player

- Sửa lỗi `drawFb04PlayerAt is not defined`.
- FB04 run-only UI vẫn giữ cách 2: random 1 Start thật trong 3 Start.


## v35 fix HGL02 accidental variables

- Xóa `actual_start` và `actual_path` khỏi return của HGL02 custom belief.
- Hai biến này chỉ dùng cho FB04 cách 2 random Start.
- FB04 vẫn giữ random 1 trong 3 Start và giao diện chỉ còn nút chạy thuật toán.


## v36 FB04 only actual character moves

- Sửa FB04 để khi chạy thật chỉ có 1 nhân vật thật di chuyển.
- Belief marker / dấu ? / sương mù không còn chạy theo từng bước.
- Belief BFS vẫn tính trong nền.
- Log không hiện toàn RIGHT nữa, mà hiện dạng di chuyển node thực tế: B01 → B02...


## v37 FB04 actual + belief display

- Sửa FB04 theo cách đúng để bảo vệ lý thuyết:
  - 1 nhân vật thật di chuyển.
  - Dấu ? mờ biểu diễn belief state.
  - Log ghi cả Actual và Belief.
- Dấu ? không phải nhân vật, chỉ là các vị trí AI đang nghi ngờ.
- Belief BFS vẫn chạy trên tập belief và hội tụ về {B55}.


## v38 FB04 dynamic route display
- Xóa đường route vẽ sẵn trên map FB04.
- Khi chạy: đường xanh được vẽ theo actual path của nhân vật thật.
- Đường tím đứt được vẽ theo sự dịch chuyển của các dấu ? trong belief state.
- Hai lớp đường màu khác nhau để dễ giải thích quá trình cho giảng viên.


## Final Boss Minimax Tactical Puzzle

- Thêm màn Boss cuối dạng tactical puzzle 4x4.
- Knight là MAX, Dragon là MIN.
- Rồng dùng Minimax độ sâu 3 để chọn ô phun lửa.
- Knight cần đi tới ô Dragon để lấy kho báu.
- Ô bị phun lửa biến thành dung nham và không thể đi qua.
- Boss mở khi route chính đi tới GOAL/kho báu.


## vBoss map image + dragon fire
- Đổi màn Boss cuối sang dùng ảnh đấu trường 5x5 người dùng cung cấp.
- Grid tương tác được đặt đè đúng lên ma trận A-E / 1-5 trên ảnh.
- Thêm rồng ở tổ lửa phía trên, và hiệu ứng fireball bay từ rồng đến ô bị đốt.
- Knight khởi đầu tại E3, mục tiêu là ô A3 ngay dưới tổ rồng.


## Boss fix - dùng map có rồng sẵn

- Đổi sang ảnh boss mới có rồng nằm sẵn trong đấu trường.
- Bỏ emoji/con rồng chèn thêm trên HTML.
- Chỉ giữ hiệu ứng ô: valid move, dung nham, impact.
- Fireball bay từ vị trí miệng rồng trong ảnh tới ô bị Minimax chọn.
- Sửa lỗi backend /api/boss/step do route boss dùng query trước khi khai báo.


## Boss API route fix v4
- Sửa `/api/boss/new` và `/api/boss/step` cho server đang dùng `path = unquote(self.path.split(...))`.
- Lỗi `Unexpected token '<'` là do server cũ trả HTML thay vì JSON.
- Sau khi giải nén bản này, cần tắt server đang chạy và chạy lại `python app.py`.


## Boss quick test

- Có thể click trực tiếp vào node `GOAL` / kho báu trên map chính để mở màn Boss Minimax.
- Không cần chạy lại toàn bộ đường đi trước đó.


## Boss balanced difficulty

- Giảm Minimax depth từ 3 xuống 2.
- Thêm protected path E3 -> D3 -> C3 -> B3 -> A3 để demo có thể thắng.
- Rồng vẫn dùng Minimax, nhưng không được đốt trực tiếp tuyến thắng chính.
- Lý do: nếu để Minimax tối ưu tuyệt đối, rồng sẽ dồn người chơi thua quá nhanh, không phù hợp bản demo.


## 2026-06 patch
- Boss: đổi hiệu ứng lửa sang kiểu pixel-art và ô cháy sang mảng cháy theo phối cảnh, không còn là ô vuông full cell.
- FB04: khi mở từ route chính, route sẽ dừng ở cửa sân bóng; chỉ sau khi chạy xong/đóng hầm ngục mới tiếp tục sang node kế tiếp.


## Algorithm update

- Đã bỏ Beam Search khỏi danh sách thuật toán map chính.
- Simulated Annealing được giữ làm thuật toán local search chính để thay Beam.
- Nếu frontend/browser cũ còn gửi `beam`, backend sẽ chuyển an toàn sang `simulated_annealing`.


Final: Beam Search đã được bỏ khỏi code chạy và UI. Map chính dùng Simulated Annealing thay thế.


## Added Hill Climbing

- Thêm Hill Climbing Search vào map chính.
- Beam Search vẫn đã bị bỏ.
- Map chính hiện có: BFS, DFS, IDS, UCS, Greedy, A*, Hill Climbing, Simulated Annealing.
- Hill Climbing dùng heuristic khoảng cách đến goal, luôn chọn hàng xóm tốt nhất.
- Dễ giải thích cùng Simulated Annealing: Hill Climbing dễ kẹt local optimum, SA có cơ chế thoát kẹt.


## Fix: AND-OR function alias

- Sửa lỗi JS: `triggerAndorDungeonFromMainRoute is not defined`.
- Khi route chính đi tới node M26, hàm alias sẽ mở đúng hầm AND-OR/HGL02.
- Giữ Hill Climbing, Simulated Annealing, Boss pixel fire và FB04 pause fix.


## Remove M26 dungeon trigger

- Đã xóa trigger hầm ngục ở node M26.
- M26 chỉ còn là node đường đi bình thường.
- Hầm ngục chỉ tự mở ở các node tím đúng: DUN02, HGL02, FB04.
- Số trigger M26 đã xóa: 1.


## Fix HGL02 route pause

- Sửa lỗi vào HGL02 xong route nền tự chạy tiếp và nhảy sang màn kế tiếp.
- HGL02 giờ hoạt động giống FB04: route chính dừng lại ở HGL02, chạy xong/đóng overlay mới quay lại map chính rồi đi tiếp.
- M26 vẫn là node thường, không mở hầm.


## Final QC passed

Đã kiểm tra bản này:

- JS syntax: OK
- Python compile: OK
- Map chính: BFS, DFS, IDS, UCS, Greedy, A*, Hill Climbing, Simulated Annealing đều chạy không lỗi và tìm được route.
- DUN02: Backtracking + Forward Checking chạy OK.
- HGL02: AND-OR Search chạy OK.
- FB04: Belief State + BFS chạy OK.
- Boss: Minimax chạy OK.
- M26 không còn mở hầm.
- HGL02 và FB04 đều có pause/resume, không tự nhảy sang màn kế tiếp.


## Route replay/duplicate animation fix

- Sửa lỗi thỉnh thoảng nhân vật đã tới GOAL nhưng lại chạy lại từ START.
- Nguyên nhân không phải mạng yếu mà do JS async bị gọi chồng khi bấm nút trong lúc animation đang chạy hoặc vừa kết thúc.
- Thêm route lock: trong lúc route đang chạy sẽ khóa nút thuật toán/chạy/di chuyển.
- Khi đã tới GOAL, nút di chuyển không replay lại từ đầu; muốn chạy lại thì bấm Đặt lại hoặc chọn thuật toán rồi Tìm đường lại.


## Fix runToken scope

- Sửa lỗi `runToken is not defined`.
- Viết lại route lock theo dạng try/finally để biến runToken luôn nằm đúng scope.
- Giữ cơ chế chống chạy chồng animation.


## Simple route lock fix

- Bỏ hoàn toàn cơ chế `runToken` để tránh lỗi `runToken is not defined`.
- Dùng khóa đơn giản `routeLocked` + `animatingPlayer`.
- Khi route đang chạy thì không cho bấm chồng.
- Khi đã tới GOAL thì không tự replay lại từ START.


## Final no runToken patch
- Đã xóa sạch mọi tham chiếu `runToken/routeRunToken` trong JS để tránh lỗi scope.
- JS syntax OK, Python compile OK.


## IDS visited animation fix

- IDS tìm được đường nhưng có thể duyệt hơn 70.000 trạng thái.
- Giao diện cũ vẽ từng visited node nên nhân vật nhìn như đứng im rất lâu.
- Bản này giới hạn preview visited node tối đa 650 node.
- Route vẫn giữ nguyên, nhân vật sẽ di chuyển ngay sau khi preview ngắn.


## IDS fast move fix

- IDS/IDDFS không còn vẽ 650 node visited nữa.
- Nếu IDS duyệt quá nhiều trạng thái, UI chỉ preview tối đa 80 node.
- Sau đó vẽ route và cho nhân vật di chuyển ngay, tránh cảm giác đứng im ở START.
