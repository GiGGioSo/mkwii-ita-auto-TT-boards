from PySide6.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel, QScrollArea, QFormLayout, QHBoxLayout, QCheckBox, QGroupBox, QSpinBox
from PySide6.QtCore import Qt

from .updater import Updater

WINDOW_TITLE = "MKWii ITA auto TT leaderboards"

WIDTH = 800
HEIGHT = 600

class MainWindow(QMainWindow):
	def __init__(self, parent = None):
		super(MainWindow, self).__init__(parent)

		self.setWindowTitle(WINDOW_TITLE)
		self.setBaseSize(WIDTH, HEIGHT)

		self.updater = Updater()	
		self.updater.finished.connect(self.enable_start_button)
		self.updater.stopped.connect(self.updater.stop_msg)
		self.updater.display_msg.connect(self.add_output)

		# 3laps options
		self.checked_players_check = QCheckBox("Players checked (with ID)")
		self.checked_players_check.setChecked(True)
		self.skipped_players_check = QCheckBox("Skipped players (no ID)")
		self.skipped_players_check.setChecked(True)
		self.ghosts_info_check = QCheckBox("Ghosts info")
		self.ghosts_info_check.setChecked(True)
		self.google_sheets_3laps_check = QCheckBox("Google sheets info")
		self.google_sheets_3laps_check.setChecked(True)
		# partial update rows spinbox
		self.partial_update_rows_box = QSpinBox()
		self.partial_update_rows_box.setMinimum(3)
		self.partial_update_rows_box.setMaximum(3333)
		self.partial_update_rows_box.setValue(10)
		self.partial_update_rows_label = QLabel("Partial update rows:")
		self.partial_update_rows_layout = QHBoxLayout()
		self.partial_update_rows_layout.addWidget(self.partial_update_rows_label)
		self.partial_update_rows_layout.addWidget(self.partial_update_rows_box)
		# creating common layout
		self.update_3laps_layout = QVBoxLayout()
		self.update_3laps_layout.addWidget(self.checked_players_check)
		self.update_3laps_layout.addWidget(self.skipped_players_check)
		self.update_3laps_layout.addWidget(self.ghosts_info_check)
		self.update_3laps_layout.addWidget(self.google_sheets_3laps_check)
		self.update_3laps_layout.addLayout(self.partial_update_rows_layout)
		self.update_3laps_group = QGroupBox("3laps")
		self.update_3laps_group.setCheckable(True)
		self.update_3laps_group.setLayout(self.update_3laps_layout)

		# unrestricted options
		self.unrestricteds_found = QCheckBox("Found unrestricteds")
		self.unrestricteds_found.setChecked(True)
		self.complete_times = QCheckBox("Complete timesheets")
		self.complete_times.setChecked(True)
		self.google_sheets_unr_check = QCheckBox("Google sheets info")
		self.google_sheets_unr_check.setChecked(True)
		self.update_unr_layout = QVBoxLayout()
		self.update_unr_layout.addWidget(self.unrestricteds_found)
		self.update_unr_layout.addWidget(self.complete_times)
		self.update_unr_layout.addWidget(self.google_sheets_unr_check)
		self.update_unr_group = QGroupBox("Unrestricted")
		self.update_unr_group.setCheckable(True)
		self.update_unr_group.setLayout(self.update_unr_layout)

		

		# start stop buttons
		self.start_button = QPushButton('START')
		self.start_button.clicked.connect(self.start_button_clicked)
		self.stop_button = QPushButton('STOP')
		self.stop_button.clicked.connect(self.stop_button_clicked)
		self.start_stop_layout = QHBoxLayout()
		self.start_stop_layout.addWidget(self.start_button)
		self.start_stop_layout.addWidget(self.stop_button)

		# composing left column
		self.left_layout = QVBoxLayout()
		self.left_layout.addWidget(self.update_3laps_group)
		self.left_layout.addWidget(self.update_unr_group)
		self.left_layout.addLayout(self.start_stop_layout)

		# debug scroll area
		self.scroll_layout = QFormLayout()
		self.scroll_widget = QWidget()
		self.scroll_widget.setLayout(self.scroll_layout)
		self.scroll = QScrollArea()
		self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.scroll.setWidgetResizable(True)
		self.scroll.setWidget(self.scroll_widget)

		# composing everything
		self.main_layout = QHBoxLayout()
		self.main_layout.addLayout(self.left_layout)
		self.main_layout.addWidget(self.scroll)

		# central widget
		self.everything = QWidget()
		self.everything.setLayout(self.main_layout)

		# set central widget
		self.setCentralWidget(self.everything)

	def add_output(self, msg: str) -> None:
		label = QLabel(msg)
		label.setTextInteractionFlags(Qt.TextSelectableByMouse)
		self.scroll_layout.insertRow(0, label)

	def start_button_clicked(self):
		self.start_button.setEnabled(False)
		if not self.updater.isRunning():
			self.updater.setMode(
				self.update_3laps_group.isChecked(),
				self.update_unr_group.isChecked()
				)
			self.updater.setOptions(
				self.partial_update_rows_box.value(),
				self.checked_players_check.isChecked(),
				self.skipped_players_check.isChecked(),
				self.ghosts_info_check.isChecked(),
				self.unrestricteds_found.isChecked(),
				self.complete_times.isChecked(),
				self.google_sheets_3laps_check.isChecked(),
				self.google_sheets_unr_check.isChecked()
				)
			self.updater.start()

	def enable_start_button(self):
		self.start_button.setEnabled(True)

	def stop_button_clicked(self):
		if self.updater.isRunning():
			self.updater.requestInterruption()
