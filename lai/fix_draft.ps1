$f = 'C:\_myProjects\+GPR\GPRTool\lai\DATA_DESCRIPTOR_DRAFT.md'
$c = [System.IO.File]::ReadAllText($f)
$c = $c.Replace('GPRI Global Plant Database', 'GPR Global Plant Database')
$c = $c.Replace('GPRI plugin suite', 'GPR+ plugin suite')
$c = $c.Replace('GPRI tools', 'GPR+ tools')
[System.IO.File]::WriteAllText($f, $c)
Write-Host 'done'
