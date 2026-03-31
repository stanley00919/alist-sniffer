import os
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import pyqtSignal


class FolderTreeWidget(QTreeWidget):
    folder_selected = pyqtSignal(str)  # path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel('Downloads')
        self.itemClicked.connect(self._on_item_clicked)
        self._root_path = ''

    def set_root(self, path: str):
        self._root_path = path
        self.refresh()

    def refresh(self):
        self.clear()
        if not self._root_path or not os.path.isdir(self._root_path):
            return
        root_item = QTreeWidgetItem([os.path.basename(self._root_path)])
        root_item.setData(0, 256, self._root_path)
        self._populate(root_item, self._root_path)
        self.addTopLevelItem(root_item)
        root_item.setExpanded(True)

    def _populate(self, parent_item: QTreeWidgetItem, path: str):
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name))
        except PermissionError:
            return
        for entry in entries:
            if entry.is_dir():
                child = QTreeWidgetItem([entry.name])
                child.setData(0, 256, entry.path)
                parent_item.addChild(child)
                self._populate(child, entry.path)

    def _on_item_clicked(self, item: QTreeWidgetItem, _col: int):
        path = item.data(0, 256)
        if path:
            self.folder_selected.emit(path)
