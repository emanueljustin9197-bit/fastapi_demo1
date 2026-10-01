"""Compatibility import for the notification model.

``NotificationSetting`` is defined together with ``User`` so the one-to-one
relationship is configured exactly once. This module remains available for
older imports without registering a duplicate table.
"""

from .user import NotificationSetting

__all__ = ["NotificationSetting"]
