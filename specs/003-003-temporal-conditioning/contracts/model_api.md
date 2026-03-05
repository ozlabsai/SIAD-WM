# Model API Contract

**Feature**: 003-temporal-conditioning | **Version**: v2

## Purpose

Define the contract for ActionEncoder and checkpoint loading with temporal features, ensuring backward compatibility when loading old checkpoints.

---

## Contract: ActionEncoder.\_\_init\_\_()

### Signature

```python
class ActionEncoder(nn.Module):
    def __init__(self, action_dim: int = 2, hidden_dim: int = 64, output_dim: int = 128):
        """Initialize action encoder.

        Args:
            action_dim: Input dimension (2 for v1, 4 for v2)
            hidden_dim: Hidden layer dimension (default 64)
            output_dim: Output embedding dimension (default 128)
        """
```

### Input Constraints

- **action_dim**: int ∈ {1, 2, 3, 4, ...} (typically 2 or 4)
- **hidden_dim**: int > 0 (typically 64)
- **output_dim**: int > 0 (typically 128)

### Output Guarantees

- **self.action_dim**: Stored for later reference
- **self.mlp**: Sequential with layers:
  - Linear(action_dim → hidden_dim)
  - SiLU()
  - Linear(hidden_dim → output_dim)
  - SiLU()

### Architecture Invariant

**No capacity change required** for action_dim ∈ {2, 4}:
```python
# V1: Linear(2→64) has 128 params
# V2: Linear(4→64) has 256 params
# Difference: 128 params (~0.0001% of 100M total model params)
# → Negligible, no need to increase hidden_dim
```

---

## Contract: ActionEncoder.forward()

### Signature

```python
def forward(self, a: torch.Tensor) -> torch.Tensor:
    """Encode action vector to latent space.

    Args:
        a: [B, A] action vector where A=action_dim

    Returns:
        u: [B, 128] action embedding
    """
```

### Input Constraints

- **a.shape**: [B, A] where A = self.action_dim
- **a.dtype**: torch.float32
- **a.device**: Must match model device

### Output Guarantees

- **u.shape**: [B, 128]
- **u.dtype**: torch.float32
- **u.device**: Same as input

### Behavior

```python
u = self.mlp(a)  # [B, A] → [B, 128]
return u
```

### Error Conditions

- **RuntimeError**: Shape mismatch if a.shape[1] != self.action_dim
- **TypeError**: Non-tensor input

### Example

```python
encoder = ActionEncoder(action_dim=4)  # V2: temporal features

# V2 batch
a_v2 = torch.randn(8, 4)  # [rain_anom, temp_anom, month_sin, month_cos]
u = encoder(a_v2)
assert u.shape == (8, 128)

# V1 batch (would fail if encoder initialized with action_dim=4)
a_v1 = torch.randn(8, 2)  # [rain_anom, temp_anom]
# u = encoder(a_v1)  # RuntimeError: Expected 4 dims, got 2
```

---

## Contract: WorldModel.load_state_dict()

### Purpose

Load checkpoint with automatic dimension padding for backward compatibility.

### Signature

```python
def load_state_dict(
    self,
    state_dict: dict,
    strict: bool = False,
    verbose: bool = True
) -> None:
    """Load model state with automatic action dimension upgrade.

    Args:
        state_dict: Checkpoint state dictionary
        strict: If True, require exact key match (default False for compat)
        verbose: If True, log dimension upgrade (default True)
    """
```

### Input Constraints

- **state_dict**: dict with model parameter tensors
- **strict**: bool (recommend False for backward compat)
- **verbose**: bool

### Behavior

#### Case 1: Dimension Match

```python
# Checkpoint action_dim == model action_dim
checkpoint_action_dim = state_dict['action_encoder.mlp.0.weight'].shape[1]
current_action_dim = self.action_encoder.action_dim

if checkpoint_action_dim == current_action_dim:
    # Standard loading
    super().load_state_dict(state_dict, strict=strict)
    return
```

#### Case 2: Dimension Upgrade (Checkpoint < Model)

```python
# Checkpoint action_dim=2, model action_dim=4
if checkpoint_action_dim < current_action_dim:
    # Pad Linear(2→64) to Linear(4→64)
    old_weight = state_dict['action_encoder.mlp.0.weight']  # [64, 2]
    new_weight = torch.zeros(64, current_action_dim)
    new_weight[:, :checkpoint_action_dim] = old_weight
    # new_weight[:, checkpoint_action_dim:] initialized to zero

    state_dict['action_encoder.mlp.0.weight'] = new_weight

    # Also pad bias if needed (no padding needed, bias is [64])

    if verbose:
        print(f"[ActionEncoder] Upgraded checkpoint: "
              f"{checkpoint_action_dim}→{current_action_dim} dims "
              f"(temporal features zero-initialized)")

    super().load_state_dict(state_dict, strict=strict)
    return
```

#### Case 3: Dimension Downgrade (Checkpoint > Model)

**NOT SUPPORTED** - raises error:
```python
if checkpoint_action_dim > current_action_dim:
    raise ValueError(
        f"Cannot load checkpoint with action_dim={checkpoint_action_dim} "
        f"into model with action_dim={current_action_dim}. "
        f"Upgrade model to support temporal features."
    )
```

### Output Guarantees

**After successful load**:
- Model parameters match checkpoint (with zero-padding if upgraded)
- Model can perform inference immediately
- No gradient issues (zero-initialized weights will learn if trained)

### Invariants

1. **Weight shape**: After padding, Linear layer has shape [hidden_dim, current_action_dim]
2. **Zero-init for new dims**: New temporal feature weights are exactly 0.0
3. **Existing weights unchanged**: Weather anomaly weights [64, :2] match checkpoint

### Error Conditions

