import glob
import re

print("=== Validating Mermaid Diagrams & KaTeX in all Markdown Files ===")

special_chars = ['(', ')', '[', ']', '{', '}', '/', '<', '>', ';']

for md in glob.glob("**/*.md", recursive=True):
    if "node_modules" in md or ".git" in md or "build" in md or ".gemini" in md:
        continue
    with open(md, "r", encoding="utf-8") as f:
        content = f.read()

    mermaid_blocks = re.findall(r"```mermaid(.*?)```", content, re.DOTALL)
    for b_idx, block in enumerate(mermaid_blocks):
        for line in block.splitlines():
            # Check edge labels: |...|
            edge_labels = re.findall(r"\|([^|]+)\|", line)
            for el in edge_labels:
                trimmed = el.strip()
                is_quoted = (trimmed.startswith('"') and trimmed.endswith('"'))
                if not is_quoted:
                    for ch in ['(', ')', '/', '[', ']', '{', '}']:
                        if ch in trimmed:
                            print(f"[EDGE WARNING] {md}: Unquoted special char '{ch}' in edge label |{trimmed}| -> line: {line.strip()}")
                            break
print("Validation scan completed.")
