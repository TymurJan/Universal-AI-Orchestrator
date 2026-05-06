[Diagnostics.CodeAnalysis.SuppressMessageAttribute("PSAvoidAssignmentToAutomaticVariable", "")]
param()

$out = "d:\ГО Талан UA\Talan UA Antigravity manager\_lessons_output.txt"
$final = @()

3..8 | ForEach-Object {
    $num = $_
    $path = "d:\ГО Талан UA\Освіта\Від фінансування до реалізації\tmp$num\word\document.xml"
    
    if (Test-Path $path) {
        $raw = Get-Content $path -Raw -Encoding UTF8
        $final += "=== УРОК $num ==="
        
        $rgx1 = [regex]::new('<w:b/>.*?<w:t[^>]*>([^<]+)</w:t>', [System.Text.RegularExpressions.RegexOptions]::Singleline)
        $res1 = $rgx1.Matches($raw)
        
        $list1 = @()
        foreach ($i in $res1) {
            $txt = $i.Groups[1].Value.Trim()
            if ($txt.Length -gt 3) { $list1 += $txt }
        }
        
        $rgx2 = [regex]::new('<w:t[^>]*>([^<]{5,})</w:t>')
        $res2 = $rgx2.Matches($raw)
        
        $list2 = @()
        $limit = 0
        foreach ($j in $res2) {
            if ($limit -ge 20) { break }
            $val = $j.Groups[1].Value.Trim()
            if ($val.Length -gt 10) { 
                $list2 += $val 
                $limit++
            }
        }
        
        $final += "BOLD: " + ($list1 -join " | ")
        $final += "FIRST TEXT: " + ($list2 -join " / ")
        $final += ""
    } else {
        $final += "=== УРОК ${num}: FILE NOT FOUND ==="
        $final += ""
    }
}

$final | Out-File -FilePath $out -Encoding UTF8
Write-Host "Done. Output saved to: $out"
