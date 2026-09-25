import sys
import time
import threading
from pathlib import Path

import mss
import win32api
import win32con

from PySide6.QtCore import (
    Qt,
    QTimer,
    QRect,
    QPoint,
    QThread,
    Signal,
)

from PySide6.QtGui import (
    QImage,
    QPainter,
    QPen,
    QBrush,
    QColor,
    QPolygon,
    QIcon,
    QPixmap,
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QSizePolicy,
)


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

ICON_PATH = ASSETS_DIR / "logo.ico"
LOGO_PATH = ASSETS_DIR / "logo.jpeg"


# ============================================================
# THREAD DE CAPTURA
# ============================================================

class CaptureThread(QThread):
    frame_ready = Signal()

    def __init__(self, monitor_index=1, fps=60):
        super().__init__()

        self.monitor_index = monitor_index
        self.target_fps = fps

        self.running = False

        self.lock = threading.Lock()
        self.latest_frame = None

        self.frame_width = 0
        self.frame_height = 0

        self.capture_fps = 0.0

    def set_monitor(self, monitor_index):
        self.monitor_index = monitor_index

    def set_fps(self, fps):
        self.target_fps = max(1, fps)

    def get_latest_frame(self):
        with self.lock:
            return self.latest_frame

    def run(self):
        self.running = True

        frame_counter = 0
        fps_start = time.perf_counter()

        try:
            with mss.mss() as sct:

                monitors = sct.monitors

                if self.monitor_index >= len(monitors):
                    self.monitor_index = 1

                monitor = monitors[self.monitor_index]

                next_frame_time = time.perf_counter()

                while self.running:

                    # ------------------------------------------------
                    # Captura
                    # ------------------------------------------------

                    screenshot = sct.grab(monitor)

                    width = screenshot.width
                    height = screenshot.height

                    # MSS retorna BGRA.
                    # Mantemos os bytes diretamente para evitar
                    # conversões desnecessárias com NumPy/PIL.
                    frame = bytes(screenshot.bgra)

                    with self.lock:
                        self.latest_frame = frame
                        self.frame_width = width
                        self.frame_height = height

                    self.frame_ready.emit()

                    # ------------------------------------------------
                    # Contador de FPS
                    # ------------------------------------------------

                    frame_counter += 1

                    now = time.perf_counter()

                    elapsed = now - fps_start

                    if elapsed >= 1.0:
                        self.capture_fps = frame_counter / elapsed

                        frame_counter = 0
                        fps_start = now

                    # ------------------------------------------------
                    # Controle de FPS
                    # ------------------------------------------------

                    frame_interval = 1.0 / max(1, self.target_fps)

                    next_frame_time += frame_interval

                    sleep_time = next_frame_time - time.perf_counter()

                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    else:
                        next_frame_time = time.perf_counter()

        except Exception as e:
            print(f"Erro na captura: {e}")

        self.running = False

    def stop(self):
        self.running = False

        if self.isRunning():
            self.wait(2000)


# ============================================================
# PREVIEW
# ============================================================

class PreviewWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumSize(400, 250)

        self.image = None

        self.frame_width = 0
        self.frame_height = 0

        self.control_enabled = False

        self.monitor_geometry = QRect()

        self.show_welcome = True

        self.setMouseTracking(True)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

    # --------------------------------------------------------
    # Configurações
    # --------------------------------------------------------

    def set_monitor_geometry(self, geometry):
        self.monitor_geometry = geometry

    def set_control_enabled(self, enabled):
        self.control_enabled = enabled

    def set_welcome(self, enabled):
        self.show_welcome = enabled
        self.update()

    # --------------------------------------------------------
    # Recebe frame
    # --------------------------------------------------------

    def set_frame(self, frame, width, height):

        if not frame:
            return

        self.frame_width = width
        self.frame_height = height

        try:
            self.image = QImage(
                frame,
                width,
                height,
                width * 4,
                QImage.Format.Format_ARGB32
            )

        except Exception as e:
            print(f"Erro ao criar QImage: {e}")
            return

        self.show_welcome = False

        self.update()

    # --------------------------------------------------------
    # Conversão Preview -> Monitor real
    # --------------------------------------------------------

    def preview_to_screen(self, pos):

        if self.frame_width <= 0 or self.frame_height <= 0:
            return None

        widget_width = self.width()
        widget_height = self.height()

        if widget_width <= 0 or widget_height <= 0:
            return None

        scale_x = widget_width / self.frame_width
        scale_y = widget_height / self.frame_height

        scale = min(scale_x, scale_y)

        rendered_width = self.frame_width * scale
        rendered_height = self.frame_height * scale

        offset_x = (widget_width - rendered_width) / 2
        offset_y = (widget_height - rendered_height) / 2

        x = (pos.x() - offset_x) / scale
        y = (pos.y() - offset_y) / scale

        if x < 0 or y < 0:
            return None

        if x >= self.frame_width or y >= self.frame_height:
            return None

        monitor_x = int(
            self.monitor_geometry.x()
            + (x / self.frame_width)
            * self.monitor_geometry.width()
        )

        monitor_y = int(
            self.monitor_geometry.y()
            + (y / self.frame_height)
            * self.monitor_geometry.height()
        )

        return QPoint(monitor_x, monitor_y)

    # --------------------------------------------------------
    # Cursor
    # --------------------------------------------------------

    def draw_cursor(self, painter):

        if not self.control_enabled:
            return

        cursor_pos = win32api.GetCursorPos()

        monitor_x = self.monitor_geometry.x()
        monitor_y = self.monitor_geometry.y()

        monitor_width = self.monitor_geometry.width()
        monitor_height = self.monitor_geometry.height()

        if monitor_width <= 0 or monitor_height <= 0:
            return

        relative_x = (
            cursor_pos[0] - monitor_x
        ) / monitor_width

        relative_y = (
            cursor_pos[1] - monitor_y
        ) / monitor_height

        if relative_x < 0 or relative_x > 1:
            return

        if relative_y < 0 or relative_y > 1:
            return

        widget_width = self.width()
        widget_height = self.height()

        scale_x = widget_width / self.frame_width
        scale_y = widget_height / self.frame_height

        scale = min(scale_x, scale_y)

        rendered_width = self.frame_width * scale
        rendered_height = self.frame_height * scale

        offset_x = (widget_width - rendered_width) / 2
        offset_y = (widget_height - rendered_height) / 2

        x = int(
            offset_x
            + relative_x * rendered_width
        )

        y = int(
            offset_y
            + relative_y * rendered_height
        )

        size = 18

        points = QPolygon([
            QPoint(x, y),

            QPoint(
                x + int(size * 0.35),
                y + int(size * 0.28)
            ),

            QPoint(
                x + int(size * 0.28),
                y + int(size * 0.34)
            ),

            QPoint(
                x + int(size * 0.55),
                y + int(size * 0.62)
            ),

            QPoint(
                x + int(size * 0.70),
                y + int(size * 0.52)
            ),

            QPoint(
                x + int(size * 1.00),
                y + int(size * 0.70)
            ),

            QPoint(
                x + int(size * 0.88),
                y + int(size * 0.82)
            ),

            QPoint(
                x + int(size * 0.58),
                y + int(size * 0.62)
            ),

            QPoint(
                x + int(size * 0.48),
                y + int(size * 0.78)
            ),

            QPoint(
                x + int(size * 0.35),
                y + int(size * 0.45)
            ),
        ])

        painter.setPen(
            QPen(
                QColor(0, 0, 0),
                2
            )
        )

        painter.setBrush(
            QBrush(
                QColor(255, 255, 255)
            )
        )

        painter.drawPolygon(points)

    # --------------------------------------------------------
    # Pintura
    # --------------------------------------------------------

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.SmoothPixmapTransform,
            False
        )

        # ----------------------------------------------------
        # Fundo
        # ----------------------------------------------------

        painter.fillRect(
            self.rect(),
            QColor("#111111")
        )

        # ----------------------------------------------------
        # Tela inicial
        # ----------------------------------------------------

        if self.show_welcome or self.image is None:

            self.draw_welcome(painter)

            painter.end()
            return

        # ----------------------------------------------------
        # Calcula escala mantendo proporção
        # ----------------------------------------------------

        widget_rect = self.rect()

        image_width = self.image.width()
        image_height = self.image.height()

        if image_width <= 0 or image_height <= 0:
            painter.end()
            return

        scale_x = widget_rect.width() / image_width
        scale_y = widget_rect.height() / image_height

        scale = min(scale_x, scale_y)

        draw_width = int(image_width * scale)
        draw_height = int(image_height * scale)

        x = (
            widget_rect.width()
            - draw_width
        ) // 2

        y = (
            widget_rect.height()
            - draw_height
        ) // 2

        target_rect = QRect(
            x,
            y,
            draw_width,
            draw_height
        )

        # ----------------------------------------------------
        # Desenha imagem
        # ----------------------------------------------------

        painter.drawImage(
            target_rect,
            self.image
        )

        # ----------------------------------------------------
        # Cursor
        # ----------------------------------------------------

        self.draw_cursor(painter)

        painter.end()

    # --------------------------------------------------------
    # Tela inicial
    # --------------------------------------------------------

    def draw_welcome(self, painter):

        width = self.width()
        height = self.height()

        center_x = width // 2

        # ----------------------------------------------------
        # Logo
        # ----------------------------------------------------

        logo_size = min(
            110,
            max(70, int(height * 0.22))
        )

        logo_x = center_x - logo_size // 2

        logo_y = int(
            height * 0.28
        )

        if LOGO_PATH.exists():

            pixmap = QPixmap(
                str(LOGO_PATH)
            )

            if not pixmap.isNull():

                pixmap = pixmap.scaled(
                    logo_size,
                    logo_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

                painter.drawPixmap(
                    logo_x,
                    logo_y,
                    pixmap
                )

        # ----------------------------------------------------
        # Título
        # ----------------------------------------------------

        title_y = logo_y + logo_size + 25

        painter.setPen(
            QColor("#f2f2f2")
        )

        font = painter.font()

        font.setBold(True)
        font.setPointSize(24)

        painter.setFont(font)

        title = "PyScreenControl"

        title_rect = QRect(
            0,
            title_y,
            width,
            40
        )

        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignCenter,
            title
        )

        # ----------------------------------------------------
        # Subtítulo
        # ----------------------------------------------------

        subtitle_y = title_y + 40

        font = painter.font()

        font.setBold(False)
        font.setPointSize(11)

        painter.setFont(font)

        painter.setPen(
            QColor("#aaaaaa")
        )

        subtitle_rect = QRect(
            0,
            subtitle_y,
            width,
            30
        )

        painter.drawText(
            subtitle_rect,
            Qt.AlignmentFlag.AlignCenter,
            "Visualização e controle de segunda tela"
        )

    # --------------------------------------------------------
    # Mouse
    # --------------------------------------------------------

    def mouseMoveEvent(self, event):

        if not self.control_enabled:
            return

        screen_pos = self.preview_to_screen(
            event.position().toPoint()
        )

        if screen_pos is None:
            return

        win32api.SetCursorPos(
            (
                screen_pos.x(),
                screen_pos.y()
            )
        )

    def mousePressEvent(self, event):

        if not self.control_enabled:
            return

        screen_pos = self.preview_to_screen(
            event.position().toPoint()
        )

        if screen_pos is None:
            return

        win32api.SetCursorPos(
            (
                screen_pos.x(),
                screen_pos.y()
            )
        )

        button = event.button()

        if button == Qt.MouseButton.LeftButton:

            win32api.mouse_event(
                win32con.MOUSEEVENTF_LEFTDOWN,
                0,
                0,
                0,
                0
            )

        elif button == Qt.MouseButton.RightButton:

            win32api.mouse_event(
                win32con.MOUSEEVENTF_RIGHTDOWN,
                0,
                0,
                0,
                0
            )

        elif button == Qt.MouseButton.MiddleButton:

            win32api.mouse_event(
                win32con.MOUSEEVENTF_MIDDLEDOWN,
                0,
                0,
                0,
                0
            )

    def mouseReleaseEvent(self, event):

        if not self.control_enabled:
            return

        button = event.button()

        if button == Qt.MouseButton.LeftButton:

            win32api.mouse_event(
                win32con.MOUSEEVENTF_LEFTUP,
                0,
                0,
                0,
                0
            )

        elif button == Qt.MouseButton.RightButton:

            win32api.mouse_event(
                win32con.MOUSEEVENTF_RIGHTUP,
                0,
                0,
                0,
                0
            )

        elif button == Qt.MouseButton.MiddleButton:

            win32api.mouse_event(
                win32con.MOUSEEVENTF_MIDDLEUP,
                0,
                0,
                0,
                0
            )

    def mouseDoubleClickEvent(self, event):

        if not self.control_enabled:
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        screen_pos = self.preview_to_screen(
            event.position().toPoint()
        )

        if screen_pos is None:
            return

        win32api.SetCursorPos(
            (
                screen_pos.x(),
                screen_pos.y()
            )
        )

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTDOWN,
            0,
            0,
            0,
            0
        )

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTUP,
            0,
            0,
            0,
            0
        )

        time.sleep(0.05)

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTDOWN,
            0,
            0,
            0,
            0
        )

        win32api.mouse_event(
            win32con.MOUSEEVENTF_LEFTUP,
            0,
            0,
            0,
            0
        )

    def wheelEvent(self, event):

        if not self.control_enabled:
            return

        delta = event.angleDelta().y()

        if delta == 0:
            return

        win32api.mouse_event(
            win32con.MOUSEEVENTF_WHEEL,
            0,
            0,
            delta,
            0
        )


