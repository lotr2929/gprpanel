import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_traits.py"
txt = open(f, encoding="utf-8", errors="replace").read()
changes = []

# Fix field name: salt_tolerance -> salinity_tolerance
if '"salt_tolerance":' in txt:
    txt = txt.replace('"salt_tolerance":', '"salinity_tolerance":', 1)
    changes.append("salt_tolerance -> salinity_tolerance")

# Fix WARN to buffer instead of printing mid-progress
OLD = ('        except Exception as e:\n'
       '            if attempt == 2: print(f"\\n  WARN: upsert failed: {e}")\n'
       '            else: time.sleep(2)')
NEW = ('        except Exception as e:\n'
       '            if attempt == 2: _warnings.append(f"WARN: upsert failed: {e}")\n'
       '            else: time.sleep(2)')
if OLD in txt:
    txt = txt.replace(OLD, NEW, 1)
    changes.append("WARN buffered")

# Add _warnings list and print at end
OLD2 = '    buf, done = [], 0'
NEW2 = '    buf, done, _warnings = [], 0, []'
if OLD2 in txt:
    txt = txt.replace(OLD2, NEW2, 1)
    changes.append("_warnings list added")

OLD3 = ('    elapsed = time.time() - t0\n'
        '    print(f"\\n\\nDone in {int(elapsed//60)}m {int(elapsed%60)}s.")')
NEW3 = ('    elapsed = time.time() - t0\n'
        '    print()\n'
        '    for w in _warnings: print(f"  {w}")\n'
        '    print(f"\\nDone in {int(elapsed//60)}m {int(elapsed%60)}s.")')
if OLD3 in txt:
    txt = txt.replace(OLD3, NEW3, 1)
    changes.append("warnings printed after loop")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
print("Done.")
