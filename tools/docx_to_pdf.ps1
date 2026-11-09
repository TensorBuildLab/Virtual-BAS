# Export a .docx to PDF with Microsoft Word (for checking the Word layout).
#   powershell -ExecutionPolicy Bypass -File tools/docx_to_pdf.ps1 paper/manuscript.docx out.pdf
param([string]$In, [string]$Out)
$in = (Resolve-Path $In).Path
$out = [System.IO.Path]::GetFullPath($Out)
$w = New-Object -ComObject Word.Application
$w.Visible = $false
try {
    $d = $w.Documents.Open($in, $false, $true)
    $d.Fields.Update() | Out-Null
    $d.ExportAsFixedFormat($out, 17)
    $d.Close($false)
} finally {
    $w.Quit()
}
Write-Output "exported $out"
