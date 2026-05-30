import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_traits.py"
txt = open(f, encoding="utf-8", errors="replace").read()
changes = []

# 1. Truncate "complete" label
OLD1 = '    progress(matched, matched, total, t0, "complete")'
NEW1 = '    progress(matched, matched, total, t0, "done")'
if OLD1 in txt: txt = txt.replace(OLD1, NEW1, 1); changes.append("complete->done")
else: changes.append("MISS: complete label")

# 2. Better 400 error reporting - show response body
OLD2 = ('        except Exception as e:\n'
        '            if attempt == 2: _warnings.append(f"WARN: upsert failed: {e}")\n'
        '            else: time.sleep(2)')
NEW2 = ('        except Exception as e:\n'
        '            if attempt == 2:\n'
        '                body = ""\n'
        '                try: body = e.response.text[:200]\n'
        '                except: pass\n'
        '                _warnings.append(f"WARN 400: {body or str(e)[:120]}")\n'
        '            else: time.sleep(2)')
if OLD2 in txt: txt = txt.replace(OLD2, NEW2, 1); changes.append("400 body logged")
else: changes.append("MISS: except block")

open(f, "w", encoding="utf-8").write(txt)
for c in changes: print(c)
