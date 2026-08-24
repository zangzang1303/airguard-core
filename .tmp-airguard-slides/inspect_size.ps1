$ppt = New-Object -ComObject PowerPoint.Application
$deckPath = Join-Path (Get-Location) 'presentation\AirGuard-AI-Pitch-Deck.pptx'
$deck = $ppt.Presentations.Open($deckPath, $true, $false, $false)
Write-Output "width=$($deck.PageSetup.SlideWidth); height=$($deck.PageSetup.SlideHeight); size=$($deck.PageSetup.SlideSize)"
$deck.Close()
$ppt.Quit()
