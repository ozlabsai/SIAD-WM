"""Acceptance tests for WorldModel

Tests per MODEL.md Section 11:
- A.2) Transition shape tests
- A.3) Rollout shape tests
- B) Determinism test
- D) Training smoke test
- E) Residual heatmap generation test
"""

import pytest
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from siad.model.wm import WorldModel
from siad.train.losses import compute_jepa_world_model_loss


class TestWorldModelShapes:
    """Shape contract tests per MODEL.md Section 11.A"""
    
    def test_transition_shape(self):
        """Transition shape: [2,256,512] + [2,A] → [2,256,512]"""
        model = WorldModel(
            in_channels=8,
            latent_dim=512,
            action_dim=1,
            dropout=0.0
        )
        model.train(False)
        
        # Input tokens and actions
        z = torch.randn(2, 256, 512)
        a = torch.randn(2, 1)  # Single action (rain_anom)
        
        with torch.no_grad():
            z_next = model.transition(z, a)
        
        assert z_next.shape == (2, 256, 512), \
            f"Expected transition output (2, 256, 512), got {z_next.shape}"
    
    def test_rollout_shape(self):
        """Rollout shape: [2,256,512] + [2,6,A] → [2,6,256,512]"""
        model = WorldModel(
            in_channels=8,
            latent_dim=512,
            action_dim=1,
            dropout=0.0
        )
        model.train(False)
        
        # Initial tokens and action sequence
        z0 = torch.randn(2, 256, 512)
        a_seq = torch.randn(2, 6, 1)  # 6-month rollout
        
        with torch.no_grad():
            z_pred = model.rollout(z0, a_seq, H=6)
        
        assert z_pred.shape == (2, 6, 256, 512), \
            f"Expected rollout output (2, 6, 256, 512), got {z_pred.shape}"
    
    def test_encode_interface(self):
        """Encode interface: [2,8,256,256] → [2,256,512]"""
        model = WorldModel(in_channels=8, latent_dim=512)
        model.train(False)
        
        x = torch.randn(2, 8, 256, 256)
        
        with torch.no_grad():
            z = model.encode(x)
        
        assert z.shape == (2, 256, 512), \
            f"Expected encode output (2, 256, 512), got {z.shape}"
    
    def test_encode_targets_interface(self):
        """Target encoding: [2,8,256,256] → [2,256,512]"""
        model = WorldModel(in_channels=8, latent_dim=512)
        model.train(False)
        
        x = torch.randn(2, 8, 256, 256)
        
        with torch.no_grad():
            z_target = model.encode_targets(x)
        
        assert z_target.shape == (2, 256, 512), \
            f"Expected target output (2, 256, 512), got {z_target.shape}"


class TestDeterminism:
    """Determinism tests per MODEL.md Section 11.B"""
    
    def test_transition_deterministic(self):
        """Transition is deterministic when stochastic disabled"""
        model = WorldModel(in_channels=8, latent_dim=512, dropout=0.0)
        model.train(False)
        
        torch.manual_seed(42)
        z = torch.randn(2, 256, 512)
        a = torch.randn(2, 1)
        
        with torch.no_grad():
            z_next1 = model.transition(z, a)
        
        with torch.no_grad():
            z_next2 = model.transition(z, a)
        
        assert torch.allclose(z_next1, z_next2, atol=1e-6), \
            "Transition outputs differ (non-deterministic)"
    
    def test_rollout_deterministic(self):
        """Rollout is deterministic when stochastic disabled"""
        model = WorldModel(in_channels=8, latent_dim=512, dropout=0.0)
        model.train(False)
        
        torch.manual_seed(42)
        z0 = torch.randn(2, 256, 512)
        a_seq = torch.randn(2, 6, 1)
        
        with torch.no_grad():
            z_pred1 = model.rollout(z0, a_seq, H=6)
        
        with torch.no_grad():
            z_pred2 = model.rollout(z0, a_seq, H=6)
        
        assert torch.allclose(z_pred1, z_pred2, atol=1e-6), \
            "Rollout outputs differ (non-deterministic)"


