"""
Refactored GUI for ViT Image Retrieval System.

Improvements over the original:
  1. Centralized theme system (theme.py) — no more hardcoded colors/fonts
  2. Drag & drop support for query image selection
  3. Loading overlay during searches
  4. Responsive results grid (auto column count based on width)
  5. Keyboard shortcuts (Ctrl+O=Open query, Ctrl+Enter=Search, Ctrl+L=Load index)
  6. Cleaner widget tree with helper methods
  7. Better error feedback and status indicators
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import logging
logging.getLogger('faiss.loader').setLevel(logging.WARNING)

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QFileDialog, QSpinBox,
    QProgressBar, QScrollArea, QGridLayout, QMessageBox, QLineEdit,
    QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QFontMetrics
from PyQt5.QtWidgets import QShortcut

from vit_image_retrieval.core.feature_extractor import ImageFeatureExtractor
from vit_image_retrieval.core.retrieval_system import ImageRetrievalSystem
from vit_image_retrieval.core.image_display import EnhancedImageDisplay
from vit_image_retrieval.gui.theme import LIGHT
from vit_image_retrieval.gui.i18n import t, toggle_lang

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  Helper: DropTargetLabel
# ═══════════════════════════════════════════════════════════════

class DropTargetLabel(QLabel):
    """A label that accepts dragged image files via drag-and-drop."""

    fileDropped = pyqtSignal(str)

    def __init__(self, text: str, theme, parent=None):
        super().__init__(text, parent)
        self._theme = theme
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(110)
        self.setWordWrap(True)
        self._update_style(False)

    def _update_style(self, hover: bool):
        border_color = self._theme.accent if hover else self._theme.border
        self.setStyleSheet(f"""
            QLabel {{
                background: {self._theme.bg_secondary};
                border: 2px dashed {border_color};
                border-radius: {self._theme.radius_md};
                padding: {self._theme.padding_lg};
                font-size: {self._theme.font_sm};
                color: {self._theme.text_muted};
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile().lower()
            if path.endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                self._update_style(True)
                event.acceptProposedAction()
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self._update_style(False)

    def dropEvent(self, event: QDropEvent):
        self._update_style(False)
        if event.mimeData().hasUrls():
            path = event.mimeData().urls()[0].toLocalFile()
            self.fileDropped.emit(path)


# ═══════════════════════════════════════════════════════════════
#  Helper: LoadingOverlay
# ═══════════════════════════════════════════════════════════════

class LoadingOverlay(QWidget):
    """Semi-transparent overlay shown during long operations."""

    def __init__(self, parent: QWidget = None, text: str = "Processing..."):
        super().__init__(parent)
        self._text = text
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.hide()

    def show_with(self, text: str = None):
        if text:
            self._text = text
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.raise_()
        self.show()

    def resizeEvent(self, event):
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QColor, QPen, QFont
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))
        p.setPen(QPen(Qt.white, 2))
        p.setFont(QFont("Segoe UI", 16, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, self._text)
        p.end()


# ═══════════════════════════════════════════════════════════════
#  FeatureExtractionWorker (kept from original — solid design)
# ═══════════════════════════════════════════════════════════════

class FeatureExtractionWorker(QThread):
    """Worker thread for feature extraction to prevent GUI freezing."""
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, image_dir, retrieval_system, index_path, metadata_path):
        super().__init__()
        self.image_dir = image_dir
        self.retrieval_system = retrieval_system
        self.index_path = index_path
        self.metadata_path = metadata_path

    def run(self):
        try:
            self.retrieval_system.index_images(
                self.image_dir,
                progress_callback=self.progress.emit
            )
            self.retrieval_system.save(self.index_path, self.metadata_path)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


# ═══════════════════════════════════════════════════════════════
#  FeatureExtractionTab
# ═══════════════════════════════════════════════════════════════

