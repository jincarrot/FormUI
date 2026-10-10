"""Static preview using the shipped Fluent textures; requires Pillow.

Run: python tools/preview_fluent_ui.py
This is a design preview, not a screenshot of Minecraft.
"""
from pathlib import Path
from PIL import Image, ImageDraw
from generate_fluent_ui import PALETTES
from preview_flutter_ui import shape as draw_shape, text

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'resource/textures/ui/fluent'


def shape(canvas, name, box, color, scale=1.0):
    draw_shape(canvas, name, box, color, assets=ASSETS, ui_scale=1.0, scale=scale)


def render():
    canvas = Image.new('RGBA', (1180, 810), '#E8EDF2')
    text(canvas, 'FormUI / Fluent Qt', (40, 26), '202020', 27)
    text(canvas, 'Compact window chrome, subtle borders and blue accents', (40, 66), '606060', 16)
    for x, theme in ((32, 'light'), (610, 'dark')):
        c = PALETTES[theme]
        shape(canvas, 'window', (x+3, 121, x+539, 755), 'C8D0D8')
        shape(canvas, 'window', (x, 116, x+536, 750), c['surface'])
        shape(canvas, 'window_outline', (x, 116, x+536, 750), c['frame'])
        shape(canvas, 'app', (x+16, 128, x+34, 146), c['primary'])
        text(canvas, 'Fluent Qt / '+theme.capitalize(), (x+46, 130), c['text'], 14)
        shape(canvas, 'close', (x+504, 130, x+518, 144), c['text'])
        shape(canvas, 'card', (x+12, 158, x+524, 738), c['card'])
        shape(canvas, 'card_outline', (x+12, 158, x+524, 738), c['outline'])
        text(canvas, 'Settings & preferences', (x+32, 181), c['text'], 26)
        text(canvas, 'Personalize your in-game experience', (x+32, 222), c['muted'], 14)
        for bx, by, caption, bg, fg, outlined in (
            (x+32, 265, 'Save changes', c['primary'], c['on_primary'], False),
            (x+282, 265, 'Reset defaults', c['button'], c['text'], True),
            (x+32, 317, 'Outlined', c['button'], c['text'], True),
            (x+282, 317, 'Learn more', None, c['primary'], False)):
            if bg:
                shape(canvas, 'button', (bx, by, bx+222, by+36), bg)
            if outlined:
                shape(canvas, 'button_outline', (bx, by, bx+222, by+36),
                      c['primary'] if caption == 'Outlined' else c['outline'])
            text(canvas, caption, (bx+111, by+18), fg, 15, centered=True)
        for bx, caption, value, dropdown in (
            (x+32, 'Player name', 'Steve', False),
            (x+282, 'Quality', 'Balanced', True)):
            text(canvas, caption, (bx, 386), c['muted'], 14)
            shape(canvas, 'button', (bx, 410, bx+222, 446), c['button'] if dropdown else c['field'])
            shape(canvas, 'button_outline', (bx, 410, bx+222, 446), c['outline'])
            text(canvas, value, (bx+12, 420), c['text'], 15)
            if dropdown:
                shape(canvas, 'chevron', (bx+194, 422, bx+206, 434), c['text'])
            else:
                ImageDraw.Draw(canvas).line((bx+4, 445, bx+218, 445), fill='#'+c['primary'], width=2)
        text(canvas, 'Enable sound', (x+32, 488), c['text'], 16)
        shape(canvas, 'switch', (x+479, 488, x+504, 501), c['primary'], scale=.5)
        shape(canvas, 'circle', (x+493, 490, x+502, 499), c['on_primary'])
        text(canvas, 'Volume', (x+32, 541), c['text'], 14)
        text(canvas, '60', (x+484, 541), c['muted'], 14)
        shape(canvas, 'track', (x+42, 576, x+494, 580), c['track'])
        shape(canvas, 'track', (x+42, 576, x+313, 580), c['primary'])
        shape(canvas, 'circle', (x+301, 566, x+325, 590), c['outline'])
        shape(canvas, 'circle', (x+302, 567, x+324, 589), c['button'])
        shape(canvas, 'circle', (x+307, 572, x+319, 584), c['primary'])
        ImageDraw.Draw(canvas).line((x+32, 619, x+504, 619), fill='#'+c['outline'])
        text(canvas, 'Steve / live preview', (x+32, 642), c['text'], 14)
        text(canvas, 'Title bar: close button only', (x+32, 669), c['muted'], 13)
        shape(canvas, 'button', (x+336, 685, x+504, 721), c['error'])
        text(canvas, 'Close window', (x+420, 703), 'FFFFFF', 14, centered=True)
    text(canvas, 'Static asset preview / final rendering and touch behavior require Minecraft',
         (32, 783), '606060', 13)
    path = ROOT / 'docs/fluent-ui-preview.png'
    canvas.convert('RGB').save(path)
    print(path)


if __name__ == '__main__':
    render()
