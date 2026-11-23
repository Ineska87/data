param([Parameter(Mandatory = $true)][string]$PageDirectory)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Foundation, ContentType=WindowsRuntime]

$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and
        $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } |
    Select-Object -First 1

function Read-WinRtResult($Operation, [type]$Type) {
    $task = $asTask.MakeGenericMethod($Type).Invoke($null, @($Operation))
    return $task.GetAwaiter().GetResult()
}

$language = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages |
    Where-Object { $_.LanguageTag -match '^pl(?:-|$)' } | Select-Object -First 1
if (!$language) { throw 'Missing local Polish OCR language' }
$recognizer = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
if (!$recognizer) { throw 'Polish OCR engine unavailable' }

$pages = foreach ($file in Get-ChildItem -LiteralPath $PageDirectory -Filter '*.png' -File | Sort-Object Name) {
    $image = Read-WinRtResult ([Windows.Storage.StorageFile]::GetFileFromPathAsync($file.FullName)) ([Windows.Storage.StorageFile])
    $inputStream = Read-WinRtResult ($image.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    try {
        $decoder = Read-WinRtResult ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($inputStream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Read-WinRtResult ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        try {
            $result = Read-WinRtResult ($recognizer.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
            ($result.Lines.Text -join "`n")
        }
        finally { $bitmap.Dispose() }
    }
    finally { $inputStream.Dispose() }
}
ConvertTo-Json -InputObject @($pages) -Compress
