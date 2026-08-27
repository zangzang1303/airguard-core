# ĐẶC TẢ NÂNG CẤP TOÀN DIỆN AI CHAT AGENT (AIRGUARD AI - VINHOMES OCEAN PARK 1)

> **Mã tài liệu:** `AIRGUARD-SPEC-AICOMP-202608`  
> **Thời điểm lập:** 2026-08-27T19:45:00+07:00  
> **Phiên bản:** v2.0.0 — Geospatial Intelligence & Conversational UX Upgrade  
> **Tác giả:** AI System Architect & Tech Lead  
> **Trạng thái:** Sẵn sàng triển khai (Ready for Implementation)

---

## MỤC LỤC

1. [TỔNG QUAN BỐI CẢNH VÀ MỤC TIÊU DỰ ÁN](#1-tổng-quan-bối-cảnh-và-mục-tiêu-dự-án)
2. [KIẾN TRÚC VÀ CƠ CHẾ VẬN HÀNH HIỆN TẠI](#2-kiến-trúc-và-cơ-chế-vận-hành-hiện-tại)
3. [PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ CÁC LỖI THỰC TẾ](#3-phân-tích-nguyên-nhân-gốc-rễ-các-lỗi-thực-tế)
4. [ĐẶC TẢ THIẾT KẾ FORMAT PHẢN HỒI THÂN THIỆN NGƯỜI DÙNG (UX FORMAT)](#4-đặc-tả-thiết-kế-format-phản-hồi-thân-thiện-người-dùng-ux-format)
5. [ĐẶC TẢ BẢN ĐỒ TRI THỨC KHÔNG GIAN 100% OCEAN PARK 1](#5-đặc-tả-bản-đồ-tri-thức-không-gian-100-ocean-park-1)
6. [ĐẶC TẢ BỘ NHẬN DIỆN Ý ĐỊNH NGỮ CẢNH (SEMANTIC INTENT & CONTEXT ROUTER)](#6-đặc-tả-bộ-nhận-diện-ý-định-ngữ-cảnh-semantic-intent--context-router)
7. [HỢP NHẤT LUỒNG XỬ LÝ GATEWAY (UNIFIED GATEWAY PIPELINE)](#7-hợp-nhất-luồng-xử-lý-gateway-unified-gateway-pipeline)
8. [KẾ HOẠCH TRIỂN KHAI & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)](#8-kế-hoạch-triển-khai--tiêu-chí-nghiệm-thu-acceptance-criteria)

---

## 1. TỔNG QUAN BỐI CẢNH VÀ MỤC TIÊU DỰ ÁN

### 1.1. Bối cảnh dự án
AirGuard AI là nền tảng quan trắc môi trường và hỗ trợ cư dân/Ban Quản Lý tại **Vinhomes Ocean Park 1 (OCP1)**. Hệ thống kết hợp:
* **Hạ tầng IoT mô phỏng:** 5 trạm quan trắc đại diện (**S01** - Trục Đa Tốn, **S02** - Khu Sapphire, **S03** - Ven Hồ Ngọc Trai, **S04** - Khuôn viên VinUni, **S05** - Khu Hải Âu).
* **Nội suy không gian:** Lưới IDW 468 điểm có hiệu chỉnh hướng gió thời gian thực.
* **Đồ thị định tuyến:** Mạng lưới đường thực tế OpenStreetMap (OSM) để tính toán cung đường chạy bộ/đi dạo tối ưu tránh khói bụi.
* **Nguyên tắc an toàn (Grounding Gate):** AI Agent không được bịa đặt chỉ số môi trường; mọi con số phải có căn cứ từ dữ liệu trạm đo hoặc nội suy lưới cùng request.

### 1.2. Mục tiêu nâng cấp
Nâng cấp AI Chat Agent từ trạng thái **"Báo cáo thông số kỹ thuật thô"** sang trạng thái **"Trợ lý đô thị thông minh toàn diện"**:
1. **Am hiểu 100% địa bàn OCP1:** Nhận diện toàn bộ trục đường, ngõ phụ, phân khu, toà nhà, trường học, bệnh viện, tiện ích.
2. **Hiểu sâu ngữ cảnh:** Nhận diện đúng ý định phủ định (*"ngoài chạy bộ..."*), so sánh (*"khu nào ô nhiễm nhất..."*), hỏi tiếp đa lượt (*"ở đó thì sao..."*).
3. **Format trả lời thân thiện:** Bố cục sáng sủa, có icon trực quan, đưa ra lời khuyên thực tế cho sức khỏe thay vì in disclaimer kỹ thuật làm khó người dùng.
4. **Đồng bộ tuyệt đối giữa Bản đồ & Chat Box:** Map vẽ cái gì thì Chat giải thích chuẩn xác cái đó, xóa bỏ hoàn toàn hiện tượng ghi đè câu trả lời mặc định.

---

## 2. KIẾN TRÚC VÀ CƠ CHẾ VẬN HÀNH HIỆN TẠI

### 2.1. Sơ đồ Luồng Dữ liệu (Data Flow)

```text
                                 [Người dùng nhập câu hỏi vào Chat]
                                                 │
                                                 ▼
                             ┌───────────────────────────────────────┐
                             │    Conversational Gate (Main API)     │
                             │   Phân loại: social vs domain query   │
                             └───────────────────┬───────────────────┘
                                                 │
                  ┌──────────────────────────────┴──────────────────────────────┐
                  │ (Nếu là domain query)                                       │
                  ▼                                                             ▼
┌──────────────────────────────────────────┐                  ┌──────────────────────────────────────────┐
│   Pipeline 1: Isolated Agent (:8001)     │                  │  Pipeline 2: Geospatial Interactive      │
│   (src/agents/graph.py)                  │                  │  (backend/app/services/geospatial_agent) │
├──────────────────────────────────────────┤                  ├──────────────────────────────────────────┤
│ 1. Lexicon Router (grounding.py)         │                  │ 1. Trích xuất toạ độ / POI / Origin      │
│ 2. Tool Calling (get_spatial_air_quality)│                  │ 2. Định tuyến đường OSM (Dijkstra/A*)    │
│ 3. Response Composer (ghép template thô) │                  │ 3. Tạo Map Actions (Polyline, Markers)   │
│ 4. Sinh answer dạng: "Bản đồ nội suy...  │                  │ 4. Sinh lời giải thích lộ trình (km, AQI)│
│    468 điểm lưới... disclaimer kỹ thuật" │                  │                                          │
└─────────────────────┬────────────────────┘                  └─────────────────────┬────────────────────┘
                      │                                                             │
                      └──────────────────────────────┬──────────────────────────────┘
                                                     │
                                                     ▼
                                 ┌───────────────────────────────────────┐
                                 │     Backend Gateway (main.py:1151)    │
                                 │  ⚠️ Xung đột / Ghi đè Response:       │
                                 │  result["answer"] = agent_result      │
                                 └───────────────────┬───────────────────┘
                                                     │
                                                     ▼
                                 [Giao diện React Frontend]
                                 • Bản đồ: Nhận Map Action từ Pipeline 2 (Vẽ đường)
                                 • Khung chat: Nhận text từ Pipeline 1 (In lưới IDW thô)
```

---

## 3. PHÂN TÍCH NGUYÊN NHÂN GỐC RỄ CÁC LỖI THỰC TẾ

### 3.1. Bảng Đối chiếu 4 Lỗi Điển hình

| Mã lỗi | Câu hỏi của Người dùng | Hiện tượng trên Bản đồ (Map) | Hiện tượng trong Khung Chat | Nguyên nhân Kỹ thuật Gốc rễ |
|:---:|---|---|---|---|
| **BUG-01** | *"Tìm đoạn đường chạy bộ phù hợp nhất tối nay"* | ✅ Vẽ đúng lộ trình chạy bộ xanh/vàng 2.1km qua VinUni. | ❌ Trả về: *"Bản đồ nội suy aqi ở mốc hiện tại có khoảng giá trị 41.3-344.2 AQI trên 468 điểm lưới. Lưới idw-dispersion-v2.0..."* | Tại `backend/app/main.py:1151`, `result["answer"]` bị gán đè bằng `agent_result["answer"]`. Isolated Agent chạy intent `SPATIAL` dạng lưới thô, xóa sạch phân tích cự ly/tuyến đường của `geospatial_agent`. |
| **BUG-02** | *"Khu nào đang ô nhiễm nhất?"* | ✅ Đánh dấu đúng Trục Đa Tốn (S01) kèm cờ đỏ *"Điểm ô nhiễm nhất"*. | ❌ Trả về: *"Bản đồ nội suy aqi ở mốc hiện tại có khoảng giá trị 71.2-344.1 AQI trên 468 điểm lưới..."* | Router trong `grounding.py` gom cụm từ *"khu nào"* vào `overview` thay vì `find_worst_location`, sau đó câu trả lời phân tích tên trạm tiếp tục bị ghi đè bằng text lưới IDW. |
| **BUG-03** | *"ngoài chạy bộ tôi muốn hoạt động khác trong nhà được không"* | ❌ Vẫn vẽ tiếp lộ trình chạy bộ ngoài trời. | ❌ Trả về đoạn văn bản lưới IDW thô. | Matcher trong `grounding.py` quét trúng từ khóa `"chay bo"`, bỏ qua cấu trúc phủ định *"ngoài..."* và từ khóa chính *"trong nhà"* (`recommend_indoor_activity`). |
| **BUG-04** | *"chất lượng không khí tại đường Hải Đăng"* | ❌ Trỏ mặc định vào VinUni (#1 Khuyến nghị). | ❌ Trả về: *"Khu vực VinUni là địa điểm phù hợp nhất để hoạt động ngoài trời..."* | `SpatialRegistry.POIS` và `SPATIAL_LOCATIONS` thiếu định nghĩa cho `Đường Hải Đăng`. Khi không tìm thấy toạ độ, hệ thống tự động rơi vào fallback gợi ý địa điểm tốt nhất toàn khu (VinUni). |

---

## 4. ĐẶC TẢ THIẾT KẾ FORMAT PHẢN HỒI THÂN THIỆN NGƯỜI DÙNG (UX FORMAT)

### 4.1. Cấu trúc Chuẩn 4 Thành phần của một Phản hồi
Mọi câu trả lời của Trợ lý AI trong khung chat phải tuân theo cấu trúc 4 khối rõ ràng:

1. **Khối 1 — Trả lời Trực diện (Direct Conclusion):** Trả lời ngay câu hỏi của người dùng kèm icon sinh động (1-2 câu).
2. **Khối 2 — Thông số Môi trường Chính (Key Highlights):** Liệt kê các chỉ số thiết thực (AQI, PM2.5, mức độ chất lượng, cự ly/thời gian) bằng gạch đầu dòng gọn gàng.
3. **Khối 3 — Khuyến nghị Hành động Thiết thực (Actionable Advice):** Hướng dẫn cụ thể dựa theo vai trò (cư dân thường / nhóm nhạy cảm / người tập thể thao).
4. **Khối 4 — Ghi chú Nguồn dữ liệu Tinh gọn (Footnote):** Nêu nguồn gốc dữ liệu ngắn gọn ở chân phản hồi, không chèn thuật ngữ kỹ thuật khó hiểu vào thân bài.

---

### 4.2. Bộ Mẫu Câu trả lời Chuẩn (Golden Response Templates)

#### Mẫu 1: Gợi ý Tuyến đường Chạy bộ / Đi dạo (`recommend_running_route`)
```markdown
🏃‍♂️ **Gợi ý Cung đường Chạy bộ Phù hợp Tối nay (Cự ly ~{distance_km} km)**

* **Lộ trình:** Xuất phát từ **{origin_name}** ➔ chạy dọc **{via_roads}** ➔ đích đến **{destination_name}**.
* **Chất lượng không khí trên tuyến:** **AQI {avg_aqi} ({aqi_label})**, $\text{PM}_{2.5} \approx {avg_pm25}\ \mu\text{g/m}^3$, không gian thoáng mát và ít xe cộ.
* **Thời điểm lý tưởng:** {recommended_time_window}.

💡 **Lời khuyên sức khỏe:** Tuyến đường này có chất lượng không khí trong lành nhất khu vực tối nay. Nếu bạn thuộc nhóm nhạy cảm, nên chạy với nhịp độ vừa phải và uống đủ nước.

📍 *Chi tiết tuyến đường và các trạm đo liên quan đã được vẽ trực quan trên bản đồ.*
```

#### Mẫu 2: Phân tích Khu vực Ô nhiễm nhất (`find_worst_location`)
```markdown
⚠️ **Khu vực Đang Ô nhiễm Nhất: {station_name} (Trạm {station_id})**

* **Chỉ số hiện tại:** **AQI {aqi} ({aqi_category_vi})** — $\text{PM}_{2.5}: {pm25}\ \mu\text{g/m}^3$, $\text{CO}_2: {co2}\text{ ppm}$, Tiếng ồn: {noise_db}\text{ dB}.
* **Nguyên nhân chính:** Nằm gần trục đường giao thông chính, mật độ phương tiện cao vào giờ cao điểm.
* **Khu vực trong lành nhất để thay thế:** **{best_station_name}** với **AQI {best_aqi}**.

💡 **Khuyến nghị:** Cư dân và đặc biệt là trẻ nhỏ, người cao tuổi nên hạn chế tập thể dục hoặc đi dạo kéo dài tại khu vực này. Khi di chuyển qua đây nên đeo khẩu trang chống bụi mịn.

📍 *Vị trí và bán kính ảnh hưởng đã được đánh dấu cảnh báo trên bản đồ.*
```

#### Mẫu 3: Gợi ý Hoạt động Trong nhà Thay thế (`recommend_indoor_activity`)
```markdown
🏠 **Gợi ý Hoạt động Trong nhà Thích hợp & An toàn**

Hiện tại một số khu vực ngoài trời đang có chỉ số AQI tăng cao ({current_summary}). Chuyển sang sinh hoạt và tập luyện trong nhà là lựa chọn rất tốt cho sức khỏe!

* 🏋️ **Tập luyện thể thao:** Tập gym, yoga hoặc chạy máy tại phòng gym nội khu tòa nhà ({subdivision_name}).
* 🛍️ **Vui chơi & Mua sắm:** Dạo chơi tại **TTTM Vincom Mega Mall Ocean Park** (không gian kín, có hệ thống điều hòa và lọc không khí trung tâm).
* 🌿 **Bảo vệ không gian sống:** Đóng bớt các cửa sổ hướng ra mặt đường lớn và duy trì bật máy lọc không khí trong phòng ngủ.
```

#### Mẫu 4: Tra cứu Chất lượng Không khí theo Tuyến đường / Địa danh Cụ thể (`get_location_environment`)
```markdown
📍 **Chất lượng Không khí tại {location_name}**

* **Chỉ số ước tính:** **AQI {aqi} ({aqi_label})** — $\text{PM}_{2.5} \approx {pm25}\ \mu\text{g/m}^3$, Nhiệt độ: {temp}°C, Độ ẩm: {humidity}%.
* **Trạm đo gần nhất:** {nearest_station_name} (cách khoảng {distance_m}m).
* **Đánh giá môi trường:** Không gian {environment_character} (ít khói bụi / nhiều cây xanh).

💡 **Khuyến nghị:** Phù hợp cho các hoạt động ngoài trời thông thường như đi dạo, thể thao nhẹ nhàng.
```

---

## 5. ĐẶC TẢ BẢN ĐỒ TRI THỨC KHÔNG GIAN 100% OCEAN PARK 1

Bổ sung toàn diện danh mục toạ độ địa lý, alias tìm kiếm và loại hình không gian vào [`backend/app/services/spatial_registry.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/services/spatial_registry.py) và [`src/agents/policies/spatial_response.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/src/agents/policies/spatial_response.py):

### 5.1. Danh mục Tuyến đường & Trục Giao thông

| ID Tuyến đường | Tên Tuyến đường | Toạ độ Tâm (Lat, Lng) | Trạm đại diện | Alias nhận diện tiếng Việt |
|---|---|---|:---:|---|
| `road_hai_dang` | **Đường Hải Đăng** | (20.9950, 105.9421) | S02 / S04 | `đường hải đăng`, `hải đăng`, `hai dang`, `trục hải đăng`, `hải đăng 1`, `hải đăng 2`, `hải đăng 3`, `hải đăng 5`, `hải đăng 6`, `hải đăng 8` |
| `road_dai_duong` | **Đường Đại Dương** | (20.9930, 105.9440) | S04 | `đường đại dương`, `đại dương`, `dai duong`, `trục đại dương`, `đại dương 1`, `đại dương 2` |
| `road_san_ho` | **Đường San Hô** | (20.9920, 105.9480) | S04 / S03 | `đường san hô`, `san hô`, `san ho`, `trục san hô`, `san hô 1`, `san hô 6`, `san hô 16` |
| `road_sao_bien` | **Đường Sao Biển** | (20.9985, 105.9525) | S03 / S05 | `đường sao biển`, `sao biển`, `sao bien`, `sao biển 1`, `sao biển 6`, `sao biển 24` |
| `road_ngoc_trai` | **Đường Ngọc Trai** | (20.9960, 105.9510) | S03 | `đường ngọc trai`, `ngọc trai`, `ngoc trai`, `ngọc trai 1`, `ngọc trai 6`, `đảo ngọc trai` |
| `road_bien_ho` | **Đường Biển Hồ** | (20.9940, 105.9580) | S05 | `đường biển hồ`, `biển hồ`, `bien ho`, `đường ven biển hồ`, `biển hồ nước mặn` |
| `road_da_ton` | **Trục Đa Tốn / Đường Vành Đai** | (21.0008, 105.9428) | S01 | `trục đa tốn`, `đường đa tốn`, `đa tốn`, `da ton`, `đường vành đai`, `cổng chào đa tốn` |
| `road_ly_thanh_tong` | **Đường Lý Thánh Tông** | (21.0015, 105.9390) | S01 | `đường lý thánh tông`, `lý thánh tông`, `ly thanh tong`, `cao tốc hà nội hải phòng` |

---

### 5.2. Danh mục Phân khu Cư dân

| ID Phân khu | Tên Phân khu | Toạ độ (Lat, Lng) | Loại hình | Alias nhận diện tiếng Việt |
|---|---|---|:---:|---|
| `area_sapphire` | **Khu Căn hộ The Sapphire (S1, S2)** | (20.9975, 105.9430) | Cao tầng | `sapphire`, `the sapphire`, `s1`, `s2`, `sapphire 1`, `sapphire 2`, `chung cư sapphire` |
| `area_zenpark` | **Khu Căn hộ The Zenpark (Ruby)** | (20.9990, 105.9460) | Cao tầng | `zenpark`, `the zenpark`, `ruby`, `the ruby`, `vườn nhật zenpark` |
| `area_pavilion` | **Khu Căn hộ The Pavilion** | (20.9965, 105.9450) | Cao tầng | `pavilion`, `the pavilion`, `chung cư pavilion` |
| `area_ngoc_trai` | **Phân khu Biệt thự Ngọc Trai** | (20.9953, 105.9500) | Thấp tầng | `biệt thự ngọc trai`, `khu ngọc trai`, `đảo ngọc trai`, `ngọc trai đảo` |
| `area_san_ho` | **Phân khu Biệt thự San Hô** | (20.9915, 105.9485) | Thấp tầng | `biệt thự san hô`, `khu san hô`, `liền kề san hô` |
| `area_sao_bien` | **Phân khu Biệt thự Sao Biển** | (20.9985, 105.9525) | Thấp tầng | `biệt thự sao biển`, `khu sao biển`, `nhà phố sao biển` |
| `area_hai_au` | **Phân khu Biệt thự Hải Âu** | (20.9910, 105.9560) | Thấp tầng | `biệt thự hải âu`, `khu hải âu`, `thương mại hải âu` |
| `area_an_dao` | **Phân khu Liền kề An Đào** | (20.9995, 105.9415) | Thấp tầng | `an đào`, `khu an đào`, `biệt thự an đào`, `nhà phố an đào` |

---

### 5.3. Danh mục Tiện ích & Địa danh Trọng điểm

| ID Tiện ích | Tên Địa danh / Tiện ích | Toạ độ (Lat, Lng) | Trạm liên kết | Alias nhận diện |
|---|---|---|:---:|---|
| `poi_vinuni` | **Trường Đại học VinUniversity** | (20.9898, 105.9467) | S04 | `vinuni`, `đại học vinuni`, `trường vinuni`, `khuôn viên vinuni` |
| `poi_technopark` | **Tòa tháp Văn phòng TechnoPark** | (20.9890, 105.9450) | S04 | `technopark`, `tòa technopark`, `tháp technopark`, `technopark tower` |
| `poi_vincom` | **TTTM Vincom Mega Mall Ocean Park** | (20.9925, 105.9575) | S05 | `vincom`, `vincom mega mall`, `trung tâm thương mại vincom` |
| `poi_vinmec` | **Bệnh viện ĐKQT Vinmec Ocean Park** | (20.9880, 105.9520) | S04 / S05 | `vinmec`, `bệnh viện vinmec`, `khám vinmec` |
| `poi_vinschool` | **Hệ thống Trường học Vinschool** | (20.9960, 105.9440) | S02 | `vinschool`, `trường vinschool`, `mầm non vinschool`, `tiểu học vinschool` |
| `poi_lake_sweet` | **Hồ Ngọc Trai (Hồ nước ngọt 24.5ha)** | (20.9953, 105.9500) | S03 | `hồ ngọc trai`, `hồ 24ha`, `hồ trung tâm`, `hồ nước ngọt` |
| `poi_lake_salt` | **Biển Hồ Nước Mặn (6.1ha)** | (20.9945, 105.9585) | S05 | `biển hồ nước mặn`, `biển hồ`, `hồ nước mặn`, `bãi cát trắng` |
| `poi_whale_square`| **Quảng trường Cá Voi** | (20.9938, 105.9485) | S03 | `quảng trường cá voi`, `cá voi`, `công viên cá voi` |

---

## 6. ĐẶC TẢ BỘ NHẬN DIỆN Ý ĐỊNH NGỮ CẢNH (SEMANTIC INTENT & CONTEXT ROUTER)

### 6.1. Quy tắc Ưu tiên Định tuyến (Routing Precedence Rules)

```text
[User Input Message]
   │
   ├─► [1. Kiểm tra An toàn & Injection] (Safety & HITL Bypass) -> Trả lời từ chối an toàn
   │
   ├─► [2. Kiểm tra Xã giao (Social / Greeting)] -> Trả lời thân thiện tức thì (0 tool, 0 LLM)
   │
   ├─► [3. Kiểm tra Ngữ cảnh Phủ định & Trong nhà (Indoor Pivot)]
   │    • Pattern: "ngoài [chạy bộ/ngoài trời]", "thay vì...", "trong nhà", "ở nhà", "indoor"
   │    ==> Định tuyến: recommend_indoor_activity (KHÔNG vẽ đường chạy bộ)
   │
   ├─► [4. Kiểm tra Câu hỏi So sánh & Cực trị Toàn khu]
   │    • Pattern: "khu nào ô nhiễm nhất", "đâu cao nhất", "chỗ nào bẩn nhất", "nơi nào sạch nhất"
   │    ==> Định tuyến: find_worst_location / find_best_location / compare_locations
   │
   ├─► [5. Kiểm tra Địa danh / Tuyến đường Cụ thể (POI / Road Query)]
   │    • Pattern: "tại [đường Hải Đăng / VinUni / Vincom / Sapphire...]"
   │    ==> Định tuyến: get_location_environment (Lấy toạ độ chính xác và nội suy IDW tại điểm đó)
   │
   ├─► [6. Kiểm tra Tìm đường & Lộ trình Vận động (Running Route Recommendation)]
   │    • Pattern: "tìm đường", "chạy bộ", "cung đường", "lộ trình", "chạy 2km/5km"
   │    ==> Định tuyến: recommend_running_route (Sinh đường chạy OSM + Phân tích cự ly/AQI)
   │
   └─► [7. Phân tích Môi trường Trạm Đo / Dự báo Thời gian thực (Station Telemetry / Forecast)]
```

---

## 7. HỢP NHẤT LUỒNG XỬ LÝ GATEWAY (UNIFIED GATEWAY PIPELINE)

Tại [`backend/app/main.py`](file:///d:/CODE/AITHUCCHIEN/BUILD/P-074/backend/app/main.py), sửa đổi triệt để cơ chế trộn kết quả giữa Agent và Geospatial Engine:

```python
# QUY TẮC MERGE CHUẨN XÁC:
if result.get("intent") in {
    "recommend_running_route",
    "recommend_personalized_running_route",
    "find_worst_location",
    "find_best_location",
    "recommend_indoor_activity",
    "get_location_environment",
    "compare_locations",
}:
    # 1. Giữ nguyên câu trả lời phân tích chi tiết, thân thiện của Geospatial Engine
    # 2. Đồng bộ các Map Actions (vẽ tuyến đường, highlight điểm ô nhiễm, zoom bản đồ)
    # 3. Kèm theo danh sách bằng chứng (Evidence & Sources) đã được validate từ trạm đo/IDW
    return result
```

* **Kết quả đạt được:**
  * Khung chat hiển thị câu trả lời trau chuốt, đầy đủ cự ly, số liệu AQI, tên đường.
  * Bản đồ Leaflet đồng bộ hiển thị đúng polyline lộ trình hoặc vòng tròn cảnh báo đỏ tại trạm tương ứng.
  * Không còn hiện tượng văn bản lưới IDW kỹ thuật thô đè lên câu trả lời.

---

## 8. KẾ HOẠCH TRIỂN KHAI & TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA)

### 8.1. Kế hoạch Triển khai theo 4 Bước

```text
[BƯỚC 1: MỞ RỘNG TRI THỨC ĐỊA LÝ]
  ├── Cập nhật backend/app/services/spatial_registry.py (Thêm Hải Đăng, Đại Dương, Vincom, Vinmec...)
  └── Cập nhật src/agents/policies/spatial_response.py (Đồng bộ catalog tọa độ OCP1)

[BƯỚC 2: NÂNG CẤP ROUTER NGỮ CẢNH & PHỦ ĐỊNH]
  ├── Cập nhật src/agents/policies/grounding.py (Bổ sung rule phủ định, ưu tiên indoor over running)
  └── Cập nhật backend/app/services/geospatial_agent_service.py (Phân loại intent thông minh)

[BƯỚC 3: CHUẨN HÓA TEMPLATE TRẢ LỜI THÂN THIỆN]
  ├── Cập nhật các template trong geospatial_agent_service.py & response_composer.py
  └── Thêm icon, tách khối Direct Answer / Highlights / Advice / Footnote

[BƯỚC 4: SỬA LUỒNG MERGE TẠI GATEWAY & KIỂM THỬ]
  ├── Cập nhật backend/app/main.py (Không gán đè văn bản IDW thô lên kết quả routing/spatial)
  ├── Chạy toàn bộ test suite (pytest tests/) đảm bảo pass 100%
  └── Build Frontend, test trực tiếp trên trình duyệt & Deploy Azure demo
```

---

### 8.2. Tiêu chí Nghiệm thu (Acceptance Criteria)

1. ✅ **Test Case 1 (Tìm đường chạy bộ):** Hỏi *"Tìm đoạn đường chạy bộ phù hợp nhất tối nay"*, chat phải trả về: Lộ trình qua đường nào, cự ly bao nhiêu km, chất lượng AQI và lời khuyên chạy; Bản đồ vẽ đúng tuyến đường.
2. ✅ **Test Case 2 (Khu vực ô nhiễm nhất):** Hỏi *"Khu nào đang ô nhiễm nhất?"*, chat phải gọi đích danh *Trục Đa Tốn (S01)* với chỉ số AQI cụ thể và đưa ra trạm sạch nhất thay thế; Bản đồ khoanh đỏ trạm S01.
3. ✅ **Test Case 3 (Ngữ cảnh phủ định / Trong nhà):** Hỏi *"ngoài chạy bộ tôi muốn hoạt động khác trong nhà được không"*, AI không được vẽ đường chạy bộ, mà phải gợi ý tập gym/yoga trong nhà, đi Vincom và đóng cửa sổ.
4. ✅ **Test Case 4 (Nhận diện Đường Hải Đăng):** Hỏi *"chất lượng không khí tại đường Hải Đăng"*, AI phải nhận diện chính xác vị trí đường Hải Đăng, trả về AQI ước tính tại đây thay vì nhảy sang VinUni.
5. ✅ **Test Suite Pass Rate:** 100% tests trong `tests/test_agents/`, `tests/test_backend/` và `tests/test_frontend/` đều PASS.
