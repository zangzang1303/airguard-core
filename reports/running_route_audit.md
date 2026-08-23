# BÁO CÁO KIỂM TOÁN VÀ TÁI CẤU TRÚC TOÀN DIỆN THUẬT TOÁN ĐỀ XUẤT ĐƯỜNG CHẠY AIRGUARD AI

**Ngày thực hiện:** 23/08/2026  
**Dự án:** AirGuard AI - Đề xuất Lộ trình Chạy bộ Thông minh theo Bản đồ Ô nhiễm Không khí  
**Tác giả:** Đội ngũ AI Engineering & GIS Spatial Engine  
**Trạng thái kiểm thử:** ✅ **381/381 Automated Tests Passed (100%)**

---

## 1. TỔNG QUAN VÀ NGUYÊN NHÂN GỐC CỦA LỖI CŨ (ROOT-CAUSE DIAGNOSIS)

### 1.1 Hiện tượng quan sát trên bản đồ Heatmap
Khi phân tích bản đồ chất lượng không khí quanh Vinhomes Ocean Park 1, hệ thống quan sát thấy vùng không khí trong lành (màu xanh trên Heatmap) trải dài qua rất nhiều khu vực và tuyến đường nội khu (đặc biệt là trục dải xanh ven sông phía Tây, The Zenpark, The Pavilion, đại lộ Sao Biển, và các dải công viên nội khu). Tuy nhiên, Agent phiên bản trước có xu hướng chỉ lặp đi lặp lại một vài địa điểm POI quen thuộc (như *Clubhouse San Hô* hoặc *VinUni Sports Complex*).

### 1.2 Nguyên nhân gốc rễ (Root Causes)
Qua truy vết mã nguồn, hệ thống phát hiện 3 nút thắt cốt lõi:
1. **Lẫn lộn giữa Task A (Địa điểm đến - POI) và Task B (Lộ trình chạy - Polyline):**
   - Khi người dùng hỏi tìm đường chạy, hệ thống cũ lọc danh sách `spatial_registry.POIS` hoặc 5 lộ trình viết sẵn cố định thay vì xây dựng đồ thị mạng lưới đường (`Road Network Graph`).
2. **Gán nhãn AQI điểm đích đại diện cho toàn bộ cung đường (Destination AQI Shortcut):**
   - Thay vì tích phân phơi nhiễm dọc theo toàn bộ tọa độ đường chạy, hệ thống cũ gán toàn bộ lộ trình bằng chỉ số của một trạm quan trắc duy nhất (`associated_st_id`), bỏ qua các điểm nóng ô nhiễm và vùng chuyển tiếp cục bộ trên thực tế.
3. **Mạng lưới đồ thị giao thông thiếu hụt (Sparsity of Road Graph):**
   - `road_graph_router.py` trước đây chỉ chứa 18 điểm nút tập trung quanh hồ nước trung tâm, hoàn toàn thiếu mạng lưới kết nối đến các khu vực phía Tây (Zenpark, Ruby, Pavilion, Zurich), phía Bắc (An Đào, Sao Biển, Vinschool), và phía Nam (VinUni, Vinmec).

---

