"""Offline SDK-call counts; these are workload measurements, not game FPS."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
import test_group_controls as groups
import test_listview as lists


def measure():
    fx = groups.GroupControlTests()
    fx.setUp()
    try:
        form = fx.make_form(width=400, height=300)
        for index in range(500):
            form.label(str(index), {'class': 'label', 'height': 20})
        for index in range(100):
            form.slider('value', 50, 0, 100, 1, {'class': 'slider'})
        fid, _ = fx.add(form)
        label_type = type(fx.ui.getControl(fid, 500).children['/value'])
        grid_module = sys.modules[fx.prefix + '.client.ui.grid']
        visits = [0]
        original = getattr(grid_module, 'iterControls', None)
        def counted(controls):
            for entry in original(controls):
                visits[0] += 1
                yield entry
        with patch.object(label_type, 'SetText', autospec=True) as writes:
            with patch.object(grid_module, 'iterControls', counted, create=True):
                for frame in range(60):
                    fx.ui.Update()
            result = {'idle_60_frames': {'slider_label_writes': writes.call_count,
                                       'grid_control_visits': visits[0]}}
        value = fx.system.observableManager.create('before')
        fx.register('performance:group', {
            'label': {'class': 'label', 'size': ['100%', 20]},
        })
        fid, _ = fx.add(fx.group_form('performance:group', {'label': {'label': value}}))
        child = fx.ui.getControl(fid, (0, 'label'))
        with patch.object(child, 'SetFullSize', wraps=child.SetFullSize) as sizes, \
                patch.object(child, 'SetFullPosition', wraps=child.SetFullPosition) as positions:
            value.setValue('after')
            result['label_update'] = {'group_geometry_writes': sizes.call_count + positions.call_count}
    finally:
        fx.tearDown()
    fx = lists.ListViewTests()
    fx.setUp()
    try:
        selected = fx.create(1)
        fid, _ = fx.fx.add(fx.form([{'label': str(i), 'value': i} for i in range(1000)], selected))
        native_type = type(fx.rows(fid)[0][0].children['/selected'])
        with patch.object(native_type, 'SetVisible', autospec=True) as writes:
            selected.setValue(999)
            result['listview_1000_rows'] = {'selection_visibility_writes': writes.call_count}
    finally:
        fx.tearDown()
    return result


if __name__ == '__main__':
    print(json.dumps(measure(), indent=2, sort_keys=True))
