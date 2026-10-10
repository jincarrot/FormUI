"""Build Material-inspired JSON UI and white, tintable textures.

Development tool, Python 3 standard library only. No runtime dependencies.
Run: python tools/generate_flutter_ui.py
"""
import json
import math
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / 'resource/textures/ui/flutter'
NS = 'fui_flutter'
TEXTURE_SCALE = 4
UI_SCALE = 0.85
ROUNDED_TEXTURES = {
    'pill': (28, 12, 0), 'pill_outline': (28, 12, 1),
    'surface': (36, 16, 0), 'field': (20, 8, 0),
    'field_outline': (20, 8, 1), 'track': (8, 2, 0),
}
PALETTES = {
    'light': dict(primary='6750A4', on_primary='FFFFFF', surface='FFFBFE',
                  container='F3EDF7', tonal='E8DEF8', on_tonal='1D192B',
                  text='1C1B1F', muted='49454F', outline='79747E',
                  error='B3261E', on_error='FFFFFF'),
    'dark': dict(primary='D0BCFF', on_primary='381E72', surface='1C1B1F',
                 container='2B2930', tonal='4A4458', on_tonal='E8DEF8',
                 text='E6E1E5', muted='CAC4D0', outline='938F99',
                 error='F2B8B5', on_error='601410'),
}


def rgb(value):
    return [round(int(value[i:i+2], 16) / 255.0, 6) for i in (0, 2, 4)]


def blend(base, overlay, alpha):
    return [round(a * (1-alpha) + b * alpha, 6) for a, b in zip(base, overlay)]


def chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack(
        '>I', zlib.crc32(kind + payload) & 0xffffffff)


def png(size, contains):
    width, height = size if isinstance(size, tuple) else (size, size)
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            coverage = sum(contains(x+(sx+.5)/4, y+(sy+.5)/4)
                           for sy in range(4) for sx in range(4))
            rows.extend((255, 255, 255, round(coverage * 255 / 16)))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack(
        '>IIBBBBB', width, height, 8, 6, 0, 0, 0)) +
        chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def rounded_distance(x, y, size, radius):
    qx, qy = abs(x-size/2)-(size/2-radius), abs(y-size/2)-(size/2-radius)
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - radius


def texture_slice(radius):
    return [round((radius+1)*UI_SCALE, 4)] * 4


def high_resolution_png(size, contains):
    return png(size*TEXTURE_SCALE, lambda x, y: contains(x/TEXTURE_SCALE, y/TEXTURE_SCALE))


def capsule_textures(folder, width, height, stroke=1):
    """Complete capsule masks at the switch aspect ratio; no nine slicing."""
    radius = height/2
    for name, border in (('switch', 0), ('switch_outline', stroke)):
        def contains(x, y, border=border):
            x, y = x/TEXTURE_SCALE, y/TEXTURE_SCALE
            dx = max(abs(x-width/2)-(width-height)/2, 0)
            distance = math.hypot(dx, y-height/2)-radius
            return distance <= 0 and (not border or distance >= -border)
        (folder / (name+'.png')).write_bytes(png(
            (width*TEXTURE_SCALE, height*TEXTURE_SCALE), contains))
        (folder / (name+'.json')).write_text(json.dumps({
            'base_size': [width, height], 'nineslice_size': [0, 0, 0, 0]}, indent=2)+'\n')


def textures():
    TEXTURES.mkdir(parents=True, exist_ok=True)
    for name, (size, radius, stroke) in ROUNDED_TEXTURES.items():
        def contains(x, y, size=size, radius=radius, stroke=stroke):
            distance = rounded_distance(x, y, size, radius*UI_SCALE)
            return distance <= 0 and (not stroke or distance >= -stroke*UI_SCALE)
        (TEXTURES / (name + '.png')).write_bytes(high_resolution_png(size, contains))
        # Logical base size stays independent of the physical 4x texture pixels.
        (TEXTURES / (name + '.json')).write_text(json.dumps(
            {'nineslice_size': texture_slice(radius), 'base_size': [size, size]}, indent=2)+'\n')
    (TEXTURES / 'circle.png').write_bytes(high_resolution_png(32, lambda x, y: math.hypot(x-16, y-16) <= 15))
    (TEXTURES / 'close.png').write_bytes(high_resolution_png(24, lambda x, y:
        5 <= x <= 19 and 5 <= y <= 19 and min(abs(x-y), abs(x+y-24)) <= 1.2))
    (TEXTURES / 'arrow.png').write_bytes(high_resolution_png(16, lambda x, y:
        4 <= y <= 11 and abs(x-8) <= (11-y)*.8))
    capsule_textures(TEXTURES, 46, 26)


