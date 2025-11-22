# gui/widgets/Config.py (Refined Design)
import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QTextEdit, QPushButton, QListWidget,
                             QListWidgetItem, QSplitter, QMessageBox,
                             QSizePolicy, QScrollArea, QGridLayout, QDialog,
                             QDialogButtonBox, QFrame, QSpacerItem) # Added QSpacerItem
from PyQt5.QtGui import QPainter, QFontMetrics, QIcon, QFont # Added QFont
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent, QPropertyAnimation, QEasingCurve, QRect # Added Animation classes
import os

from .colors import get_theme_manager

# --- Custom Dialog for Saving Preset (Minor style consistency check) ---
class SavePresetDialog(QDialog):
    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.theme_manager = theme_manager or get_theme_manager()
        self.setWindowTitle("Save Preset")
        self.setModal(True)
        # Set a default font consistent with the app
        self.setFont(QFont("Roboto", 10))

        layout = QVBoxLayout(self)
        layout.setSpacing(12) # Slightly more spacing
        layout.setContentsMargins(20, 20, 20, 20) # More padding

        self.title_label = QLabel("Preset Title:")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Enter preset title (required)")

        self.desc_label = QLabel("Description (Optional):")
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Enter optional description")
        self.desc_input.setFixedHeight(80)
        self.desc_input.setAcceptRichText(False) # Ensure plain text

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        # Ensure Save button is initially disabled if title is empty
        self.button_box.button(QDialogButtonBox.Save).setEnabled(False)
        self.title_input.textChanged.connect(lambda text: self.button_box.button(QDialogButtonBox.Save).setEnabled(bool(text.strip())))


        layout.addWidget(self.title_label)
        layout.addWidget(self.title_input)
        layout.addWidget(self.desc_label)
        layout.addWidget(self.desc_input)
        layout.addSpacing(10) # Add space before buttons
        layout.addWidget(self.button_box)

        self.update_styles()

    def update_styles(self):
        bg_color = self.theme_manager.get_color('BACKGROUND_LIGHT').name()
        text_color = self.theme_manager.get_color('TEXT').name()
        border_color = self.theme_manager.get_color('BORDER').name()
        input_bg = self.theme_manager.get_color('INPUT_BACKGROUND').name()
        button_bg = self.theme_manager.get_color('PRIMARY').name()
        button_text = self.theme_manager.get_color('TEXT_ON_PRIMARY').name()
        text_disabled_color = self.theme_manager.get_color('TEXT_DISABLED').name()
        primary_light = self.theme_manager.get_color('PRIMARY_LIGHT').name()
        primary_dark = self.theme_manager.get_color('PRIMARY_DARK').name()
        bg_dark = self.theme_manager.get_color('BACKGROUND_DARK').name()

        self.setStyleSheet(f"QDialog {{ background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 5px; }}")

        label_style = f"color: {text_color}; font-family: Roboto; font-size: 13px; font-weight: bold;"
        self.title_label.setStyleSheet(label_style + " background: transparent;") # Ensure transparent bg
        self.desc_label.setStyleSheet(label_style + " background: transparent;")

        input_style = f"""
            background-color: {input_bg};
            color: {text_color};
            border: 1px solid {border_color};
            border-radius: 4px;
            padding: 6px; /* Slightly more padding */
            font-family: Roboto;
            font-size: 13px;
        """
        self.title_input.setStyleSheet(input_style)
        self.desc_input.setStyleSheet(input_style)

        button_style = f"""
            QPushButton {{
                background-color: {button_bg};
                color: {button_text};
                border: none;
                border-radius: 4px;
                padding: 8px 20px; /* More horizontal padding */
                font-family: Roboto;
                font-size: 13px;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{ background-color: {primary_light}; }}
            QPushButton:pressed {{ background-color: {primary_dark}; }}
            QPushButton:disabled {{ background-color: {bg_dark}; color: {text_disabled_color}; }}
        """
        # Style Save button
        save_button = self.button_box.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setStyleSheet(button_style)
            save_button.setCursor(Qt.PointingHandCursor)

        # Style Cancel button (make it less prominent)
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        if cancel_button:
            cancel_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_dark}; /* Different background */
                    color: {text_disabled_color};
                    border: 1px solid {border_color}; /* Add border */
                    border-radius: 4px;
                    padding: 8px 20px;
                    font-family: Roboto;
                    font-size: 13px;
                    font-weight: bold;
                    min-width: 80px;
                }}
                QPushButton:hover {{ background-color: {border_color}; color: {text_color}; }}
                QPushButton:pressed {{ background-color: {bg_dark}; }}
            """)
            cancel_button.setCursor(Qt.PointingHandCursor)


    def get_details(self):
        return self.title_input.text().strip(), self.desc_input.toPlainText().strip()

# --- Widget for each Preset in the Grid (Refined Design) ---
class PresetItemWidget(QFrame):
    apply_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, title, description, parent=None, theme_manager=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.theme_manager = theme_manager or get_theme_manager()
        # self._hovering = False # No longer needed for stylesheet hover

        # Basic frame setup - styling done via stylesheet
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumHeight(110) # Slightly taller
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # --- Animation Setup ---
        self.expand_animation = QPropertyAnimation(self, b"geometry")
        self.expand_animation.setDuration(150) # ms
        self.expand_animation.setEasingCurve(QEasingCurve.InOutQuad)

        self.shrink_animation = QPropertyAnimation(self, b"geometry")
        self.shrink_animation.setDuration(150) # ms
        self.shrink_animation.setEasingCurve(QEasingCurve.InOutQuad) # Corrected indentation

        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8) # More spacing
        layout.setContentsMargins(15, 12, 15, 12) # More padding

        # Top part: Title and Delete button
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0,0,0,0)
        top_layout.setSpacing(10)

        self.title_label = QLabel(self.title)
        self.title_label.setObjectName("preset_title")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred) # Allow title to expand

        self.delete_button = QPushButton("✕") # Use multiplication sign
        self.delete_button.setObjectName("preset_delete_button")
        self.delete_button.setFixedSize(QSize(22, 22)) # Slightly smaller
        self.delete_button.setToolTip(f"Delete preset '{self.title}'")
        self.delete_button.clicked.connect(self._emit_delete)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setVisible(False) # Initially hidden, show on hover

        top_layout.addWidget(self.title_label, 1) # Give title stretch factor
        top_layout.addWidget(self.delete_button)

        # Middle part: Description
        fm = QFontMetrics(QFont("Roboto", 10)) # Use specific font size for calculation
        line_height = fm.lineSpacing()
        max_desc_height = line_height * 2 + 4 # Allow approx 2 lines
        # Replace newlines with spaces for better eliding
        desc_text = self.description.replace('\n', ' ')
        # Estimate width available for description (widget width - margins)
        available_width = self.width() - 30 if self.width() > 50 else 150 # Estimate or default
        elided_desc = fm.elidedText(desc_text, Qt.ElideRight, available_width)

        self.desc_label = QLabel(elided_desc if self.description else "No description")
        self.desc_label.setObjectName("preset_desc")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(max_desc_height)
        self.desc_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Bottom part: Apply button
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 5, 0, 0) # Add space above button
        # Center the button
        bottom_layout.addStretch(1)
        self.apply_button = QPushButton("Apply")
        self.apply_button.setObjectName("preset_apply_button")
        self.apply_button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed) # Allow button to stretch
        self.apply_button.setToolTip(f"Apply preset '{self.title}'")
        self.apply_button.clicked.connect(self._emit_apply)
        self.apply_button.setCursor(Qt.PointingHandCursor)

        bottom_layout.addWidget(self.apply_button)
        bottom_layout.addStretch(1) # Add stretch after button

        # Add elements to main layout
        layout.addLayout(top_layout)
        layout.addWidget(self.desc_label, 1) # Give description vertical stretch
        layout.addLayout(bottom_layout)

        self.update_styles()

    # --- Hover Event Handling for Animation ---
    def event(self, event):
        if event.type() == QEvent.HoverEnter:
            self.shrink_animation.stop() # Stop shrinking if currently running
            current_geo = self.geometry()
            target_geo = QRect(current_geo.x() - 1, current_geo.y() - 1,
                               current_geo.width() + 2, current_geo.height() + 2)
            self.expand_animation.setStartValue(current_geo)
            self.expand_animation.setEndValue(target_geo)
            self.expand_animation.start()
            self.delete_button.setVisible(True)
            return True
        elif event.type() == QEvent.HoverLeave:
            self.expand_animation.stop() # Stop expanding if currently running
            current_geo = self.geometry()
            # Calculate target based on the *original* size before expansion
            # This assumes the animation might be interrupted mid-way
            original_width = self.expand_animation.startValue().width() if self.expand_animation.state() == QPropertyAnimation.Running else self.shrink_animation.endValue().width() if self.shrink_animation.endValue() else self.width()
            original_height = self.expand_animation.startValue().height() if self.expand_animation.state() == QPropertyAnimation.Running else self.shrink_animation.endValue().height() if self.shrink_animation.endValue() else self.height()

            # If currently expanded (or partially), calculate shrink target
            if current_geo.width() > original_width or current_geo.height() > original_height:
                 target_geo = QRect(current_geo.x() + 1, current_geo.y() + 1,
                                    current_geo.width() - 2, current_geo.height() - 2)
                 # Ensure target doesn't go smaller than original if interrupted weirdly
                 target_geo.setWidth(max(original_width, target_geo.width()))
                 target_geo.setHeight(max(original_height, target_geo.height()))

                 self.shrink_animation.setStartValue(current_geo)
                 self.shrink_animation.setEndValue(target_geo)
                 self.shrink_animation.start()
            self.delete_button.setVisible(False)
            return True
        return super().event(event)

    def _emit_apply(self):
        self.apply_requested.emit(self.title)

    def _emit_delete(self):
         self.delete_requested.emit(self.title)

    def update_styles(self):
        """Applies theme styles to the preset item."""
        bg_color = self.theme_manager.get_color('INPUT_BACKGROUND').name()
        # bg_hover_color = self.theme_manager.get_color('BACKGROUND_LIGHT').name() # No background change on hover
        text_color = self.theme_manager.get_color('TEXT').name()
        text_disabled_color = self.theme_manager.get_color('TEXT_DISABLED').name()
        # border_color = self.theme_manager.get_color('BORDER').name() # Use primary for border
        # border_hover_color = self.theme_manager.get_color('PRIMARY_LIGHT').name() # Use primary for border
        primary_color = self.theme_manager.get_color('PRIMARY').name()
        primary_light = self.theme_manager.get_color('PRIMARY_LIGHT').name()
        primary_dark = self.theme_manager.get_color('PRIMARY_DARK').name()
        text_on_primary = self.theme_manager.get_color('TEXT_ON_PRIMARY').name()
        delete_button_bg = self.theme_manager.get_color('BACKGROUND_DARK').name()
        delete_button_hover_bg = self.theme_manager.get_color('BORDER').name() # Use border color for delete hover bg

        # Use consistent background and border width, animation handles expansion
        current_bg = bg_color # Corrected indentation
        current_border_color = primary_color
        current_border_width = "1px" # Always 1px, animation changes geometry

        # Frame style - No hover effects here anymore
        self.setStyleSheet(f"""
            PresetItemWidget {{
                background-color: {current_bg};
                border: {current_border_width} solid {current_border_color};
                border-radius: 6px; /* Slightly more rounded */
                /* No margin needed, geometry animation handles positioning */
            }}
        """)

        # Title style
        self.title_label.setStyleSheet(f"""
            color: {text_color};
            font-family: Roboto;
            font-size: 16px; /* Larger title */
            font-weight: bold;
            border: none;
            background: transparent;
        """)

        # Description style
        self.desc_label.setStyleSheet(f"""
            color: {text_disabled_color};
            font-family: Roboto;
            font-size: 12px;
            border: none;
            background: transparent;
            padding-top: 0px; /* Reduced padding */
            line-height: 1.3; /* Adjust line height if needed */
        """)

        # Apply button style
        self.apply_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {primary_color};
                color: {text_on_primary};
                border: none;
                border-radius: 4px;
                padding: 6px 12px; /* Adjusted padding */
                font-family: Roboto;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {primary_light}; }}
            QPushButton:pressed {{ background-color: {primary_dark}; }}
        """)

        # Delete button style (subtle)
        self.delete_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; /* Make transparent */
                color: {text_disabled_color};
                border: none; /* No border */
                border-radius: 11px; /* Round */
                padding: 0px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {delete_button_hover_bg};
                color: {text_color};
            }}
            QPushButton:pressed {{ background-color: {primary_dark}; }}
        """)


# --- Main Config Widget (Refined Design) ---
class ConfigWidget(QWidget):
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.theme_manager = get_theme_manager()
        if not config_manager:
            raise ValueError("ConfigManager instance is required.")
        self.config_manager = config_manager
        self.setVisible(False)
        self.move(86, 7)
        self.resize(607, 426)

        self.grid_widgets = {}

        self.setup_ui()
        self.setup_connections()
        self._populate_preset_grid()
        self._update_styles()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(18) # More spacing

        # Top Row: Title and Add Button
        top_layout = QHBoxLayout()
        self.title_label = QLabel("Config Presets")
        self.title_label.setObjectName("config_widget_title")

        self.add_button = QPushButton("+")
        self.add_button.setObjectName("add_preset_button")
        self.add_button.setToolTip("Save current configuration as a new preset")
        self.add_button.setFixedSize(QSize(32, 32)) # Slightly larger
        self.add_button.setCursor(Qt.PointingHandCursor)

        top_layout.addWidget(self.title_label)
        top_layout.addStretch()
        top_layout.addWidget(self.add_button)
        self.main_layout.addLayout(top_layout)

        # --- Scroll Area for Preset Grid ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("preset_scroll_area")
        # Remove default frame/border from scroll area itself
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(18) # More spacing between items
        self.grid_layout.setContentsMargins(5, 5, 10, 5) # Adjust padding (more right for scrollbar)

        self.scroll_area.setWidget(self.grid_container)
        self.main_layout.addWidget(self.scroll_area, 1)

    def setup_connections(self):
        self.theme_manager.themeChanged.connect(self._update_styles)
        self.add_button.clicked.connect(self._show_save_dialog)

    def _clear_grid(self):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item is None: continue # Skip if item is already gone

            widget = item.widget()
            spacer = item.spacerItem()

            if widget is not None:
                try:
                    widget.apply_requested.disconnect()
                    widget.delete_requested.disconnect()
                except (TypeError, RuntimeError): pass # Ignore if already disconnected or deleted
                except Exception as e: print(f"Error disconnecting signals: {e}")
                widget.deleteLater()
            elif spacer is not None:
                 # Remove spacer items explicitly
                 self.grid_layout.removeItem(spacer)

        self.grid_widgets.clear()


    def _populate_preset_grid(self):
        self._clear_grid()
        presets = self.config_manager.get_presets()
        sorted_titles = sorted(presets.keys())

        # Remove existing "no presets" label if present
        no_presets_label = self.grid_container.findChild(QLabel, "no_presets_label")
        if no_presets_label:
            no_presets_label.deleteLater()

        if not sorted_titles:
            no_presets_label = QLabel("No presets saved yet. Click '+' to save the current config.")
            no_presets_label.setAlignment(Qt.AlignCenter)
            no_presets_label.setObjectName("no_presets_label")
            self.grid_layout.addWidget(no_presets_label, 0, 0, 1, 2) # Span 2 columns
            text_disabled_color = self.theme_manager.get_color('TEXT_DISABLED').name()
            no_presets_label.setStyleSheet(f"color: {text_disabled_color}; font-style: italic; padding: 30px; background: transparent;")
            # Add stretchers to keep the label centered when grid is empty
            self.grid_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding), 1, 0, 1, 2) # Span columns
            self.grid_layout.addItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 2) # Add column spacer


        else:
            num_columns = 2
            row, col = 0, 0
            for title in sorted_titles:
                preset_data = presets[title]
                item_widget = PresetItemWidget(title, preset_data.get("description", ""),
                                               theme_manager=self.theme_manager)
                item_widget.apply_requested.connect(self._apply_selected_preset)
                item_widget.delete_requested.connect(self._delete_selected_preset)
                self.grid_layout.addWidget(item_widget, row, col)
                self.grid_widgets[title] = item_widget
                col += 1
                if col >= num_columns:
                    col = 0
                    row += 1

            # Add stretchers AFTER the items
            self.grid_layout.setRowStretch(row + 1, 1) # Stretch below last row
            self.grid_layout.setColumnStretch(num_columns, 1) # Stretch right of last column

        self._update_styles()

    def _show_save_dialog(self):
        dialog = SavePresetDialog(self, self.theme_manager)
        if dialog.exec_() == QDialog.Accepted:
            title, description = dialog.get_details()
            if not title:
                QMessageBox.warning(self, "Missing Title", "Preset title cannot be empty.")
                return
            if title in self.config_manager.get_presets():
                reply = QMessageBox.question(self, "Confirm Overwrite",
                                             f"A preset named '{title}' already exists. Overwrite it?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No: return
            success = self.config_manager.save_preset(title, description)
            if success:
                QMessageBox.information(self, "Preset Saved", f"Preset '{title}' saved successfully.")
                self._populate_preset_grid()
            else:
                QMessageBox.critical(self, "Error Saving", "Could not save the preset.")

    def _apply_selected_preset(self, title: str):
        reply = QMessageBox.question(self, "Confirm Apply",
                                     f"Apply preset '{title}'? This will overwrite your current settings.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        success = self.config_manager.apply_preset(title)
        if success:
            QMessageBox.information(self, "Preset Applied", f"Preset '{title}' applied successfully.\nUI elements will update.")
        else:
            QMessageBox.critical(self, "Error Applying", f"Could not apply preset '{title}'.")

    def _delete_selected_preset(self, title: str):
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete the preset '{title}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success = self.config_manager.delete_preset(title)
            if success:
                QMessageBox.information(self, "Preset Deleted", f"Preset '{title}' deleted.")
                self._populate_preset_grid()
            else:
                QMessageBox.critical(self, "Error Deleting", f"Could not delete preset '{title}'.")

    def _update_title_style(self):
        if hasattr(self, 'title_label'):
            self.title_label.setStyleSheet(f"""
                color: {self.theme_manager.get_color('TEXT').name()};
                font-family: Roboto;
                font-size: 22px; /* Slightly smaller main title */
                font-weight: bold;
                background: transparent;
            """)

    def _update_styles(self):
        print("ConfigWidget updating styles (Refined Design)...")
        bg_color = self.theme_manager.get_color('BACKGROUND_LIGHT').name()
        scroll_bg_color = self.theme_manager.get_color('BACKGROUND').name() # Use main bg for scroll area content
        text_color = self.theme_manager.get_color('TEXT').name()
        text_disabled_color = self.theme_manager.get_color('TEXT_DISABLED').name()
        border_color = self.theme_manager.get_color('BORDER').name()
        primary_color = self.theme_manager.get_color('PRIMARY').name()
        primary_light = self.theme_manager.get_color('PRIMARY_LIGHT').name()
        primary_dark = self.theme_manager.get_color('PRIMARY_DARK').name()
        text_on_primary = self.theme_manager.get_color('TEXT_ON_PRIMARY').name()

        # Update main title
        self._update_title_style()

        # Update Add button style
        if hasattr(self, 'add_button'):
            self.add_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {primary_color};
                    color: {text_on_primary};
                    border: none;
                    border-radius: 16px; /* Fully round */
                    font-family: Roboto;
                    font-size: 20px; /* Larger '+' sign */
                    font-weight: bold;
                    padding-bottom: 2px; /* Adjust '+' position */
                }}
                QPushButton:hover {{ background-color: {primary_light}; }}
                QPushButton:pressed {{ background-color: {primary_dark}; }}
            """)

        # Update scroll area and container background
        if hasattr(self, 'scroll_area'):
            # Use transparent background for scroll area itself
            self.scroll_area.setStyleSheet(f"""
                QScrollArea {{ background-color: transparent; border: none; }}
            """)
            # Style scrollbars
            scrollbar_style = f"""
                QScrollBar:vertical {{
                    border: none;
                    background: transparent; /* Make scrollbar track transparent */
                    width: 8px; /* Thinner scrollbar */
                    margin: 0px 0px 0px 0px;
                }}
                QScrollBar::handle:vertical {{
                    background: {border_color}; /* Handle color */
                    min-height: 25px;
                    border-radius: 4px; /* Rounded handle */
                }}
                 QScrollBar::handle:vertical:hover {{
                    background: {primary_light}; /* Handle hover color */
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    border: none; background: none; height: 0px;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
            """
            self.scroll_area.verticalScrollBar().setStyleSheet(scrollbar_style)

        if hasattr(self, 'grid_container'):
             # Ensure container background is transparent to show main widget bg
             self.grid_container.setStyleSheet(f"background-color: transparent; border: none;")

        # Update style of the "No presets" label if it exists
        no_presets_label = self.grid_container.findChild(QLabel, "no_presets_label")
        if no_presets_label:
             no_presets_label.setStyleSheet(f"color: {text_disabled_color}; font-style: italic; padding: 30px; background: transparent;")

        # Update styles of existing preset items in the grid
        for item_widget in self.grid_widgets.values():
            if hasattr(item_widget, 'update_styles'):
                item_widget.update_styles()

        self.update()

    def paintEvent(self, event):
        # Base class handles painting based on stylesheets
        super().paintEvent(event)
