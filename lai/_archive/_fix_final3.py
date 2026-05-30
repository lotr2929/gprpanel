import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
f = r"C:\_myProjects\+GPR\gprpanel\index.html"
lines = open(f, encoding="utf-8", errors="replace").readlines()
start = end = -1
for i, line in enumerate(lines):
    if "function openFullAccount()" in line: start = i
    if start >= 0 and i > start and line.strip() == "}": end = i; break
print(f"start={start} end={end}")
print(repr(lines[start]))
print(repr(lines[end]))
