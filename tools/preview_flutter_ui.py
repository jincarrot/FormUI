"""Static palette/texture preview, not a game screenshot. Requires Pillow.

Development use only: python tools/preview_flutter_ui.py
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from generate_flutter_ui import PALETTES, UI_SCALE

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'resource/textures/ui/flutter'


def font(size):
    for path in ('C:/Windows/Fonts/segoeui.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def shape(canvas, name, box, color, assets=ASSETS, ui_scale=UI_SCALE, scale=1.0):
    texture = Image.open(assets / (name+'.png')).convert('RGBA')
    width, height = box[2]-box[0], box[3]-box[1]
    meta = assets / (name+'.json')
    if meta.exists():
        metadata = json.loads(meta.read_text())
        corner = metadata['nineslice_size'][0]
        source_x = round(corner*texture.width/metadata['base_size'][0])
        source_y = round(corner*texture.height/metadata['base_size'][1])
        target_corner = round(corner/ui_scale*scale)
        tx = [0, source_x, texture.width-source_x, texture.width]
        ty = [0, source_y, texture.height-source_y, texture.height]
        dx = [0, target_corner, width-target_corner, width]
        dy = [0, target_corner, height-target_corner, height]
        resized = Image.new('RGBA', (width, height))
        for y in range(3):
            for x in range(3):
                if dx[x+1] <= dx[x] or dy[y+1] <= dy[y]:
                    continue
                patch = texture.crop((tx[x], ty[y], tx[x+1], ty[y+1]))
                patch = patch.resize((dx[x+1]-dx[x], dy[y+1]-dy[y]), Image.Resampling.LANCZOS)
                resized.paste(patch, (dx[x], dy[y]))
    else:
        resized = texture.resize((width, height), Image.Resampling.LANCZOS)
    tinted = Image.new('RGBA', resized.size, '#'+color)
    tinted.putalpha(resized.getchannel('A'))
    canvas.alpha_composite(tinted, (box[0], box[1]))


def text(canvas, value, point, color, size=16, centered=False):
    draw = ImageDraw.Draw(canvas)
    draw.text(point, value, font=font(size), fill='#'+color,
              anchor='mm' if centered else 'lt')


def render():
    canvas = Image.new('RGBA', (1000, 760), '#E6E2ED')
    text(canvas, 'FormUI / Flutter', (42, 26), '1C1B1F', 26)
    text(canvas, 'Material-inspired native controls', (42, 65), '49454F', 15)
    for x, theme in ((32, 'light'), (516, 'dark')):
        c = PALETTES[theme]
        shape(canvas, 'surface', (x+2, 116, x+450, 708), 'CDC7D9')
        shape(canvas, 'surface', (x, 112, x+448, 702), c['surface'])
        text(canvas, theme.capitalize()+' theme', (x+24, 138), c['text'], 23)
        shape(canvas, 'close', (x+396, 138, x+420, 162), c['muted'])
        text(canvas, 'Buttons', (x+24, 193), c['muted'], 14)
        for bx, by, title, bg, fg, outline in (
                (x+24, 219, 'Filled', c['primary'], c['on_primary'], False),
                (x+236, 219, 'Tonal', c['tonal'], c['on_tonal'], False),
                (x+24, 277, 'Outlined', c['surface'], c['primary'], True),
                (x+236, 277, 'Text', c['surface'], c['primary'], False)):
            if title != 'Text':
                shape(canvas, 'pill', (bx, by, bx+188, by+40), bg)
            if outline:
                shape(canvas, 'pill_outline', (bx, by, bx+188, by+40), fg)
            text(canvas, title, (bx+94, by+20), fg, centered=True)
        text(canvas, 'Name', (x+28, 339), c['muted'], 14)
        text(canvas, 'Quality', (x+240, 339), c['muted'], 14)
        for bx in (x+24, x+236):
            shape(canvas, 'field', (bx, 365, bx+188, 405), c['container'])
        shape(canvas, 'field_outline', (x+24, 365, x+212, 405), c['outline'])
        text(canvas, 'Hello, Material', (x+38, 377), c['text'], 15)
        text(canvas, 'Balanced', (x+250, 377), c['text'], 15)
        shape(canvas, 'arrow', (x+394, 377, x+408, 391), c['text'])
        text(canvas, 'Enable effects', (x+24, 446), c['text'])
        shape(canvas, 'switch', (x+396, 447, x+420, 461), c['primary'])
        shape(canvas, 'circle', (x+407, 448, x+418, 459), c['on_primary'])
        text(canvas, 'Volume', (x+24, 506), c['muted'], 14)
        text(canvas, '40', (x+395, 506), c['primary'], 14)
        shape(canvas, 'track', (x+32, 544, x+416, 552), c['tonal'])
        shape(canvas, 'track', (x+32, 544, x+186, 552), c['primary'])
        shape(canvas, 'circle', (x+174, 536, x+198, 560), c['primary'])
        ImageDraw.Draw(canvas).line((x+24, 592, x+424, 592), fill='#'+c['outline'], width=1)
        text(canvas, 'Reactive values. Consistent controls.', (x+24, 618), c['muted'], 14)
        shape(canvas, 'pill', (x+236, 650, x+424, 686), c['error'])
        text(canvas, 'Close', (x+330, 668), c['on_error'], centered=True)
    text(canvas, 'Static asset preview / inspect final rendering in Minecraft', (32, 728), '49454F', 13)
    compact = Image.new('RGBA', canvas.size, '#E6E2ED')
    compact.paste(canvas.crop((0, 0, 1000, 100)), (0, 0))
    compact.paste(canvas.crop((0, 714, 1000, 760)), (0, 714))
    for x in (32, 516):
        region = canvas.crop((x, 112, x+450, 708))
        smaller = region.resize((round(450*UI_SCALE), round(596*UI_SCALE)), Image.Resampling.LANCZOS)
        compact.alpha_composite(smaller, (x+(450-smaller.width)//2, 112+(596-smaller.height)//2))
    path = ROOT / 'docs/flutter-ui-preview.png'
    compact.convert('RGB').save(path)
    print(path)


if __name__ == '__main__':
    render()
