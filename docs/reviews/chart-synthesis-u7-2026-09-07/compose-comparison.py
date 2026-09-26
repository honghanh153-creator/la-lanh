from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[3]
REVIEW = Path(__file__).resolve().parent
SOURCE = ROOT / "docs/design-directions/home-2026-09-02-v2/02-cosmic-glass-signal.png"
source = Image.open(SOURCE).convert("RGB").resize((417, 834), Image.Resampling.LANCZOS)

for pass_number in (1, 2):
    implementation = Image.open(
        REVIEW / f"home-dark-pass{pass_number}-417x834.png"
    ).convert("RGB")
    canvas = Image.new("RGB", (888, 876), "#11111a")
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 14), "SOURCE · COSMIC GLASS SIGNAL", fill="#f9f2e6")
    draw.text((453, 14), f"IMPLEMENTATION · PASS {pass_number}", fill="#f9f2e6")
    canvas.paste(source, (18, 42))
    canvas.paste(implementation, (453, 42))
    canvas.save(REVIEW / f"comparison-pass{pass_number}.png", quality=95)
