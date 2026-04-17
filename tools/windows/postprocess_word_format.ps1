param(
    [Parameter(Mandatory = $true)][string]$InputDocx,
    [Parameter(Mandatory = $true)][string]$OutputDocx,
    [string]$Config = "",
    [string]$Figlog = "",
    [string]$FiglogOut = ""
)

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
chcp 65001 | Out-Null
[Console]::InputEncoding = $utf8NoBom
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom
$ErrorActionPreference = "Stop"

$wdAlignParagraphCenter = 1
$wdLineSpaceSingle = 0
$wdLineSpaceExactly = 4
$wdActiveEndPageNumber = 3
$wdColorBlack = 0
$wdUnderlineNone = 0
$wdHeaderFooterPrimary = 1
$wdCollapseEnd = 0
$wdFieldPage = 33
$wdFieldNumPages = 26

function Get-DefaultDocumentFormats {
    @{
        "legacy" = @{
            profile = "legacy"
            body = @{
                font_cn = "SimSun"
                font_en = "Times New Roman"
                line_spacing_pt = 23.0
            }
            captions = @{
                figure = @{
                    line_spacing_pt = 23.0
                }
            }
            header_footer = @{
                enabled = $false
                header_text = ""
                header_font_cn = "SimSun"
                header_font_en = "Times New Roman"
                header_size_pt = 10.5
                footer_size_pt = 10.5
            }
        }
        "cuit-undergrad-zh" = @{
            profile = "cuit-undergrad-zh"
            body = @{
                font_cn = "SimSun"
                font_en = "Times New Roman"
                line_spacing_pt = 20.0
            }
            captions = @{
                figure = @{
                    line_spacing_pt = 20.0
                }
            }
            header_footer = @{
                enabled = $true
                header_text = "成都信息工程大学学士学位论文"
                header_font_cn = "SimSun"
                header_font_en = "Times New Roman"
                header_size_pt = 10.5
                footer_size_pt = 10.5
            }
        }
    }
}

function Merge-Hashtable {
    param(
        [hashtable]$Base,
        [hashtable]$Override
    )

    $result = @{}
    foreach ($key in $Base.Keys) {
        $result[$key] = $Base[$key]
    }
    if (-not $Override) {
        return $result
    }
    foreach ($key in $Override.Keys) {
        if ($result.ContainsKey($key) -and $result[$key] -is [hashtable] -and $Override[$key] -is [System.Collections.IDictionary]) {
            $result[$key] = Merge-Hashtable -Base $result[$key] -Override ([hashtable]$Override[$key])
        } else {
            $result[$key] = $Override[$key]
        }
    }
    return $result
}

function Convert-JsonObjectToHashtable {
    param($InputObject)

    if ($null -eq $InputObject) {
        return $null
    }
    if ($InputObject -is [System.Collections.IDictionary]) {
        $result = @{}
        foreach ($key in $InputObject.Keys) {
            $result[$key] = Convert-JsonObjectToHashtable -InputObject $InputObject[$key]
        }
        return $result
    }
    if ($InputObject -is [System.Collections.IEnumerable] -and -not ($InputObject -is [string])) {
        $items = @()
        foreach ($item in $InputObject) {
            $items += ,(Convert-JsonObjectToHashtable -InputObject $item)
        }
        return $items
    }
    if ($InputObject.PSObject -and $InputObject.PSObject.Properties.Count -gt 0) {
        $result = @{}
        foreach ($property in $InputObject.PSObject.Properties) {
            $result[$property.Name] = Convert-JsonObjectToHashtable -InputObject $property.Value
        }
        return $result
    }
    return $InputObject
}

function Resolve-DocumentFormat {
    param([string]$ConfigPath)

    $profiles = Get-DefaultDocumentFormats
    $rawDocumentFormat = @{}
    if ($ConfigPath -and (Test-Path -LiteralPath $ConfigPath)) {
        $rawConfig = Convert-JsonObjectToHashtable -InputObject (Get-Content -LiteralPath $ConfigPath -Encoding UTF8 -Raw | ConvertFrom-Json)
        if ($rawConfig.ContainsKey("document_format") -and $rawConfig.document_format) {
            $rawDocumentFormat = [hashtable]$rawConfig.document_format
        }
    }

    $profileName = "legacy"
    if ($rawDocumentFormat.ContainsKey("profile") -and $rawDocumentFormat.profile) {
        $profileName = [string]$rawDocumentFormat.profile
    }
    if (-not $profiles.ContainsKey($profileName)) {
        $profileName = "legacy"
    }

    $base = [hashtable]$profiles[$profileName]
    $override = @{}
    foreach ($key in $rawDocumentFormat.Keys) {
        if ($key -ne "profile") {
            $override[$key] = $rawDocumentFormat[$key]
        }
    }
    return Merge-Hashtable -Base $base -Override $override
}

