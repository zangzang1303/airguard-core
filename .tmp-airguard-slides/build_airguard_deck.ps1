$ErrorActionPreference = 'Stop'

$outFile = Join-Path (Get-Location) 'presentation\AirGuard-AI-Pitch-Deck.pptx'
$archImage = Join-Path (Get-Location) 'image\Kiến trúc tổng thể.png'
$hitlImage = Join-Path (Get-Location) 'image\Luồng cảnh báo và phê duyệt.png'

$ppt = New-Object -ComObject PowerPoint.Application
$ppt.Visible = -1
$deck = $ppt.Presentations.Add()
$deck.PageSetup.SlideSize = 15 # ppSlideSizeOnScreen16x9

$black = 0
$white = 16777215
$gray = 15132390
$midGray = 10066329
$blue = 16042487
$blueStrong = 16744448
$scale = 0.75

function Add-Text($slide, $text, $x, $y, $w, $h, $size, $color = $black, $bold = $false, $font = 'Aptos', $align = 1) {
  $x *= $scale; $y *= $scale; $w *= $scale; $h *= $scale; $size *= $scale
  $shape = $slide.Shapes.AddTextbox(1, $x, $y, $w, $h)
  $shape.TextFrame.TextRange.Text = $text
  $shape.TextFrame.TextRange.Font.Name = $font
  $shape.TextFrame.TextRange.Font.Size = $size
  $shape.TextFrame.TextRange.Font.Bold = [int]$bold
  $shape.TextFrame.TextRange.Font.Color.RGB = $color
  $shape.TextFrame.TextRange.ParagraphFormat.Alignment = $align
  $shape.TextFrame.MarginLeft = 0
  $shape.TextFrame.MarginRight = 0
  $shape.TextFrame.MarginTop = 0
  $shape.TextFrame.MarginBottom = 0
  return $shape
}

function Add-Rect($slide, $x, $y, $w, $h, $fill, $line = $fill) {
  $x *= $scale; $y *= $scale; $w *= $scale; $h *= $scale
  $shape = $slide.Shapes.AddShape(1, $x, $y, $w, $h)
  $shape.Fill.ForeColor.RGB = $fill
  $shape.Line.ForeColor.RGB = $line
  return $shape
}

function Add-Title($slide, $number, $title) {
  Add-Text $slide "AIRGUARD AI  /  2026" 42 24 300 22 12 $midGray $true | Out-Null
  Add-Text $slide $title 42 55 875 68 26 $black $true | Out-Null
  Add-Text $slide $number 895 662 50 18 11 $midGray $false 'Aptos' 3 | Out-Null
}

function Add-Notes($slide, $text) {
  try { $slide.NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text = $text } catch {}
}

function Add-BulletBlock($slide, $items, $x, $y, $w, $size = 20) {
  $text = ($items | ForEach-Object { "• $_" }) -join "`r"
  $shape = Add-Text $slide $text $x $y $w 260 $size $black $false
  $shape.TextFrame.TextRange.ParagraphFormat.SpaceAfter = 12
  return $shape
}

# 1 — Cover
$s = $deck.Slides.Add(1, 12)
Add-Text $s 'AIRGUARD AI' 42 42 250 24 14 $midGray $true | Out-Null
Add-Text $s "Quan sát môi trường,`nhỗ trợ quyết định an toàn" 42 177 875 155 36 $black $true | Out-Null
Add-Text $s 'MVP giám sát chất lượng môi trường tại Vinhomes Ocean Park 1' 42 360 720 36 22 $midGray $false | Out-Null
Add-Rect $s 42 470 720 3 $blueStrong | Out-Null
Add-Text $s '5 trạm mô phỏng  •  Dashboard AQI-first  •  AI Agent có kiểm soát' 42 498 780 28 18 $black $false | Out-Null
Add-Text $s 'Dữ liệu MVP từ simulator — không phải quan trắc được chứng nhận.' 42 520 780 20 12 $midGray $false | Out-Null
Add-Notes $s 'Mở đầu: AirGuard AI là MVP minh họa chuỗi dữ liệu từ thu thập đến hỗ trợ ra quyết định. Hệ thống không thay thế quan trắc chính thức hay tư vấn y tế.'

