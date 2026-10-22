import re
import os

with open('report_assets/generate_diagrams.html', 'r', encoding='utf-8') as f:
    content = f.read()

svgs = re.findall(r'<svg.*?</svg>', content, re.DOTALL)
names = ['diag_fig1_overview', 'diag_fig3_2_flowchart', 'diag_fig3_3_dfd', 'diag_fig3_5_usecase']

for name, svg in zip(names, svgs):
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:16px; background:#ffffff; display:flex; justify-content:center; align-items:center; }}
  svg {{ width: 100%; max-width: 820px; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.06); }}
</style>
</head>
<body>
{svg}
</body>
</html>"""
    with open(f'report_assets/{name}.html', 'w', encoding='utf-8') as out:
        out.write(html)
    print(f'Wrote report_assets/{name}.html')