- **ValueError**: Checkpoint action_dim > model action_dim (downgrade not supported)
- **KeyError**: Missing required parameter in state_dict
- **RuntimeError**: Shape mismatch for non-padded parameters

---

## Contract: infer_action_dim_from_state_dict()

### Purpose

Helper function to detect action_dim from checkpoint without loading model.

### Signature

```python
def infer_action_dim_from_state_dict(state_dict: dict) -> int:
    """Infer action_dim from checkpoint weights.

    Args:
        state_dict: Checkpoint state dictionary

    Returns:
        action_dim: int (2 for v1, 4 for v2, etc.)
    """
```

### Behavior

```python
weight_key = 'action_encoder.mlp.0.weight'
if weight_key in state_dict:
    weight_shape = state_dict[weight_key].shape  # [hidden_dim, action_dim]
    action_dim = weight_shape[1]
    return action_dim
else:
    # Fallback: assume v1 if action encoder not found
    return 2
```

### Error Conditions

- **KeyError**: If weight_key format changes (unlikely, but defensible)
- **IndexError**: If weight tensor has unexpected ndim

---

## Backward Compatibility Guarantees

### Loading V1 Checkpoint in V2 Model

**Scenario**: User has old v1 checkpoint (action_dim=2), loads into v2 model (action_dim=4).

**Guarantee**: Checkpoint loads successfully, temporal features start from zero.

**Behavior**:
```python
model = WorldModel(action_dim=4)  # V2 model
checkpoint = torch.load('checkpoint_v1.pth')  # action_dim=2

model.load_state_dict(checkpoint, strict=False)
# [ActionEncoder] Upgraded checkpoint: 2→4 dims (temporal features zero-initialized)

# Model works immediately
a_v2 = torch.randn(8, 6, 4)  # [B, H, 4]
z_pred = model.rollout(z0, a_v2, H=6)  # No error
```

**Temporal feature behavior after loading**:
- Initial weights: `model.action_encoder.mlp[0].weight[:, 2:4] == 0`
- Initial bias: unchanged (applies to all input dims)
- First forward pass: Temporal features contribute zero to embedding (neutral)
- After training: Weights learn to use temporal features

### Loading V2 Checkpoint in V1 Model

**Scenario**: User accidentally tries to load v2 checkpoint (action_dim=4) in old v1 model (action_dim=2).

**Guarantee**: Fails with clear error message.

**Behavior**:
```python
model = WorldModel(action_dim=2)  # V1 model
checkpoint = torch.load('checkpoint_v2.pth')  # action_dim=4

model.load_state_dict(checkpoint, strict=False)
# ValueError: Cannot load checkpoint with action_dim=4 into model with action_dim=2.
# Upgrade model to support temporal features.
```

---

## Testing Contract

### Unit Tests Required

1. **test_action_encoder_init**: Verify mlp layers have correct shapes for action_dim ∈ {2, 4}
2. **test_action_encoder_forward_v1**: Forward pass with [B, 2] input
3. **test_action_encoder_forward_v2**: Forward pass with [B, 4] input
4. **test_checkpoint_dimension_match**: Load v2 checkpoint into v2 model (no padding)
5. **test_checkpoint_dimension_upgrade**: Load v1 checkpoint into v2 model (with padding)
6. **test_checkpoint_dimension_downgrade_error**: Verify error when loading v2 into v1
7. **test_infer_action_dim**: Verify correct action_dim inference from checkpoints

### Integration Tests Required

1. **test_v1_checkpoint_v2_data**: Load v1 checkpoint, train on v2 data, verify temporal weights learn
2. **test_zero_init_neutrality**: Verify zero-initialized temporal weights don't affect existing predictions
3. **test_full_upgrade_workflow**: V1 checkpoint → V2 model → V2 data → Training → Convergence

---

## Example Upgrade Workflow

```python
# Step 1: Load old v1 checkpoint into v2 model
model_v2 = WorldModel(action_dim=4)
checkpoint_v1 = torch.load('baseline_v1.pth')
model_v2.load_state_dict(checkpoint_v1, strict=False)
# [ActionEncoder] Upgraded checkpoint: 2→4 dims

# Step 2: Verify temporal weights are zero-initialized
temporal_weights = model_v2.action_encoder.mlp[0].weight[:, 2:4]
assert torch.allclose(temporal_weights, torch.zeros_like(temporal_weights))

# Step 3: Load v2 dataset with temporal features
dataset_v2 = SIADDataset('dataset_v2.h5')
batch = dataset_v2[0]
assert batch['actions_rollout'].shape == (6, 4)  # [H, A=4]

# Step 4: Train (temporal weights will learn)
optimizer = torch.optim.AdamW(model_v2.parameters(), lr=1e-4)
for epoch in range(10):
    loss, metrics = train_step(model_v2, batch, optimizer)
    print(f"Epoch {epoch}: loss={loss:.4f}")

# Step 5: Verify temporal weights are no longer zero (learning happened)
temporal_weights_trained = model_v2.action_encoder.mlp[0].weight[:, 2:4]
assert not torch.allclose(temporal_weights_trained, torch.zeros_like(temporal_weights_trained))
```

---

## Summary

**Key Contracts**:
1. `ActionEncoder.__init__()`: Configurable action_dim, default=2 for backward compat
2. `ActionEncoder.forward()`: Enforces input shape [B, action_dim]
3. `WorldModel.load_state_dict()`: Automatic dimension padding for v1→v2 upgrade
4. `infer_action_dim_from_state_dict()`: Helper to detect checkpoint version

**Backward Compatibility**: V1 checkpoints load in V2 model with zero-initialized temporal features. V2 checkpoints fail fast in V1 model.

**Testing**: 7 unit tests + 3 integration tests required.
