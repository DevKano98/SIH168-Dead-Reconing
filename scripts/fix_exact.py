def replace_exact(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    pairs = [
        ("($x_{\\text{last}} - x_{\\text{first}}$)", "(x<sub>last</sub> &minus; x<sub>first</sub>)"),
        ("$P \\ge 0.50$", "<i>P</i> &ge; 0.50"),
        ("$|\\hat{v}_{\\text{Py}} - \\hat{v}_{\\text{Kt}}| &lt; 10^{-5}\\text{ m/s}$", "|v&#770;<sub>Py</sub> &minus; v&#770;<sub>Kt</sub>| &lt; 10<sup>&minus;5</sup> m/s"),
        ("Settings $\\to$ About Phone", "Settings &rarr; About Phone"),
        ("About Phone $\\to$ tap", "About Phone &rarr; tap"),
        ("Settings $\\to$ System", "Settings &rarr; System"),
        ("System $\\to$ Developer Options", "System &rarr; Developer Options"),
        ("Developer Options $\\to$ scroll", "Developer Options &rarr; scroll"),
        ("mock location app\" $\\to$ choose", "mock location app\" &rarr; choose")
    ]

    for old, new in pairs:
        content = content.replace(old, new)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Replaced exact strings in {filepath}")

replace_exact('continuum-idr-platform/index.html')
replace_exact('docs_site/index.html')
