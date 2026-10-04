def replace_to(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = content.replace(r'$\to$', '&rarr;')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Replaced $\\to$ in {filepath}")

replace_to('continuum-idr-platform/index.html')
replace_to('docs_site/index.html')