# 2 — Problem
$s = $deck.Slides.Add(2, 12); Add-Title $s '02' 'Bài toán: dữ liệu chưa đủ để hành động đúng lúc'
Add-Text $s 'Người dùng cần câu trả lời nhanh, có ngữ cảnh và có trách nhiệm.' 42 133 800 30 20 $midGray $false | Out-Null
$questions = @('Khu vực nào đang cần chú ý?', 'Chỉ số có còn mới và đáng tin cậy không?', 'Tôi nên làm gì, và ai chịu trách nhiệm với hành động đó?')
for ($i=0; $i -lt 3; $i++) {
  $x = 42 + 300*$i
  Add-Rect $s $x 250 260 195 $gray | Out-Null
  Add-Text $s ('0' + ($i+1)) $x 275 50 25 15 $blueStrong $true | Out-Null
  Add-Text $s $questions[$i] $x 325 220 90 21 $black $true | Out-Null
}
Add-Text $s 'Cư dân  •  Người nhạy cảm  •  Người tập thể thao ngoài trời  •  Quản lý vận hành' 42 500 860 30 18 $black $false | Out-Null
Add-Notes $s 'Vấn đề không chỉ là có số PM2.5 hay CO2. Người dùng cần biết dữ liệu có tin cậy không và cần làm gì. Với quản lý, mọi hành động phải có bằng chứng và người chịu trách nhiệm.'

# 3 — Architecture
$s = $deck.Slides.Add(3, 12); Add-Title $s '03' 'Giải pháp: từ sensor đến quyết định trong một luồng dữ liệu'
if (Test-Path $archImage) { $s.Shapes.AddPicture($archImage, $false, $true, 346.5, 108.75, 337.5, 300) | Out-Null }
Add-Text $s 'Sensor simulator → MQTT + validation → PostgreSQL → FastAPI → Dashboard & AI Agent' 42 155 365 125 24 $black $true | Out-Null
Add-BulletBlock $s @('5 trạm S01–S05; PM2.5, CO2, tiếng ồn, nhiệt độ.', 'Backend là system of record.', 'Dữ liệu invalid, stale hoặc offline bị chặn trước downstream action.') 42 335 370 18 | Out-Null
Add-Text $s 'Nguồn: sơ đồ kiến trúc nội bộ AirGuard AI' 42 635 380 16 11 $midGray $false | Out-Null
Add-Notes $s 'Dữ liệu từ năm trạm mô phỏng đi qua MQTT, được kiểm tra chất lượng, lưu vào PostgreSQL và phục vụ qua FastAPI. Dashboard và Agent chỉ dùng dữ liệu do backend cung cấp.'

# 4 — Product value
$s = $deck.Slides.Add(4, 12); Add-Title $s '04' 'Dashboard AQI-first: nhìn nhanh, đi sâu, theo dõi xu hướng'
Add-Text $s 'AQI là điểm bắt đầu; các chỉ số thành phần và freshness giải thích điều gì đang xảy ra.' 42 130 800 30 19 $midGray $false | Out-Null
$items = @('Bản đồ 5 trạm và trạng thái freshness', 'AQI tổng quan; PM2.5, CO2, tiếng ồn, nhiệt độ để xem chi tiết', 'Lịch sử và forecast ngắn hạn 1–3 giờ', 'Cảnh báo theo rule cho nhiều chỉ số và trạng thái offline')
Add-BulletBlock $s $items 42 205 760 20 | Out-Null
Add-Rect $s 42 465 855 55 $blue | Out-Null
Add-Text $s 'Minh bạch: mọi payload MVP mang nhãn source = simulator; không trình bày như số liệu quan trắc chính thức.' 63 477 805 30 15 $black $true | Out-Null
Add-Notes $s 'Người dùng bắt đầu với AQI để có bức tranh nhanh, sau đó xem chỉ số thành phần và trạng thái freshness. Chúng em giữ nhãn simulator để tránh hiểu đây là dữ liệu quan trắc chính thức.'

# 5 — AI grounding
$s = $deck.Slides.Add(5, 12); Add-Title $s '05' 'AI hữu ích khi được grounding và có ranh giới rõ ràng'
Add-Rect $s 42 158 390 405 $blue | Out-Null
Add-Text $s 'AI Agent có thể' 66 188 300 30 24 $black $true | Out-Null
Add-BulletBlock $s @('Trả lời hiện trạng, so sánh, forecast và cảnh báo.', 'Diễn giải theo profile người dùng.', 'Tạo proposal có bằng chứng.') 66 245 320 17 | Out-Null
Add-Rect $s 508 158 390 405 $gray | Out-Null
Add-Text $s 'AI Agent không được' 532 188 330 30 24 $black $true | Out-Null
Add-BulletBlock $s @('Tự tạo số liệu, ngưỡng hay cảnh báo.', 'Truy cập trực tiếp PostgreSQL/MQTT.', 'Tự phê duyệt hoặc gửi command.') 532 245 320 17 | Out-Null
Add-Notes $s 'Trọng tâm không phải là AI nói trôi chảy. Agent chỉ diễn giải tool result của cùng request; nếu thiếu dữ liệu, Agent nói rõ chưa đủ dữ liệu. Agent không có quyền phê duyệt hoặc điều khiển thiết bị.'

