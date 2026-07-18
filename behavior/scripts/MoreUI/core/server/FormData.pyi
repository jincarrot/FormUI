# -*- coding: utf-8 -*-
from typing import Callable, TypeVar, Generic, TypedDict, overload

T = TypeVar("T")
U = TypeVar("U")

class CustomControl:
    
    @staticmethod
    def register(identifier, controlDef):
        # type: (str, str) -> None
        """
        注册一个自定义控件。
        
        -- identifier: 控件标识符，必须唯一。

        -- controlDef: 控件定义，如oreui_controls.green_btn。
        """

class ObservableOptions(TypedDict):
    clientWritable: bool | Observable[bool]

class DynamicForm:
    pass

class Observable(Generic[T]):
    """
    A class that represents data that can be Observed. Extensively used for UI.
    """

    @property
    def typeId(self) -> T:
        pass

    def getData(self) -> T:
        pass
    
    def setData(self, data: T) -> None:
        pass
        
    def subscribe(self, callback: Callable[[T], None]):
        pass
    
    def unsubscribe(self, callback: Callable[[T], None]):
        pass

    @overload
    @staticmethod
    def create(data: bool, options: ObservableOptions=...) -> Observable[bool]: ...


    @overload
    @staticmethod
    def create(data: int, options: ObservableOptions=...) -> Observable[int]: ...

    @overload
    @staticmethod
    def create(data: float, options: ObservableOptions=...) -> Observable[float]: ...

    @overload
    @staticmethod
    def create(data: str, options: ObservableOptions=...) -> Observable[str]: ...
    
class Options(TypedDict):
    visible: bool | Observable[bool]

class ButtonOptions(Options): ...

class DividerOptions(Options): ...

class LabelOptions(Options): ...

class SliderOptions(Options): ...

class TextFieldOptions(Options): ...

class ToggleOptions(Options): ...

class DropdownOptions(Options): ...

class DropdownItem(TypedDict): 
    label: str
    value: int

class CustomOptions(TypedDict):
    movable: bool | Observable[bool]
    resizable: bool | Observable[bool]
    style: str = "oreui"
    closable: bool | Observable[bool]

class BarOptions(CustomOptions):
    direction: str

class CustomForm(DynamicForm):
    """
    一种可以添加按钮、文本、开关、下拉框、滑动条等控件的自定义表单。

    允许使用动态数据并使得表单动态刷新。
    """

    @property
    def formId(self) -> int: 
        """表单的内部分配id。"""
    
    def button(self, label: str | Observable[str], onClick: Callable[[], None], options: ButtonOptions = ...) -> CustomForm: 
        """
        添加一个按钮。
        
        --label - 按钮文本。

        --onClick - 按钮按下时触发的回调函数。

        --options? - 按钮选项。

        返回自身
        """
    
    def close(self) -> CustomForm: 
        """
        关闭此表单。
        """

    def divider(self, options: DividerOptions = ...) -> CustomForm: 
        """
        添加一条分割线。
        
        --options - 分割线选项
        
        返回自身
        """

    def dropdown(self, label: str | Observable[str], value: Observable[int], items: list[DropdownItem], options: DropdownOptions=...): 
        """
        添加一个下拉框。
        
        --label - 标签文本
        
        --value - 当前选中值。（必须为Observable<str>，且须clientWritable设置为True）

        --items - 下拉框显示内容

        --options - 下拉框选项

        返回自身
        """

    def label(self, text: str | Observable[str], options: LabelOptions = ...) -> CustomForm: 
        """
        添加一个文本。
        
        --text - 文本内容。
        
        --options? - 文本选项。
        
        返回自身
        """

    def show(self) -> CustomForm: 
        """
        向玩家展示此表单。
        """
    
    def slider(
            self, 
            label: str | Observable[str], 
            value: Observable[int], 
            minValue: int | Observable[int], 
            maxValue: int | Observable[int], 
            options: SliderOptions=...
        ) -> CustomForm: 
        """
        添加一个滑动条。
        
        --label - 滑动条标签文本。
        
        --value - 当前滑动条的值。（必须为Observable<int>，且须clientWritable设置为True）

        --minValue - 最小值

        --maxValue - 最大值

        --options? - 滑动条选项

        返回自身
        """

    def spacer(self, options: Options=...) -> CustomForm: 
        """
        添加一段空白（效果同添加空白文本）

        --options? - 空白选项

        返回自身
        """

    def textField(self, label: str | Observable[str], text: Observable[str], options: TextFieldOptions=...) -> CustomForm: 
        """
        添加一个文本输入框。
        
        --label - 文本输入框标签文本。
        
        --text - 文本内容（必须为Observable<str>，且须clientWritable设置为True）
        
        --options? - 文本输入框选项
        
        返回自身
        """

    def toggle(self, label: str | Observable[str], toggled: Observable[bool], options: ToggleOptions=...) -> CustomForm: 
        """
        添加一个开关。
        
        --label - 开关标签文本
        
        --toggled - 开关状态（必须为Observable<bool>，且须clientWritable设置为True）
        
        --options? - 开关选项
        
        返回自身
        """
        
    @staticmethod
    def create(playerId: str, title: str | Observable[str], options: CustomOptions={}) -> CustomForm: 
        """
        创建一个自定义表单。

        --playerId - 需要接收到此表单的玩家playerId

        --title - 表单标题

        --options? - 表单选项

        返回自定义表单对象
        """
    
