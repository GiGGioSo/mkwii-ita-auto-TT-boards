from PySide6.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel, QScrollArea, QFormLayout, QHBoxLayout, QCheckBox, QGroupBox, QSpinBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from .updater import Updater

WINDOW_TITLE = "MKWii ITA auto TT leaderboards"

WIDTH = 800
HEIGHT = 600

FONT = "Inter"

BASE_FONT_SIZE = 10

class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)

        self.setWindowTitle(WINDOW_TITLE)
        self.setBaseSize(WIDTH, HEIGHT)
        self.setFont(QFont(FONT, BASE_FONT_SIZE, QFont.Normal))

        self.updater = Updater()
        self.updater.finished.connect(self.update_finished_routine)
        self.updater.stopped.connect(self.updater.stop_msg)
        self.updater.display_msg.connect(self.add_output)

        # 3laps options
        self.rkg_dl_3lap = QCheckBox("check 1")
        self.rkg_dl_3lap.setChecked(True)
        self.check_2_3lap = QCheckBox("check 2")
        self.check_2_3lap.setChecked(True)
        self.check_3_3lap = QCheckBox("check 3")
        self.check_3_3lap.setChecked(True)
        ## partial update rows spinbox
        self.track_skip_box_3lap = QSpinBox()
        self.track_skip_box_3lap.setMinimum(0)
        self.track_skip_box_3lap.setMaximum(31)
        self.track_skip_box_3lap.setValue(0)
        self.track_skip_label_3lap = QLabel("Tracks to skip: ")
        self.track_skip_layout_3lap = QHBoxLayout()
        self.track_skip_layout_3lap.addWidget(self.track_skip_label_3lap)
        self.track_skip_layout_3lap.addWidget(self.track_skip_box_3lap)
        ## creating common layout
        self.update_layout_3lap = QVBoxLayout()
        self.update_layout_3lap.setAlignment(Qt.AlignTop)
        self.update_layout_3lap.addWidget(self.rkg_dl_3lap)
        self.update_layout_3lap.addWidget(self.check_2_3lap)
        self.update_layout_3lap.addWidget(self.check_3_3lap)
        self.update_layout_3lap.addLayout(self.track_skip_layout_3lap)
        self.update_group_3lap = QGroupBox("3lap")
        self.update_group_3lap.setCheckable(True)
        self.update_group_3lap.setLayout(self.update_layout_3lap)

        # flap options
        self.rkg_dl_flap = QCheckBox("Download new Ghosts")
        self.rkg_dl_flap.setChecked(True)
        self.check_2_flap = QCheckBox("check 2")
        self.check_2_flap.setChecked(True)
        self.check_3_flap = QCheckBox("check 3")
        self.check_3_flap.setChecked(True)
        ## partial update rows spinbox flap
        self.track_skip_box_flap = QSpinBox()
        self.track_skip_box_flap.setMinimum(0)
        self.track_skip_box_flap.setMaximum(31)
        self.track_skip_box_flap.setValue(0)
        self.track_skip_label_flap = QLabel("Tracks to skip: ")
        self.track_skip_layout_flap = QHBoxLayout()
        self.track_skip_layout_flap.addWidget(self.track_skip_label_flap)
        self.track_skip_layout_flap.addWidget(self.track_skip_box_flap)
        ## creating common layout
        self.update_layout_flap = QVBoxLayout()
        self.update_layout_flap.setAlignment(Qt.AlignTop)
        self.update_layout_flap.addWidget(self.rkg_dl_flap)
        self.update_layout_flap.addWidget(self.check_2_flap)
        self.update_layout_flap.addWidget(self.check_3_flap)
        self.update_layout_flap.addLayout(self.track_skip_layout_flap)
        self.update_group_flap = QGroupBox("Flap")
        self.update_group_flap.setCheckable(True)
        self.update_group_flap.setLayout(self.update_layout_flap)

        ## Composing Update times section, with both 3laps and flap groupboxes
        self.update_layout_all = QVBoxLayout()
        self.update_layout_all.setAlignment(Qt.AlignTop)
        self.update_layout_all.addWidget(self.update_group_3lap)
        self.update_layout_all.addWidget(self.update_group_flap)
        self.update_group_all = QGroupBox("Update times")
        self.update_group_all.setCheckable(False)
        self.update_group_all.setLayout(self.update_layout_all)


        # unrestricted options
        self.check_print_info_unr = QCheckBox("Print info")
        self.check_print_info_unr.setChecked(True)
        self.update_unr_layout = QVBoxLayout()
        self.update_unr_layout.setAlignment(Qt.AlignTop)
        self.update_unr_layout.addWidget(self.check_print_info_unr)
        self.update_unr_group = QGroupBox("Update unrestricteds")
        self.update_unr_group.setCheckable(True)
        self.update_unr_group.setLayout(self.update_unr_layout)

        # start stop buttons
        self.start_button = QPushButton('START')
        self.start_button.clicked.connect(self.start_button_clicked)
        self.start_button.setFont(QFont(FONT, 15, QFont.Normal))
        self.stop_button = QPushButton('STOP')
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.stop_button.setFont(QFont(FONT, 15, QFont.Normal))
        self.stop_button.setEnabled(False)
        self.start_stop_layout = QHBoxLayout()
        self.start_stop_layout.addWidget(self.start_button)
        self.start_stop_layout.addWidget(self.stop_button)

        # composing left column
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.update_group_all)
        self.left_layout.addWidget(self.update_unr_group)
        self.left_layout.addStretch()
        self.left_layout.addLayout(self.start_stop_layout)

        # debug scroll area on the right
        self.scroll_layout = QFormLayout()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.scroll_layout)
        self.scroll_area = QScrollArea()
        self.scroll_area.setMinimumWidth(400)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)

        # composing everything
        self.main_layout = QHBoxLayout()
        self.main_layout.addLayout(self.left_layout)
        self.main_layout.addWidget(self.scroll_area)

        # central widget
        self.everything = QWidget()
        self.everything.setLayout(self.main_layout)

        # set central widget
        self.setCentralWidget(self.everything)

    def add_output(self, msg: str) -> None:
        label = QLabel(msg)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setOpenExternalLinks(True)
        self.scroll_layout.insertRow(0, label)

    def start_button_clicked(self):
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        if not self.updater.isRunning():
            self.updater.setMode(
                self.update_group_3lap.isChecked(),
                self.update_group_flap.isChecked(),
                self.update_unr_group.isChecked(),
                )
            self.updater.setOptions(
                self.track_skip_box_3lap.value(),
                self.rkg_dl_3lap.isChecked(),
                self.check_2_3lap.isChecked(),
                self.check_3_3lap.isChecked(),
                self.track_skip_box_flap.value(),
                self.rkg_dl_flap.isChecked(),
                self.check_2_flap.isChecked(),
                self.check_3_flap.isChecked(),
                self.check_print_info_unr.isChecked(),
                )
            self.updater.start()

    def update_finished_routine(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def stop_button_clicked(self):
        if self.updater.isRunning():
            self.updater.requestInterruption()
            self.stop_button.setFont(QFont(FONT, 15, QFont.Normal))
