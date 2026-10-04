import re

def update_css(path):
    with open(path, 'r', encoding='utf-8') as f:
        css = f.read()

    # Ensure .code-content and code have white-space: pre
    old_code_css = r'\.code-content\s*\{[^}]*\}'
    new_code_css = '''.code-content {
  padding: 1.25rem 1.25rem;
  overflow-x: auto;
  font-family: var(--font-mono);
  font-size: 0.85rem;
  line-height: 1.65;
  color: #E2E8F0;
  background-color: #0F172A;
  white-space: pre !important;
}

.code-content pre,
.code-content code {
  font-family: var(--font-mono) !important;
  font-size: inherit !important;
  white-space: pre !important;
  color: inherit !important;
  display: block;
  margin: 0;
  padding: 0;
}'''

    css = re.sub(old_code_css, new_code_css, css)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(css)
    print(f"Updated CSS in {path}")

update_css('continuum-idr-platform/styles.css')
update_css('docs_site/styles.css')
