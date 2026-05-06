$sourceDir = "D:\ГО Талан UA\Від фінансування до реалізації"
$files = Get-ChildItem -Path $sourceDir -Filter "*.docx"
foreach ($file in $files) {
    if ($file.Name -match "Навчання №(\d+)\.docx") {
        $num = $Matches[1]
        $dest = Join-Path $sourceDir "tmp$num"
        if (-not (Test-Path $dest)) {
            New-Item -ItemType Directory -Path $dest | Out-Null
        }
        # Use tar -xf which works with .docx (zip) directly
        & tar -xf $file.FullName -C $dest
    }
}
