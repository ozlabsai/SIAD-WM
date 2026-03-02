"""SIAD World Model Components

Per MODEL.md v0.2 - JEPA-centered token-based world model

Exports:
    - WorldModel: Main JEPA world model (from wm.py)
    - ContextEncoder: Context encoder f_θ (from encoder.py)
    - TargetEncoderEMA: Target encoder f_θ̄ with EMA (from encoder.py)
    - ActionEncoder: Action encoder h_φ (from actions.py)
    - TransitionModel: Transition model F_ψ (from transition.py)
    - create_world_model_from_config: Factory function for config-driven instantiation

Legacy components (deprecated, use for backward compatibility only):
    - Available in siad.model.legacy.*
"""

# New MODEL.md v0.2 compliant implementation
from .wm import WorldModel, create_world_model_from_config
from .encoder import ContextEncoder, TargetEncoderEMA
from .actions import ActionEncoder
from .transition import TransitionModel

# HuggingFace-compatible wrapper
from .hf_model import SIADWorldModel, SIADConfig, WorldModelOutput

__all__ = [
    "WorldModel",
    "create_world_model_from_config",
    "ContextEncoder",
    "TargetEncoderEMA",
    "ActionEncoder",
    "TransitionModel",
    "SIADWorldModel",
    "SIADConfig",
    "WorldModelOutput",
]