class FeatureExtractionTab(QWidget):
    def __init__(self, model_dir=None, theme=None):
        super().__init__()
        self._theme = theme or LIGHT
        self._lang = self._theme.language if hasattr(self._theme, 'language') else "en"
        self.model_dir = model_dir
        self.retrieval_system = ImageRetrievalSystem(
            feature_extractor=ImageFeatureExtractor(model_dir=model_dir)
        )
        self.selected_dir = None
        self.worker = None
        self._setup_ui()
        self._apply_theme()
        self.retranslate_ui()

    def retranslate_ui(self):
        """Refresh all UI text according to current language."""
        lang = self._lang
        self.title.setText(t("fe_title", lang))
        self.desc.setText(t("fe_desc", lang))
        self.dir_label.setText(t("fe_dir_label", lang))
        self.dir_path_label.setText(t("fe_no_dir", lang))
        self.select_dir_btn.setText(t("fe_browse", lang))
        self.name_label.setText(t("fe_index_name", lang))
        self.index_name_input.setPlaceholderText(t("fe_index_placeholder", lang))
        self.extract_btn.setText(t("fe_extract_btn", lang))

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(22)
        layout.setContentsMargins(18, 18, 18, 18)

        # Title
        self.title = QLabel()
        self.title.setStyleSheet(self._theme.label_style(bold=True, size=self._theme.font_xl))
        layout.addWidget(self.title)

        self.desc = QLabel()
        self.desc.setWordWrap(True)
        self.desc.setStyleSheet(self._theme.label_style(size=self._theme.font_md))
        layout.addWidget(self.desc)

        # ── Directory selection ──
        dir_frame = QFrame()
        dir_frame.setObjectName("card")
        dir_layout = QVBoxLayout(dir_frame)
        dir_layout.setSpacing(16)
        dir_layout.setContentsMargins(18, 18, 18, 18)

        self.dir_label = self._make_label("")
        self.dir_label.setStyleSheet(self._theme.label_style(bold=True))
        dir_layout.addWidget(self.dir_label)

        dir_row = QHBoxLayout()
        self.dir_path_label = QLabel()
        self.dir_path_label.setStyleSheet(self._theme.info_panel_style())
        self.dir_path_label.setWordWrap(True)

        self.select_dir_btn = QPushButton()
        self.select_dir_btn.setStyleSheet(self._theme.secondary_btn())
        self.select_dir_btn.setMinimumWidth(120)
        self.select_dir_btn.clicked.connect(self._select_directory)

        dir_row.addWidget(self.dir_path_label, stretch=1)
        dir_row.addWidget(self.select_dir_btn)
        dir_layout.addLayout(dir_row)

        # ── Index name ──
        name_row = QHBoxLayout()
        self.name_label = self._make_label("")
        name_row.addWidget(self.name_label)
        self.index_name_input = QLineEdit()
        self.index_name_input.setStyleSheet(self._theme.input_style())
        name_row.addWidget(self.index_name_input, stretch=1)
        dir_layout.addLayout(name_row)

        # ── Progress ──
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(36)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self._theme.border};
                border-radius: {self._theme.radius_md};
                text-align: center; height: 36px;
                font-size: {self._theme.font_md};
            }}
            QProgressBar::chunk {{
                background: {self._theme.accent};
                border-radius: 5px;
            }}
        """)
        dir_layout.addWidget(self.progress_bar)

        # ── Extract button ──
        btn_row = QHBoxLayout()
        self.extract_btn = QPushButton("Extract Features")
        self.extract_btn.setStyleSheet(self._theme.primary_btn(disabled=True))
        self.extract_btn.setEnabled(False)
        self.extract_btn.setMinimumHeight(54)
        self.extract_btn.clicked.connect(self._start_extraction)
        btn_row.addStretch()
        btn_row.addWidget(self.extract_btn)
        btn_row.addStretch()
        dir_layout.addLayout(btn_row)

        # ── Status ──
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        dir_layout.addWidget(self.status_label)

        layout.addWidget(dir_frame)
        layout.addStretch()
        self.setLayout(layout)

    # ── Helpers ──

    def _make_label(self, text: str, bold: bool = False, size: Optional[str] = None) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(self._theme.label_style(bold=bold, size=size or self._theme.font_sm))
        return lbl

    def _apply_theme(self):
        self.setStyleSheet(f"""
            FeatureExtractionTab {{
                background: {self._theme.bg_primary};
            }}
            QFrame#card {{
                background: {self._theme.bg_secondary};
                border: 2px solid {self._theme.border};
                border-radius: {self._theme.radius_lg};
            }}
            {self._theme.scrollbar_style}
        """)

    # ── Slots ──

    def _select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if dir_path:
            self.selected_dir = dir_path
            self.dir_path_label.setText(dir_path)
            self.extract_btn.setEnabled(True)
            self.extract_btn.setStyleSheet(self._theme.primary_btn())
            self.status_label.setVisible(False)

    def _start_extraction(self):
        if not self.selected_dir:
            QMessageBox.warning(self, t("warning", self._lang),
                                t("fe_warning_no_dir", self._lang))
            return

        self.extract_btn.setEnabled(False)
        self.extract_btn.setStyleSheet(self._theme.primary_btn(disabled=True))
        self.select_dir_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(False)

        custom_name = self.index_name_input.text().strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = ''.join(c if c.isalnum() else '_' for c in custom_name) if custom_name else ""

        if safe_name:
            index_path = f"index_{safe_name}_{timestamp}.faiss"
            meta_path = f"metadata_{safe_name}_{timestamp}.json"
        else:
            index_path = f"index_{timestamp}.faiss"
            meta_path = f"metadata_{timestamp}.json"

        self.worker = FeatureExtractionWorker(
            self.selected_dir, self.retrieval_system, index_path, meta_path
        )
        self.worker.progress.connect(self._update_progress)
        self.worker.finished.connect(self._extraction_finished)
        self.worker.error.connect(self._extraction_error)
        self.worker.start()

    def _update_progress(self, value: int):
        self.progress_bar.setValue(value)

    def _extraction_finished(self):
        lang = self._lang
        self.progress_bar.setVisible(False)
        done_text = t("fe_done", lang, index=self.worker.index_path, meta=self.worker.metadata_path)
        self.status_label.setText(done_text)
        self.status_label.setStyleSheet(
            f"font-size: {self._theme.font_sm}; color: {self._theme.success};"
        )
        self.status_label.setVisible(True)
        self.extract_btn.setEnabled(True)
        self.extract_btn.setStyleSheet(self._theme.primary_btn())
        self.select_dir_btn.setEnabled(True)
        QMessageBox.information(
            self, t("fe_success_title", lang),
            t("fe_success_msg", lang, index=self.worker.index_path, meta=self.worker.metadata_path)
        )

    def _extraction_error(self, error_msg: str):
        lang = self._lang
        self.progress_bar.setVisible(False)
        self.status_label.setText(t("fe_error_msg", lang, error=error_msg))
        self.status_label.setStyleSheet(
            f"font-size: {self._theme.font_sm}; color: {self._theme.danger};"
        )
        self.status_label.setVisible(True)
        self.extract_btn.setEnabled(True)
        self.extract_btn.setStyleSheet(self._theme.primary_btn())
        self.select_dir_btn.setEnabled(True)
        QMessageBox.critical(self, t("fe_error_title", lang),
                             t("fe_error_msg", lang, error=error_msg))


# ═══════════════════════════════════════════════════════════════
#  RetrievalTab
# ═══════════════════════════════════════════════════════════════

class RetrievalTab(QWidget):
    def __init__(self, model_dir=None, theme=None):
        super().__init__()
        self._theme = theme or LIGHT
        self._lang = self._theme.language if hasattr(self._theme, 'language') else "en"
        self.model_dir = model_dir
        self.retrieval_system: Optional[ImageRetrievalSystem] = None
        self.query_image_path: Optional[str] = None
        self._overlay: Optional[LoadingOverlay] = None
        self._results_placeholder: Optional[QLabel] = None

        self._setup_ui()
        self._apply_theme()
        self._register_shortcuts()
        self.retranslate_ui()
        self.try_load_latest_index()

    def retranslate_ui(self):
        """Refresh all visible text according to current language."""
        lang = self._lang
        # Index section
        self.idx_title.setText(t("rt_index_section", lang))
        self.current_index_label.setText(t("rt_no_index", lang))
        self.load_latest_btn.setText(t("rt_latest_btn", lang))
        self.load_latest_btn.setToolTip(t("rt_latest_tip", lang))
        self.load_specific_btn.setText(t("rt_load_btn", lang))
        self.load_specific_btn.setToolTip(t("rt_load_tip", lang))
        # Query section
        self.q_title.setText(t("rt_query_section", lang))
        qt = self.query_image_path
        if qt:
            self.drop_target.setText(t("rt_selected", lang, name=os.path.basename(qt)))
            self.query_label.setText(os.path.basename(qt))
        else:
            self.drop_target.setText(t("rt_drop_hint", lang))
            self.query_label.setText(t("rt_no_query", lang))
        self.select_query_btn.setText(t("rt_query_browse", lang))
        self.select_query_btn.setToolTip(t("rt_query_tip", lang))
        # Search controls
        self.topk_label.setText(t("rt_topk", lang))
        self.search_btn.setText(t("rt_search_btn", lang))
        self.search_btn.setToolTip(t("rt_search_tip", lang))
        self.shortcut_hint.setText(t("rt_shortcuts", lang))
        # Results placeholder
        self._results_placeholder.setText(t("rt_no_search_yet", lang))
        self.results_title.setText(t("rt_similarity", lang))

    # ─── UI Setup ────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(22)
        layout.setContentsMargins(18, 18, 18, 18)

        # ═══ Index section ═══
        idx_frame = QFrame()
        idx_frame.setObjectName("card")
        idx_layout = QVBoxLayout(idx_frame)
        idx_layout.setSpacing(16)
        idx_layout.setContentsMargins(18, 18, 18, 18)

        idx_header = QHBoxLayout()
        self.idx_title = self._make_label("")
        self.idx_title.setStyleSheet(self._theme.label_style(bold=True))
        idx_header.addWidget(self.idx_title)
        idx_header.addStretch()
        idx_layout.addLayout(idx_header)

        idx_row = QHBoxLayout()
        self.current_index_label = QLabel("No index loaded")
        self.current_index_label.setStyleSheet(self._theme.info_panel_style())
        idx_row.addWidget(self.current_index_label, stretch=1)

        self.load_latest_btn = QPushButton("Latest")
        self.load_latest_btn.setStyleSheet(self._theme.secondary_btn())
        self.load_latest_btn.setToolTip("Auto-detect the most recent .faiss file in current folder")
        self.load_latest_btn.clicked.connect(self.try_load_latest_index)

        self.load_specific_btn = QPushButton("Load...")
        self.load_specific_btn.setStyleSheet(self._theme.secondary_btn())
        self.load_specific_btn.setToolTip("Browse and select a .faiss index file manually")
        self.load_specific_btn.clicked.connect(self._load_specific_index)

        idx_row.addWidget(self.load_latest_btn)
        idx_row.addWidget(self.load_specific_btn)
        idx_layout.addLayout(idx_row)
        layout.addWidget(idx_frame)

        # ═══ Query section ═══
        q_frame = QFrame()
        q_frame.setObjectName("card")
        q_layout = QVBoxLayout(q_frame)
        q_layout.setSpacing(16)
        q_layout.setContentsMargins(18, 18, 18, 18)

        q_header = QHBoxLayout()
        self.q_title = self._make_label("")
        self.q_title.setStyleSheet(self._theme.label_style(bold=True))
        q_header.addWidget(self.q_title)
        q_layout.addLayout(q_header)

        # Drop target
        self.drop_target = DropTargetLabel("", self._theme)
        self.drop_target.fileDropped.connect(self._on_image_dropped)
        q_layout.addWidget(self.drop_target)

        # Browse row
        browse_row = QHBoxLayout()
        self.query_label = QLabel("No image selected")
        self.query_label.setStyleSheet(self._theme.info_panel_style())
        browse_row.addWidget(self.query_label, stretch=1)

        self.select_query_btn = QPushButton()
        self.select_query_btn.setStyleSheet(self._theme.secondary_btn())
        self.select_query_btn.setToolTip("")
        self.select_query_btn.clicked.connect(self._select_query_image)
        browse_row.addWidget(self.select_query_btn)
        q_layout.addLayout(browse_row)
        layout.addWidget(q_frame)

        # ═══ Search controls ═══
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(14)

        self.topk_label = self._make_label("")
        ctrl_layout.addWidget(self.topk_label)
        self.num_results_spin = QSpinBox()
        self.num_results_spin.setRange(1, 50)
        self.num_results_spin.setValue(5)
        self.num_results_spin.setMinimumHeight(40)
        self.num_results_spin.setStyleSheet(self._theme.input_style())
        ctrl_layout.addWidget(self.num_results_spin)
        ctrl_layout.addSpacing(24)

        self.search_btn = QPushButton()
        self.search_btn.setStyleSheet(self._theme.primary_btn(disabled=True))
        self.search_btn.setEnabled(False)
        self.search_btn.setMinimumHeight(52)
        self.search_btn.setMinimumWidth(160)
        self.search_btn.setToolTip("")
        self.search_btn.clicked.connect(self._perform_search)
        ctrl_layout.addWidget(self.search_btn)
        ctrl_layout.addStretch()
        layout.addLayout(ctrl_layout)

        # Keyboard hint
        self.shortcut_hint = QLabel()
        self.shortcut_hint.setStyleSheet(
            f"font-size: {self._theme.font_xs}; color: {self._theme.text_muted};"
        )
        layout.addWidget(self.shortcut_hint)

        # ═══ Results area ═══
        self.results_title = self._make_label("")
        self.results_title.setStyleSheet(self._theme.label_style(bold=True))
        layout.addWidget(self.results_title)

        # Results placeholder (shown before any search)
        self._results_placeholder = QLabel()
        self._results_placeholder.setAlignment(Qt.AlignCenter)
        self._results_placeholder.setStyleSheet(f"""
            QLabel {{
                color: {self._theme.text_muted};
                font-size: {self._theme.font_lg};
                padding: 40px;
                border: 2px dashed {self._theme.border};
                border-radius: {self._theme.radius_lg};
                background: {self._theme.bg_secondary};
            }}
        """)
        self._results_placeholder.setWordWrap(True)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setMinimumHeight(300)
        self.results_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background: transparent; }}"
        )

        self.results_container = QWidget()
        self.results_grid = QGridLayout()
        self.results_grid.setSpacing(20)
        self.results_container.setLayout(self.results_grid)
        self.results_scroll.setWidget(self.results_container)

        layout.addWidget(self._results_placeholder)
        layout.addWidget(self.results_scroll, stretch=1)
        self.setLayout(layout)

    # ─── Little helpers ─────────────────────────────────────

    def _make_label(self, text: str, bold: bool = False, size: Optional[str] = None) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(self._theme.label_style(bold=bold, size=size or self._theme.font_sm))
        return lbl

    def _apply_theme(self):
        self.setStyleSheet(f"""
            RetrievalTab {{
                background: {self._theme.bg_primary};
            }}
            QFrame#card {{
                background: {self._theme.bg_secondary};
                border: 2px solid {self._theme.border};
                border-radius: {self._theme.radius_lg};
            }}
            {self._theme.scrollbar_style}
        """)

    def _register_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self._select_query_image)
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._perform_search)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._load_specific_index)

    # ─── Query image ────────────────────────────────────────

    def _select_query_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Query Image", "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self._set_query_image(path)

    def _on_image_dropped(self, path: str):
        self._set_query_image(path)

    def _set_query_image(self, path: str):
        self.query_image_path = path
        self.query_label.setText(os.path.basename(path))
        self.drop_target.setText(t("rt_selected", self._lang, name=os.path.basename(path)))
        self.drop_target.setStyleSheet(f"""
            QLabel {{
                background: {self._theme.success_light};
                border: 2px solid {self._theme.success};
                border-radius: {self._theme.radius_md};
                padding: {self._theme.padding_lg};
                font-size: {self._theme.font_sm};
                color: {self._theme.success};
                font-weight: 600;
            }}
        """)
        if self.retrieval_system:
            self.search_btn.setEnabled(True)
            self.search_btn.setStyleSheet(self._theme.primary_btn())

    # ─── Index loading ──────────────────────────────────────

    def try_load_latest_index(self) -> bool:
        """Auto-load the most recent .faiss + .json from the current working directory."""
        try:
            cwd = Path.cwd()
            faiss_files = list(cwd.glob("*.faiss"))
            json_files = list(cwd.glob("*.json"))
            if not faiss_files or not json_files:
                self.current_index_label.setText(t("rt_no_index_guide", self._lang))
                self.current_index_label.setToolTip(t("rt_no_index_tip", self._lang))
                return False

            latest_idx = max(faiss_files, key=lambda f: f.stat().st_mtime)
            latest_meta = max(json_files, key=lambda f: f.stat().st_mtime)
            return self._load_index(str(latest_idx), str(latest_meta))
        except Exception as e:
            logger.error(f"Auto-load index error: {e}")
            self.current_index_label.setText(t("rt_load_error", self._lang, error=str(e))[:60])
            return False

    def _load_specific_index(self):
        idx_path, _ = QFileDialog.getOpenFileName(
            self, "Select Index File", "", "FAISS Files (*.faiss)"
        )
        if not idx_path:
            return

        base = os.path.splitext(idx_path)[0]
        meta_path = f"{base}.json"
        if not os.path.exists(meta_path):
            meta_path, _ = QFileDialog.getOpenFileName(
                self, "Select Metadata File", "", "JSON Files (*.json)"
            )
            if not meta_path:
                return
        self._load_index(idx_path, meta_path)

    def _load_index(self, idx_path: str, meta_path: str) -> bool:
        try:
            self.retrieval_system = ImageRetrievalSystem(
                index_path=idx_path, metadata_path=meta_path
            )
            name = os.path.basename(idx_path)
            count = self.retrieval_system.index.ntotal
            self.current_index_label.setText(
                t("rt_index_loaded", self._lang, name=name, count=count)
            )
            self.search_btn.setEnabled(bool(self.query_image_path))
            if self.query_image_path:
                self.search_btn.setStyleSheet(self._theme.primary_btn())
            return True
        except Exception as e:
            logger.error(f"Load index error: {e}")
            QMessageBox.critical(
                self, t("rt_load_error_title", self._lang),
                t("rt_load_error", self._lang, error=str(e))
            )
            return False

    # ─── Search ─────────────────────────────────────────────

    def _perform_search(self):
        lang = self._lang
        if not self.query_image_path:
            QMessageBox.warning(self, t("warning", lang), t("rt_warning_no_query", lang))
            return
        if not self.retrieval_system:
            QMessageBox.warning(self, t("warning", lang), t("rt_warning_no_index", lang))
            return

        self._show_loading(True)
        # Use a single-shot timer so the UI updates before heavy work
        QTimer.singleShot(50, self._do_search)

    def _do_search(self):
        try:
            k = self.num_results_spin.value()
            results = self.retrieval_system.search(self.query_image_path, k=k)
            self._display_results(results)
        except Exception as e:
            QMessageBox.critical(
                self, t("error", self._lang),
                t("rt_search_error", self._lang, error=str(e))
            )
        finally:
            self._show_loading(False)

    def _show_loading(self, visible: bool):
        searching = t("rt_searching", self._lang)
        search_btn = t("rt_search_btn", self._lang)
        if visible:
            if not self._overlay:
                self._overlay = LoadingOverlay(self.results_scroll, searching)
            self._overlay.show_with(searching)
            self.search_btn.setEnabled(False)
            self.search_btn.setText(searching)
        else:
            if self._overlay:
                self._overlay.hide()
            self.search_btn.setEnabled(True)
            self.search_btn.setText(search_btn)
            if self.retrieval_system and self.query_image_path:
                self.search_btn.setStyleSheet(self._theme.primary_btn())

    # ─── Results display ────────────────────────────────────

    def _display_results(self, results: List[Tuple]):
        """Display results in a responsive grid."""
        # Hide placeholder, show scroll area
        self._results_placeholder.setVisible(False)
        self.results_scroll.setVisible(True)

        # Clear previous
        while self.results_grid.count():
            item = self.results_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        if not results:
            empty = QLabel(t("rt_no_results", self._lang))
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color: {self._theme.text_muted}; font-size: {self._theme.font_lg};"
            )
            self.results_grid.addWidget(empty, 0, 0)
            return

        # Compute column count based on available width
        w = self.results_scroll.viewport().width() if self.results_scroll.viewport() else 600
        max_cols = max(1, min(4, w // 280))

        for rank, (path, similarity, metadata) in enumerate(results, 1):
            card = self._build_result_card(rank, path, similarity, metadata)
            r = (rank - 1) // max_cols
            c = (rank - 1) % max_cols
            self.results_grid.addWidget(card, r, c)

    def _build_result_card(self, rank: int, path: str, similarity: float,
                           metadata: dict) -> QFrame:
        """Build a styled card widget for one search result."""
        card = QFrame()
        card.setObjectName("result-card")
        card.setStyleSheet(f"""
            QFrame#result-card {{
                background: {self._theme.bg_primary};
                border: 2px solid {self._theme.border};
                border-radius: {self._theme.radius_lg};
            }}
            QFrame#result-card:hover {{
                border-color: {self._theme.accent};
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(12)
        layout.setContentsMargins(14, 14, 14, 14)

        # Rank badge
        rank_colors = {
            1: ("#FFD700", "#8B6914"),
            2: ("#C0C0C0", "#555555"),
            3: ("#CD7F32", "#5C3A1E"),
        }
        bg, fg = rank_colors.get(rank, (self._theme.accent_light, self._theme.accent))
        badge = QLabel(f"#{rank}")
        badge.setStyleSheet(self._theme.badge_style(bg, fg))
        badge.setAlignment(Qt.AlignCenter)
        badge.setMaximumWidth(70)
        layout.addWidget(badge)

        # Image
        img = EnhancedImageDisplay()
        img.set_image(path)
        layout.addWidget(img)

        # Info
        sim_pct = int(similarity * 100)
        sim_lbl = t("rt_similarity", self._lang)
        dist_lbl = t("rt_distance", self._lang)
        file_lbl = t("rt_file", self._lang)
        info = (
            f"{sim_lbl}: {similarity:.3f}  ({sim_pct}%)\n"
            f"{dist_lbl}: {metadata.get('distance', 0):.3f}\n"
            f"{file_lbl}: {os.path.basename(path)}"
        )
        info_lbl = QLabel(info)
        info_lbl.setAlignment(Qt.AlignCenter)
        info_lbl.setStyleSheet(f"""
            QLabel {{
                background: {self._theme.bg_tertiary};
                padding: {self._theme.padding_md};
                border-radius: {self._theme.radius_md};
                font-size: {self._theme.font_md};
                color: {self._theme.text_primary};
                font-weight: 600;
            }}
        """)
        layout.addWidget(info_lbl)
        return card


