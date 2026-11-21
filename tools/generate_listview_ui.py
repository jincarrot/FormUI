"""Generate ListView templates from the shipped theme rows and scrollbars."""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def label(text, color, size, offset, anchor='top_left'):
    return {
        'type': 'label', 'text': text, 'color': color, 'font_type': 'smooth',
        'anchor_from': anchor, 'anchor_to': anchor, 'size': size,
        'max_size': size, 'offset': offset, 'layer': 3,
    }


def build(theme):
    ore = theme == 'oreui'
    source = json.loads((ROOT / 'resource/ui' / (
        'oreui_dropdowns.json' if ore else theme + '.json')).read_text(encoding='utf-8'))
    namespace = 'fui_ore_listviews' if ore else 'fui_' + theme + '_listviews'
    result = {'namespace': namespace}
    for prefix in (('',) if ore else ('', 'dark_')):
        dark = bool(prefix) or ore
        foreground = [0.94, 0.94, 0.94] if dark else [0.13, 0.13, 0.15]
        accent = ([0.35, 0.78, 0.25] if ore else
                  ([0.78, 0.69, 0.98] if dark else [0.40, 0.31, 0.64]) if theme == 'flutter' else
                  ([0.38, 0.75, 1.0] if dark else [0, 0.40, 0.66]))
        scroll = ('fui_ore_panels.scroll_panel_thin' if ore else
                  'fui_' + theme + '.' + prefix + 'scroll')
        row = copy.deepcopy(source['dropdown_items' if ore else prefix + 'dropdown_item@common.button'])
        row.pop('bindings', None)
        row['size'] = ['100%', 32]
        row['offset'] = [0, 0]
        row['layer'] = 1
        # Selection persists independently of native hover/pressed button states.
        row['controls'].append({'selected@fui.w': {
            'visible': False, 'color': accent, 'size': [3, '100%-8px'],
            'anchor_from': 'left_middle', 'anchor_to': 'left_middle',
            'offset': [2, 0], 'layer': 4,
        }})
        result[prefix + 'listview_item' + ('' if ore else '@common.button')] = row
        result[prefix + 'listview'] = {
            'type': 'panel', 'size': ['100%', 160],
            'anchor_from': 'top_left', 'anchor_to': 'top_left',
            'controls': [
                {'label': label('', foreground, ['100%-8px', 20], [4, 0])},
                {'background@fui.w': {
                    'color': ([0.18, 0.18, 0.19] if dark else [0.94, 0.94, 0.96]),
                    'anchor_from': 'top_left', 'anchor_to': 'top_left',
                    'offset': [0, 24], 'size': ['100%', '100%-24px'], 'layer': 0,
                }},
                {'content@' + scroll: {
                    'anchor_from': 'top_left', 'anchor_to': 'top_left',
                    'offset': [4, 28], 'size': ['100%-8px', '100%-32px'], 'layer': 1,
                }},
                {'empty': label('暂无内容', foreground, ['100%-16px', 24], [8, 36])},
            ],
        }
    return result


def main():
    for theme in ('oreui', 'flutter', 'fluent'):
        path = ROOT / 'resource/ui' / (theme + '_listviews.json')
        path.write_text(json.dumps(build(theme), ensure_ascii=False, indent=4) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
