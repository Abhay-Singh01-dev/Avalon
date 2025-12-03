# Avalon Development Server Startup Script
Write-Host "🚀 Starting Avalon Development Servers..." -ForegroundColor Cyan

# Start Backend Server
Write-Host "`n📡 Starting Backend API Server (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:/Users/abhay/Desktop/AI/Pharma AI/backend'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start Frontend Server
Write-Host "`n🎨 Starting Frontend Dev Server (Port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'c:/Users/abhay/Desktop/AI/Pharma AI'; npm run dev"

Write-Host "`n✅ Both servers are starting up!" -ForegroundColor Green
Write-Host "   - Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "   - Frontend UI: http://localhost:3000" -ForegroundColor White
Write-Host "`n⚠️  Two PowerShell windows will open - do not close them!" -ForegroundColor Yellow
Write-Host "   Press Ctrl+C in those windows to stop the servers.`n" -ForegroundColor White