# 6 — HITL
$s = $deck.Slides.Add(6, 12); Add-Title $s '06' 'Human-in-the-Loop: khuyến nghị đi cùng trách nhiệm'
if (Test-Path $hitlImage) { $s.Shapes.AddPicture($hitlImage, $false, $true, 367.5, 108.75, 315, 296.25) | Out-Null }
Add-Text $s "Alert hợp lệ`n↓`nProposal pending`n↓`nManager approve / reject`n↓`nAudit & device simulator" 42 160 350 280 26 $black $true | Out-Null
Add-Notes $s 'Agent chỉ tạo proposal pending. Manager là người approve hoặc reject. Khi được duyệt, dispatcher mới phát command; audit giúp truy vết toàn bộ hành trình quyết định.'

# 7 — Metrics
$s = $deck.Slides.Add(7, 12); Add-Title $s '07' 'Metrics: phản hồi lõi đủ nhanh cho quy mô demo'
$metrics = @(@('20','5 trạm × 4 chỉ số'), @('0,010 ms','MQTT validation p95'), @('98.069','message/giây'), @('4,88 ms','Heatmap 468 điểm p95'))
for ($i=0; $i -lt 4; $i++) {
  $x = 42 + 220*$i
  Add-Rect $s $x 230 190 180 $(if ($i % 2 -eq 0) {$blue} else {$gray}) | Out-Null
  Add-Text $s $metrics[$i][0] $x 270 170 38 28 $black $true 'Aptos Display' | Out-Null
  Add-Text $s $metrics[$i][1] $x 330 162 45 16 $black $false | Out-Null
}
Add-Text $s 'Dashboard polling: 30 giây  •  Simulator publish: 30 giây' 42 495 650 26 18 $black $true | Out-Null
Add-Text $s 'Đo cục bộ 24/08/2026. Microbenchmark xử lý trong tiến trình; chưa bao gồm broker, database và network.' 42 510 835 20 12 $midGray $false | Out-Null
Add-Notes $s 'Nhóm tự đo các tác vụ lõi tại máy hiện tại. Đây là microbenchmark, không phải độ trễ end-to-end. Số liệu cho thấy phần tính toán lõi không phải nút thắt với quy mô demo.'

# 8 — Feasibility
$s = $deck.Slides.Add(8, 12); Add-Title $s '08' 'Tính khả thi: pipeline end-to-end và kịch bản kiểm chứng'
Add-Text $s 'Đã triển khai' 42 148 300 28 24 $black $true | Out-Null
Add-BulletBlock $s @('Simulator → MQTT → database → API → dashboard.', 'Rule engine cảnh báo đa chỉ số.', 'Forecast baseline 1–3 giờ từ dữ liệu fresh.', 'Agent grounded + deterministic fallback.', 'Proposal, phê duyệt, audit, device simulator.') 42 198 410 16 | Out-Null
Add-Rect $s 510 155 388 400 $gray | Out-Null
Add-Text $s 'Demo kiểm chứng' 535 190 300 28 24 $black $true | Out-Null
Add-BulletBlock $s @('Normal: map + source + freshness.', 'Spike: alert sau chuỗi đo hợp lệ.', 'Stale / duplicate: bị chặn.', 'Agent thiếu dữ liệu: từ chối suy đoán.', 'Proposal: pending → approve/reject → audit.') 535 240 310 16 | Out-Null
Add-Notes $s 'Tính khả thi không chỉ nằm ở UI. Pipeline lõi đã có, và runbook demo bao gồm cả normal, spike, stale/duplicate, Agent thiếu dữ liệu, cùng luồng approval/reject.'

# 9 — Direction
$s = $deck.Slides.Add(9, 12); Add-Title $s '09' 'Định hướng: mở rộng minh bạch, có kiểm soát'
Add-Rect $s 42 170 395 300 $blue | Out-Null
Add-Text $s 'Ngắn hạn' 68 203 200 28 24 $black $true | Out-Null
Add-BulletBlock $s @('Chốt ngưỡng cảnh báo, severity, tọa độ trạm và vai trò Manager.', 'Hoàn thiện weather, notification và worker bất đồng bộ.') 68 252 330 16 | Out-Null
Add-Rect $s 505 170 395 300 $gray | Out-Null
Add-Text $s 'Trung hạn' 531 203 200 28 24 $black $true | Out-Null
Add-BulletBlock $s @('Tích hợp sensor thật và xác thực thực địa.', 'Đánh giá/backtest forecast.', 'Bổ sung authentication/RBAC production và observability.') 531 252 330 16 | Out-Null
Add-Text $s 'Mở rộng trên nền tảng có kiểm soát dữ liệu, minh bạch AI và trách nhiệm con người.' 42 550 820 48 25 $black $true | Out-Null
Add-Notes $s 'Bước tiếp theo không phải là thêm nhiều AI, mà là xác nhận rule và nguồn dữ liệu thực, sau đó tích hợp sensor thật, đánh giá mô hình và hoàn thiện bảo mật production.'

$deck.SaveAs($outFile)
$deck.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
Write-Output $outFile
