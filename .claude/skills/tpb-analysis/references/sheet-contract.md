# Hợp đồng cột với Google Sheet

Sheet `1z4DhdV41EQa9eAi3-L6Hg4oRl4igtuc5Iz5wIMXAvJA`, tab `TPB Stock Monitor`.

## Ranh giới sở hữu

| Vùng | Ai ghi | Nội dung |
|---|---|---|
| `L1` / `M1` | **người dùng** | nhãn `Holding AVG Price` / giá vốn bình quân (VND) |
| `L2` / `M2` | **người dùng** | nhãn `Holding Volume` / khối lượng, `0` nếu đứng ngoài |
| `A` | kẻ sẵn | ngày phiên — khoá để tìm dòng |
| `B`–`I` | **skill** | nhật ký, xem bảng dưới |
| `J` | công thức sheet | `=(B{row}-$M$1)*$M$2` |

Skill **không bao giờ** ghi vào L, M hay J. Ràng buộc này nằm trong `Code.gs` chứ không phụ
thuộc Claude nhớ: ghi bắt đầu từ cột B (`FIRST_WRITE_COL = 2`) và dài đúng 8 cột.

Số tiền lãi/lỗ để sheet tự tính bằng công thức — nó không nên phụ thuộc việc một mô hình
ngôn ngữ nhân đúng hay sai.

## Cột nhật ký, dữ liệu từ dòng 4

| Cột | Tên | Nội dung |
|---|---|---|
| B | `Close` | giá đóng cửa phiên gần nhất, VND nguyên |
| C | `Volume` | KLGD kèm bội số so với TB20, ví dụ `6.285.000 (0,81× TB20)` |
| D | `Signal` | `MUA THÊM` / `GIỮ` / `GIẢM TỶ TRỌNG` / `THOÁT` / `ĐỨNG NGOÀI` |
| E | `Độ tin` | `Cao` / `TB` / `Thấp` |
| F | `Lý do` | một câu, **bắt buộc chứa số** |
| G | `Mức giá canh` | hỗ trợ / kháng cự / cắt lỗ |
| H | `Next Step plan` | dạng `nếu … thì …` |
| I | `Kiểm chứng` | chấm lại nhận định 5 phiên trước: `Đúng` / `Sai` / `Chưa rõ` + một câu |

## Vì sao mỗi cột tồn tại

- **`Signal` dùng động từ hành động**, không dùng BUY/HOLD/SELL. Người dùng đang nắm cổ
  phiếu, nên câu hỏi thật là "làm gì với vị thế hiện có", không phải "cổ phiếu này tốt hay xấu".
- **`Độ tin` là bắt buộc.** Không có nó thì không phân biệt được nói đúng lúc tự tin với nói
  đúng lúc mò — và như vậy thì không chấm điểm được.
- **`Kiểm chứng` là trái tim của thiết kế.** Nhận định sai bị ghi vĩnh viễn ngay cạnh nhận
  định mới. Đây là cơ chế duy nhất khiến hệ khá lên thay vì lặp lại cùng một giọng lạc quan.

Ngày nghỉ và cuối tuần: cột B ghi `—`, các cột còn lại bỏ trống. Không bịa số.
