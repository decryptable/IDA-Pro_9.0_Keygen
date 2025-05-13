if (-not (Test-Path ".git")) {
    Write-Host "Error: This directory is not a Git repository." -ForegroundColor Red
    exit 1
}

Write-Host "Git repository detected.`n" -ForegroundColor Green

$localTags = git tag
if (-not $localTags) {
    Write-Host "There is no local tag." -ForegroundColor Yellow
} else {
    Write-Host "Local tags found:" -ForegroundColor Green
    $localTags | ForEach-Object { Write-Host " - $_" -ForegroundColor Gray }
}

$remoteTags = git ls-remote --tags origin | ForEach-Object {
    ($_ -split "refs/tags/")[-1]
} | Where-Object { $_ -ne "" }

if (-not $remoteTags) {
    Write-Host "`nNo remote tag at origin." -ForegroundColor Yellow
} else {
    Write-Host "`nGitHub remote tags (origin):" -ForegroundColor Green
    $remoteTags | ForEach-Object { Write-Host " - $_" -ForegroundColor Gray }
}

Write-Host "`nAre you sure you want to remove all local and remote (origin) tags?" -ForegroundColor Yellow
$confirm = Read-Host "Type 'yes' to continue"

if ($confirm -ne "yes") {
    Write-Host "Action cancelled by user." -ForegroundColor Red
    exit 0
}

if ($localTags) {
    foreach ($tag in $localTags) {
        git tag -d $tag | Out-Null
    }
    Write-Host "All local tags have been removed." -ForegroundColor Green
}

if ($remoteTags) {
    foreach ($tag in $remoteTags) {
        git push origin ":refs/tags/$tag" | Out-Null
    }
    Write-Host "All remote tags on GitHub have been removed." -ForegroundColor Green
}

Write-Host "`nFinished." -ForegroundColor Green
