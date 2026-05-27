$f = 'C:\_myProjects\+GPR\gprpanel\index.html'
$c = [System.IO.File]::ReadAllText($f)

# Fix the stray --> on status line and insert the Documentation tab
$old = "  <div id=""status"">Connecting…</div> -->`r`n  <div class=""report-overlay"""
$new = @"
  <div id="status">Connecting…</div>

  <!-- ── TAB 3: DOCUMENTATION ── -->
  <div id="tab-docs" class="tab-content">
    <div id="doc-contents" class="doc-contents">
      <h3>GPR Global Plant Database</h3>
      <div class="doc-toc-item" onclick="openDocSection(0)">
        <span class="doc-toc-num">Abs</span>
        <div><div class="doc-toc-title">Abstract</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(1)">
        <span class="doc-toc-num">1</span>
        <div><div class="doc-toc-title">Background and Summary</div>
             <div class="doc-toc-sub">GPR metric · existing gap · this database</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(2)">
        <span class="doc-toc-num">2</span>
        <div><div class="doc-toc-title">Methods</div>
             <div class="doc-toc-sub">4 source tiers · merging · schema design</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(3)">
        <span class="doc-toc-num">3</span>
        <div><div class="doc-toc-title">Data Records</div>
             <div class="doc-toc-sub">34,429 species · tier and category distribution</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(4)">
        <span class="doc-toc-num">4</span>
        <div><div class="doc-toc-title">Technical Validation</div>
             <div class="doc-toc-sub">Name validation · LAI plausibility · tier integrity</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(5)">
        <span class="doc-toc-num">5</span>
        <div><div class="doc-toc-title">Usage Notes</div>
             <div class="doc-toc-sub">GPRSELECT workflow · urban LAI · climate filtering</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(6)">
        <span class="doc-toc-num">6</span>
        <div><div class="doc-toc-title">Limitations</div>
             <div class="doc-toc-sub">7 disclosed limitations</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(7)">
        <span class="doc-toc-num">7</span>
        <div><div class="doc-toc-title">Future Development</div>
             <div class="doc-toc-sub">v1.1 – v2.0 roadmap</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(8)">
        <span class="doc-toc-num">8</span>
        <div><div class="doc-toc-title">Code Availability</div>
             <div class="doc-toc-sub">Python processing scripts</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(9)">
        <span class="doc-toc-num">9</span>
        <div><div class="doc-toc-title">References</div>
             <div class="doc-toc-sub">11 primary sources</div></div>
      </div>
      <div class="doc-version">Working draft v0.1 · May 2026 · Target: <em>Scientific Data</em> (Nature Research)</div>
    </div>
    <div id="doc-section-view" class="doc-section">
      <div class="doc-back" onclick="closeDocSection()">
        <i class="ti ti-arrow-left"></i> Contents
      </div>
      <div class="doc-body" id="doc-body"></div>
    </div>
  </div>

  <div class="report-overlay"
"@

# Try both CRLF and LF variants
if ($c.Contains("</div> -->`r`n  <div class=""report-overlay""")) {
    $c = $c.Replace("</div> -->`r`n  <div class=""report-overlay""", "</div>`r`n`r`n  <!-- __ TAB 3 placeholder -->`r`n  <div class=""report-overlay""")
    Write-Host "CRLF match found"
} elseif ($c.Contains("</div> -->`n  <div class=""report-overlay""")) {
    $c = $c.Replace("</div> -->`n  <div class=""report-overlay""", "</div>`n`n  <div class=""report-overlay""")
    Write-Host "LF match found"
} else {
    Write-Host "Pattern not found - searching..."
    $idx = $c.IndexOf('Connecting')
    Write-Host "Connecting at index: $idx"
    Write-Host "Context: $($c.Substring([Math]::Max(0,$idx-5), [Math]::Min(100,$c.Length-$idx+5)))"
}