function Find-ParagraphByText {
    param($Doc, [string]$Text)
    foreach ($paragraph in $Doc.Paragraphs) {
        if ($paragraph.Range.Text.Trim() -eq $Text) {
            return $paragraph
        }
    }
    return $null
}

function Insert-TocAtParagraph {
    param($Doc, $Paragraph)
    $range = $Paragraph.Range
    $range.Text = ""
    $null = $Doc.TablesOfContents.Add($range, $true, 1, 3, $true, $true, $true)
}

function Set-NoCompressImages {
    param($App)
    try {
        $App.Options.DoNotCompressPicturesInFile = $true
    } catch {
    }
}

function Set-StylesBlack {
    param($Doc)
    $targets = @("Normal", "Heading 1", "Heading 2", "Heading 3", "Heading 4", "Hyperlink", "FollowedHyperlink", "Caption")
    for ($i = 1; $i -le 9; $i++) {
        $targets += "TOC $i"
    }
    foreach ($name in $targets) {
        try {
            $style = $Doc.Styles.Item($name)
            $style.Font.Color = $wdColorBlack
            if ($name -in @("Hyperlink", "FollowedHyperlink")) {
                $style.Font.Underline = $wdUnderlineNone
            }
        } catch {
        }
    }
}

function Set-HyperlinksBlack {
    param($Doc)
    try {
        foreach ($hyperlink in $Doc.Hyperlinks) {
            try {
                $hyperlink.Range.Font.Color = $wdColorBlack
                $hyperlink.Range.Font.Underline = $wdUnderlineNone
            } catch {
            }
        }
    } catch {
    }
}

function Restore-ReferenceFieldSuperscripts {
    param($Doc)
    try {
        foreach ($field in $Doc.Fields) {
            try {
                $codeText = [string]$field.Code.Text
                $normalized = (($codeText -split '\s+') | Where-Object { $_ -ne "" }) -join ' '
                if ($normalized -notmatch '(^| )REF ref_\d+($| )') {
                    continue
                }
                $field.Result.Font.Superscript = $true
                $field.Result.Font.Color = $wdColorBlack
                $field.Result.Font.Underline = $wdUnderlineNone
            } catch {
            }
        }
    } catch {
    }
}

function Test-ReferenceFieldSuperscripts {
    param($Doc)
    $failures = @()
    try {
        foreach ($field in $Doc.Fields) {
            try {
                $codeText = [string]$field.Code.Text
                $normalized = (($codeText -split '\s+') | Where-Object { $_ -ne "" }) -join ' '
                if ($normalized -notmatch '(^| )REF (ref_\d+)($| )') {
                    continue
                }
                $refId = $matches[2]
                $resultText = [string]$field.Result.Text
                $resultText = $resultText.Trim()
                if (-not $resultText) {
                    $failures += "${refId}:<empty>"
                    continue
                }
                if (-not [bool]$field.Result.Font.Superscript) {
                    $failures += "${refId}:$resultText"
                }
            } catch {
            }
        }
    } catch {
    }
    return $failures
}

