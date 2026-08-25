$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$samplePath = Join-Path $repositoryRoot "samples\03_referral_email.eml"
$outputDirectory = Join-Path $repositoryRoot "outputs"
$outputPath = Join-Path $outputDirectory "loom-intake-003.json"

$request = @{
    intake_id = "INT-LOOM-003"
    channel = "referral_email"
    payload = [System.IO.File]::ReadAllText($samplePath, [System.Text.Encoding]::UTF8)
} | ConvertTo-Json

Write-Host "Sending incomplete referral intake..." -ForegroundColor Cyan

Add-Type -AssemblyName System.Net.Http
$httpClient = New-Object System.Net.Http.HttpClient
$httpContent = New-Object System.Net.Http.StringContent(
    $request,
    [System.Text.Encoding]::UTF8,
    "application/json"
)

try {
    $httpResponse = $httpClient.PostAsync(
        "http://localhost:8000/v1/intakes",
        $httpContent
    ).GetAwaiter().GetResult()
    $responseBody = $httpResponse.Content.ReadAsStringAsync().GetAwaiter().GetResult()
    if (-not $httpResponse.IsSuccessStatusCode) {
        throw "Intake API returned HTTP $([int]$httpResponse.StatusCode): $responseBody"
    }
    $result = $responseBody | ConvertFrom-Json
}
finally {
    $httpContent.Dispose()
    $httpClient.Dispose()
}

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
$result |
    ConvertTo-Json -Depth 30 |
    Set-Content -LiteralPath $outputPath -Encoding utf8

Write-Host ""
Write-Host "STATUS:" -ForegroundColor Yellow
$result.processing_status

Write-Host ""
Write-Host "MISSING FIELDS:" -ForegroundColor Yellow
$result.result.missing_fields

Write-Host ""
Write-Host "HUMAN REVIEW REQUIRED:" -ForegroundColor Yellow
$result.result.human_review_required

Write-Host ""
Write-Host "URGENCY:" -ForegroundColor Yellow
$result.result.urgency | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "ATTORNEY SUMMARY:" -ForegroundColor Yellow
$result.result.attorney_summary

Write-Host ""
Write-Host "TRACE ID:" -ForegroundColor Yellow
$result.trace_id

Write-Host ""
Write-Host "Full result saved to:" -ForegroundColor Green
Write-Host $outputPath
