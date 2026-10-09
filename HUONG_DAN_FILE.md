# Bản đồ file của project Pickleball AI

Project có 2 phần tách biệt:

- **Phần A – Web Dink Radar** (bản đang dùng): chọn video là tự phân tích, chạy trong trình duyệt.
- **Phần B – Pipeline Python trong WSL** (bản cũ): chạy bằng lệnh `./chay_phan_tich.sh`, xuất ra `output.json`.

Muốn chỉnh giao diện hoặc cách phân tích của web thì **chỉ cần mở Phần A**.

---

## Phần A – Web Dink Radar

**Thư mục trên máy:** `C:\Users\tamki\Downloads\pickleball_ai_run\dink_radar_web\`
**Link online:** https://claude.ai/artifact/WjvJ3nSz9RoEGJP4W2iYRK

| File | Địa chỉ đầy đủ | Công dụng | Có nên sửa không |
|---|---|---|---|
| `index.html` | `...\dink_radar_web\index.html` | **Toàn bộ web nằm trong file này**: giao diện, màu sắc, tìm sân, khung xương, bóng, chấm điểm. | **Có.** Đây là file duy nhất cần sửa. |
| `XEM_THU.bat` | `...\dink_radar_web\XEM_THU.bat` | Double-click để mở web trên máy (`http://localhost:8000`) và xem thử sau khi sửa. | Không |
| `HUONG_DAN_FILE.md` | `...\dink_radar_web\HUONG_DAN_FILE.md` | File bạn đang đọc. | Không |
| `sample_clip80.json` | `...\dink_radar_web\sample_clip80.json` | Dữ liệu trận mẫu, hiện ra khi vừa mở web. | Không |
| `mp\pose_model.wasm` | `...\dink_radar_web\mp\pose_model.wasm` | Mô hình AI nhận khung xương (MediaPipe Pose, bản *full*). Đuôi `.wasm` chỉ để trang web tải được. | **Không được sửa** |
| `mp\vision_wasm_internal.wasm` | `...\dink_radar_web\mp\vision_wasm_internal.wasm` | Bộ máy chạy mô hình AI trong trình duyệt. | **Không được sửa** |

### Trong `index.html`, cần sửa gì thì tìm ở đâu

Trong VS Code, bấm **Ctrl+G** rồi gõ số dòng để nhảy tới, hoặc **Ctrl+F** để tìm theo tên.

| Muốn chỉnh | Tìm (Ctrl+F) | Dòng (khoảng) | Ghi chú |
|---|---|---|---|
| **4 chấm góc sân tự tìm bị lệch** | `function detectCourt` | 1385 | Hàm tìm sân tự động. Số `70` ở dòng 1391 là độ "dễ tính" khi so màu sân: tăng lên nếu sân bị thiếu góc, giảm xuống nếu sân bị lấn ra ngoài. Cách nhanh hơn, không cần sửa code: bấm nút **ADJUST COURT** rồi kéo 4 chấm. |
| Vùng phóng to để bắt người ở xa và người ở gần | `function courtCrops` | 1544 | Chia sân thành 4 góc để AI tìm người. |
| Màu bóng (đang là vàng chanh/cam neon) | `hdeg >= 44 && hdeg <= 90` | 1493 | Dải màu tính bằng độ (0–360). |
| Bộ dò bóng (cỡ bóng, độ nhảy tối đa) | `class BallTracker` | 1463 | |
| Màu của P1–P4 | `const PCOL` | 372 | Mã màu hex. |
| Trọng số chấm điểm MVP | `const W_DIST` | 378 | Đang là 40% quãng đường, 35% tốc độ, 25% số cú đánh. |
| Cách tính tốc độ bóng | `function computeSpeeds` | 531 | |
| Gán P1–P4 (đội gần, đội xa) | `function reassignIds` | 479 | |
| Vùng sân (Kitchen / Transition / Baseline) | `function zoneOf` | 654 | |
| Kiểu vẽ khung xương | `function drawSkeleton` | 847 | Độ dày nét, độ phát sáng. |
| Nhãn trên đầu người chơi | `function drawTag` | 882 | |
| Bảng radar sân nhỏ | `function drawRadar` | 961 | |
| Độ phân giải khi phân tích | `1280 / av.videoWidth` | 1599 | Giảm xuống thì phân tích nhanh hơn nhưng kém chính xác hơn. |
| Màu nền, font chữ toàn trang | `:root{` | 16 | Các biến `--bg`, `--accent`… |
| Tên web, logo | `class="brand"` | 222 | |

