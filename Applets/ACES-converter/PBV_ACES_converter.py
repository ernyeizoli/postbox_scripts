"""
PBV ACES Converter
Standalone GUI application to convert images from sRGB to ACEScg using OpenColorIO.

Author: PostBox Visual
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox, QListWidget,
    QListWidgetItem, QFrame, QSplitter
)

try:
    import PyOpenColorIO as OCIO
    OCIO_AVAILABLE = True
except ImportError:
    OCIO_AVAILABLE = False


# --- Constants ---
SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.exr', '.bmp']
APP_NAME = "PBV ACES Converter"
APP_VERSION = "1.0.0"

# Texture type keywords (from PBV_vray_material_from_folder.py)
TEXTURE_KEYWORDS = {
    'texturesColor': ['diffuse', 'diff', 'albedo', 'alb', 'base', 'col', 'color', 'basecolor'],
    'texturesMetal': ['metalic', 'metalness', 'metal', 'mtl', 'met'],
    'texturesSpecular': ['specularity', 'specular', 'spec', 'spc'],
    'texturesRough': ['roughness', 'rough', 'rgh'],
    'texturesGloss': ['gloss', 'glossy', 'glossiness'],
    'texturesTrans': ['transmisson', 'transparency', 'trans'],
    'texturesEmm': ['emission', 'emissive', 'emit', 'emm'],
    'texturesAlpha': ['alpha', 'opacity', 'opac'],
    'texturesBump': ['bump', 'bmp', 'height', 'displacement', 'displace', 'disp'],
    'texturesNormal': ['normal', 'nor', 'nrm', 'nrml', 'norm']
}

def is_color_texture(filename):
    """Check if a filename is a color/diffuse texture based on keywords."""
    name_lower = filename.lower()
    # Split by common separators to check individual parts
    parts = name_lower.replace('-', '_').replace('.', '_').split('_')
    
    color_keywords = TEXTURE_KEYWORDS['texturesColor']
    
    # Check if any part matches a color keyword
    for part in parts:
        if any(kw in part for kw in color_keywords):
            return True
    return False


class ConversionWorker(QThread):
    """Background worker for image conversion."""
    progress = Signal(int, str)  # progress percentage, message
    log = Signal(str, str)  # message, level (info/success/error/warning)
    finished = Signal(int, int)  # success count, error count
    
    def __init__(self, files, ocio_config_path, input_cs, output_cs, output_format, output_folder):
        super().__init__()
        self.files = files
        self.ocio_config_path = ocio_config_path
        self.input_cs = input_cs
        self.output_cs = output_cs
        self.output_format = output_format
        self.output_folder = output_folder
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    def run(self):
        if not OCIO_AVAILABLE:
            self.log.emit("ERROR: PyOpenColorIO is not installed!", "error")
            self.finished.emit(0, len(self.files))
            return
        
        try:
            config = OCIO.Config.CreateFromFile(self.ocio_config_path)
            processor = config.getProcessor(self.input_cs, self.output_cs)
            cpu = processor.getDefaultCPUProcessor()
        except Exception as e:
            self.log.emit(f"ERROR: Failed to create OCIO processor: {e}", "error")
            self.finished.emit(0, len(self.files))
            return
        
        success_count = 0
        error_count = 0
        total = len(self.files)
        
        for i, file_path in enumerate(self.files):
            if self._cancelled:
                self.log.emit("Conversion cancelled by user.", "warning")
                break
            
            try:
                self.log.emit(f"Converting: {os.path.basename(file_path)}...", "info")
                
                # Step 1: Load image
                self.log.emit("  Step 1: Loading image...", "info")
                img = Image.open(file_path).convert('RGB')
                self.log.emit(f"  Image size: {img.size}", "info")
                
                # Step 2: Convert to numpy array
                self.log.emit("  Step 2: Converting to numpy array...", "info")
                pixels = np.array(img, dtype=np.float32) / 255.0
                self.log.emit(f"  Array shape: {pixels.shape}, dtype: {pixels.dtype}", "info")
                
                # Step 3: Ensure C-contiguous
                self.log.emit("  Step 3: Making array contiguous...", "info")
                pixels = np.ascontiguousarray(pixels)
                self.log.emit(f"  Contiguous: {pixels.flags['C_CONTIGUOUS']}", "info")
                
                # Step 4: Apply OCIO transform
                self.log.emit("  Step 4: Applying OCIO transform...", "info")
                cpu.applyRGB(pixels)
                self.log.emit("  OCIO transform complete", "info")
                
                # Prepare output path
                base_name = Path(file_path).stem
                output_ext = self.output_format.lower()
                output_path = os.path.join(self.output_folder, f"{base_name}_ACEScg.{output_ext}")
                
                # Step 5: Save based on format
                self.log.emit(f"  Step 5: Saving as {output_ext}...", "info")
                if output_ext == 'exr':
                    self._save_exr(pixels, output_path)
                else:
                    # Clip values for non-HDR formats
                    pixels_clipped = np.clip(pixels * 255, 0, 255).astype(np.uint8)
                    self.log.emit(f"  Clipped array shape: {pixels_clipped.shape}", "info")
                    out_img = Image.fromarray(pixels_clipped, mode='RGB')
                    out_img.save(output_path)
                
                self.log.emit(f"✓ {os.path.basename(file_path)} → {os.path.basename(output_path)}", "success")
                success_count += 1
                
            except Exception as e:
                import traceback
                self.log.emit(f"✗ {os.path.basename(file_path)}: {str(e)}", "error")
                self.log.emit(f"  Traceback: {traceback.format_exc()}", "error")
                error_count += 1
            
            progress = int((i + 1) / total * 100)
            self.progress.emit(progress, f"Processing {i + 1}/{total}...")
        
        self.finished.emit(success_count, error_count)
    
    def _save_exr(self, pixels, output_path):
        """Save as EXR using OpenImageIO if available, otherwise fallback to TIFF."""
        try:
            import OpenImageIO as oiio
            height, width, channels = pixels.shape
            spec = oiio.ImageSpec(width, height, channels, oiio.FLOAT)
            out = oiio.ImageOutput.create(output_path)
            out.open(output_path, spec)
            out.write_image(pixels)
            out.close()
        except ImportError:
            # Fallback: save as 32-bit TIFF (PIL can handle this with 'F' mode per channel)
            # Or save as 8-bit TIFF when OpenImageIO is not available
            alt_path = output_path.replace('.exr', '.tiff')
            
            # Convert to 8-bit for PIL compatibility (loses HDR data but works)
            pixels_8bit = np.clip(pixels * 255, 0, 255).astype(np.uint8)
            img = Image.fromarray(pixels_8bit, mode='RGB')
            img.save(alt_path, format='TIFF')
            self.log.emit(f"  (Saved as 8-bit TIFF - install OpenImageIO for EXR/HDR support)", "warning")


class ACESConverterWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.files = []
        self.worker = None
        self.ocio_config_path = None
        
        self.setup_ui()
        self.load_ocio_config()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # === Header ===
        header = QLabel(f"🎨 {APP_NAME}")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setStyleSheet("color: #2196F3; margin-bottom: 5px;")
        layout.addWidget(header)
        
        subtitle = QLabel("Convert images from sRGB to ACEScg using OpenColorIO")
        subtitle.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(subtitle)
        
        # === OCIO Configuration ===
        ocio_group = QGroupBox("OCIO Configuration")
        ocio_layout = QHBoxLayout(ocio_group)
        
        self.ocio_path_edit = QLineEdit()
        self.ocio_path_edit.setPlaceholderText("Path to OCIO config.ocio file...")
        self.ocio_path_edit.setReadOnly(True)
        ocio_layout.addWidget(self.ocio_path_edit, 1)
        
        self.ocio_browse_btn = QPushButton("Browse...")
        self.ocio_browse_btn.clicked.connect(self.browse_ocio_config)
        ocio_layout.addWidget(self.ocio_browse_btn)
        
        self.ocio_status = QLabel()
        ocio_layout.addWidget(self.ocio_status)
        
        layout.addWidget(ocio_group)
        
        # === Source Files ===
        source_group = QGroupBox("Source Files")
        source_layout = QVBoxLayout(source_group)
        
        btn_row = QHBoxLayout()
        self.select_files_btn = QPushButton("📄 Select Files...")
        self.select_files_btn.clicked.connect(self.select_files)
        btn_row.addWidget(self.select_files_btn)
        
        self.select_folder_btn = QPushButton("📁 Select Folder...")
        self.select_folder_btn.clicked.connect(self.select_folder)
        btn_row.addWidget(self.select_folder_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_files)
        btn_row.addWidget(self.clear_btn)
        
        btn_row.addStretch()
        source_layout.addLayout(btn_row)
        
        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(100)
        self.file_list.setMaximumHeight(150)
        source_layout.addWidget(self.file_list)
        
        self.file_count_label = QLabel("No files selected")
        self.file_count_label.setStyleSheet("color: #666;")
        source_layout.addWidget(self.file_count_label)
        
        layout.addWidget(source_group)
        
        # === Conversion Settings ===
        settings_group = QGroupBox("Conversion Settings")
        settings_layout = QVBoxLayout(settings_group)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Input Color Space:"))
        self.input_cs_combo = QComboBox()
        self.input_cs_combo.setMinimumWidth(200)
        row1.addWidget(self.input_cs_combo)
        row1.addStretch()
        settings_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Output Color Space:"))
        self.output_cs_combo = QComboBox()
        self.output_cs_combo.setMinimumWidth(200)
        row2.addWidget(self.output_cs_combo)
        row2.addStretch()
        settings_layout.addLayout(row2)
        
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Output Format:"))
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["EXR", "TIFF", "PNG"])
        self.output_format_combo.setMinimumWidth(100)
        row3.addWidget(self.output_format_combo)
        row3.addStretch()
        settings_layout.addLayout(row3)
        
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Output Folder:"))
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("Same as source (or select folder)")
        row4.addWidget(self.output_folder_edit, 1)
        self.output_folder_btn = QPushButton("Browse...")
        self.output_folder_btn.clicked.connect(self.browse_output_folder)
        row4.addWidget(self.output_folder_btn)
        settings_layout.addLayout(row4)
        
        layout.addWidget(settings_group)
        
        # === Progress ===
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("Ready")
        self.progress_label.setStyleSheet("color: #666;")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # === Log ===
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setMinimumHeight(120)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # === Action Buttons ===
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.convert_btn = QPushButton("🚀 Convert")
        self.convert_btn.setMinimumWidth(120)
        self.convert_btn.setMinimumHeight(35)
        self.convert_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.convert_btn.clicked.connect(self.start_conversion)
        btn_layout.addWidget(self.convert_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumWidth(80)
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QComboBox, QListWidget, QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #444;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px 15px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
        """)
    
    def load_ocio_config(self):
        """Load OCIO config from environment variable or prompt user."""
        ocio_env = os.environ.get('OCIO')
        
        if ocio_env and os.path.exists(ocio_env):
            self.set_ocio_config(ocio_env)
            self.log_message(f"Loaded OCIO config from environment: {ocio_env}", "info")
        else:
            # Show dialog prompting user to select config
            QMessageBox.warning(
                self,
                "OCIO Config Not Found",
                "No OCIO configuration file found in environment variable.\n\n"
                "Please select your ACES config.ocio file to continue."
            )
            self.browse_ocio_config()
    
    def browse_ocio_config(self):
        """Browse for OCIO config file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OCIO Config File",
            "",
            "OCIO Config (*.ocio);;All Files (*)"
        )
        if file_path:
            self.set_ocio_config(file_path)
    
    def set_ocio_config(self, config_path):
        """Set and validate OCIO config."""
        self.ocio_config_path = config_path
        self.ocio_path_edit.setText(config_path)
        
        if not OCIO_AVAILABLE:
            self.ocio_status.setText("⚠️ OCIO not installed")
            self.ocio_status.setStyleSheet("color: #ff9800;")
            return
        
        try:
            config = OCIO.Config.CreateFromFile(config_path)
            self.ocio_status.setText("✓ Valid")
            self.ocio_status.setStyleSheet("color: #4CAF50;")
            
            # Populate color space dropdowns
            self.input_cs_combo.clear()
            self.output_cs_combo.clear()
            
            # OCIO 2.x uses getColorSpaces() which returns an iterator
            color_spaces = [cs.getName() for cs in config.getColorSpaces()]
            self.input_cs_combo.addItems(color_spaces)
            self.output_cs_combo.addItems(color_spaces)
            
            # Try to find and select appropriate defaults
            for i, cs in enumerate(color_spaces):
                cs_lower = cs.lower()
                if 'srgb' in cs_lower and 'texture' in cs_lower:
                    self.input_cs_combo.setCurrentIndex(i)
                elif 'acescg' in cs_lower:
                    self.output_cs_combo.setCurrentIndex(i)
            
            self.log_message(f"Loaded {len(color_spaces)} color spaces from config", "success")
            
        except Exception as e:
            self.ocio_status.setText("✗ Invalid")
            self.ocio_status.setStyleSheet("color: #f44336;")
            self.log_message(f"Error loading OCIO config: {e}", "error")
    
    def select_files(self):
        """Select individual image files."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",
            "Images (*.jpg *.jpeg *.png *.tif *.tiff *.exr *.bmp);;All Files (*)"
        )
        if files:
            self.add_files(files)
    
    def select_folder(self):
        """Select a folder and add only COLOR/DIFFUSE textures (not technical textures)."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            files = []
            skipped = 0
            for f in os.listdir(folder):
                # Check if it's a supported image extension
                if any(f.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
                    # Only include color/diffuse textures, skip technical textures
                    if is_color_texture(f):
                        files.append(os.path.join(folder, f))
                    else:
                        skipped += 1
            
            if files:
                self.add_files(files)
                if skipped > 0:
                    self.log_message(f"Added {len(files)} color texture(s), skipped {skipped} technical texture(s)", "info")
            else:
                QMessageBox.information(
                    self, "No Color Textures",
                    f"No diffuse/albedo/color textures found in folder.\n\n"
                    f"Skipped {skipped} technical texture(s) (normal, roughness, etc.).\n\n"
                    f"Use 'Select Files' to manually choose specific files."
                )
    
    def add_files(self, files):
        """Add files to the list."""
        for f in files:
            if f not in self.files:
                self.files.append(f)
                item = QListWidgetItem(os.path.basename(f))
                item.setToolTip(f)
                self.file_list.addItem(item)
        
        self.file_count_label.setText(f"{len(self.files)} file(s) selected")
    
    def clear_files(self):
        """Clear all selected files."""
        self.files.clear()
        self.file_list.clear()
        self.file_count_label.setText("No files selected")
    
    def browse_output_folder(self):
        """Browse for output folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder_edit.setText(folder)
    
    def log_message(self, message, level="info"):
        """Add message to log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "info": "#e0e0e0",
            "success": "#4CAF50",
            "warning": "#ff9800",
            "error": "#f44336"
        }
        color = colors.get(level, "#e0e0e0")
        
        self.log_text.append(f'<span style="color:#888">[{timestamp}]</span> '
                            f'<span style="color:{color}">{message}</span>')
    
    def start_conversion(self):
        """Start the conversion process."""
        if not self.files:
            QMessageBox.warning(self, "No Files", "Please select files to convert.")
            return
        
        if not self.ocio_config_path:
            QMessageBox.warning(self, "No OCIO Config", "Please select an OCIO configuration file.")
            return
        
        # Determine output folder
        output_folder = self.output_folder_edit.text().strip()
        if not output_folder:
            output_folder = os.path.dirname(self.files[0])
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Disable UI during conversion
        self.convert_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Start worker thread
        self.worker = ConversionWorker(
            files=self.files.copy(),
            ocio_config_path=self.ocio_config_path,
            input_cs=self.input_cs_combo.currentText(),
            output_cs=self.output_cs_combo.currentText(),
            output_format=self.output_format_combo.currentText(),
            output_folder=output_folder
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.log_message)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
        self.log_message("Starting conversion...", "info")
    
    def on_progress(self, percent, message):
        """Update progress bar."""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)
    
    def on_finished(self, success, errors):
        """Handle conversion completion."""
        self.convert_btn.setEnabled(True)
        self.progress_label.setText("Done")
        
        if errors == 0:
            self.log_message(f"✓ Conversion complete! {success} file(s) converted successfully.", "success")
        else:
            self.log_message(f"Conversion finished. {success} succeeded, {errors} failed.", "warning")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ACESConverterWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
