"""Cognitia Dynamic Cognitive Documents.

Defines deterministic, provenance-aware document projections over canonical
Cognitia state. Documents are human-facing representations only; they never
become sources of truth, authority, or execution commands.
"""

from cognitia.documents.diff import (
    ChangeEntry,
    ChangeType,
    DocumentChange,
)
from cognitia.documents.intent import (
    DocumentIntent,
    IntentType,
)
from cognitia.documents.projection import (
    DeterministicDocumentProjection,
)
from cognitia.documents.provider import (
    DeterministicMockDocumentProvider,
    DynamicDocumentCapability,
)
from cognitia.documents.service import (
    DocumentService,
    InMemoryDocumentService,
)
from cognitia.documents.specification import (
    DocumentSpecification,
    SectionSpecification,
)
from cognitia.documents.types import (
    DocumentReference,
    DocumentSection,
    DocumentVersion,
    DynamicDocument,
    SectionContent,
    SectionType,
)