function Format-InlineShapes {
    param($Doc, [hashtable]$DocumentFormat)

    $lineSpacing = 23.0
    if ($DocumentFormat.ContainsKey("captions") -and $DocumentFormat.captions.figure.line_spacing_pt) {
        $lineSpacing = [double]$DocumentFormat.captions.figure.line_spacing_pt
    }
    foreach ($shape in $Doc.InlineShapes) {
        try {
            $paragraph = $shape.Range.Paragraphs(1)
            $paragraph.Range.ParagraphFormat.Alignment = $wdAlignParagraphCenter
            $paragraph.Range.ParagraphFormat.LineSpacingRule = $wdLineSpaceSingle
            $paragraph.Range.ParagraphFormat.SpaceBefore = 12
            $paragraph.Range.ParagraphFormat.SpaceAfter = 12
            $caption = $paragraph.Next()
            if ($null -ne $caption) {
                $caption.Range.ParagraphFormat.Alignment = $wdAlignParagraphCenter
                $caption.Range.ParagraphFormat.LineSpacingRule = $wdLineSpaceExactly
                $caption.Range.ParagraphFormat.LineSpacing = $lineSpacing
            }
        } catch {
        }
    }
}

function Apply-HeaderFooter {
    param($Doc, [hashtable]$DocumentFormat)

    if (-not $DocumentFormat.ContainsKey("header_footer")) {
        return
    }
    $headerFooter = [hashtable]$DocumentFormat.header_footer
    if (-not $headerFooter.enabled) {
        return
    }
    $body = [hashtable]$DocumentFormat.body
    $lineSpacing = if ($body.line_spacing_pt) { [double]$body.line_spacing_pt } else { 20.0 }
    $headerText = [string]$headerFooter.header_text
    $headerFontCn = [string]$headerFooter.header_font_cn
    $headerFontEn = [string]$headerFooter.header_font_en
    $headerSize = [double]$headerFooter.header_size_pt
    $footerSize = [double]$headerFooter.footer_size_pt

    for ($index = 1; $index -le $Doc.Sections.Count; $index++) {
        $section = $Doc.Sections.Item($index)

        try { $section.Headers($wdHeaderFooterPrimary).LinkToPrevious = $false } catch {}
        try { $section.Footers($wdHeaderFooterPrimary).LinkToPrevious = $false } catch {}

        $headerRange = $section.Headers($wdHeaderFooterPrimary).Range
        $headerRange.Text = $headerText
        $headerRange.ParagraphFormat.Alignment = $wdAlignParagraphCenter
        $headerRange.ParagraphFormat.LineSpacingRule = $wdLineSpaceExactly
        $headerRange.ParagraphFormat.LineSpacing = $lineSpacing
        $headerRange.Font.NameFarEast = $headerFontCn
        $headerRange.Font.Name = $headerFontEn
        $headerRange.Font.Size = $headerSize
        $headerRange.Font.Bold = 0
        $headerRange.Font.Color = $wdColorBlack

        $footer = $section.Footers($wdHeaderFooterPrimary)
        $footerRange = $footer.Range
        $footerRange.Text = ""
        $footerRange.ParagraphFormat.Alignment = $wdAlignParagraphCenter
        $footerRange.ParagraphFormat.LineSpacingRule = $wdLineSpaceExactly
        $footerRange.ParagraphFormat.LineSpacing = $lineSpacing
        $footerRange.Font.NameFarEast = "SimSun"
        $footerRange.Font.Name = "Times New Roman"
        $footerRange.Font.Size = $footerSize
        $footerRange.Font.Bold = 0
        $footerRange.Font.Color = $wdColorBlack

        $footerRange.InsertAfter("第")
        $footerRange.Collapse($wdCollapseEnd)
        $null = $Doc.Fields.Add($footerRange, $wdFieldPage)

        $footerRange = $footer.Range
        $footerRange.Collapse($wdCollapseEnd)
        $footerRange.InsertAfter("页 共")
        $footerRange.Collapse($wdCollapseEnd)
        $null = $Doc.Fields.Add($footerRange, $wdFieldNumPages)

        $footerRange = $footer.Range
        $footerRange.Collapse($wdCollapseEnd)
        $footerRange.InsertAfter("页")
    }
}

