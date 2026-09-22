"""Config schema and loader.

See `rimtrans.config.schema.RimTransConfig` for the schema and
`rimtrans.config.loader.load_config` for the entry point.
"""

from rimtrans.config.loader import load_config
from rimtrans.config.schema import (
    GlossaryConfig,
    ProviderConfig,
    ProviderKind,
    RimTransConfig,
    RouterPolicyConfig,
    SemanticTypeOverride,
    TranslationMemoryConfig,
)

__all__ = [
    "GlossaryConfig",
    "ProviderConfig",
    "ProviderKind",
    "RimTransConfig",
    "RouterPolicyConfig",
    "SemanticTypeOverride",
    "TranslationMemoryConfig",
    "load_config",
]