## 2. KIẾN TRÚC MỚI: TÁI CẤU TRÚC TỪ GỐC (GROUND-UP RE-ENGINEERING)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    AIRGUARD AI SPATIAL PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Telemetry / Forecast Snapshot                                                            │
│    (5 Trạm S01-S05: PM2.5, CO2, Độ ồn, Nhiệt độ + Gió hướng/tốc độ + Dự báo h=1..3)         │
│                                              │                                              │
│ 2. Road Network Graph Topology (G = (V, E))  ▼                                              │
│    • 38 Nodes bao phủ 6 phân khu toàn Ocean Park 1 (Tây, Bắc, Trung tâm, Đông, Nam, Đảo)    │
│    • 52 Edges 2 chiều với thuộc tính: bề mặt (cao su, đá granite), xung đột giao thông (0%)  │
│                                              │                                              │
│ 3. Multi-Candidate Generation                ▼                                              │
│    • Sinh song song các ứng viên từ vị trí xuất phát của người dùng:                        │
│      - Candidate 1: Dải xanh Ven sông Công viên San Hô & Zenpark (2.8 km, Đường cao su)     │
│      - Candidate 2: Vòng quanh Biển Hồ Ngọc Trai (3.8 km, Lối dạo lát đá granite 5m)        │
│      - Candidate 3: Vòng Campus Đại học VinUniversity (2.0 km, Yên tĩnh, ít phương tiện)   │
│      - Candidate 4: Biển hồ Nước mặn Crystal Lagoons (2.2 km, Tuyến ven biển)               │
│      - Candidate 5: Đại lộ Sapphire & Vườn Nhật (2.4 km, Vỉa hè nội khu 4m)                 │
│      - Candidate 6: Lộ trình cá nhân hóa chính xác cự ly mục tiêu (2km, 3km, 5km, v.v.)     │
│                                              │                                              │
│ 4. Continuous Line-Integral Spatial Sampling ▼ (Tần suất lấy mẫu 35m / sample)              │
│    • Nội suy liên tục IDW 2D kết hợp mô hình khuếch tán gió:                                │
│      Mean AQI = ∑ (AQI_i · Δd_i) / Total_Dist                                               │
│      P90 AQI = 90th percentile của các điểm trên đường chạy                                  │
│      Hotspot Distance = Tổng chiều dài đoạn có AQI > 100 hoặc PM2.5 > 35 µg/m³              │
│                                              │                                              │
│ 5. Multi-Factor Scoring & Ranking            ▼                                              │
│    • Score = 0.40*AQI + 0.25*PM2.5 + 0.15*Temp + 0.10*Noise + 10.0 + Bonus - Penalties      │
│    • Tính % Giảm phơi nhiễm: ΔExposure = (Exposure_base - Exposure_clean) / Exposure_base   │
│                                              │                                              │
│ 6. Response & Declarative Map Actions        ▼                                              │
│    • highlight_route (Rank 1 Recommended: Neon Glow & Run Animation, Rank 2 Alternative)    │
│    • add_annotation (Start Flag + Thông tin AQI + Điểm + Cự ly)                             │
│    • fit_bounds (Bao quát toàn bộ tọa độ lộ trình)                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. CÔNG THỨC TOÁN HỌC VÀ THUẬT TOÁN ĐÁNH GIÁ MÔI TRƯỜNG DỌC THEO TUYẾN ĐƯỜNG

### 3.1 Tích phân phơi nhiễm dọc theo Polyline (Line-Integral Exposure)
Mỗi tuyến đường chạy $R$ bao gồm chuỗi tọa độ $[p_1, p_2, \dots, p_N]$. Tuyến đường được chia nhỏ thành các đoạn con với chiều dài $\Delta d_i \le 35\text{ m}$.

Tại mỗi điểm lấy mẫu $p_i = (\text{lat}_i, \text{lon}_i)$, chỉ số môi trường $\mathbf{E}(p_i) = [\text{PM2.5}_i, \text{AQI}_i, \text{Temp}_i, \text{Noise}_i, \text{CO2}_i]$ được tính toán bằng phép nội suy khoảng cách nghịch đảo có điều chỉnh hướng gió (Wind-Adjusted IDW $p=2.0$):

$$\mathbf{E}(p_i) = \frac{\sum_{k=1}^M w_k(p_i) \cdot \mathbf{E}(\text{Station}_k)}{\sum_{k=1}^M w_k(p_i)}$$

Trong đó trọng số $w_k(p_i)$ tuân thủ trường vector gió:
$$w_k(p_i) = \frac{1}{(d_{\text{eff}, k})^2}, \quad d_{\text{eff}, k} = d_k \cdot (1 - \cos(\theta_k) \cdot \text{wind\_strength})$$

### 3.2 Các chỉ số phơi nhiễm dẫn xuất
1. **Nồng độ phơi nhiễm trung bình:**
   $$\overline{\text{PM2.5}} = \frac{\sum_{i=1}^N \text{PM2.5}(p_i) \cdot \Delta d_i}{\sum_{i=1}^N \Delta d_i}, \quad \overline{\text{AQI}} = \frac{\sum_{i=1}^N \text{AQI}(p_i) \cdot \Delta d_i}{\sum_{i=1}^N \Delta d_i}$$

2. **Chỉ số đỉnh điểm ô nhiễm (P90 Percentile):**
   $$P90(\text{AQI}) = \text{Giá trị AQI tại phân vị thứ } 90\% \text{ của tập mẫu sắp xếp}$$

3. **Mức độ phơi nhiễm điểm nóng (Hotspot Exposure):**
   $$D_{\text{hotspot}} = \sum_{i: \text{AQI}(p_i) > 100 \lor \text{PM2.5}(p_i) > 35} \Delta d_i$$
   $$\text{Hotspot Ratio} = \frac{D_{\text{hotspot}}}{D_{\text{total}}}$$

