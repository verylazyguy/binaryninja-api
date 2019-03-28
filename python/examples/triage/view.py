import traceback
import binaryninjaui
from binaryninja.settings import Settings
from binaryninja import log
from binaryninjaui import View, ViewType, UIContext, ViewFrame
from PySide2.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QSplitter
from PySide2.QtCore import Qt
from . import headers
from . import entropy
from . import imports
from . import exports
from . import sections
from . import byte


class TriageView(QScrollArea, View):
	def __init__(self, parent, data):
		QScrollArea.__init__(self, parent)
		View.__init__(self)
		self.setupView(self)
		self.data = data
		self.currentOffset = 0
		self.byteView = None
		self.fullAnalysisButton = None

		container = QWidget(self)
		layout = QVBoxLayout()

		entropyGroup = QGroupBox("Entropy")
		entropyLayout = QVBoxLayout()
		entropyLayout.addWidget(entropy.EntropyWidget(entropyGroup, self, self.data))
		entropyGroup.setLayout(entropyLayout)
		layout.addWidget(entropyGroup)

		hdr = None
		try:
			if self.data.view_type == "PE":
				hdr = headers.PEHeaders(self.data)
			elif self.data.view_type != "Raw":
				hdr = headers.GenericHeaders(self.data)
		except:
			log.log_error(traceback.format_exc())

		if hdr is not None:
			headerGroup = QGroupBox("Headers")
			headerLayout = QVBoxLayout()
			headerWidget = headers.HeaderWidget(headerGroup, hdr)
			headerLayout.addWidget(headerWidget)
			headerGroup.setLayout(headerLayout)
			layout.addWidget(headerGroup)

		if self.data.executable:
			importExportSplitter = QSplitter(Qt.Horizontal)

			importGroup = QGroupBox("Imports")
			importLayout = QVBoxLayout()
			importLayout.addWidget(imports.ImportsWidget(importGroup, self, self.data))
			importGroup.setLayout(importLayout)
			importExportSplitter.addWidget(importGroup)

			exportGroup = QGroupBox("Exports")
			exportLayout = QVBoxLayout()
			exportLayout.addWidget(exports.ExportsWidget(exportGroup, self, self.data))
			exportGroup.setLayout(exportLayout)
			importExportSplitter.addWidget(exportGroup)

			layout.addWidget(importExportSplitter)

			if self.data.view_type != "PE":
				segmentsGroup = QGroupBox("Segments")
				segmentsLayout = QVBoxLayout()
				segmentsWidget = sections.SegmentsWidget(segmentsGroup, self.data)
				segmentsLayout.addWidget(segmentsWidget)
				segmentsGroup.setLayout(segmentsLayout)
				layout.addWidget(segmentsGroup)
				if len(segmentsWidget.segments) == 0:
					segmentsGroup.hide()

			sectionsGroup = QGroupBox("Sections")
			sectionsLayout = QVBoxLayout()
			sectionsWidget = sections.SectionsWidget(sectionsGroup, self.data)
			sectionsLayout.addWidget(sectionsWidget)
			sectionsGroup.setLayout(sectionsLayout)
			layout.addWidget(sectionsGroup)
			if len(sectionsWidget.sections) == 0:
				sectionsGroup.hide()

			buttonLayout = QHBoxLayout()
			buttonLayout.addStretch(1)
			self.fullAnalysisButton = QPushButton("Start Full Analysis")
			self.fullAnalysisButton.clicked.connect(self.startFullAnalysis)
			buttonLayout.addWidget(self.fullAnalysisButton)
			layout.addLayout(buttonLayout)
			layout.addStretch(1)
		else:
			self.byteView = byte.ByteView(self, self.data)
			View.setBinaryDataNavigable(self, True)
			layout.addWidget(self.byteView, 1)

		container.setLayout(layout)
		self.setWidgetResizable(True)
		self.setWidget(container)

		if self.fullAnalysisButton is not None and Settings().get_string("analysis.mode", data) == "full":
			self.fullAnalysisButton.hide()

	def getData(self):
		return self.data

	def getCurrentOffset(self):
		if self.byteView is not None:
			return self.byteView.getCurrentOffset()
		return self.currentOffset

	def getSelectionOffsets(self):
		if self.byteView is not None:
			return self.byteView.getSelectionOffsets()
		return (self.currentOffset, self.currentOffset)

	def setCurrentOffset(self, offset):
		self.currentOffset = offset
		UIContext.updateStatus(True)

	def getFont(self):
		return binaryninjaui.getMonospaceFont(self)

	def navigate(self, addr):
		if self.byteView:
			return self.byteView.navigate(addr)
		else:
			return self.navigate(addr)

	def startFullAnalysis(self):
		Settings().set_string("analysis.mode", "full", self.data)
		for f in self.data.functions:
			if f.analysis_skipped:
				f.reanalyze()
		self.data.update_analysis()
		self.fullAnalysisButton.hide()

	def navigateToFileOffset(self, offset):
		if self.byteView is None:
			addr = self.data.get_address_for_data_offset(offset)
			view_frame = ViewFrame.viewFrameForWidget(self)
			if view_frame is None:
				return
			if addr is None:
				view_frame.navigate("Hex:Raw", offset)
			else:
				view_frame.navigate("Linear:" + view_frame.getCurrentDataType(), addr)
		else:
			if self.data == self.data.file.raw:
				addr = offset
			else:
				addr = self.data.get_address_for_data_offset(offset)
			if addr is None:
				view_frame = ViewFrame.viewFrameForWidget(self)
				if view_frame is not None:
					view_frame.navigate("Hex:Raw", offset)
			else:
				self.byteView.navigate(addr)
				self.byteView.setFocus(Qt.OtherFocusReason)

	def focusInEvent(self, event):
		if self.byteView is not None:
			self.byteView.setFocus(Qt.OtherFocusReason)


class TriageViewType(ViewType):
	def __init__(self):
		super(TriageViewType, self).__init__("Triage", "Triage Summary")

	def getPriority(self, data, filename):
		is_full = Settings().get_string("analysis.mode", data) == "full"
		always_prefer = Settings().get_bool("triage.always_prefer", data)
		prefer_for_raw = Settings().get_bool("triage.prefer_for_raw", data)
		if data.executable and (always_prefer or not is_full):
			return 100
		if len(data) > 0:
			if always_prefer or data.executable or prefer_for_raw:
				return 25
			return 1
		return 0

	def create(self, data, view_frame):
		return TriageView(view_frame, data)


Settings().register_group("triage", "Triage")
Settings().register_setting("triage.always_prefer", """
	{
		"title" : "Always Prefer Triage Summary View",
		"type" : "boolean",
		"default" : false,
		"description" : "Always prefer opening binaries in Triage Summary view, even when performing full analysis."
	}
	""")

Settings().register_setting("triage.prefer_for_raw", """
	{
		"title" : "Prefer Triage Summary View for Raw Files",
		"type" : "boolean",
		"default" : true,
		"description" : "Prefer opening raw files in Triage Summary view."
	}
	""")

ViewType.registerViewType(TriageViewType())