class BarForm(DynamicForm):

    @staticmethod
    def create(playerId: str, title: str | Observable[str], options: BarOptions={}) -> BarForm: 
        """
        创建一个自定义表单。

        --playerId - 需要接收到此表单的玩家playerId

        --title - 表单标题

        --options? - 表单选项

        返回自定义表单对象
        """

    def close(self) -> BarForm: 
        """
        关闭此表单。
        """
        
    def button(self, label: str | Observable[str], onClick: Callable[[], None], options: ButtonOptions = ...) -> BarForm: 
        """
        添加一个按钮。
        
        --label - 按钮文本。

        --onClick - 按钮按下时触发的回调函数。

        --options? - 按钮选项。

        返回自身
        """

    def show(self) -> BarForm: 
        """
        向玩家展示此表单。
        """

class SidebarOptions(TypedDict):
    movable: bool | Observable[bool]
    resizable: bool | Observable[bool]
    closable: bool | Observable[bool]
    style: str

class TabOptions(TypedDict): ...

class SidebarForm(DynamicForm):
    """
    带左侧图标标签栏的表单。

    左侧从上到下排布多个正方形图标标签按钮，点击某个标签即在右侧主区域显示其绑定的 CustomForm。
    每个标签内容都是普通的 CustomForm，复用与 MoreUI 相同的渲染管线，因此所有控件类型都可用。
    """

    @property
    def formId(self) -> int:
        """表单的内部分配id。"""

    @staticmethod
    def create(playerId: str, options: SidebarOptions = ...) -> SidebarForm:
        """
        创建一个侧边栏标签表单。

        --playerId - 需要接收到此表单的玩家playerId

        --options? - 表单选项

        返回侧边栏表单对象
        """

    def tab(self, iconPath: str, form: CustomForm, options: TabOptions = ...) -> SidebarForm:
        """
        添加一个标签页。

        --iconPath - 标签按钮显示的图标贴图路径（如 "textures/ui/icon"）。

        --form - 点击此标签时在右侧显示的表单（CustomForm）。

        --options? - 标签选项（暂未启用任何功能）。

        返回自身
        """

    def show(self) -> SidebarForm:
        """
        向玩家展示此表单，并默认显示第一个标签页。
        """

    def close(self) -> SidebarForm:
        """
        关闭此表单。
        """

class FormLayout:
    """
    表单样式设置。
    
    需要先在MoreUI样式中定义网格，以此排布ui位置、大小等。
    """

    @property
    def position(self) -> list[int | Observable[int]]: 
        """
        表单所处的位置(x, y)。

        以屏幕左上角为坐标原点(0, 0)。

        如，定义MoreUI布局后为2行2列，此属性设置为[0, 1]，即会将表单设置在第一列第二行的位置。
        """
    
    @position.setter
    def position(self, value: list[int | Observable[int]]): ...
    
    @property
    def offset(self) -> list[float | Observable[float]]: 
        """
        表单的偏移量(x, y)，单位: 像素。
        """
    
    @offset.setter
    def offset(self, value: list[float | Observable[float]]): ...
    
    @property
    def size(self) -> list[int | Observable[int]]: 
        """
        表单大小(x, y)。
        """
    
    @size.setter
    def size(self, value: list[int | Observable[int]]): ...
    
    @property
    def margin(self) -> list[float | Observable[float]]: 
        """
        表单内边距（上，右，下，左），单位: 像素
        """
    
    @margin.setter
    def margin(self, value: list[float | Observable[float]]): ...

    @property
    def layer(self) -> int | Observable[int]: 
        """
        表单层级，整数，默认为-1。

        层级较高的表单会覆盖层级较低的表单。
        """

    @layer.setter
    def layer(self, value: int | Observable[int]): ...

