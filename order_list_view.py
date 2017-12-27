from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.label import Label
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior

NUM_DISPLAY_COLUMNS = 10

Builder.load_string('''
<OrderLabel@Label>:
    size: self.texture_size
    padding: 4, 4
<SelectableOrderLabel>:
    size: (max(self.parent.cols_minimum[self.col], self.texture_size[0]), self.texture_size[1]) if self.parent and self.col else self.texture_size
    padding: 4, 4
    # Draw a background to indicate selection
    canvas.before:
        Color:
            rgba: (.0, 0.9, .1, .3) if self.selected else (0, 0, 0, 1)
        Rectangle:
            pos: self.pos
            size: self.size
<OrderListView>:
    viewclass: 'OrderLabel'
    RecycleGridLayout:
        id: layout
        default_size: dp(1), dp(1)
        default_size_hint: None, None
        size_hint: None, None
        width: self.minimum_width
        height: self.minimum_height
        cols: 10
<SelectableOrderListView>:
    viewclass: 'SelectableOrderLabel'
    SelectableRecycleGridLayout:
        id: layout
        default_size: dp(1), dp(1)
        default_size_hint: None, None
        size_hint: None, None
        width: self.minimum_width
        height: self.minimum_height
        cols: 10
        multiselect: True
        touch_multiselect: True
''')

class SelectableRecycleGridLayout(FocusBehavior, LayoutSelectionBehavior, RecycleGridLayout):
    ''' Adds selection and focus behaviour to the view. '''

class OrderLabel(RecycleDataViewBehavior, Label):
    pass

class SelectableOrderLabel(OrderLabel):
    ''' Add selection support to the Label '''
    index = None
    col = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        return super(SelectableOrderLabel, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableOrderLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            # header unselectable
            if 0 <= self.index < self.parent.cols:
                return
            self.notifyOrderSelected()
            # calculate the cell indices for this row to highlight the whole row
            first = int(self.index / self.parent.cols) * self.parent.cols
            last = first + self.parent.cols - 1
            for cell in range(first, last + 1):
                self.parent.select_with_touch(cell, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected

    def notifyOrderSelected(self):
        widget = self
        while not isinstance(widget, SelectableOrderListView) and widget.parent is not widget:
            widget = widget.parent
        if not isinstance(widget, SelectableOrderListView):
            Logger.error("Could not find ancestor SelectableOrderListView.")
        widget.orderSelected(self.orderId)

class OrderListView(RecycleView):
    pass

class SelectableOrderListView(RecycleView):
    def __init__(self, **kwargs):
        super(SelectableOrderListView, self).__init__(**kwargs)
        self.selectedOrderIds = []

    def orderSelected(self, orderId):
        if orderId not in self.selectedOrderIds:
            self.selectedOrderIds.append(orderId)
        else:
            self.selectedOrderIds.remove(orderId)

    def getSelectedOrderIds(self):
        return self.selectedOrderIds
