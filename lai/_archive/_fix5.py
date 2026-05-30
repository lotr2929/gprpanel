import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\GPRTool\lai\enrich_usda_traits.py"
txt = open(f, encoding="utf-8", errors="replace").read()

OLD = '''def progress(done, matched, total, t0, last_sp):
    elapsed = time.time() - t0
    rate    = done / elapsed if elapsed > 0 else 1
    eta     = (matched - done) / rate if rate > 0 and matched > done else 0
    pct     = int(done / matched * 100) if matched else 0
    bar     = "#" * (pct // 5) + "-" * (20 - pct // 5)
    sp      = (last_sp[:26] + "..") if len(last_sp) > 28 else last_sp.ljust(28)
    print(f"\\r  [{bar}] {pct:>3}%  {done:>5}/{matched} matched"
          f"  {int(elapsed//60)}m{int(elapsed%60):02d}s  eta {int(eta//60)}m{int(eta%60):02d}s"
          f"  {sp}", end="", flush=True)'''

NEW = '''def progress(done, matched, total, t0, last_sp):
    elapsed = time.time() - t0
    rate    = done / elapsed if elapsed > 0 else 1
    eta     = (matched - done) / rate if rate > 0 and matched > done else 0
    pct     = int(done / matched * 100) if matched else 0
    bar     = "#" * (pct // 5) + "-" * (20 - pct // 5)
    sp      = (last_sp[:14] + "..") if len(last_sp) > 16 else last_sp
    line    = f"  [{bar}] {pct:>3}%  {done:>5}/{matched}  {int(elapsed//60)}m{int(elapsed%60):02d}s  eta {int(eta//60)}m{int(eta%60):02d}s  {sp}"
    # Pad/truncate to exactly 76 chars so line never wraps and \\r always works
    line = line[:76].ljust(76)
    print("\\r" + line, end="", flush=True)'''

if OLD in txt:
    txt = txt.replace(OLD, NEW, 1)
    open(f, "w", encoding="utf-8").write(txt)
    print("progress fixed - 76 char cap")
else:
    print("MISS")
