# Phase 2.5 Reliability Testing Suite - Execution Script for Windows PowerShell
# Run: .\run_phase2_5_tests.ps1

param(
    [Parameter(HelpMessage = "Run only specific test (load, idempotency, recovery, chaos)")]
    [string]$TestModule = "all"
)

# Set strict mode
Set-StrictMode -Version Latest

# Colors
function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host ("╔" + ("═" * 60) + "╗") -ForegroundColor Cyan
    Write-Host ("║ Phase 2.5 Reliability Testing Suite") -ForegroundColor Cyan
    Write-Host ("║ $Message") -ForegroundColor Cyan
    Write-Host ("╚" + ("═" * 60) + "╝") -ForegroundColor Cyan
    Write-Host ""
}

function Write-SubHeader {
    param([string]$Message)
    Write-Host ""
    Write-Host "━━━ $Message ━━━" -ForegroundColor Yellow
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Check-Docker {
    Write-SubHeader "Checking Docker"
    
    try {
        $output = docker ps 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Docker daemon not running. Please start Docker Desktop or Docker service."
            exit 1
        }
        Write-Success "Docker daemon is running"
    }
    catch {
        Write-Error-Custom "Docker not found. Please install Docker."
        exit 1
    }
}

function Check-Containers {
    Write-SubHeader "Checking Containers"
    
    $requiredContainers = @("fairlens_api", "fairlens_worker", "fairlens_redis")
    $missing = 0
    
    foreach ($container in $requiredContainers) {
        $isRunning = docker ps --format "{{.Names}}" | Where-Object { $_ -eq $container }
        
        if ($isRunning) {
            Write-Success "$container is running"
        }
        else {
            Write-Error-Custom "$container not running"
            $missing++
        }
    }
    
    if ($missing -gt 0) {
        Write-Host ""
        Write-Warning-Custom "To start containers:"
        Write-Host "  cd infra/"
        Write-Host "  docker compose up -d"
        exit 1
    }
}

function Check-API-Health {
    Write-SubHeader "Checking API Health"
    
    $maxRetries = 10
    $retry = 0
    
    while ($retry -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "API is responsive"
                return
            }
        }
        catch {
            # Continue
        }
        
        $retry++
        if ($retry -lt $maxRetries) {
            Write-Host "  Waiting for API... (attempt $retry/$maxRetries)"
            Start-Sleep -Seconds 2
        }
    }
    
    Write-Error-Custom "API is not responding"
    Write-Host "  Check logs: docker logs fairlens_api"
    exit 1
}

function Install-Dependencies {
    Write-SubHeader "Installing Test Dependencies"
    
    pip install -q pytest pytest-asyncio httpx 2>&1 | Out-Null
    Write-Success "Dependencies installed"
}

function Run-TestModule {
    param(
        [string]$Module,
        [string]$Description
    )
    
    Write-SubHeader "Running: $Description"
    
    $testsDir = Join-Path $PSScriptRoot "tests\phase2_5"
    Push-Location $testsDir
    
    try {
        pytest "$Module" -v --tb=short --color=yes
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$Description passed"
            return 0
        }
        else {
            Write-Error-Custom "$Description failed"
            return 1
        }
    }
    finally {
        Pop-Location
    }
}

function Main {
    Write-Header "Starting Phase 2.5 Tests"
    
    # Pre-flight checks
    Check-Docker
    Check-Containers
    Check-API-Health
    Install-Dependencies
    
    # Run test suites
    $failed = 0
    
    if ($TestModule -eq "all" -or $TestModule -eq "load") {
        if ((Run-TestModule "test_load.py" "Load & Concurrency Testing") -ne 0) {
            $failed++
        }
    }
    
    if ($TestModule -eq "all" -or $TestModule -eq "idempotency") {
        if ((Run-TestModule "test_idempotency.py" "Idempotency Testing") -ne 0) {
            $failed++
        }
    }
    
    if ($TestModule -eq "all" -or $TestModule -eq "recovery") {
        if ((Run-TestModule "test_recovery.py" "Failure Recovery Testing") -ne 0) {
            $failed++
        }
    }
    
    if ($TestModule -eq "all" -or $TestModule -eq "chaos") {
        if ((Run-TestModule "test_chaos.py" "Chaos Testing") -ne 0) {
            $failed++
        }
    }
    
    # Final report
    Write-Header "Test Execution Complete"
    
    if ($failed -eq 0) {
        Write-Success "All test suites passed!"
        Write-Host ""
        Write-Success "System is production-ready for reliability."
        Write-Host ""
        exit 0
    }
    else {
        Write-Error-Custom "$failed test suite(s) failed"
        Write-Host ""
        Write-Warning-Custom "Review logs above for failures."
        Write-Host ""
        exit 1
    }
}

# Trap Ctrl+C
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { 
    Write-Warning-Custom "Test interrupted"
    exit 130
}

Main
