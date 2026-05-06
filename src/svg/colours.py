"""Shared colour mapping used by the UI, animator and video producer.

Keep a canonical mapping of human-facing names to hex values here so
the preview and exported video use the same colours.
"""
COLOUR_MODE_MAP = {
    # UI-facing names (existing UI uses Red/Green/Cyan/White)
    "Red": "#FF0000",
    "Green": "#00FF00",
    "Cyan": "#00FFFF",
    "White": "#FFFFFF",
    # keep older names for backwards compatibility
    "Blue": "#00B7FF",
    "Purple": "#BB86FC",
    "Grayscale": "#D0D0D0",
}


def resolve_colour(colour_mode):
    return COLOUR_MODE_MAP.get(colour_mode, COLOUR_MODE_MAP["Blue"])
