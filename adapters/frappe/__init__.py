"""Frappe ERPNext Cognitia Adapter Package.

Provides event translation, lifecycle experience aggregation,
human rule management, and read-only cognitive advisory presentation for Frappe.
"""

from __future__ import annotations

from adapters.frappe.advisory import FrappeAdvisory
from adapters.frappe.client import FrappeCognitiaAdapter
from adapters.frappe.events import FrappeEvent, FrappeEventType
from adapters.frappe.experience import ERPLifecycleType, FrappeExperienceBuilder
from adapters.frappe.translator import FrappeEventTranslator

__all__ = [
    "ERPLifecycleType",
    "FrappeAdvisory",
    "FrappeCognitiaAdapter",
    "FrappeEvent",
    "FrappeEventType",
    "FrappeExperienceBuilder",
    "FrappeEventTranslator",
]