function Update-FigureLog {
    param($Doc, [string]$InputCsv, [string]$OutputCsv)
    if (-not $InputCsv -or -not (Test-Path -LiteralPath $InputCsv)) {
        return
    }

    $rows = Import-Csv -LiteralPath $InputCsv -Encoding UTF8
    $captionToPage = @{}
    foreach ($shape in $Doc.InlineShapes) {
        try {
            $paragraph = $shape.Range.Paragraphs(1)
            $caption = $paragraph.Next()
            if ($null -eq $caption) {
                continue
            }
            $captionText = $caption.Range.Text.Trim()
            if (-not $captionText.StartsWith("图")) {
                continue
            }
            $page = [int]$caption.Range.Information($wdActiveEndPageNumber)
            $captionToPage[$captionText] = $page
        } catch {
        }
    }

    foreach ($row in $rows) {
        $caption = [string]$row.figure_caption
        if ($captionToPage.ContainsKey($caption)) {
            $row.inserted_page = [string]$captionToPage[$caption]
        }
    }

    $outputDir = Split-Path -Parent $OutputCsv
    if ($outputDir) {
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
    }
    $rows | Select-Object figure_caption, source_path, processed_path, inserted_page | Export-Csv -LiteralPath $OutputCsv -NoTypeInformation -Encoding UTF8
    $csvText = Get-Content -LiteralPath $OutputCsv -Encoding UTF8 -Raw
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($OutputCsv, $csvText, $utf8NoBom)
}

$documentFormat = Resolve-DocumentFormat -ConfigPath $Config
$inputPath = (Resolve-Path -LiteralPath $InputDocx).Path
$outputDir = Split-Path -Parent $OutputDocx
if ($outputDir) {
    New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
}
$workingDir = Join-Path $env:TEMP ("workflow_bundle_postprocess_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $workingDir | Out-Null
$workingDocx = Join-Path $workingDir "working_final.docx"
Copy-Item -LiteralPath $inputPath -Destination $workingDocx -Force
$outputPath = $workingDocx
$workingFigureLogOut = if ($FiglogOut) { Join-Path $workingDir "figure_insert_log_final.csv" } else { "" }

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $null

try {
    Set-NoCompressImages -App $word
    $doc = $word.Documents.Open($outputPath)
    if ($null -eq $doc) {
        try { $doc = $word.ActiveDocument } catch {}
    }
    if ($null -eq $doc) {
        throw "Word failed to open document: $outputPath"
    }

    $tocPlaceholder = '（请在 Word 中插入“目录”，并更新域以生成目录。）'
    $tocParagraph = Find-ParagraphByText -Doc $doc -Text $tocPlaceholder
    if ($null -ne $tocParagraph) {
        Insert-TocAtParagraph -Doc $doc -Paragraph $tocParagraph
    }

    Set-StylesBlack -Doc $doc
    Set-HyperlinksBlack -Doc $doc
    Format-InlineShapes -Doc $doc -DocumentFormat $documentFormat
    Apply-HeaderFooter -Doc $doc -DocumentFormat $documentFormat

    try { $doc.Fields.Update() | Out-Null } catch {}
    try {
        foreach ($toc in $doc.TablesOfContents) {
            try { $toc.Update() | Out-Null } catch {}
        }
    } catch {}

    Restore-ReferenceFieldSuperscripts -Doc $doc

    if ($Figlog -and $FiglogOut) {
        Update-FigureLog -Doc $doc -InputCsv $Figlog -OutputCsv $workingFigureLogOut
    }

    $citationFailures = @(Test-ReferenceFieldSuperscripts -Doc $doc)
    if ($citationFailures.Count -gt 0) {
        $sampleFailures = @($citationFailures | Select-Object -First 10)
        throw ("citation superscript audit failed: " + ($sampleFailures -join ", "))
    }

    if ($null -eq $doc) {
        try { $doc = $word.ActiveDocument } catch {}
    }
    if ($null -eq $doc) {
        throw "Word document handle lost before save: $outputPath"
    }
    $doc.Save()
    Copy-Item -LiteralPath $workingDocx -Destination $OutputDocx -Force
    if ($Figlog -and $FiglogOut -and (Test-Path -LiteralPath $workingFigureLogOut)) {
        $figlogOutDir = Split-Path -Parent $FiglogOut
        if ($figlogOutDir) {
            New-Item -ItemType Directory -Force -Path $figlogOutDir | Out-Null
        }
        Copy-Item -LiteralPath $workingFigureLogOut -Destination $FiglogOut -Force
    }
} finally {
    if ($null -ne $doc) {
        try { $doc.Close($false) } catch {}
    }
    try { $word.Quit() } catch {}
    try {
        if (Test-Path -LiteralPath $workingDir) {
            Remove-Item -LiteralPath $workingDir -Recurse -Force
        }
    } catch {}
}
