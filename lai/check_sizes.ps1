Get-ChildItem "C:\_myProjects\+GPR\GPRTool\lai\*.csv" | ForEach-Object {
    $lines = (Get-Content $_.FullName).Count
    $mb = [math]::Round($_.Length/1MB, 2)
    Write-Host ("{0,-50} {1,7} lines   {2,6} MB" -f $_.Name, $lines, $mb)
}
