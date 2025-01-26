from PyQt5.QtGui import QColor


class Colors:
    # Base theme colors
    BACKGROUND = QColor("#1A1B26")
    PRIMARY = QColor("#7AA2F7")
    SECONDARY = QColor("#414868")
    ACCENT = QColor("#BB9AF7")
    TEXT = QColor("#C0CAF5")
    ERROR = QColor("#F7768E")

    # UI Region colors
    SIDEBAR_BACKGROUND = QColor("#0F141A")  # Previously RECTANGLE
    BACKGROUND_DARKER = QColor("#16171F")  # Used in background gradient
    PANEL_BACKGROUND = QColor("#0B0C12")  # Previously RECTANGLE_TRANSPARENT

    # Overlay and FPS display
    AIM_INDICATOR = QColor(255, 0, 0, 127)  # Previously OVERLAY_RED
    FPS_GRADIENT_START = QColor(122, 162, 247)  # Cool tone start
    FPS_GRADIENT_MIDDLE = QColor(187, 154, 247)  # Warm tone middle
    FPS_GRADIENT_END = QColor(122, 162, 247)  # Cool tone end

    # Button and UI effects
    BUTTON_SHADOW = QColor(0, 0, 0, 50)  # Used for hover effects
    UI_ELEMENT = QColor(255, 255, 255)  # Used for UI elements like snowflakes
    SNOWFLAKE = QColor(255, 255, 255)

    # Icon state unselected
    UNSELECTED_ELEMENT_1 = QColor("#414868")  # Matches SECONDARY for consistency
    UNSELECTED_ELEMENT_2 = QColor("#9F83D8")  # Slightly Darker than ACCENT

    SELECTED_ELEMENT_1 = QColor("#7AA2F7") # Matches PRIMARY for consistency
    SELECTED_ELEMENT_2 = QColor("#BB9AF7") # Matches ACCENT for consistency

    # Additional UI states
    HOVER_HIGHLIGHT = QColor("#545B89")  # Slightly lighter than SECONDARY
    ACTIVE_ELEMENT = QColor("#7AA2F7")  # Matches PRIMARY for consistency

    # Settings-specific colors
    SETTINGS_BACKGROUND = QColor("#0B0C12")
    SECTION_HEADER = QColor("#7AA2F7")
    SECTION_BORDER = QColor("#414868")
    INPUT_BACKGROUND = QColor("#16171F")
    INPUT_HIGHLIGHT = QColor("#2A2D3A")
    TOGGLE_ACTIVE = QColor("#73DACA")
    TOGGLE_INACTIVE = QColor("#545B89")