class FormLayoutDict(TypedDict):
    position: list[int]=(0, 0)
    size: list[int]=(1, 1)
    offset: list[float]=(0, 0)
    margin: list[float]=(0, 0)
    layer: int=-1

class MoreUICustomData:

    @property
    def form(self) -> CustomForm: ...
    
    @property
    def layout(self) -> FormLayout: ...

    @property
    def mayCloseAll(self) -> bool: ...

class MoreUIBarData:

    @property
    def form(self) -> BarForm: ...
    
    @property
    def layout(self) -> FormLayout: ...

    @property
    def mayCloseAll(self) -> bool: ...
    
class MoreUILayout:
    """
    UI样式。

    将屏幕划分为m行n列的区域（网格），以便排布。
    """
    @property
    def row(self) -> list[int | float] | tuple[int | float]: 
        """
        定义要划分的行数。
        
        接受一个数字型列表。
        
        列表大小即为行数，列表元素值为这一行的宽度比例。
        
        如，设置为[1, 2, 1]，意为3行，行宽度比例为1: 2: 1
        """

    @row.setter
    def row(self, value: list[int | float] | tuple[int | float]): ...

    @property
    def column(self) -> list[int | float] | tuple[int | float]: 
        """
        定义要划分的列数。
        
        接受一个数字型列表。
        
        列表大小即为列数，列表元素值为这一列的宽度比例。
        
        如，设置为[1, 2, 1]，意为3列，列宽度比例为1: 2: 1
        """

    @column.setter
    def column(self, value: list[int | float] | tuple[int | float]): ...
    
class MoreUILayoutDict(TypedDict):
    row: list[int]
    column: list[int]

class MoreUI:
    """
    MoreUI (Multiple oreUI), 一种含有多个表单，内置oreUI风格的UI。
    """
    
    @staticmethod
    def create(playerId: str, layout: MoreUILayoutDict=...) -> MoreUI: 
        """
        创建MoreUI。
        
        --playerId - 需要接收到此表单的玩家id

        --layout? - UI布局。
        """
    
    def addCustomForm(self, title: str | Observable[str], options: CustomOptions=..., layout: FormLayoutDict=...) -> MoreUICustomData: 
        """
        向UI添加一个自定义表单(CustomForm)。

        --title - 表单标题。

        --options? - 表单创建选项。

        --layout? - 表单布局。

        返回表单数据
        """

    def addBarForm(self, title: str | Observable[str], options: CustomOptions=..., layout: FormLayoutDict=...) -> MoreUIBarData: 
        """
        向UI添加一个侧边栏表单(BarForm)。

        --title - 表单标题。

        --options? - 表单创建选项。

        --layout? - 表单布局。

        返回表单数据
        """
    
    @property
    def layout(self) -> MoreUILayout:
        """
        UI布局。
        """

    @layout.setter
    def layout(self, style: MoreUILayoutDict): ...

    def addForm(self, form: DynamicForm, layout: FormLayoutDict=...) -> MoreUICustomData:
        """
        向UI添加一个已经创建好的表单。

        --form - 表单对象(CustomForm)

        --layout? - 表单布局

        返回表单数据
        """

    def removeForm(self, form: MoreUICustomData):
        """
        移除一个表单
        
        --form - 表单对象
        
        返回自身
        """

    def show(self):
        """
        向玩家发送表单。
        """

    def close(self):
        """
        关闭表单
        """

class UIRawMessage(TypedDict):
    """文本组件"""
    
    Rawtext: list[UIRawMessage]
    Text: str | Observable[str]
    Translate: str | Observable[str]
    With: list[str] | UIRawMessage
    Sprite: str | UIRawMessage
