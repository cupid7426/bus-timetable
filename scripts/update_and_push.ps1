# 時刻表を取得し、変更があればGitHubへpushする（タスクスケジューラ用）
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONUTF8 = "1"
python scripts/fetch.py
git add docs/data.json
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
  git commit -m "chore: update timetable"
  git push
}
