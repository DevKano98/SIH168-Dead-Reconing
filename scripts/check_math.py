import glob
import re
import os

print("=== Checking Markdown KaTeX & Math Syntax ===")
errors = 0
for md in glob.glob("**/*.md", recursive=True):
    # Skip node_modules or .git
    if "node_modules" in md or ".git" in md or "build" in md or ".gemini" in md:
        continue
    with open(md, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for \text{..._...}
    matches = re.findall(r"\\text\{[^}]*_[^}]*\}", content)
    if matches:
        print(f"ERROR: Found text underscore in {md}: {matches}")
        errors += 1

    # Check for unescaped _ in math blocks $$ ... $$ and $ ... $
    # KaTeX fails on _ inside \text{} or when malformed
    math_blocks = re.findall(r"\$\$(.*?)\$\$", content, re.DOTALL)
    for block in math_blocks:
        if block.count("{") != block.count("}"):
            print(f"ERROR: Mismatched braces in {md}:\n{block.strip()}")
            errors += 1

print(f"Done check. Errors found: {errors}")
