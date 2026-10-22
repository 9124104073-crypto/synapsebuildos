import os
import re
import json

with open('docs/architecture-flow.svg', 'r', encoding='utf-8') as f:
    arch_svg = f.read()

with open('report_assets/generate_diagrams.html', 'r', encoding='utf-8') as f:
    gen_content = f.read()

# Fix unescaped ampersands in gen_content
gen_content_fixed = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', gen_content)
arch_svg_fixed = re.sub(r'&(?!(?:amp|lt|gt|quot|apos);)', '&amp;', arch_svg)

svgs = re.findall(r'<svg.*?</svg>', gen_content_fixed, re.DOTALL)

names = [
    'fig1_1_synapse_overview.png',
    'final_fig3_2_flowchart_clean.png',
    'fig3_3_synapse_dfd.png',
    'final_fig3_5_usecase_clean.png'
]

items = []
items.append({'name': 'fig3_1_clean.png', 'svg': arch_svg_fixed, 'w': 1640, 'h': 1020})

for name, s in zip(names, svgs):
    vb_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', s)
    if vb_match:
        w, h = int(vb_match.group(1)), int(vb_match.group(2))
    else:
        w, h = 800, 600
    items.append({'name': name, 'svg': s, 'w': w, 'h': h})

json_str = json.dumps(items)

html_template = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Render Clean Canvas</title>
</head>
<body style="font-family:sans-serif; padding:20px;">
<h2>Rendering Clean Diagrams to PNG (Lossless Vector 2X)...</h2>
<div id="log"></div>

<script>
const items = __JSON_ITEMS__;
async function renderAll() {
  const log = document.getElementById('log');
  for (const item of items) {
    log.innerHTML += `<div>Processing ${item.name} (${item.w}x${item.h})...</div>`;
    
    const parser = new DOMParser();
    const doc = parser.parseFromString(item.svg, 'image/svg+xml');
    const parserError = doc.querySelector('parsererror');
    if (parserError) {
      log.innerHTML += `<div style="color:red;">XML PARSE ERROR in ${item.name}: ${parserError.textContent}</div>`;
      continue;
    }
    const svgEl = doc.querySelector('svg');
    svgEl.setAttribute('width', item.w);
    svgEl.setAttribute('height', item.h);
    
    const svgXml = new XMLSerializer().serializeToString(svgEl);
    const blob = new Blob([svgXml], {type: 'image/svg+xml;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    
    await new Promise((resolve) => {
      const img = new Image();
      img.onload = async () => {
        const pad = 24;
        const scale = 2; // high-dpi 2x
        const canvas = document.createElement('canvas');
        canvas.width = (item.w + pad * 2) * scale;
        canvas.height = (item.h + pad * 2) * scale;
        const ctx = canvas.getContext('2d');
        ctx.scale(scale, scale);
        
        ctx.fillStyle = item.name === 'fig3_1_clean.png' ? '#1a1a18' : '#ffffff';
        ctx.fillRect(0, 0, item.w + pad * 2, item.h + pad * 2);
        
        ctx.drawImage(img, pad, pad, item.w, item.h);
        
        const dataUrl = canvas.toDataURL('image/png');
        
        try {
          const resp = await fetch('http://127.0.0.1:8089', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({filename: item.name, image: dataUrl})
          });
          log.innerHTML += `<div style="color:green;">✔ Successfully saved ${item.name}!</div>`;
        } catch (err) {
          log.innerHTML += `<div style="color:red;">✘ Error saving ${item.name}: ${err.message}</div>`;
        }
        URL.revokeObjectURL(url);
        resolve();
      };
      img.onerror = (e) => {
        log.innerHTML += `<div style="color:red;">✘ Failed to load SVG image for ${item.name}</div>`;
        URL.revokeObjectURL(url);
        resolve();
      };
      img.src = url;
    });
  }
  log.innerHTML += '<h3>All Diagrams Rendered Cleanly!</h3>';
}
window.addEventListener('load', renderAll);
</script>
</body>
</html>"""

html = html_template.replace('__JSON_ITEMS__', json_str)

with open('report_assets/render_clean_canvas.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated report_assets/render_clean_canvas.html successfully with escaped XML!")