def image(color, texture='pill', **extra):
    result = dict(type='image', texture='textures/ui/flutter/'+texture,
                  color=color, size=['100%', '100%'], layer=0, bilinear=True)
    # Icons/circles are scaled; only backgrounds use nine slicing.
    if texture in ROUNDED_TEXTURES:
        result['nineslice_size'] = texture_slice(ROUNDED_TEXTURES[texture][1])
    result.update(extra)
    return result


def label(color, **extra):
    result = dict(type='label', color=color, font_type='smooth',
                  font_scale_factor=1.0, text='', max_size=['100%', '100%'], layer=2)
    result.update(extra)
    return result


def panel(size, controls, **extra):
    result = dict(type='panel', size=size, anchor_from='top_left',
                  anchor_to='top_left', controls=controls)
    result.update(extra)
    return result


def button(bg, fg, outlined=False, text_only=False, arrow=False, icon=False):
    result = {'type': 'button', 'size': ['100%', '100%'],
              '$pressed_button_name': '%netease_editor_template_namespace.click',
              'button_mappings': [], 'is_handle_button_move_event': True,
              'default_control': 'default', 'hover_control': 'hover',
              'pressed_control': 'pressed', 'controls': []}
    for state, alpha in (('default', 0), ('hover', .08), ('pressed', .16)):
        controls = []
        if not text_only or alpha:
            controls.append({'background': image(blend(bg, fg, alpha))})
        if outlined:
            controls.append({'outline': image(fg, 'pill_outline', layer=1)})
        if icon:
            controls.append({'icon': image(fg, 'close', size=[18, 18], layer=2)})
        else:
            controls.append({'label': label(fg,
                **({'anchor_from': 'left_middle', 'anchor_to': 'left_middle',
                    'offset': [12, 0], 'max_size': ['100%-40px', '100%']} if arrow else
                   {'max_size': ['100%-32px', '100%']}))})
        if arrow:
            controls.append({'arrow': image(fg, 'arrow', size=[12, 12], layer=2,
                anchor_from='right_middle', anchor_to='right_middle', offset=[-12, 0])})
        result['controls'].append({state: dict(type='panel', visible=state=='default', controls=controls)})
    return result