Số dòng sẽ xê dịch sau khi bạn sửa, nên ưu tiên tìm theo tên.

### Quy trình sửa bằng vibe code

1. Mở thư mục `dink_radar_web` trong VS Code (**File → Open Folder**).
2. Nhờ AI trong VS Code sửa `index.html`. Ví dụ: "trong function detectCourt, làm cho 4 góc sân bám sát vạch trắng hơn".
3. Double-click `XEM_THU.bat`, Chrome sẽ mở `http://localhost:8000`. Chọn video để thử. Nếu bạn cài extension **Live Server** thì có thể dùng nó thay cho file `.bat`.
4. Khi đã ưng, gửi file `index.html` cho Claude và nhờ cập nhật lên link online. Link sẽ giữ nguyên.

**Lưu ý:** đừng mở `index.html` bằng cách double-click trực tiếp. Mở kiểu đó, trình duyệt sẽ không cho tải mô hình AI. Luôn mở qua `XEM_THU.bat` hoặc Live Server.

---

## Phần B – Pipeline Python trong WSL (bản cũ)

**Thư mục chạy chính:** `\\wsl.localhost\Ubuntu\home\tamki\pickleball_ai\pickleball_ai\`
(Trong Ubuntu là `~/pickleball_ai/pickleball_ai`. Mở bằng VS Code: trong Ubuntu gõ `code .`)

| File / thư mục | Công dụng |
|---|---|
| `chay_phan_tich.sh` | Chạy toàn bộ phân tích bằng 1 lệnh. |
| `analyze.py` | Chương trình chính, xuất ra `output.json`. |
| `pipeline\ball.py` | Dò bóng bằng màu và bộ lọc Kalman. |
| `pipeline\pose.py` | Lấy khung xương (MediaPipe) và phóng to nửa sân xa. |
| `pipeline\player_ids.py` | Gán P1–P4 theo đội gần và đội xa. |
| `pipeline\calibrate.py` | Đổi pixel sang mét và tính tốc độ bóng. |
| `pipeline\scoring.py` | Chấm điểm và chọn MVP. |
| `pipeline\scene.py` | Bỏ qua cảnh replay và cảnh cận. |
| `tools\pick_corners.py` | Cửa sổ để click tay 4 góc sân. |
| `tools\render_overlay.py` | Vẽ kết quả lên video. |
| `tools\rescore.py` | Chấm điểm lại mà không cần chạy lại khung xương. |
| `tools\tune_ball_color.py` | Chỉnh màu bóng bằng thanh trượt. |
| `viewer\` | Trang xem kết quả bản cũ. Web Dink Radar đã thay thế phần này. |
| `models\pose_landmarker_full.task` | Mô hình AI khung xương (cùng mô hình với web). |
| `ket_qua\<tên video>\` | Kết quả mỗi lần chạy: `output.json`, `corners.json`, `video.mp4`, `ket_qua_overlay.mp4`, `run_log.txt`. |
| `CLAUDE.md` | Ghi chú cho AI khi sửa code. |
| `.venv\` | Môi trường Python. **Không được sửa.** |

**Bản sao dự phòng:** `C:\Users\tamki\Downloads\pickleball_ai_run\pickleball_ai_fixed\` chứa cùng các file trên. Bản chạy thật là bản trong WSL.

---

## File có thể xoá

| Địa chỉ | Lý do |
|---|---|
| `C:\Users\tamki\Downloads\pickleball_ai_run\web_hud\` (cả thư mục) | File tạm Claude dùng để chuyển dữ liệu, cùng bản HTML cũ không còn dùng. |
| `C:\Users\tamki\raw\zFwYJpRG95U.*` và `PPA_Chicago_Cup_1733.mp4` | Video gốc tải về (khoảng 1 GB). Chỉ xoá nếu bạn không cần dùng lại. |

Các file còn lại trong `C:\Users\tamki\Downloads\pickleball_ai_run\` là kết quả của lần chạy `clip80`: `clip80.mp4`, `output.json`, `ket_qua_overlay.mp4`, `run_log.txt`, `pickleball_ai_ket_qua.xlsx`, `overlay_preview.jpg`, `ball_check.jpg`. Giữ lại để xem lại thì tốt, xoá đi cũng không ảnh hưởng gì đến web.
