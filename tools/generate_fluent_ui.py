"""Generate Fluent Qt inspired native UI. Development use, Python 3 only.

Run: python tools/generate_fluent_ui.py
Geometry rasterization uses the existing standard-library texture helpers.
"""
import json
import math
from pathlib import Path
from generate_flutter_ui import high_resolution_png, rounded_distance, rgb, blend, scale_switches, capsule_textures

ROOT = Path(__file__).resolve().parents[1]
NS = 'fui_fluent'
TEXTURES = ROOT / 'resource/textures/ui/fluent'
ROUNDED_TEXTURES = {
    'button': (20, 4, 0), 'button_outline': (20, 4, 1),
    'window': (32, 8, 0), 'window_outline': (32, 8, 1),
    'card': (24, 6, 0), 'card_outline': (24, 6, 1),
    'track': (8, .5, 0),
}
PALETTES = {
    'light': dict(primary='0078D4', on_primary='FFFFFF', surface='F3F3F3',
                  card='FBFBFB', button='FFFFFF', field='FFFFFF',
                  text='202020', muted='606060', outline='D1D1D1',
                  frame='BFBFBF', track='8A8A8A', error='C42B1C'),
    'dark': dict(primary='60CDFF', on_primary='003E5C', surface='202020',
                 card='272727', button='323232', field='2D2D2D',
                 text='F5F5F5', muted='C5C5C5', outline='494949',
                 frame='555555', track='9A9A9A', error='C42B1C'),
}


def texture_slice(radius):
    return [radius+1] * 4


def textures():
    TEXTURES.mkdir(parents=True, exist_ok=True)
    for name, (size, radius, stroke) in ROUNDED_TEXTURES.items():
        def contains(x, y, size=size, radius=radius, stroke=stroke):
            d = rounded_distance(x, y, size, radius)
            return d <= 0 and (not stroke or d >= -stroke)
        (TEXTURES / (name+'.png')).write_bytes(high_resolution_png(size, contains))
        (TEXTURES / (name+'.json')).write_text(json.dumps({
            'base_size': [size, size], 'nineslice_size': texture_slice(radius)}, indent=2)+'\n')
    (TEXTURES / 'circle.png').write_bytes(high_resolution_png(32,
        lambda x, y: math.hypot(x-16, y-16) <= 15))
    (TEXTURES / 'close.png').write_bytes(high_resolution_png(24,
        lambda x, y: 5 <= x <= 19 and 5 <= y <= 19 and min(abs(x-y), abs(x+y-24)) <= .8))
    (TEXTURES / 'chevron.png').write_bytes(high_resolution_png(16,
        lambda x, y: 3 <= x <= 13 and abs(y-(11-abs(x-8))) <= .7))
    (TEXTURES / 'app.png').write_bytes(high_resolution_png(24,
        lambda x, y: 3 <= x <= 21 and 3 <= y <= 21 and abs(x-12) >= 1 and abs(y-12) >= 1))
    capsule_textures(TEXTURES, 40, 20)


def image(color, texture='button', **extra):
    result = dict(type='image', texture='textures/ui/fluent/'+texture,
                  color=color, size=['100%', '100%'], layer=0, bilinear=True)
    if texture in ROUNDED_TEXTURES:
        result['nineslice_size'] = texture_slice(ROUNDED_TEXTURES[texture][1])
    result.update(extra)
    return result


def label(color, **extra):
    result = dict(type='label', color=color, font_type='smooth', font_size='normal',
                  font_scale_factor=1.0, text='', max_size=['100%', '100%'], layer=2)
    result.update(extra)
    return result


def panel(size, controls, **extra):
    result = dict(type='panel', size=size, anchor_from='top_left',
                  anchor_to='top_left', controls=controls)
    result.update(extra)
    return result


