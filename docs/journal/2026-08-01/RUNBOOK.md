# AirGuard AI - Cai dat va chay

Tat ca lenh ben duoi chay tu root repository, tru khi co ghi chu khac. Python luon duoc goi qua root `.venv`.

## 1. Yeu cau

- Python 3.12
- Node.js 22
- npm 10
- Docker Desktop va Docker Compose neu muon chay PostgreSQL/Mosquitto/toan bo stack

## 2. Tao hoac sua venv

Neu `.venv` da co va chay duoc, bo qua lenh tao venv.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe --version
```

Neu `.venv` ton tai nhung tro toi Python cu:

```powershell
python -m venv --upgrade .venv
```

Khong bat buoc activate. Goi truc tiep `.venv\Scripts\python.exe` giup chac chan dung dung moi truong ao.

## 3. Cai Python dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r simulators\sensor_simulator\requirements.txt
```

## 4. Cai frontend dependencies

```powershell
cd frontend
npm.cmd install
cd ..
```

Neu npm bao `UNABLE_TO_VERIFY_LEAF_SIGNATURE`, tao CA bundle tu Windows certificate store cho terminal hien tai:

```powershell
$bundlePath = 'C:\tmp\airguard-windows-roots.pem'
$certificates = @(Get-ChildItem Cert:\CurrentUser\Root) + @(Get-ChildItem Cert:\LocalMachine\Root)
$pem = foreach ($certificate in $certificates) {
    '-----BEGIN CERTIFICATE-----'
    [Convert]::ToBase64String($certificate.RawData, [Base64FormattingOptions]::InsertLineBreaks)
    '-----END CERTIFICATE-----'
}
[System.IO.File]::WriteAllLines($bundlePath, $pem, [System.Text.Encoding]::ASCII)
$env:NODE_EXTRA_CA_CERTS = $bundlePath
cd frontend
npm.cmd install
cd ..
```

Khong dung `npm config set strict-ssl false`.

## 5. Cau hinh moi truong

```powershell
Copy-Item .env.example .env
```

Gia tri mac dinh phu hop local demo. Khong commit secret vao `.env`.

## 6. Chay bang Docker Compose

Sau khi cai Docker Desktop:

```powershell
docker compose up --build
```

Dia chi:

- Dashboard: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- MQTT: localhost:1883
- MQTT WebSocket: localhost:9001

Dung stack:

```powershell
docker compose down
```

## 7. Chay tung thanh phan local

Khoi dong PostgreSQL va MQTT bang Docker:

```powershell
docker compose up -d postgres mqtt
```

Terminal 1 - backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - frontend:

```powershell
cd frontend
npm.cmd run dev -- --host 0.0.0.0 --port 5173
```

Terminal 3 - sensor simulator, chay tu root:

```powershell
.\.venv\Scripts\python.exe simulators\sensor_simulator\sensor_simulator.py
```

## 8. Kiem tra nhanh

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/api/v1/stations
Invoke-RestMethod http://localhost:8000/api/v1/stations/S01/current
Invoke-RestMethod 'http://localhost:8000/api/v1/stations/S01/history?hours=6'
Invoke-RestMethod http://localhost:8000/api/v1/alerts
```

Kiem tra Python syntax:

```powershell
.\.venv\Scripts\python.exe -m py_compile backend\app\main.py backend\app\services\agent_service.py backend\app\services\forecast_service.py simulators\sensor_simulator\sensor_simulator.py
```

Build frontend:

```powershell
cd frontend
npm.cmd run build
npm.cmd audit --audit-level=high
cd ..
```

## 9. Demo flow

1. Chay stack.
2. Mo Swagger va kiem tra `/health`.
3. Mo `/api/v1/stations` de thay 5 tram.
4. Mo dashboard va xem 5 marker PM2.5 tren OpenStreetMap.
5. Theo doi log simulator publish MQTT measurement/status.
6. Trinh bay forecast, AI Agent, HITL va device control la skeleton/TODO cua giai doan tiep theo.

## 10. Commit de push GitHub

```powershell
git status
git add .env.example .gitignore README.md docker-compose.yml backend data docs frontend mqtt simulators AIRGUARD_AGENT_BRIEF.md
git commit -m "feat: scaffold AirGuard AI MVP"
git push
```