# ============================================================
# JANELA PRINCIPAL
# ============================================================

class ScreenMirror(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "PyScreenControl"
        )

        self.setWindowIcon(
            QIcon(str(ICON_PATH))
        )

        self.resize(
            1100,
            700
        )

        self.setMinimumSize(
            800,
            550
        )

        self.capture_thread = None

        self.setup_ui()

        self.refresh_monitors()

        # ----------------------------------------------------
        # Timer de atualização da interface
        # ----------------------------------------------------

        self.render_timer = QTimer(self)

        self.render_timer.timeout.connect(
            self.update_preview
        )

        self.render_timer.start(16)

        # ----------------------------------------------------
        # Timer do FPS
        # ----------------------------------------------------

        self.fps_timer = QTimer(self)

        self.fps_timer.timeout.connect(
            self.update_fps
        )

        self.fps_timer.start(500)

    # ========================================================
    # INTERFACE
    # ========================================================

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        main_layout.setContentsMargins(
            10,
            10,
            10,
            10
        )

        main_layout.setSpacing(
            8
        )

        

        # ----------------------------------------------------
        # Barra de controles
        # ----------------------------------------------------

        controls = QFrame()

        controls.setObjectName(
            "controls"
        )

        controls_layout = QHBoxLayout(
            controls
        )

        controls_layout.setContentsMargins(
            10,
            8,
            10,
            8
        )

        controls_layout.setSpacing(
            8
        )

        # ----------------------------------------------------
        # Monitor
        # ----------------------------------------------------

        monitor_label = QLabel(
            "Monitor:"
        )

        self.monitor_combo = QComboBox()

        self.monitor_combo.setMinimumWidth(
            180
        )

        self.monitor_combo.currentIndexChanged.connect(
            self.monitor_changed
        )

        controls_layout.addWidget(
            monitor_label
        )

        controls_layout.addWidget(
            self.monitor_combo
        )

        # ----------------------------------------------------
        # FPS
        # ----------------------------------------------------

        fps_label = QLabel(
            "FPS:"
        )

        self.fps_spin = QSpinBox()

        self.fps_spin.setRange(
            15,
            120
        )

        self.fps_spin.setValue(
            60
        )

        self.fps_spin.setSuffix(
            " FPS"
        )

        self.fps_spin.valueChanged.connect(
            self.fps_changed
        )

        controls_layout.addWidget(
            fps_label
        )

        controls_layout.addWidget(
            self.fps_spin
        )

        # ----------------------------------------------------
        # Controle
        # ----------------------------------------------------

        self.control_combo = QComboBox()

        self.control_combo.addItems([
            "Somente visualização",
            "Controle pela janela"
        ])

        self.control_combo.currentIndexChanged.connect(
            self.control_mode_changed
        )

        controls_layout.addWidget(
            self.control_combo
        )

        # ----------------------------------------------------
        # Always on top
        # ----------------------------------------------------

        self.always_on_top = QCheckBox(
            "Sempre no topo"
        )

        self.always_on_top.stateChanged.connect(
            self.toggle_always_on_top
        )

        controls_layout.addWidget(
            self.always_on_top
        )

        # ----------------------------------------------------
        # Espaçador
        # ----------------------------------------------------

        controls_layout.addStretch()

        # ----------------------------------------------------
        # FPS real
        # ----------------------------------------------------

        self.fps_label = QLabel(
            "Captura: -- FPS"
        )

        controls_layout.addWidget(
            self.fps_label
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        self.status_label = QLabel(
            "Parado"
        )

        controls_layout.addWidget(
            self.status_label
        )

        # ----------------------------------------------------
        # Botão
        # ----------------------------------------------------

        self.start_button = QPushButton(
            "Iniciar"
        )

        self.start_button.setMinimumWidth(
            100
        )

        self.start_button.clicked.connect(
            self.toggle_capture
        )

        controls_layout.addWidget(
            self.start_button
        )

        main_layout.addWidget(
            controls
        )

        # ----------------------------------------------------
        # Preview
        # ----------------------------------------------------

        self.preview = PreviewWidget()

        self.preview.setObjectName(
            "preview"
        )

        main_layout.addWidget(
            self.preview,
            1
        )

        # ====================================================
        # ESTILO
        # ====================================================

        self.setStyleSheet("""
            QMainWindow {
                background: #e9ecef;
            }

            QWidget {
                font-size: 10pt;
            }

            #preview {
                background: #111111;
                border: 1px solid #303030;
                border-radius: 6px;
            }

            #controls {
                background: white;
                border: 1px solid #d7d7d7;
                border-radius: 6px;
            }

            QLabel {
                color: #333333;
            }

            QComboBox,
            QSpinBox {
                background: white;
                border: 1px solid #c8c8c8;
                border-radius: 4px;
                padding: 5px 8px;
                min-height: 20px;
            }

            QComboBox:hover,
            QSpinBox:hover {
                border: 1px solid #999999;
            }

            QPushButton {
                background: #1976d2;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 7px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #1565c0;
            }

            QPushButton:pressed {
                background: #0d47a1;
            }

            QCheckBox {
                spacing: 5px;
            }
        """)

    # ========================================================
    # MONITORES
    # ========================================================

    def refresh_monitors(self):

        self.monitor_combo.blockSignals(
            True
        )

        self.monitor_combo.clear()

        with mss.mss() as sct:

            monitors = sct.monitors

            # monitors[0] é o desktop virtual inteiro.
            # Começamos no monitor 1.
            for index in range(
                1,
                len(monitors)
            ):

                monitor = monitors[index]

                text = (
                    f"Monitor {index} - "
                    f"{monitor['width']}x"
                    f"{monitor['height']}"
                )

                self.monitor_combo.addItem(
                    text,
                    index
                )

        self.monitor_combo.blockSignals(
            False
        )

        if self.monitor_combo.count() > 0:

            self.monitor_combo.setCurrentIndex(
                0
            )

            self.update_monitor_geometry()

    # ========================================================
    # MONITOR ALTERADO
    # ========================================================

    def monitor_changed(self, index):

        self.update_monitor_geometry()

        if self.capture_thread:

            monitor_index = self.monitor_combo.itemData(
                index
            )

            if monitor_index is not None:
                self.capture_thread.set_monitor(
                    monitor_index
                )

    def update_monitor_geometry(self):

        index = self.monitor_combo.currentData()

        if index is None:
            return

        try:

            with mss.mss() as sct:

                monitor = sct.monitors[index]

                geometry = QRect(
                    monitor["left"],
                    monitor["top"],
                    monitor["width"],
                    monitor["height"]
                )

                self.preview.set_monitor_geometry(
                    geometry
                )

        except Exception as e:

            print(
                f"Erro ao obter monitor: {e}"
            )

    # ========================================================
    # FPS
    # ========================================================

    def fps_changed(self, value):

        if self.capture_thread:

            self.capture_thread.set_fps(
                value
            )

    # ========================================================
    # CONTROLE
    # ========================================================

    def control_mode_changed(self, index):

        enabled = index == 1

        self.preview.set_control_enabled(
            enabled
        )

    # ========================================================
    # ALWAYS ON TOP
    # ========================================================

    def toggle_always_on_top(self, state):

        enabled = (
            state == Qt.CheckState.Checked.value
        )

        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint,
            enabled
        )

        self.show()

    # ========================================================
    # INICIAR / PARAR
    # ========================================================

    def toggle_capture(self):

        if self.capture_thread is None:

            self.start_capture()

        else:

            self.stop_capture()

    # ========================================================
    # INICIAR CAPTURA
    # ========================================================

    def start_capture(self):

        monitor_index = self.monitor_combo.currentData()

        if monitor_index is None:

            self.status_label.setText(
                "Nenhum monitor disponível"
            )

            return

        fps = self.fps_spin.value()

        self.update_monitor_geometry()

        self.preview.set_welcome(
            False
        )

        self.capture_thread = CaptureThread(
            monitor_index=monitor_index,
            fps=fps
        )

        self.capture_thread.start()

        self.start_button.setText(
            "Parar"
        )

        self.status_label.setText(
            "Capturando"
        )

        self.monitor_combo.setEnabled(
            False
        )

    # ========================================================
    # PARAR CAPTURA
    # ========================================================

    def stop_capture(self):

        if self.capture_thread:

            self.capture_thread.stop()

            self.capture_thread = None

        self.preview.image = None

        self.preview.frame_width = 0
        self.preview.frame_height = 0

        self.preview.set_welcome(
            True
        )

        self.start_button.setText(
            "Iniciar"
        )

        self.status_label.setText(
            "Parado"
        )

        self.fps_label.setText(
            "Captura: -- FPS"
        )

        self.monitor_combo.setEnabled(
            True
        )

    # ========================================================
    # ATUALIZA PREVIEW
    # ========================================================

    def update_preview(self):

        if not self.capture_thread:
            return

        frame = self.capture_thread.get_latest_frame()

        if frame is None:
            return

        width = self.capture_thread.frame_width
        height = self.capture_thread.frame_height

        if width <= 0 or height <= 0:
            return

        self.preview.set_frame(
            frame,
            width,
            height
        )

    # ========================================================
    # FPS
    # ========================================================

    def update_fps(self):

        if not self.capture_thread:

            self.fps_label.setText(
                "Captura: -- FPS"
            )

            return

        fps = self.capture_thread.capture_fps

        self.fps_label.setText(
            f"Captura: {fps:.0f} FPS"
        )

    # ========================================================
    # FECHAR
    # ========================================================

    def closeEvent(self, event):

        if self.capture_thread:

            self.capture_thread.stop()

            self.capture_thread = None

        event.accept()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    # --------------------------------------------------------
    # Ícone global
    # --------------------------------------------------------

    if ICON_PATH.exists():

        app.setWindowIcon(
            QIcon(str(ICON_PATH))
        )

    # --------------------------------------------------------
    # Janela
    # --------------------------------------------------------

    window = ScreenMirror()

    window.show()

    sys.exit(
        app.exec()
    )