def button(c, kind='button', arrow=False, close=False):
    primary = kind == 'primary_button'
    danger = kind == 'danger_button'
    link = kind == 'hyperlink_button'
    bg = c['primary'] if primary else c['error'] if danger else c['button']
    fg = c['on_primary'] if primary else [1, 1, 1] if danger else c['primary'] if link else c['text']
    result = {'type': 'button', 'size': ['100%', '100%'],
              '$pressed_button_name': '%netease_editor_template_namespace.click',
              'button_mappings': [], 'is_handle_button_move_event': True,
              'default_control': 'default', 'hover_control': 'hover',
              'pressed_control': 'pressed', 'controls': []}
    for state, alpha in (('default', 0), ('hover', .05), ('pressed', .10)):
        controls = []
        state_fg = fg
        if close:
            state_fg = [1, 1, 1] if alpha else c['text']
            if alpha:
                controls.append({'background': image(
                    c['error'] if state == 'hover' else blend(c['error'], [0, 0, 0], .15),
                    'button')})
        elif not link:
            controls.append({'background': image(blend(bg, fg, alpha))})
            if not primary and not danger:
                controls.append({'outline': image(c['outline'], 'button_outline', layer=1)})
                controls.append({'bottom_edge@fui.w': {
                    'size': ['100%-8px', 1], 'color': c['outline'], 'layer': 1,
                    'anchor_from': 'bottom_middle', 'anchor_to': 'bottom_middle', 'offset': [0, -1]}})
        elif alpha:
            controls.append({'background': image(blend(c['card'], c['text'], alpha))})
        if close:
            controls.append({'icon': image(state_fg, 'close', size=[14, 14], layer=2)})
        else:
            controls.append({'label': label(state_fg, **({
                'anchor_from': 'left_middle', 'anchor_to': 'left_middle',
                'offset': [12, 0], 'max_size': ['100%-36px', '100%']} if arrow else {
                'max_size': ['100%-20px', '100%']}))})
        if arrow:
            controls.append({'chevron': image(fg, 'chevron', size=[12, 12], layer=2,
                anchor_from='right_middle', anchor_to='right_middle', offset=[-10, 0])})
        result['controls'].append({state: dict(type='panel', visible=state == 'default', controls=controls)})
    return result