# ═══════════════════════════════════════════════════════════════
#  MainWindow
# ═══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self, theme=None):
        super().__init__()
        self._theme = theme or LIGHT
        self._lang = "en"
        self.model_dir = self._resolve_model_dir()

        self.setWindowTitle(t("window_title", self._lang))
        self.setMinimumSize(900, 650)

        # ── Tab widget ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {self._theme.bg_primary};
            }}
            QTabBar {{
                min-height: 64px;
                max-height: 72px;
            }}
            QTabBar::tab {{
                background: {self._theme.bg_secondary};
                color: {self._theme.text_secondary};
                min-height: 50px;
                padding: 6px 40px;
                margin-right: 4px;
                border-top-left-radius: {self._theme.radius_md};
                border-top-right-radius: {self._theme.radius_md};
                font-size: 36px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background: {self._theme.bg_primary};
                color: {self._theme.accent};
                border-bottom: 3px solid {self._theme.accent};
            }}
            QTabBar::tab:hover {{
                color: {self._theme.text_primary};
            }}
        """)
        tab_bar = self.tabs.tabBar()
        tab_bar.setExpanding(True)
        tab_bar.setElideMode(Qt.ElideNone)
        tab_bar.setMinimumHeight(64)
        tab_bar.setMaximumHeight(72)

        self.extraction_tab = FeatureExtractionTab(
            model_dir=self.model_dir, theme=self._theme
        )
        self.retrieval_tab = RetrievalTab(
            model_dir=self.model_dir, theme=self._theme
        )
        self.tabs.addTab(self.extraction_tab, "")
        self.tabs.addTab(self.retrieval_tab, "")

        # ── Language button (corner widget — shares tab parent boundaries) ──
        cur = "EN" if self._lang == "en" else "中文"
        self.lang_btn = QPushButton(cur)
        self.lang_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._theme.bg_secondary};
                color: {self._theme.accent};
                border: 1px solid {self._theme.border};
                border-radius: {self._theme.radius_md};
                padding: 16px 28px;
                font-size: 28px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {self._theme.accent_light};
                border-color: {self._theme.accent};
            }}
        """)
        self.lang_btn.clicked.connect(self._toggle_language)
        self.lang_btn.setToolTip(
            "Switch to 中文" if self._lang == "en" else "Switch to English"
        )
        # Use corner widget — right edge of button = right edge of tab content
        self.tabs.setCornerWidget(self.lang_btn, Qt.TopRightCorner)

        # ── Layout ──
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # ── Tab text ──
        self._update_tab_text()
        # Dynamic tab width after text is set
        self._resize_tabs()

    # ── Tab sizing ──

    def _resize_tabs(self):
        """Double the tab button width for readability."""
        bar = self.tabs.tabBar()
        fm = QFontMetrics(bar.font())
        max_w = 0
        for i in range(bar.count()):
            text = bar.tabText(i)
            w = fm.horizontalAdvance(text)
            if any('一' <= c <= '鿿' for c in text):
                w = int(w * 1.15)
            max_w = max(max_w, w)
        # Width: (text + 40px padding) * 2 * 1.1 per tab
        min_full = int((max_w + 40) * 2 * 1.1)
        bar.setMinimumWidth(min_full * bar.count())

    # ── Language toggle ──

    def _toggle_language(self):
        """Toggle between English and Chinese."""
        self._lang = toggle_lang(self._lang)
        self.setWindowTitle(t("window_title", self._lang))

        # Button: show only current language
        cur = "EN" if self._lang == "en" else "中文"
        tip = "Switch to 中文" if self._lang == "en" else "Switch to English"
        self.lang_btn.setText(cur)
        self.lang_btn.setToolTip(tip)

        # Tab bar font: English +1pt
        bar = self.tabs.tabBar()
        f = bar.font()
        f.setPointSize(f.pointSize() if self._lang == "en" else f.pointSize() - 1)
        if self._lang == "en":
            f.setPointSize(f.pointSize() + 1)
        bar.setFont(f)

        # Propagate to tabs
        self.extraction_tab._lang = self._lang
        self.retrieval_tab._lang = self._lang
        self.extraction_tab.retranslate_ui()
        self.retrieval_tab.retranslate_ui()
        self._update_tab_text()
        self._resize_tabs()

    def _update_tab_text(self):
        """Refresh tab labels."""
        self.tabs.setTabText(0, t("tab_extraction", self._lang))
        self.tabs.setTabText(1, t("tab_retrieval", self._lang))

    @staticmethod
    def _resolve_model_dir() -> str:
        try:
            home = Path.home()
            d = home / '.vit_image_retrieval' / 'models'
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"Model directory: {d}")
            return str(d)
        except Exception:
            import tempfile
            d = Path(tempfile.gettempdir()) / '.vit_image_retrieval' / 'models'
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"Model directory (fallback): {d}")
            return str(d)
            home = Path.home()
            d = home / '.vit_image_retrieval' / 'models'
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"Model directory: {d}")
            return str(d)
        except Exception:
            import tempfile
            d = Path(tempfile.gettempdir()) / '.vit_image_retrieval' / 'models'
            d.mkdir(parents=True, exist_ok=True)
            logger.info(f"Model directory (fallback): {d}")
            return str(d)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
