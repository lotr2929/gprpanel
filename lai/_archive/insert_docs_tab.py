import re

f = r'C:\_myProjects\+GPR\gprpanel\index.html'
with open(f, encoding='utf-8') as fh:
    c = fh.read()

docs_tab = '''
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
             <div class="doc-toc-sub">GPR metric &#183; existing gap &#183; this database</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(2)">
        <span class="doc-toc-num">2</span>
        <div><div class="doc-toc-title">Methods</div>
             <div class="doc-toc-sub">4 source tiers &#183; merging &#183; schema design</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(3)">
        <span class="doc-toc-num">3</span>
        <div><div class="doc-toc-title">Data Records</div>
             <div class="doc-toc-sub">34,429 species &#183; tier and category distribution</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(4)">
        <span class="doc-toc-num">4</span>
        <div><div class="doc-toc-title">Technical Validation</div>
             <div class="doc-toc-sub">Name validation &#183; LAI plausibility &#183; tier integrity</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(5)">
        <span class="doc-toc-num">5</span>
        <div><div class="doc-toc-title">Usage Notes</div>
             <div class="doc-toc-sub">GPRSELECT workflow &#183; urban LAI &#183; climate filtering</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(6)">
        <span class="doc-toc-num">6</span>
        <div><div class="doc-toc-title">Limitations</div>
             <div class="doc-toc-sub">7 disclosed limitations</div></div>
      </div>
      <div class="doc-toc-item" onclick="openDocSection(7)">
        <span class="doc-toc-num">7</span>
        <div><div class="doc-toc-title">Future Development</div>
             <div class="doc-toc-sub">v1.1 &#8211; v2.0 roadmap</div></div>
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
      <div class="doc-version">Working draft v0.1 &#183; May 2026 &#183; Target: <em>Scientific Data</em> (Nature Research)</div>
    </div>
    <div id="doc-section-view" class="doc-section">
      <div class="doc-back" onclick="closeDocSection()">
        <i class="ti ti-arrow-left"></i> Contents
      </div>
      <div class="doc-body" id="doc-body"></div>
    </div>
  </div>

'''

# Fix stray --> and insert docs tab before report overlay
c = c.replace(
    'Connecting\u2026</div> -->\n  <div class="report-overlay"',
    'Connecting\u2026</div>\n' + docs_tab + '  <div class="report-overlay"'
)

with open(f, 'w', encoding='utf-8') as fh:
    fh.write(c)

print('Done. Docs tab inserted.')
