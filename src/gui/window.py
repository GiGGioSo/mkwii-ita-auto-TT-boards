from PySide6.QtWidgets import QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel, QScrollArea, QFormLayout, QHBoxLayout
from PySide6.QtCore import QSize, Qt

from .updater import Updater

WINDOW_TITLE = "MKWii ITA auto TT leaderboards"

WIDTH = 800
HEIGHT = 600

class MainWindow(QMainWindow):
	def __init__(self, parent = None):
		super(MainWindow, self).__init__(parent)

		self.setWindowTitle(WINDOW_TITLE)
		self.setFixedSize(QSize(WIDTH, HEIGHT))

		self.updater = Updater()
		self.updater.finished.connect(self.updater_finished)
		self.updater.display_msg.connect(self.add_output)

		self.start_button = QPushButton('START')
		self.start_button.clicked.connect(self.start_button_clicked)

		self.stop_button = QPushButton('STOP')
		self.stop_button.clicked.connect(self.stop_button_clicked)


		# scroll area widget contents - layout
		self.scroll_layout = QFormLayout()

		# scroll area widget contents
		self.scroll_widget = QWidget()
		self.scroll_widget.setLayout(self.scroll_layout)

		# scroll area
		self.scroll = QScrollArea()
		self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.scroll.setWidgetResizable(True)
		self.scroll.setWidget(self.scroll_widget)

		# main layout
		self.left_layout = QVBoxLayout()

		# add all main to the main vLayout
		self.left_layout.addWidget(self.start_button)
		self.left_layout.addWidget(self.stop_button)

		self.main_layout = QHBoxLayout()

		self.main_layout.addLayout(self.left_layout)
		self.main_layout.addWidget(self.scroll)

		# central widget
		self.everything = QWidget()
		self.everything.setLayout(self.main_layout)

		# set central widget
		self.setCentralWidget(self.everything)

	def add_output(self, msg: str) -> None:
		self.scroll_layout.addRow(QLabel(msg))

	def start_button_clicked(self):
		self.start_button.setEnabled(False)
		if not self.updater.isRunning():
			self.updater.start()

	def updater_finished(self):
		self.start_button.setEnabled(True)
		self.add_output("Task finished or stopped.\n\n\n\n")

	def stop_button_clicked(self):
		if self.updater.isRunning():
			self.updater.requestInterruption()