class TestTrainingSmoke:
    """Training smoke test per MODEL.md Section 11.D"""
    
    def test_loss_finite_on_random_data(self):
        """Loss returns finite values on random tensors"""
        # Create random predictions and targets
        z_pred = torch.randn(2, 6, 256, 512)
        z_target = torch.randn(2, 6, 256, 512)
        
        loss, metrics = compute_jepa_world_model_loss(z_pred, z_target)
        
        assert torch.isfinite(loss), f"Loss is not finite: {loss}"
        assert loss.item() >= 0, f"Loss is negative: {loss.item()}"
        
        # Check all metrics are finite
        for key, value in metrics.items():
            assert not torch.isnan(torch.tensor(value)), \
                f"Metric {key} is NaN: {value}"
    
    def test_forward_backward_pass(self):
        """Full forward + backward pass completes without errors"""
        model = WorldModel(
            in_channels=8,
            latent_dim=512,
            action_dim=1,
            dropout=0.0
        )
        
        # Create synthetic batch
        x_context = torch.randn(2, 8, 256, 256)
        a_seq = torch.randn(2, 6, 1)
        x_targets = torch.randn(2, 6, 8, 256, 256)
        
        # Forward pass
        z0 = model.encode(x_context)
        z_pred = model.rollout(z0, a_seq, H=6)
        
        # Encode targets (batch processing)
        B, H, C, Hp, Wp = x_targets.shape
        x_targets_flat = x_targets.view(B * H, C, Hp, Wp)
        z_target_flat = model.encode_targets(x_targets_flat)
        z_target = z_target_flat.view(B, H, 256, 512)
        
        # Compute loss
        loss, metrics = compute_jepa_world_model_loss(z_pred, z_target)
        
        # Backward pass
        loss.backward()
        
        # Check gradients exist and are finite
        for name, param in model.named_parameters():
            if param.requires_grad:
                assert param.grad is not None, f"No gradient for {name}"
                assert torch.isfinite(param.grad).all(), \
                    f"Non-finite gradients in {name}"
    
    def test_loss_decreases_with_optimizer(self):
        """Loss decreases (or stays stable) over a few optimization steps"""
        model = WorldModel(in_channels=8, latent_dim=512, action_dim=1, dropout=0.0)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
        
        # Create fixed synthetic batch
        torch.manual_seed(42)
        x_context = torch.randn(4, 8, 256, 256)
        a_seq = torch.randn(4, 6, 1)
        x_targets = torch.randn(4, 6, 8, 256, 256)
        
        initial_loss = None
        final_loss = None
        
        for step in range(10):
            optimizer.zero_grad()
            
            # Forward
            z0 = model.encode(x_context)
            z_pred = model.rollout(z0, a_seq, H=6)
            
            # Targets
            B, H, C, Hp, Wp = x_targets.shape
            x_targets_flat = x_targets.view(B * H, C, Hp, Wp)
            z_target_flat = model.encode_targets(x_targets_flat)
            z_target = z_target_flat.view(B, H, 256, 512)
            
            # Loss
            loss, _ = compute_jepa_world_model_loss(z_pred, z_target)
            
            if step == 0:
                initial_loss = loss.item()
            if step == 9:
                final_loss = loss.item()
            
            # Backward + update
            loss.backward()
            optimizer.step()
            
            # Update target encoder EMA
            model.update_target_encoder(step=step)
            
            assert torch.isfinite(loss), f"Loss became non-finite at step {step}"
        
        # Loss should decrease or stay stable (not increase dramatically)
        assert final_loss <= initial_loss * 1.5, \
            f"Loss increased too much: {initial_loss:.4f} → {final_loss:.4f}"


class TestResidualHeatmap:
    """Residual heatmap generation per MODEL.md Section 11.E"""
    
    def test_residual_map_generation(self):
        """Compute residual map and verify 16×16 shape"""
        model = WorldModel(in_channels=8, latent_dim=512, dropout=0.0)
        model.train(False)
        
        # Single tile, single month
        x_context = torch.randn(1, 8, 256, 256)
        a = torch.randn(1, 1, 1)  # Single step
        x_target = torch.randn(1, 8, 256, 256)
        
        with torch.no_grad():
            # Predict
            z0 = model.encode(x_context)
            z_pred = model.rollout(z0, a, H=1)  # [1, 1, 256, 512]
            
            # Target
            z_target = model.encode_targets(x_target).unsqueeze(1)  # [1, 1, 256, 512]
            
            # Compute per-token residual
            # L2 normalize
            z_pred_norm = torch.nn.functional.normalize(z_pred, p=2, dim=-1)
            z_target_norm = torch.nn.functional.normalize(z_target, p=2, dim=-1)
            
            # Cosine distance per token
            cos_sim = (z_pred_norm * z_target_norm).sum(dim=-1)  # [1, 1, 256]
            residual = 1 - cos_sim  # [1, 1, 256]
            
            # Reshape to 16×16 heatmap
            residual_map = residual.squeeze().view(16, 16)  # [16, 16]
        
        assert residual_map.shape == (16, 16), \
            f"Expected residual map (16, 16), got {residual_map.shape}"
        
        # Verify values are in reasonable range [0, 2]
        # (cosine distance is in [0, 2] where 0=identical, 2=opposite)
        assert (residual_map >= 0).all(), "Negative residuals detected"
        assert (residual_map <= 2).all(), "Residuals exceed expected range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
