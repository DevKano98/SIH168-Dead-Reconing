import re

def clean_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    replacements = [
        (r'\(\$x_\\text\{last\} - x_\\text\{first\}\$\)', '(x<sub>last</sub> &minus; x<sub>first</sub>)'),
        (r'\$P\(\\text\{stopped\}\)\$', '<i>P</i>(stopped)'),
        (r'\$\|\\hat\{v\}_\\text\{Py\} - \\hat\{v\}_\\text\{Kt\}\| &lt; 10\^\{-5\}\\text\{ m/s\}\$', '|v&#770;<sub>Py</sub> &minus; v&#770;<sub>Kt</sub>| &lt; 10<sup>&minus;5</sup> m/s'),
        (r'\(\$E, N\$ in meters\)', '(E, N in meters)'),
        (r'\(\$85\\%\$ inertial / \$15\\%\$ centerline pull\)', '(85% inertial / 15% centerline pull)'),
        (r'Settings \$\\to\$ About Phone', 'Settings &rarr; About Phone'),
        (r'About Phone \$\\to\$ tap', 'About Phone &rarr; tap'),
        (r'Settings \$\\to\$ System', 'Settings &rarr; System'),
        (r'System \$\\to\$ Developer Options', 'System &rarr; Developer Options'),
        (r'Developer Options \$\\to\$ scroll', 'Developer Options &rarr; scroll'),
        (r'mock location app" \$\\to\$ choose', 'mock location app" &rarr; choose'),
    ]

    for pattern, repl in replacements:
        html = re.sub(pattern, repl, html)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'Successfully updated remaining markup in {filepath}')

clean_html('continuum-idr-platform/index.html')
clean_html('docs_site/index.html')