def scale_layout(node):
    """Scale absolute layout units/fonts while preserving parent percentages and metadata."""
    def dimension(value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return round(value*UI_SCALE, 4)
        if isinstance(value, str):
            return re.sub(r'\d+(?:\.\d+)?(?=px)',
                          lambda match: '%g' % (float(match.group())*UI_SCALE), value)
        if isinstance(value, list):
            return [dimension(item) for item in value]
        return value
    if isinstance(node, dict):
        for key, value in list(node.items()):
            name = key.split('|')[0].lstrip('$')
            if (name != 'nineslice_size' and (name in ('size', 'offset', 'min_size', 'max_size')
                    or name.endswith(('_size', '_offset', 'font_scale_factor')))):
                node[key] = dimension(value)
            else:
                scale_layout(value)
    elif isinstance(node, list):
        for child in node:
            scale_layout(child)


def scale_switches(ui, scale=.5):
    """Shrink switch geometry only, retaining text and the row's layout."""
    for prefix in ('', 'dark_'):
        switch = ui[prefix+'switch@common_toggles.switch_toggle']
        switch['size'] = [round(value*scale, 4) for value in switch['size']]
        for checked in ('checked', 'unchecked'):
            for state in ('', '_hover'):
                visual = ui[prefix+'switch_'+checked+state]
                for entry in visual['controls']:
                    node = next(iter(entry.values()))
                    for key in ('size', 'offset'):
                        if key in node:
                            node[key] = [round(value*scale, 4) if isinstance(value, (int, float))
                                         else value for value in node[key]]


def build():
    ui = {'namespace': NS}
    for theme, palette in PALETTES.items():
        c = {key: rgb(value) for key, value in palette.items()}
        prefix = '' if theme == 'light' else 'dark_'
        def ref(name):
            return NS+'.'+prefix+name
        for kind, bg, fg, outlined, text_only in (
            ('filled_button', c['primary'], c['on_primary'], False, False),
            ('tonal_button', c['tonal'], c['on_tonal'], False, False),
            ('outlined_button', c['surface'], c['primary'], True, False),
            ('text_button', c['surface'], c['primary'], False, True),
            ('danger_button', c['error'], c['on_error'], False, False)):
            ui[prefix+kind+'_native@common.button'] = button(bg, fg, outlined, text_only)
            ui[prefix+kind] = panel(['100%', 44], [{
                'button@'+ref(kind+'_native'): {'size': ['100%', 36]}}])
        ui[prefix+'label'] = panel(['100%', '100%c'], [{'label': label(c['text'],
            anchor_from='top_left', anchor_to='top_left', max_size=['100%', 'default'])}])
        ui[prefix+'divider'] = panel(['100%', 16], [{'line@fui.w': {
            'size': ['100%', 1], 'color': blend(c['surface'], c['outline'], .4)}}])

        # Native switch_toggle retains the SDK's /this_toggle control and input behavior.
        for checked in (False, True):
            name = 'checked' if checked else 'unchecked'
            for hover in (False, True):
                ui[prefix+'switch_'+name+('_hover' if hover else '')] = dict(type='panel', controls=[
                    {'track': image(blend(c['primary'] if checked else c['container'],
                                         c['text'], .08 if hover else 0), 'switch',
                                    nineslice_size=[0, 0, 0, 0], keep_ratio=False)},
                    *([] if checked else [{'outline': image(c['outline'], 'switch_outline', layer=1,
                        nineslice_size=[0, 0, 0, 0], keep_ratio=False)}]),
                    {'thumb': image(c['on_primary'] if checked else c['outline'], 'circle',
                        size=[20, 20] if checked else [16, 16], layer=2,
                        anchor_from='right_middle' if checked else 'left_middle',
                        anchor_to='right_middle' if checked else 'left_middle',
                        offset=[-3, 0] if checked else [5, 0])}])
        switch = {'size': [46, 26]}
        for checked in ('checked', 'unchecked'):
            for state in ('', '_hover', '_locked', '_locked_hover'):
                switch['$'+checked+state+'_control'] = ref('switch_'+checked+('_hover' if 'hover' in state else ''))
        ui[prefix+'switch@common_toggles.switch_toggle'] = switch
        ui[prefix+'toggle'] = panel(['100%', 44], [
            {'label': label(c['text'], anchor_from='left_middle', anchor_to='left_middle',
                            max_size=['100%-60px', '100%'])},
            {'toggle@'+ref('switch'): {'anchor_from': 'right_middle',
                                     'anchor_to': 'right_middle', 'offset': [-4, 0]}}])

        for state in ('', '_hover'):
            ui[prefix+'field_background'+state] = dict(type='panel', layer=-1, controls=[
                {'fill': image(c['container'], 'field')},
                {'outline': image(c['primary'] if state else c['outline'], 'field_outline', layer=1)}])
        ui[prefix+'textfield_native@common.text_edit_box'] = {
            'type': 'edit_box', '$text_background_default': ref('field_background'),
            '$text_background_hover': ref('field_background_hover'),
            '$text_box_text_color': c['text'], '$place_holder_text_color': c['muted'],
            '$place_holder_text': '', '$font_size': 'normal', '$font_scale_factor': 1.0,
            '$text_box_name': '%netease_editor_template_namespace.message',
            '$text_edit_box_content_binding_name': '#netease_editor_template_namespace.message_content',
            '$text_edit_box_label_anchor_point': 'right_middle',
            '$text_edit_box_label_min_size': ['100%-24px', 0],
            '$text_edit_box_label_size': ['default', 'default'], 'max_length': 512,
            'anchor_from': 'bottom_middle', 'anchor_to': 'bottom_middle', 'size': ['100%', 36]}
        ui[prefix+'textfield'] = panel(['100%', 64], [
            {'label': label(c['muted'], anchor_from='top_left', anchor_to='top_left',
                            offset=[4, 2], max_size=['100%-8px', 18])},
            {'textfield@'+ref('textfield_native'): {'offset': [0, -8]}}])

        ui[prefix+'dropdown_native@common.button'] = button(c['container'], c['text'], arrow=True)
        ui[prefix+'dropdown'] = panel(['100%', 64], [
            {'label': label(c['muted'], anchor_from='top_left', anchor_to='top_left', offset=[4, 2],
                            max_size=['100%-8px', 18])},
            {'dropdown_box@'+ref('dropdown_native'): {'anchor_from': 'bottom_middle',
                'anchor_to': 'bottom_middle', 'offset': [0, -8], 'size': ['100%', 36], 'layer': 1}},
            {'content_panel': panel(['100%', 36], [
                {'background': image(c['container'], 'field')},
                {'outline': image(blend(c['container'], c['outline'], .4), 'field_outline', layer=1)}],
                anchor_from='top_middle', anchor_to='top_middle', offset=[0, 20], layer=6, visible=False)}])
        item = button(c['container'], c['text'])
        item['size'], item['layer'] = ['100%', 36], 7
        # Runtime row offsets are measured from the menu's top, not its center.
        item.update(anchor_from='top_middle', anchor_to='top_middle', offset=[0, 0])
        # The library updates a single label shared by all three button states.
        for entry in item['controls']:
            state = next(iter(entry.values()))
            state['controls'] = [child for child in state['controls'] if 'label' not in child]
        item['controls'].append({'button_label': label(c['text'], anchor_from='left_middle',
            anchor_to='left_middle', offset=[12, 0], max_size=['100%-24px', '100%'])})
        ui[prefix+'dropdown_item@common.button'] = item

        # Reuse the existing slider input bindings while replacing every visual child.
        ui[prefix+'slider_native@fui_ore_sliders.slider_common'] = {
            '$slider_name': 'netease_slider_name', '$slider_direction': 'horizontal',
            '$slider_box_size': [20, 20],
            **{'$slider_box'+state+'_layout': ref('slider_thumb')
               for state in ('', '_hover', '_indent', '_locked')},
            'default_control': 'track', 'hover_control': 'track_hover',
            'progress_control': 'progress', 'progress_hover_control': 'progress_hover',
            'controls': [
                {'slider_box@common.slider_box': {'$slider_box_layout': '$slider_box_layout',
                    '$slider_box_size': '$slider_box_size', '$slider_track_button': '$slider_name'}},
                {'track': image(c['tonal'], 'track', size=['100%', 6])},
                {'track_hover': image(c['tonal'], 'track', size=['100%', 6], visible=False)},
                {'progress': image(c['primary'], 'track', size=['100%', 6], clip_direction='left')},
                {'progress_hover': image(c['primary'], 'track', size=['100%', 6],
                                         clip_direction='left', visible=False)}]}
        ui[prefix+'slider_thumb'] = image(c['primary'], 'circle', layer=3)
        ui[prefix+'slider'] = panel(['100%', 60], [
            {'label': label(c['muted'], anchor_from='top_left', anchor_to='top_left',
                            offset=[4, 2], max_size=['100%-52px', 18])},
            {'value': label(c['primary'], anchor_from='top_right', anchor_to='top_right', offset=[-4, 2])},
            {'slider@'+ref('slider_native'): {'anchor_from': 'bottom_middle',
                'anchor_to': 'bottom_middle', 'offset': [0, -16], 'size': ['100%-24px', 20]}}])

        ui[prefix+'close@common.button'] = button(c['surface'], c['muted'], text_only=True, icon=True)
        ui[prefix+'scroll_thumb'] = image(blend(c['surface'], c['outline'], .65), 'track')
        ui[prefix+'scroll_track@fui.blank'] = {}
        ui[prefix+'scroll@common.scrolling_panel'] = {
            '$scroll_background_image_control': 'fui.blank', '$show_background': False,
            '$scrolling_content': 'fui_ore_panels.scrolling_content',
            '$scroll_box_mouse_image_control': ref('scroll_thumb'),
            '$scroll_box_touch_image_control': ref('scroll_thumb'),
            '$scroll_track_image_control': ref('scroll_track'),
            '$scroll_size': [6, '100%'], '$scroll_size_touch': [6, '100%'],
            '$scroll_bar_contained': True, '$scroll_box_size': ['100%', '100%'],
            '$scroll_box_visible_touch': True, '$use_touch_mode': True,
            '$scroll_bar_and_track_size': ['100%c', '100%-4px'],
            '$scroll_bar_right_padding_size': [0, 0],
            '$scroll_view_port_offset': [0, 0], '$scroll_view_port_offset_touch': [0, 0],
            '$scroll_view_port_size': ['100%-10px', '100%-4px'],
            '$scroll_view_port_size_touch': ['100%-10px', '100%-4px']}
        ui[theme+'_panel'] = panel(['61.2%y', '76.5%'], [
            {'shadow': image([0, 0, 0], 'surface', alpha=.18, offset=[0, 3])},
            {'background': image(c['surface'], 'surface', layer=1)},
            {'header': panel(['100%', 52], [
                {'title': label(c['text'], anchor_from='left_middle', anchor_to='left_middle',
                    offset=[20, 0], font_scale_factor=1.5, max_size=['100%-80px', '100%'])},
                {'close@'+ref('close'): {'size': [32, 32], 'anchor_from': 'right_middle',
                    'anchor_to': 'right_middle', 'offset': [-12, 0]}}], layer=8)},
            {'content@'+ref('scroll'): {'size': ['100%-32px', '100%-68px'],
                'anchor_from': 'top_left', 'anchor_to': 'top_left', 'offset': [16, 52], 'layer': 2}}],
            anchor_from='center', anchor_to='center')
    scale_layout(ui)
    scale_switches(ui)
    return ui


if __name__ == '__main__':
    textures()
    target = ROOT / 'resource/ui/flutter.json'
    target.write_text(json.dumps(build(), ensure_ascii=False, indent=4)+'\n', encoding='utf-8')
    print('Generated %s and textures/ui/flutter/' % target)