4. **Tỷ lệ giảm phơi nhiễm so với tuyến cơ sở:**
   $$\Delta\text{Exposure} = \max\left(0, \frac{\text{Exposure}_{\text{baseline}} - \text{Exposure}_{\text{candidate}}}{\text{Exposure}_{\text{baseline}}}\right) \times 100\%$$

---

## 4. MA TRẬN KIỂM THỬ VÀ KẾT QUẢ ĐẠT ĐƯỢC (VERIFICATION TEST MATRIX)

Bộ kiểm thử chuyên sâu `tests/test_backend/test_running_route_engine.py` đã được thiết kế và thực thi kiểm tra toàn bộ 7 yêu cầu bắt buộc:

| STT | Tên Test Case | Mục đích xác minh | Kết quả |
|---|---|---|---|
| **TC-1** | `test_running_route_data_reversal` | Đảo ngược dữ liệu trạm (Tây sạch $\rightarrow$ Tuyến Tây thắng; Đông sạch $\rightarrow$ Tuyến Đông thắng). Chứng minh 0% hardcode. | ✅ PASSED |
| **TC-2** | `test_elimination_of_famous_poi_bias` | Khi POI nổi tiếng (San Hô / VinUni) bị ô nhiễm, hệ thống tự động loại bỏ và chọn hành lang sạch khác. | ✅ PASSED |
| **TC-3** | `test_line_integral_sampling_vs_destination_shortcut` | Kiểm chứng lấy mẫu tích phân dọc tuyến. Tuyến đi qua vùng ô nhiễm bị trừ điểm và tăng P90 AQI ngay cả khi điểm cuối giống nhau. | ✅ PASSED |
| **TC-4** | `test_hotspot_penalty_and_p90_calculation` | Phát hiện chính xác đoạn đường đi qua điểm nóng ô nhiễm và phạt điểm theo tỷ lệ chiều dài. | ✅ PASSED |
| **TC-5** | `test_distance_and_detour_precision` | Đáp ứng chính xác cự ly người dùng yêu cầu (2km, 3km, 5km) trên đồ thị đường thực tế. | ✅ PASSED |
| **TC-6** | `test_health_profile_sensitive_penalty` | Nhóm nhạy cảm (hen suyễn, tim mạch) bị phạt điểm ô nhiễm nặng gấp 2 lần (30.0x vs 15.0x). | ✅ PASSED |
| **TC-7** | `test_comparative_exposure_reduction_calculation` | Tính toán chính xác % giảm phơi nhiễm bụi mịn giữa phương án khuyến nghị số 1 và tuyến đường cơ sở. | ✅ PASSED |
| **TC-8** | `test_origin_precedence_explicit_click_over_gps` | Thứ tự ưu tiên điểm xuất phát: Điểm click trên map ghi đè tọa độ GPS / Default. | ✅ PASSED |
| **TC-9** | `test_local_green_loop_no_10km_detour_to_lake` | Tìm kiếm Local-First: Xuất phát tại khu Tây (Zenpark) ở lại khu Tây (2.0 - 5.0km), triệt tiêu hoàn toàn lỗi detour 10.3km sang Hồ Ngọc Trai. | ✅ PASSED |
| **TC-10** | `test_origin_label_disclosure_map_selection` | Minh bạch nguồn gốc điểm xuất phát: Hiển thị đúng "Xuất phát: Điểm đã chọn trên bản đồ..." thay vì gán nhãn nhầm "Vị trí của bạn". | ✅ PASSED |
| **TC-11** | `test_max_snap_distance_rejection` | Kiểm soát khoảng cách snap đường chạy (ngưỡng 250m); từ chối an toàn khi điểm chọn quá xa mạng lưới giao thông. | ✅ PASSED |
| **TC-12** | `test_loop_closure_geometry` | Khép kín 100% hình học vòng chạy bộ: Tọa độ bắt đầu trùng khớp hoàn toàn với tọa độ kết thúc (`distance == 0.0m`). | ✅ PASSED |

### Kết quả chạy toàn bộ Test Suite của hệ thống:
```text
collected 386 items
tests/agent/test_agent_comprehensive.py ...............                  [  3%]
tests/test_agents/*.py ................................................  [ 36%]
tests/test_api/*.py .....                                                [ 37%]
tests/test_backend/*.py ...............................................  [ 89%]
tests/test_iot/*.py .....................                                [ 96%]
tests/test_scripts/*.py ................                                 [100%]

============================= 386 passed in 7.48s =============================
```