def build():
    ui = {'namespace': NS}
    for theme, palette in PALETTES.items():
        c = {key: rgb(value) for key, value in palette.items()}
        prefix = '' if theme == 'light' else 'dark_'
        def ref(name):
            return NS+'.'+prefix+name
        for kind in ('primary_button', 'button', 'outlined_button', 'hyperlink_button', 'danger_button'):
            native = button(c, kind)
            if kind == 'outlined_button':
                for entry in native['controls']:
                    state = next(iter(entry.values()))
                    for child in state['controls']:
                        if 'outline' in child:
                            child['outline']['color'] = c['primary']
            ui[prefix+kind+'_native@common.button'] = native
            ui[prefix+kind] = panel(['100%', 38], [{
                'button@'+ref(kind+'_native'): {'size': ['100%', 30]}}])
        ui[prefix+'label'] = panel(['100%', '100%c'], [{'label': label(c['text'],
            anchor_from='top_left', anchor_to='top_left', max_size=['100%', 'default'])}])
        ui[prefix+'divider'] = panel(['100%', 14], [{'line@fui.w': {
            'size': ['100%', 1], 'color': c['outline']}}])
        for checked in (False, True):
            name = 'checked' if checked else 'unchecked'
            for hover in (False, True):
                controls = [{'track': image(blend(c['primary'] if checked else c['card'],
                    c['text'], .06 if hover else 0), 'switch',
                    nineslice_size=[0, 0, 0, 0], keep_ratio=False)}]
                if not checked:
                    controls.append({'outline': image(c['track'], 'switch_outline', layer=1,
                        nineslice_size=[0, 0, 0, 0], keep_ratio=False)})
                controls.append({'thumb': image(c['on_primary'] if checked else c['muted'], 'circle',
                    size=[14, 14], layer=2, anchor_from='right_middle' if checked else 'left_middle',
                    anchor_to='right_middle' if checked else 'left_middle',
                    offset=[-3, 0] if checked else [3, 0])})
                ui[prefix+'switch_'+name+('_hover' if hover else '')] = dict(type='panel', controls=controls)
        switch = {'size': [40, 20]}
        for checked in ('checked', 'unchecked'):
            for state in ('', '_hover', '_locked', '_locked_hover'):
                switch['$'+checked+state+'_control'] = ref('switch_'+checked+('_hover' if 'hover' in state else ''))
        ui[prefix+'switch@common_toggles.switch_toggle'] = switch
        ui[prefix+'toggle'] = panel(['100%', 38], [
            {'label': label(c['text'], anchor_from='left_middle', anchor_to='left_middle',
                            max_size=['100%-52px', '100%'])},
            {'toggle@'+ref('switch'): {'anchor_from': 'right_middle',
                                     'anchor_to': 'right_middle', 'offset': [-4, 0]}}])
        for hover in (False, True):
            ui[prefix+'field_background'+('_hover' if hover else '')] = dict(type='panel', layer=-1, controls=[
                {'fill': image(c['field'])},
                {'outline': image(c['outline'], 'button_outline', layer=1)},
                {'underline@fui.w': {'size': ['100%-6px', 2 if hover else 1],
                    'color': c['primary'] if hover else c['track'], 'layer': 2,
                    'anchor_from': 'bottom_middle', 'anchor_to': 'bottom_middle', 'offset': [0, -1]}}])
        ui[prefix+'textfield_native@common.text_edit_box'] = {
            'type': 'edit_box', '$text_background_default': ref('field_background'),
            '$text_background_hover': ref('field_background_hover'), '$text_box_text_color': c['text'],
            '$place_holder_text_color': c['muted'], '$place_holder_text': '', '$font_size': 'normal',
            '$font_scale_factor': 1.0, '$text_box_name': '%netease_editor_template_namespace.message',
            '$text_edit_box_content_binding_name': '#netease_editor_template_namespace.message_content',
            '$text_edit_box_label_anchor_point': 'right_middle', '$text_edit_box_label_min_size': ['100%-20px', 0],
            '$text_edit_box_label_size': ['default', 'default'], 'max_length': 512,
            'anchor_from': 'bottom_middle', 'anchor_to': 'bottom_middle', 'size': ['100%', 30]}
        ui[prefix+'textfield'] = panel(['100%', 56], [
            {'label': label(c['muted'], anchor_from='top_left', anchor_to='top_left',
                offset=[0, 2], max_size=['100%', 16])},
            {'textfield@'+ref('textfield_native'): {'offset': [0, -6]}}])
        ui[prefix+'dropdown_native@common.button'] = button(c, arrow=True)
        ui[prefix+'dropdown'] = panel(['100%', 56], [
            {'label': label(c['muted'], anchor_from='top_left', anchor_to='top_left',
                offset=[0, 2], max_size=['100%', 16])},
            {'dropdown_box@'+ref('dropdown_native'): {'anchor_from': 'bottom_middle',
                'anchor_to': 'bottom_middle', 'offset': [0, -6], 'size': ['100%', 30], 'layer': 1}},
            {'content_panel': panel(['100%', 30], [
                {'background': image(c['card'], 'card')},
                {'outline': image(c['outline'], 'card_outline', layer=1)}],
                anchor_from='top_middle', anchor_to='top_middle', offset=[0, 20], layer=6, visible=False)}])
        item = button(c, 'hyperlink_button')
        item['size'], item['layer'] = ['100%', 30], 7
        # Runtime row offsets are measured from the menu's top, not its center.
        item.update(anchor_from='top_middle', anchor_to='top_middle', offset=[0, 0])
        for entry in item['controls']:
            state = next(iter(entry.values()))
            state['controls'] = [child for child in state['controls'] if 'label' not in child]
        item['controls'].append({'button_label': label(c['text'], anchor_from='left_middle',
            anchor_to='left_middle', offset=[12, 0], max_size=['100%-24px', '100%'])})
        ui[prefix+'dropdown_item@common.button'] = item
        ui[prefix+'slider_thumb'] = dict(type='panel', layer=3, controls=[
            {'border': image(c['outline'], 'circle')},
            {'surface': image(c['button'], 'circle', size=['90%', '90%'], layer=1)},
            {'dot': image(c['primary'], 'circle', size=['60%', '60%'], layer=2)}])
        ui[prefix+'slider_native@fui_ore_sliders.slider_common'] = {
            '$slider_name': 'netease_slider_name', '$slider_direction': 'horizontal', '$slider_box_size': [18, 18],
            **{'$slider_box'+state+'_layout': ref('slider_thumb') for state in ('', '_hover', '_indent', '_locked')},
            'default_control': 'track', 'hover_control': 'track_hover',
            'progress_control': 'progress', 'progress_hover_control': 'progress_hover',
            'controls': [
                {'slider_box@common.slider_box': {'$slider_box_layout': '$slider_box_layout',
                    '$slider_box_size': '$slider_box_size', '$slider_track_button': '$slider_name'}},
                {'track': image(c['track'], 'track', size=['100%', 3])},
                {'track_hover': image(c['track'], 'track', size=['100%', 3], visible=False)},
                {'progress': image(c['primary'], 'track', size=['100%', 3], clip_direction='left')},
                {'progress_hover': image(c['primary'], 'track', size=['100%', 3], clip_direction='left', visible=False)}]}
        ui[prefix+'slider'] = panel(['100%', 52], [
            {'label': label(c['text'], anchor_from='top_left', anchor_to='top_left', offset=[0, 2],
                max_size=['100%-40px', 16])},
            {'value': label(c['muted'], anchor_from='top_right', anchor_to='top_right', offset=[0, 2])},
            {'slider@'+ref('slider_native'): {'anchor_from': 'bottom_middle', 'anchor_to': 'bottom_middle',
                'offset': [0, -10], 'size': ['100%-18px', 18]}}])
        ui[prefix+'close@common.button'] = button(c, close=True)
        ui[prefix+'scroll_thumb'] = image(c['track'], 'track')
        ui[prefix+'scroll_track@fui.blank'] = {}
        ui[prefix+'scroll@common.scrolling_panel'] = {
            '$scroll_background_image_control': 'fui.blank', '$show_background': False,
            '$scrolling_content': 'fui_ore_panels.scrolling_content',
            '$scroll_box_mouse_image_control': ref('scroll_thumb'), '$scroll_box_touch_image_control': ref('scroll_thumb'),
            '$scroll_track_image_control': ref('scroll_track'), '$scroll_size': [4, '100%'],
            '$scroll_size_touch': [4, '100%'], '$scroll_bar_contained': True,
            '$scroll_box_size': ['100%', '100%'], '$scroll_box_visible_touch': True, '$use_touch_mode': True,
            '$scroll_bar_and_track_size': ['100%c', '100%-4px'], '$scroll_bar_right_padding_size': [0, 0],
            '$scroll_view_port_offset': [0, 0], '$scroll_view_port_offset_touch': [0, 0],
            '$scroll_view_port_size': ['100%-8px', '100%-4px'], '$scroll_view_port_size_touch': ['100%-8px', '100%-4px']}
        ui[theme+'_panel'] = panel(['92%y', '80%'], [
            {'shadow': image([0, 0, 0], 'window', alpha=.18, offset=[0, 3])},
            {'background': image(c['surface'], 'window', layer=1)},
            {'border': image(c['frame'], 'window_outline', layer=2)},
            {'header': panel(['100%', 32], [
                {'app': image(c['primary'], 'app', size=[14, 14], layer=2,
                    anchor_from='left_middle', anchor_to='left_middle', offset=[12, 0])},
                {'title': label(c['text'], anchor_from='left_middle', anchor_to='left_middle',
                    offset=[34, 0], max_size=['100%-92px', '100%'])},
                {'close@'+ref('close'): {'size': [40, 28], 'anchor_from': 'right_middle',
                    'anchor_to': 'right_middle', 'offset': [-4, 0]}}], layer=8)},
            {'body': panel(['100%-20px', '100%-44px'], [
                {'background': image(c['card'], 'card')},
                {'border': image(c['outline'], 'card_outline', layer=1)}], offset=[10, 34], layer=2)},
            {'content@'+ref('scroll'): {'size': ['100%-44px', '100%-68px'],
                'anchor_from': 'top_left', 'anchor_to': 'top_left', 'offset': [22, 46], 'layer': 3}}],
            anchor_from='center', anchor_to='center')
    scale_switches(ui)
    return ui


if __name__ == '__main__':
    textures()
    target = ROOT / 'resource/ui/fluent.json'
    target.write_text(json.dumps(build(), ensure_ascii=False, indent=4)+'\n', encoding='utf-8')
    print('Generated %s and textures/ui/fluent/' % target)
