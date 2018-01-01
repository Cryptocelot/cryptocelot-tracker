import os

from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup

Builder.load_string('''
<ImportDialog@Popup>:
    id: view
    title: "Select a CSV file from Bittrex, Kraken, or Poloniex."
    content: layout
    auto_dismiss: False
    size_hint: None, None
    size: 400, 400
    BoxLayout:
        id: layout
        orientation: 'vertical'
        size: self.minimum_size
        FileChooserListView:
            id: chooser
            filters: ['*.csv']
        BoxLayout:
            orientation: 'horizontal'
            size_hint: 1, None
            size: self.minimum_size
            Button:
                id: cancelButton
                text: 'Cancel'
                on_release: view.dismiss()
                size_hint: 0.5, None
                size: self.texture_size
                padding: 8, 8
            Button:
                id: okButton
                text: 'OK'
                size_hint: 0.5, None
                size: self.texture_size
                padding: 8, 8
''')

class ImportDialog(Popup):
    def __init__(self, okCallback):
        super(ImportDialog, self).__init__()
        self.ids.chooser.path = os.path.expanduser('~')
        self.ids.chooser.bind(on_submit=lambda *_: okCallback(self, self.ids.chooser.selection))
        self.ids.okButton.bind(on_release=lambda *_: okCallback(self, self.ids.chooser.selection))
