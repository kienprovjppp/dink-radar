# Rally B · PPA Chicago Cup — trạng thái phiên làm việc

**Trang tương tác (riêng tư):** https://claude.ai/artifact/5ewsNu7BQSqZeeTtQZLNvM
**Video nguồn:** GitHub Release `rally-video`, file `PPA.-.Trim.mp4`. Rally B nằm ở đoạn 0:38.21 đến 0:58.41 (20,2 giây).

## Đã xong

| Bước | Kết quả | File |
|---|---|---|
| 1. Chuẩn bị | Cắt rally B. Camera đứng yên (lệch < 0,1 px). Video gốc 29,97 fps: đo trên frame gốc rồi nội suy lên 60 fps | `page/rally.mp4`, `page/rally.webm` |
| 4. Sân | 4 góc fit từ vạch trắng; kitchen, đường giữa và lưới khớp ảnh | `court.json`, `checks/court_check_crop.png` |
| 3. Bóng | Dò ứng viên + beam search: 437/606 frame, không đoạn nào bị kẹt | `ball_raw.json`, `ball_nat.json` |
| 5. Người chơi | 4 khung xương, gán theo màu áo + bên sân, quét lưới khi mất dấu, bước refine lấp khoảng trống: P1 97%, P2 95%, P3 100%, P4 100% | `pose.npz`, `checks/pose_check.jpg` |
| 2 + 6. Cú đánh | 46 ứng viên (tiếng + bóng đổi hướng), 8 agent kiểm chứng trên ảnh, 16 cú đánh + 13 lần nảy | `strikes_nat.json`, `strike_verification.json` |
| 7. Điểm | P1 83 · P2 73 · P4 62 · P3 62 | `prep.json` |
| 8. Trang | Lớp phủ, bảng bên phải, timeline, thẻ báo cáo cuối, báo cáo viết tiếng Việt | `page/`, `texts.json` |

## Chưa làm (dừng theo yêu cầu)

1. **Quay video MP4 60 fps** (bước 8):
   ```bash
   node rallyscope/scripts/record.mjs rallyscope/runs/ppa_trim_rally_b/page out.mp4
   ffmpeg -i out.mp4 -i <rally B cắt từ video gốc, có tiếng> -filter_complex "[1:a]apad[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -shortest final.mp4
   ```
2. **Kiểm tra bước 9 đầy đủ**: chụp màn hình lúc giao bóng, một cú phía xa, một cú phía gần, cú cuối và thẻ báo cáo (`node rallyscope/scripts/shots.mjs <page> qa 0.9 6.1 9.2 17.7 end+4`), rồi so 3 frame của MP4 với trang.

## Những điều cần biết khi làm tiếp

- Tiếng trong bản phát sóng trễ hình khoảng 2–3 frame, nên thời điểm chạm bóng được đọc từ hình.
- Bóng trong video không có viền tối, nên `ball_viterbi.py cands` chạy với `--chan yellow` (độ vàng của bóng).
- Hệ số chiều cao người theo phối cảnh của camera này là `--kh 0.25` (quy trình gốc dùng 0.42 cho camera khác).
- P2 mất khung xương khoảng 1 giây khi lao người (frame gốc 260–284). Trang hiển thị là "POSE LOST".
- Vị trí 5 lần nảy bị che được ước lượng từ đường bay (các mục dạng `[frame, x, y]` trong `strikes_nat.json`).

## Chạy lại từ dữ liệu đã lưu

```bash
python rallyscope/scripts/resample.py ball_nat.json pose.npz strikes_nat.json --src-fps 29.97 --frames 1212 --out-dir .
python rallyscope/scripts/prep.py court.json ball60.json strikes60.json pose60.npz prep.json --end 1101
python rallyscope/scripts/finalize.py build prep.json texts.json page/data.json --video page/rally.mp4
```
