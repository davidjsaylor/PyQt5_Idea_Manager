import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QVBoxLayout, QMenu, 
    QInputDialog, QMessageBox, QWidget, QSlider, QLabel, 
    QDialog, QDialogButtonBox, QToolBar, QAction, QFontComboBox, 
    QSpinBox, QLineEdit, QSystemTrayIcon, QStyle, qApp, QCheckBox, 
    QHBoxLayout, QFrame, QRadioButton, QButtonGroup
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QEvent

script_path = os.path.dirname(__file__)

class SettingsDialog(QDialog):
    def __init__(self, parent=None, transparency=0.99, theme='Light', font_family='Verdana', font_size=10, window_title='Ideas', autostart=False):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        self.setGeometry(300, 300, 400, 400)

        layout = QVBoxLayout()

        def create_frame(label_text, widget):
            frame = QFrame()
            frame.setFrameShape(QFrame.Box)
            frame_layout = QHBoxLayout()
            label = QLabel(label_text)
            label.setStyleSheet('border: none;')
            frame_layout.addWidget(label)
            frame_layout.addWidget(widget)
            frame.setLayout(frame_layout)
            return frame

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(10)
        self.slider.setMaximum(100)
        self.slider.setValue(int(transparency * 100))
        layout.addWidget(create_frame('Window Transparency', self.slider))

        self.light_theme_radio = QRadioButton('Light')
        self.dark_theme_radio = QRadioButton('Dark')
        self.theme_group = QButtonGroup()
        self.theme_group.addButton(self.light_theme_radio)
        self.theme_group.addButton(self.dark_theme_radio)
        if theme == 'Light':
            self.light_theme_radio.setChecked(True)
        else:
            self.dark_theme_radio.setChecked(True)

        theme_frame = QFrame()
        theme_frame.setFrameShape(QFrame.Box)
        theme_layout = QHBoxLayout()
        theme_label = QLabel('Theme')
        theme_label.setStyleSheet('border: none;')
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        theme_frame.setLayout(theme_layout)
        layout.addWidget(theme_frame)

        self.font_family_selector = QFontComboBox()
        self.font_family_selector.setCurrentFont(QFont(font_family))
        layout.addWidget(create_frame('Font Family', self.font_family_selector))

        self.font_size_selector = QSpinBox()
        self.font_size_selector.setRange(6, 72)
        self.font_size_selector.setValue(font_size)
        layout.addWidget(create_frame('Font Size', self.font_size_selector))

        self.title_input = QLineEdit(window_title)
        self.title_input.setFixedWidth(200)
        layout.addWidget(create_frame('Window Title', self.title_input))

        self.autostart_checkbox = QCheckBox()
        self.autostart_checkbox.setChecked(autostart)
        self.autostart_checkbox.setFixedWidth(20)
        layout.addWidget(create_frame('Start with OS', self.autostart_checkbox))

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)
        self.apply_theme_stylesheet(theme)

    def apply_theme_stylesheet(self, theme):
        if theme == 'Dark':
            self.setStyleSheet('''
                QCheckBox {
                    border: 1px solid #52b1ee;
                }
                QFrame {
                    border: 1px solid #1f1f1f;
                }
            ''')
        else:
            self.setStyleSheet('''
                QCheckBox {
                    border: none;
                }
                QFrame {
                    border: 1px solid darkgray;
                }
            ''')

    def get_transparency(self):
        return self.slider.value() / 100

    def get_theme(self):
        return 'Dark' if self.dark_theme_radio.isChecked() else 'Light'

    def get_font_family(self):
        return self.font_family_selector.currentFont().family()

    def get_font_size(self):
        return self.font_size_selector.value()

    def get_window_title(self):
        return self.title_input.text()

    def get_autostart(self):
        return self.autostart_checkbox.isChecked()

class ProjectFeatureApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Ideas')
        self.setMinimumSize(480, 480)

        self.settings_path = os.path.join(script_path, 'settings.json')
        self.theme = 'Light'
        self.font_family = 'Verdana'
        self.font_size = 10
        self.window_title = 'Ideas'
        self.transparency = 0.99
        self.autostart = False
        self.load_settings()

        self.file_path = os.path.join(script_path, 'project_ideas.json')
        self.project_ideas = self.load_ideas()

        self.model = QStandardItemModel()
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        icon_path = None
        for ext in ['png', 'ico', 'jpg']:
            possible_icon_path = os.path.join(script_path, f'icon.{ext}')
            if os.path.exists(possible_icon_path):
                icon_path = possible_icon_path
                break

        self.tray_icon = QSystemTrayIcon(self)
        if icon_path:
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip('Ideas')

        self.tray_menu = QMenu(self)
        restore_action = QAction('Restore', self)
        restore_action.triggered.connect(self.show_normal)
        quit_action = QAction('Quit', self)
        quit_action.triggered.connect(qApp.quit)
        self.tray_menu.addAction(restore_action)
        self.tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)

        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        self.init_ui()
        self.apply_font_settings()

        if self.autostart:
            self.showMinimized()
            self.hide()
            self.tray_icon.show()

    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        self.toolbar = QToolBar('Main Toolbar')
        self.addToolBar(self.toolbar)

        self.add_project_action = QAction('Add &Idea', self)
        self.add_project_action.triggered.connect(self.add_project)
        self.toolbar.addAction(self.add_project_action)

        self.settings_button = QAction('&Settings', self)
        self.settings_button.triggered.connect(self.open_settings)
        self.toolbar.addAction(self.settings_button)

        self.exit_button = QAction('E&xit', self)
        self.exit_button.triggered.connect(qApp.quit)
        self.toolbar.addAction(self.exit_button)

        layout.addWidget(self.tree)

        self.setCentralWidget(central_widget)
        self.refresh_treeview()

    def load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, 'r') as file:
                settings = json.load(file)
                geometry = settings.get('geometry', [100, 100, 480, 480])
                self.setGeometry(*geometry)
                self.transparency = settings.get('transparency', 0.99)
                self.setWindowOpacity(self.transparency)
                self.theme = settings.get('theme', 'Light')
                self.font_family = settings.get('font_family', 'Verdana')
                self.font_size = settings.get('font_size', 10)
                self.window_title = settings.get('window_title', 'Ideas')
                self.setWindowTitle(self.window_title)
                self.autostart = settings.get('autostart', False)
                self.apply_theme(self.theme)
        else:
            self.setGeometry(100, 100, 480, 480)
            self.setWindowOpacity(self.transparency)
            self.save_settings()

    def save_settings(self):
        geometry = [self.geometry().x(), self.geometry().y(), self.geometry().width(), self.geometry().height()]
        settings = {
            'geometry': geometry,
            'transparency': self.transparency,
            'theme': self.theme,
            'font_family': self.font_family,
            'font_size': self.font_size,
            'window_title': self.window_title,
            'autostart': self.autostart
        }
        with open(self.settings_path, 'w') as file:
            json.dump(settings, file, indent=4)

        autostart_path = os.path.expanduser('~/.config/autostart/Ideas.desktop')
        if self.autostart:
            with open(autostart_path, 'w') as file:
                file.write(f'''[Desktop Entry]
Type=Application
Name=Ideas
Exec=python3 {os.path.abspath(__file__)}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
''')
        else:
            if os.path.exists(autostart_path):
                os.remove(autostart_path)

    def load_ideas(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as file:
                return json.load(file)
        return []

    def save_ideas(self):
        with open(self.file_path, 'w') as file:
            json.dump(self.project_ideas, file, indent=4)

    def refresh_treeview(self):
        self.model.clear()
        self.project_ideas.sort(key=lambda idea: idea['name'])
        for idea in self.project_ideas:
            project_item = QStandardItem(idea['name'])
            self.model.appendRow(project_item)
            for feature in idea.get('features', []):
                feature_item = QStandardItem(feature)
                project_item.appendRow(feature_item)

    def add_project(self):
        text, ok = QInputDialog.getText(self, 'Add Idea', 'Enter your project idea:')
        if ok and text:
            self.project_ideas.append({'name': text, 'features': []})
            self.save_ideas()
            self.refresh_treeview()
            self.expand_new_idea(text)

    def expand_new_idea(self, idea_name):
        for i in range(self.model.rowCount()):
            project_item = self.model.item(i)
            if project_item.text() == idea_name:
                self.tree.expand(self.model.indexFromItem(project_item))
                break

    def update_project(self, index):
        project_name = self.project_ideas[index]['name']
        text, ok = QInputDialog.getText(self, 'Update Project Idea', 'Update your project idea:', text=project_name)
        if ok and text:
            self.project_ideas[index]['name'] = text
            self.save_ideas()
            self.refresh_treeview()

    def delete_project(self, index):
        del self.project_ideas[index]
        self.save_ideas()
        self.refresh_treeview()

    def add_feature(self, index):
        text, ok = QInputDialog.getText(self, 'Add Feature', 'Enter the feature:')
        if ok and text:
            self.project_ideas[index].setdefault('features', []).append(text)
            self.save_ideas()
            self.refresh_treeview()
            self.expand_project(index)

    def expand_project(self, project_index):
        project_item = self.model.item(project_index)
        self.tree.expand(self.model.indexFromItem(project_item))

    def update_feature(self, project_index, feature_index):
        feature_name = self.project_ideas[project_index]['features'][feature_index]
        text, ok = QInputDialog.getText(self, 'Update Feature', 'Update the feature:', text=feature_name)
        if ok and text:
            self.project_ideas[project_index]['features'][feature_index] = text
            self.save_ideas()
            self.refresh_treeview()
            self.expand_project(project_index)

    def delete_feature(self, project_index, feature_index):
        del self.project_ideas[project_index]['features'][feature_index]
        self.save_ideas()
        self.refresh_treeview()
        self.expand_project(project_index)

    def show_context_menu(self, position):
        indexes = self.tree.selectedIndexes()
        if indexes:
            item = self.model.itemFromIndex(indexes[0])
            if item.parent():
                project_index = item.parent().index().row()
                feature_index = item.index().row()
                menu = QMenu()
                menu.addAction('&Update', lambda: self.update_feature(project_index, feature_index))
                menu.addAction('&Delete', lambda: self.delete_feature(project_index, feature_index))
                menu.exec_(self.tree.viewport().mapToGlobal(position) - QPoint(10, 10))
            else:
                project_index = item.index().row()
                menu = QMenu()
                menu.addAction('&Update', lambda: self.update_project(project_index))
                menu.addAction('&Delete', lambda: self.delete_project(project_index))
                menu.addSeparator()
                menu.addAction('Add &Feature', lambda: self.add_feature(project_index))
                menu.exec_(self.tree.viewport().mapToGlobal(position) - QPoint(10, 10))

    def open_settings(self):
        dialog = SettingsDialog(
            self,
            transparency=self.transparency,
            theme=self.theme,
            font_family=self.font_family,
            font_size=self.font_size,
            window_title=self.window_title,
            autostart=self.autostart
        )

        main_geometry = self.geometry()
        settings_geometry = dialog.geometry()
        center_x = main_geometry.x() + (main_geometry.width() - settings_geometry.width()) // 2
        center_y = main_geometry.y() + (main_geometry.height() - settings_geometry.height()) // 2
        dialog.move(center_x, center_y)
        
        if dialog.exec_() == QDialog.Accepted:
            self.transparency = dialog.get_transparency()
            self.setWindowOpacity(self.transparency)
            self.theme = dialog.get_theme()
            self.font_family = dialog.get_font_family()
            self.font_size = dialog.get_font_size()
            self.window_title = dialog.get_window_title()
            self.setWindowTitle(self.window_title)
            self.autostart = dialog.get_autostart()
            self.apply_theme(self.theme)
            self.apply_font_settings()
            self.save_settings()

    def apply_theme(self, theme):
        if theme == 'Dark':
            self.setStyleSheet('background-color: #2b2b2b; color: #ffffff;')
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(43, 43, 43))
            palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(43, 43, 43))
            palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.Button, QColor(43, 43, 43))
            palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
            self.setPalette(palette)
        else:
            self.setStyleSheet('')
            self.setPalette(QApplication.style().standardPalette())

    def apply_font_settings(self):
        font = QFont(self.font_family, self.font_size)
        self.tree.setFont(font)

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange and self.isMinimized():
            event.ignore()
            self.hide()
            self.tray_icon.show()
        else:
            super().changeEvent(event)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.show()

    def show_normal(self):
        self.tray_icon.hide()
        self.showNormal()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.show_normal()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_win = ProjectFeatureApp()
    main_win.show()
    sys.exit(app.exec_())
