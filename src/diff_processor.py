import subprocess
import re

def get_changed_files(base_branch="origin/main"):
    cmd = ["git", "diff", "--name-only", base_branch]
    result = subprocess.run(cmd, capture_output=True, text=True)
    files = result.stdout.strip().split("\n")
    return [f for f in files if f.endswith((".py", ".java"))]

def get_changed_lines(file_path, base_branch="origin/main"):
    cmd = ["git", "diff", base_branch, "--", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    diff = result.stdout
    pattern = re.compile(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@")
    changed_lines = []
    for match in pattern.finditer(diff):
        start, count = int(match.group(3)), int(match.group(4))
        changed_lines.extend(range(start, start + count))
    return changed_lines

def map_changes_to_symbols(symbols, changed_lines):
    impacted = []
    for s in symbols:
        start_line = s["start"][0] + 1
        end_line = s["end"][0] + 1
        if any(start_line <= line <= end_line for line in changed_lines):
            impacted.append(s)
    return impacted

if __name__ == "__main__":
    files = get_changed_files()
    for file in files:
        lines = get_changed_lines(file)
        print(f"Changed lines in {file}: {lines}")