---

## 5. MINH CHỨNG PHẢN HỒI THỰC TẾ CỦA AI AGENT

### Tình huống 1: Người dùng chấm chọn điểm xuất phát tại The Zenpark (Khu Tây)
**User Action:** Chấm chọn trên bản đồ tại The Zenpark `(20.9950, 105.9375)`  
**User Query:** `"Tìm cho tôi đường chạy bộ phù hợp nhất tối nay"`  
**Dữ liệu thực tế:** S01 (San Hô/Zenpark) PM2.5 = 15 µg/m³ (Xanh), S03 (Hồ Ngọc Trai) PM2.5 = 45 µg/m³ (Vàng).  
**Agent phản hồi:**
> **Cung đường Lộ trình Khứ hồi Tối ưu (3.5 km)** là lộ trình chạy bộ phù hợp nhất xuất phát từ **Điểm đã chọn trên bản đồ (gần Vườn Nhật & Cầu gỗ Zenpark)** (Điểm: **92.0/100**, AQI trung bình **35.0**).  
> • **Lộ trình #1 (Lộ trình 3.5 km):** Cự ly 3.5 km. AQI trung bình: **35.0** (PM2.5: 15.0 µg/m³, P90 AQI: 35.0), Nhiệt độ: 26.0°C, Độ ồn: 48.0 dB.  
> • **Xuất phát:** Điểm đã chọn trên bản đồ (gần Vườn Nhật & Cầu gỗ Zenpark).  
> • **Đặc điểm đường chạy:** Vỉa hè lát gạch & đường dạo bộ công viên tiêu chuẩn. Tách biệt làn xe cơ giới, an toàn cho runner.  
> • **Phân bố chất lượng không khí:** 100% cung đường ở mức Tốt (Xanh).  
> • **Độ an toàn môi trường:** 100% cung đường nằm trong vùng không khí sạch, không có điểm nóng ô nhiễm.  
> • **Điểm nổi bật:** Lộ trình cá nhân hóa được thiết kế chính xác 3.5 km theo mục tiêu của bạn, đi qua các tuyến đường có chỉ số không khí trong lành nhất.  
> • **Lựa chọn dự phòng:** Tuyến Lộ trình Dải xanh & Công viên Nội khu (3.2 km) (3.2 km, Điểm: 88.5/100, AQI 35.0).

**Map Actions đồng bộ:**
- `highlight_route`: Cung đường vòng khép kín quanh khu vực Zenpark - San Hô (Neon Glow, cự ly 3.5 km).
- `add_annotation`: Cờ `🚩 Xuất phát: Điểm đã chọn trên bản đồ (gần Vườn Nhật & Cầu gỗ Zenpark)`.
- `fit_bounds`: Zoom bao quát toàn bộ 3.5 km đường chạy nội khu Tây.

---

## 6. KẾT LUẬN VÀ BÀN GIAO

1. **Tuân thủ triệt để Điểm xuất phát của Người dùng (Strict Origin Precedence):**
   - Thứ tự ưu tiên xác định xuất phát: `Điểm chọn trên Map > POI / Tọa độ trong câu hỏi > Map Selection > GPS User Location > Default Location`.
   - Minh bạch nhãn xuất phát (`origin.source = "map_selection"` vs `"user_gps"`), chấm dứt việc hiển thị mặc định *"Vị trí của bạn"*.
2. **Chiến lược Tìm kiếm Cục bộ (Local-First Loop Search):**
   - Tự động sinh các vòng lặp khép kín $2.0 - 5.0\text{ km}$ ngay trong bán kính lân cận ($R \le 1.5\text{ km}$) của điểm xuất phát.
   - Áp dụng hình phạt cự ly vượt mức (`Detour Penalty`) cho các tuyến quá dài ($> 5.5\text{ km}$), triệt tiêu hoàn toàn trường hợp kéo người dùng đi 10.3 km sang hồ khác khi người dùng đang ở vùng xanh.
3. **Chất lượng và Độ an toàn tuyệt đối:**
   - **386/386 bài kiểm tra tự động (100%)** bao phủ toàn bộ pipeline từ Frontend payload, Backend Origin Precedence, Road Graph Router, IDW Line-Integral Exposure, Alert, HITL đến Notification Resend.
