$ErrorActionPreference = 'Stop'
$deckPath = Join-Path (Get-Location) 'presentation\AirGuard-AI-Pitch-Deck.pptx'
$outDir = Join-Path (Get-Location) '.tmp-airguard-slides\rendered'
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$ppt = New-Object -ComObject PowerPoint.Application
$deck = $ppt.Presentations.Open($deckPath, $true, $false, $false)
for ($i = 1; $i -le $deck.Slides.Count; $i++) {
  $target = Join-Path $outDir ("slide-{0:00}.png" -f $i)
  $deck.Slides.Item($i).Export($target, 'PNG', 1280, 720)
}
Write-Output "slides=$($deck.Slides.Count); notes=$($deck.Slides.Item(7).NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text.Length)"
$deck.Close()
$ppt.Quit()
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
