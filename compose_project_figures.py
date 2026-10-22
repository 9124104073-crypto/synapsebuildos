import os
from PIL import Image, ImageDraw, ImageFont

art_dir = r'C:\Users\KEVIN\.gemini\antigravity-ide\brain\6f0bdd6f-4e6a-4bf2-9b27-bbc2b11286f3'

def make_fig4_4():
    p_sun = os.path.join(art_dir, '3d_sun_1200_1792555999175.png')
    p_cutaway = os.path.join(art_dir, '3d_cutaway_roof_1792556008726.png')
    
    im_sun = Image.open(p_sun)
    im_cut = Image.open(p_cutaway)
    
    # im_sun is the canvas element (576 x 762). Crop the 3D model tightly
    crop_sun = im_sun.crop((15, 80, 560, 550))
    # im_cut is the full page (1370 x 993). In cutaway, 3D canvas is x: 195 to 680, y: 80 to 550
    crop_cut = im_cut.crop((200, 80, 675, 550))
    
    W, H = 1200, 1500
    comp = Image.new('RGB', (W, H), '#ffffff')
    draw = ImageDraw.Draw(comp)
    
    try:
        font_title = ImageFont.truetype('arialbd.ttf', 24)
        font_sub = ImageFont.truetype('arial.ttf', 16)
        font_badge = ImageFont.truetype('arialbd.ttf', 16)
        font_lbl = ImageFont.truetype('arialbd.ttf', 18)
        font_txt = ImageFont.truetype('arial.ttf', 15)
    except:
        font_title = font_sub = font_badge = font_lbl = font_txt = ImageFont.load_default()
        
    # Header Banner
    draw.rectangle([20, 20, W-20, 95], fill='#0f172a')
    draw.text((40, 32), "SYNAPSE BUILDOS — 3D SPATIAL & WALKTHROUGH ENGINE", fill='#ffffff', font=font_title)
    draw.text((40, 64), "Real-Time Procedural 3D Building Extrusion, Solar Simulation & Interactive Walkthrough", fill='#93c5fd', font=font_sub)
    
    # Panel 1: Exterior 3D Perspective with Sun Path
    draw.rectangle([20, 115, W-20, 780], outline='#cbd5e1', width=2, fill='#f8fafc')
    draw.rectangle([35, 130, 480, 168], fill='#2563eb')
    draw.text((45, 138), "1. 3D Exterior Perspective (Solar Arc @ 12:00 Noon)", fill='#ffffff', font=font_badge)
    
    sun_resized = crop_sun.resize((560, 470), Image.Resampling.LANCZOS)
    comp.paste(sun_resized, (40, 185))
    
    draw.rectangle([620, 185, W-40, 755], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.text((640, 205), "Key 3D Engine Capabilities:", fill='#0f172a', font=font_lbl)
    
    bullet_points = [
        "• Real-Time Procedural Extrusion: Extrudes 2D",
        "  vector floor plans into 3D solid geometry.",
        "• Parametric Wall Systems: 9-inch exterior and",
        "  4.5-inch interior partitions with plaster coats.",
        "• Opening Geometry: Accurate window cutouts,",
        "  glazed panels, lintels, and door swings.",
        "• Solar Ray-Tracing & Shadow Arc: Dynamic sun",
        "  positioning calibrated to Chennai latitude (13°N)",
        "  for passive daylight and cooling analysis.",
        "• TNCDBR Setback Verification: 3D bounding",
        "  volume checks against legal setback thresholds.",
        "• Real-Time Takeoffs: Plinth area (2,449 sf) &",
        "  PWD rate calculations update on every edit."
    ]
    cur_y = 240
    for bp in bullet_points:
        draw.text((640, cur_y), bp, fill='#334155', font=font_txt)
        cur_y += 28
        
    # Panel 2: Cutaway Interior Axonometric (Roof Off)
    draw.rectangle([20, 805, W-20, 1475], outline='#cbd5e1', width=2, fill='#f8fafc')
    draw.rectangle([35, 820, 520, 858], fill='#0d9488')
    draw.text((45, 828), "2. 3D Axonometric Cutaway (Interior Partitions & Core)", fill='#ffffff', font=font_badge)
    
    cut_resized = crop_cut.resize((560, 470), Image.Resampling.LANCZOS)
    comp.paste(cut_resized, (40, 875))
    
    draw.rectangle([620, 875, W-40, 1450], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.text((640, 895), "Spatial & Walkthrough Features:", fill='#0f172a', font=font_lbl)
    
    bullet_points_2 = [
        "• Roof-Off Cutaway Mode: Inspects double-height",
        "  living zones, staircase cores, and upper rooms.",
        "• First-Person Walking Mode: WASD navigation",
        "  with PointerLockControls at 5.3 ft eye level.",
        "• Staircase Climbing: Collision-detected ramp",
        "  volumes enable ascending from G.F. to F.F.",
        "• Furnishing Engine: Procedural beds, dining",
        "  suites, sanitary fittings, and spinning fans.",
        "• Material Finishes: Swatches for vitrified tiles,",
        "  granite counters, teak wood, and marble.",
        "• Multi-Format Export: Download directly to",
        "  IFC4 (BIM), DXF (AutoCAD), OBJ, and BOQ CSV."
    ]
    cur_y = 930
    for bp in bullet_points_2:
        draw.text((640, cur_y), bp, fill='#334155', font=font_txt)
        cur_y += 28

    out_p = 'report_assets/fig4_4_synapse_3d_models.png'
    comp.save(out_p, quality=95)
    print(f"Created clean {out_p}, size: {comp.size}")

def make_fig4_5():
    p_plan = os.path.join(art_dir, '2d_cad_floor_plan_1792552978513.png')
    p_checks = os.path.join(art_dir, 'checks_tab_1792552984587.png')
    
    im_plan = Image.open(p_plan)
    im_checks = Image.open(p_checks)
    
    # Accurate crops based on screen pixel inspection
    crop_plan = im_plan.crop((260, 120, 920, 760))
    crop_checks = im_checks.crop((925, 70, 1360, 980))
    
    W, H = 1200, 1500
    comp = Image.new('RGB', (W, H), '#ffffff')
    draw = ImageDraw.Draw(comp)
    
    try:
        font_title = ImageFont.truetype('arialbd.ttf', 24)
        font_sub = ImageFont.truetype('arial.ttf', 16)
        font_badge = ImageFont.truetype('arialbd.ttf', 16)
        font_lbl = ImageFont.truetype('arialbd.ttf', 18)
        font_txt = ImageFont.truetype('arial.ttf', 14)
    except:
        font_title = font_sub = font_badge = font_lbl = font_txt = ImageFont.load_default()
        
    # Header Banner
    draw.rectangle([20, 20, W-20, 95], fill='#1e293b')
    draw.text((40, 32), "SAMPLE ARCHITECTURAL BRIEF EXECUTION — VILLA HARMONY", fill='#ffffff', font=font_title)
    draw.text((40, 64), "3BHK Duplex Residence · 40×60 ft Plot · ECR Chennai · ₹85L Budget · TNCDBR 2019", fill='#94a3b8', font=font_sub)
    
    # Left Side: 2D Floor Plan
    draw.rectangle([20, 115, 620, 1475], outline='#cbd5e1', width=2, fill='#f8fafc')
    draw.rectangle([35, 130, 480, 168], fill='#0284c7')
    draw.text((45, 138), "1. Generated 2D Dimensioned CAD Layout", fill='#ffffff', font=font_badge)
    
    plan_resized = crop_plan.resize((560, 560), Image.Resampling.LANCZOS)
    comp.paste(plan_resized, (40, 185))
    
    # Legend below 2D plan
    draw.rectangle([40, 770, 600, 1450], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.text((55, 785), "Room Schedule & Program Metrics:", fill='#0f172a', font=font_lbl)
    
    lines = [
        "• Car Porch: 13.4 ft × 14.0 ft (Covered N-E front)",
        "• Foyer & Living: 20.1 ft × 14.0 ft (281 sf built-up)",
        "• Dining Area: 15.0 ft × 12.0 ft (180 sf central hub)",
        "• Kitchen: 12.0 ft × 12.0 ft (Agni S-E quadrant)",
        "• Ground Master Bed: 20.4 ft × 24.2 ft (Elderly-ready)",
        "• Ensuite Bath 1: 8.0 ft × 8.0 ft (Step-free shower)",
        "• Central Staircase: 5.0 ft × 12.0 ft (Load-bearing core)",
        "• F.F. Master Bed 2: Stacked over G.F. Master Bed",
        "• F.F. Bed 3 & Office: North-West cross-ventilated",
        "• Covered Balcony: 17.0 ft × 8.0 ft (East road view)",
        "• Total Plinth Area: 2,449 sq ft across G+1 floors",
        "• Front Setback: 5.0 ft | Rear: 5.0 ft | Side: 5.0 ft",
        "• Water Sump & Rainwater Harvesting: Front yard",
        "• Structural Frame: M25 Grade RCC with Fe500 steel"
    ]
    cur_y = 818
    for l in lines:
        draw.text((55, cur_y), l, fill='#334155', font=font_txt)
        cur_y += 26

    # Right Side: Automated Audit & Bylaw Checks
    draw.rectangle([640, 115, W-20, 1475], outline='#cbd5e1', width=2, fill='#f8fafc')
    draw.rectangle([655, 130, 1120, 168], fill='#16a34a')
    draw.text((665, 138), "2. Automated Compliance & Cost Audit (Live Engine)", fill='#ffffff', font=font_badge)
    
    checks_resized = crop_checks.resize((500, 680), Image.Resampling.LANCZOS)
    comp.paste(checks_resized, (660, 185))
    
    # Summary of Analysis below checks
    draw.rectangle([660, 890, W-40, 1450], fill='#ffffff', outline='#e2e8f0', width=1)
    draw.text((675, 905), "Executive Engineering Verification:", fill='#0f172a', font=font_lbl)
    
    audit_lines = [
        "✔ Overall Construction Readiness: 92 / 100",
        "✔ Bylaw Compliance Score: 100% (TNCDBR 2019 Pass)",
        "✔ Budget Adherence Score: 96 / 100 (₹69.1L vs ₹85.0L)",
        "✔ Buildability Score: 92 / 100 (Clean structural grid)",
        "✔ Sustainability Score: 70 / 100 (Cross-ventilation ready)",
        "✔ Ground Coverage: 52% (Max allowed: 65% · Compliant)",
        "✔ FSI (Floor Space Index): 1.02 (Max allowed: 1.50)",
        "✔ Building Height: 23.6 ft (Max allowed: 39 ft · G+1)",
        "✔ Passive Solar Orientation: East morning light,",
        "  West bedrooms screened with chajjas per engine audit.",
        "✔ Cost Variance: ₹15.9 Lakhs under ceiling budget,",
        "  leaving ample reserve for solar panels and interiors."
    ]
    cur_y = 940
    for l in audit_lines:
        color = '#15803d' if '✔' in l else '#334155'
        draw.text((675, cur_y), l, fill=color, font=font_txt)
        cur_y += 26
        
    out_p = 'report_assets/fig4_5_synapse_sample_design.png'
    comp.save(out_p, quality=95)
    print(f"Created clean {out_p}, size: {comp.size}")

if __name__ == '__main__':
    make_fig4_4()
    make_fig4_5()
