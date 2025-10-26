# BOT_CHESS_BTL
Bài tập lớn môn **AIT2004 - Cơ sở trí tuệ nhân tạo**

---

## 📌 Giới thiệu
**BOT_CHESS_BTL** là một chương trình mô phỏng bàn cờ vua và triển khai các chức năng cơ bản của một "chess bot".  
Bàn cờ được biểu diễn bằng một **mảng 2D kích thước 8×8** theo quy tắc chuẩn quốc tế.  

---

## ♟️ Quy ước quân cờ
Mỗi quân cờ được biểu diễn dưới dạng **`xy`**:  

- `x`: loại quân cờ  
  - `K` → King (Vua)  
  - `Q` → Queen (Hậu)  
  - `R` → Rook (Xe)  
  - `B` → Bishop (Tượng)  
  - `N` → Knight (Mã)  
  - `P` → Pawn (Tốt)  

- `y`: màu quân cờ  
  - `w` → trắng (white)  
  - `b` → đen (black)  

### Ví dụ
- `Kw` → White King (Vua trắng)  
- `Qb` → Black Queen (Hậu đen)  
- `Pw` → White Pawn (Tốt trắng)  
- `Rb` → Black Rook (Xe đen)  

---

## 🏁 Bàn cờ ban đầu
Bàn cờ được khởi tạo theo quy tắc chuẩn quốc tế:

|   | a | b | c | d | e | f | g | h |
|---|---|---|---|---|---|---|---|---|
| 8 | Rb| Nb| Bb| Qb| Kb| Bb| Nb| Rb|
| 7 | Pb| Pb| Pb| Pb| Pb| Pb| Pb| Pb|
| 6 |   |   |   |   |   |   |   |   |
| 5 |   |   |   |   |   |   |   |   |
| 4 |   |   |   |   |   |   |   |   |
| 3 |   |   |   |   |   |   |   |   |
| 2 | Pw| Pw| Pw| Pw| Pw| Pw| Pw| Pw|
| 1 | Rw| Nw| Bw| Qw| Kw| Bw| Nw| Rw|

---

## ⚙️ Môi trường & Thư viện
- **Ngôn ngữ**: Python 3.12  
- **Môi trường ảo**: `venv`

### Các thư viện sử dụng
- [chess](https://docs.python.org/3/library/math.html) → interface cho quy luật đánh cờ
- 
Cài đặt các thư viện bằng `pip`:
```bash
pip install chess
```
🚀 Chạy chương trình
Tạo môi trường ảo:
```bash
python -m venv venv
```

Kích hoạt môi trường:
Windows:
```bash
venv\Scripts\activate
```
Linux/macOS:
```bash
source venv/bin/activate
```

Cài đặt thư viện cần thiết:
```bash
pip install -r requirements.txt
```
Chạy chương trình chính:
```bash
python main.py
```

🧩 Cấu trúc dự án
```bash
BOT_CHESS_BTL/
│── README.md              # Tài liệu mô tả dự án
│── requirements.txt       # Danh sách thư viện cần thiết
│── src/                   # Source code     
    │── init.py    
    │── constant.py            # Các hằng số hỗ trợ đánh giá giá trị bàn cờ
    │── board.py               # Xử lý bàn cờ
    │── evaluation.py          # Đánh gía giá trị bàn cờ
    │── search.py              # TÌm kiếm nước đi tốt nhất   
    │── Cerebellum3Merge.rar   # Tệp nén sách khai cuộc
│── bao_cao.docx           # Bản báo cáo
│── main.py                # Empty
│── ui.py                  # UI để dễ thao tác
└── ...
```
🎯 Mục tiêu
Biểu diễn bàn cờ vua 8×8 bằng Python.

Cài đặt quy tắc di chuyển cơ bản của từng quân cờ.

Xây dựng bot có khả năng:

Sinh nước đi hợp lệ.

Lựa chọn nước đi ngẫu nhiên hoặc theo heuristic đơn giản.

Ứng dụng các thư viện toán học để hỗ trợ tính toán & tối ưu hóa.

?  Cách sử dụng
Unzip Cerebellum3Merge.rar ngay tại src để tránh phải sửa path ở src/search.py

Chạy file ui.py

Lựa chọn Max depth và Time limit cho AI

Bấm Choose side, chọn bên