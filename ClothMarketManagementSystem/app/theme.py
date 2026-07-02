"""
Color palette for the whole application.

Kept in one file so the look of the app can be changed from a single
place instead of editing every panel.
"""

NAVY = "#0B1C2C"     # main window background
SIDEBAR = "#0F2233"  # sidebar background
CARD = "#132940"     # card / table background
PANEL = "#0E2030"    # secondary panel background
ACCENT = "#1A6FA3"   # primary blue accent
HOVER = "#155882"    # hover state for accent buttons
LIGHT = "#AED6F1"    # light text, labels
WHITE = "#F0F4F8"    # main text color
GRAY = "#6B8BA4"     # muted / secondary text
SUCCESS = "#1A7A45"  # green - confirm / add actions
DANGER = "#A93226"   # red - delete / warnings
GOLD = "#C9A227"     # gold - money / revenue figures
TEAL = "#148F77"     # teal - suppliers
PURPLE = "#6C3483"   # purple - shops

# Extra colors reserved for chart series on the dashboard.
CHART_COLORS = [ACCENT, GOLD, TEAL, PURPLE, DANGER, SUCCESS]
