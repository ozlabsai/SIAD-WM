"""Training loop for SIAD World Model

Implements MODEL.md-compliant training with:
- JEPA rollout loss
- EMA target encoder updates
- Checkpointing
- Mixed precision (optional)
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
import time
from tqdm import tqdm

from siad.model import WorldModel
from siad.train.losses import compute_jepa_world_model_loss


class Trainer:
    """SIAD World Model Trainer per MODEL.md

    Uses new interfaces:
    - model.encode()
    - model.rollout()
    - model.encode_targets()
    - compute_jepa_world_model_loss()
    """

    def __init__(
        self,
        model: WorldModel,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        config: Optional[Dict] = None,
        checkpoint_dir: str = "checkpoints",
        device: Optional[torch.device] = None
    ):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Device
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        self.model.to(self.device)

        # Config
        self.config = {
            "learning_rate": 1e-4,
            "weight_decay": 1e-5,
            "epochs": 50,
            "grad_clip_norm": 1.0,
            "save_every": 5,
            "seed": 42,
            "rollout_horizon": 6,
        }
        if config:
            self.config.update(config)

        # Seed
        torch.manual_seed(self.config["seed"])
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.config["seed"])

        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config["learning_rate"],
            weight_decay=self.config["weight_decay"]
        )

        # Scheduler
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=self.config["epochs"]
        )

        # State
        self.epoch = 0
        self.global_step = 0
        self.best_val_loss = float('inf')
        self.train_losses = []
        self.val_losses = []

        print(f"Trainer initialized:")
        print(f"  Device: {self.device}")
        print(f"  Learning rate: {self.config['learning_rate']}")
        print(f"  Epochs: {self.config['epochs']}")

    def train_epoch(self) -> Tuple[float, Dict[str, float]]:
        """Train for one epoch"""
        self.model.train()
        epoch_losses = []
        epoch_metrics = {}

        pbar = tqdm(self.train_loader, desc=f"Epoch {self.epoch+1}/{self.config['epochs']}")

        for batch_idx, batch in enumerate(pbar):
            # Move to device
            x_context = batch["obs_context"].to(self.device)
            actions = batch["actions_rollout"].to(self.device)
            x_targets = batch["obs_targets"].to(self.device)

            # Forward pass per MODEL.md
            # 1. Encode context
            z0 = self.model.encode(x_context)

            # 2. Rollout predictions
            H = self.config["rollout_horizon"]
            z_pred = self.model.rollout(z0, actions, H=H)

            # 3. Encode targets (batch processing)
            B, H_batch, C, Hp, Wp = x_targets.shape
            x_targets_flat = x_targets.view(B * H_batch, C, Hp, Wp)
            z_target_flat = self.model.encode_targets(x_targets_flat)
            z_target = z_target_flat.view(B, H_batch, 256, 512)

            # 4. Compute loss
            loss, metrics = compute_jepa_world_model_loss(z_pred, z_target)

            # Backward
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            if self.config["grad_clip_norm"] > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config["grad_clip_norm"]
                )

            self.optimizer.step()

            # Update target encoder EMA
            self.model.update_target_encoder(step=self.global_step)

            # Track metrics
            epoch_losses.append(loss.item())
            for key, value in metrics.items():
                if key not in epoch_metrics:
                    epoch_metrics[key] = []
                epoch_metrics[key].append(value)

            # Update progress
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})
            self.global_step += 1

        # Aggregate
        avg_loss = sum(epoch_losses) / len(epoch_losses)
        for key in epoch_metrics:
            epoch_metrics[key] = sum(epoch_metrics[key]) / len(epoch_metrics[key])

        return avg_loss, epoch_metrics

    @torch.no_grad()
    def validate(self) -> Tuple[float, Dict[str, float]]:
        """Validate"""
        if self.val_loader is None:
            return float('nan'), {}

        self.model.eval()
        val_losses = []
        val_metrics = {}

        for batch in tqdm(self.val_loader, desc="Validation"):
            x_context = batch["obs_context"].to(self.device)
            actions = batch["actions_rollout"].to(self.device)
            x_targets = batch["obs_targets"].to(self.device)

            # Forward
            z0 = self.model.encode(x_context)
            z_pred = self.model.rollout(z0, actions, H=self.config["rollout_horizon"])

            B, H, C, Hp, Wp = x_targets.shape
            x_targets_flat = x_targets.view(B * H, C, Hp, Wp)
            z_target_flat = self.model.encode_targets(x_targets_flat)
            z_target = z_target_flat.view(B, H, 256, 512)

            loss, metrics = compute_jepa_world_model_loss(z_pred, z_target)

            val_losses.append(loss.item())
            for key, value in metrics.items():
                if key not in val_metrics:
                    val_metrics[key] = []
                val_metrics[key].append(value)

        # Aggregate
        avg_loss = sum(val_losses) / len(val_losses)
        for key in val_metrics:
            val_metrics[key] = sum(val_metrics[key]) / len(val_metrics[key])

        return avg_loss, val_metrics

    def save_checkpoint(self, filename: str, is_best: bool = False):
        """Save checkpoint"""
        checkpoint = {
            "epoch": self.epoch,
            "global_step": self.global_step,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "train_loss": self.train_losses[-1] if self.train_losses else float('nan'),
            "val_loss": self.val_losses[-1] if self.val_losses else float('nan'),
            "best_val_loss": self.best_val_loss,
            "config": self.config,
        }

        path = self.checkpoint_dir / filename
        torch.save(checkpoint, path)
        print(f"Saved checkpoint: {path}")

        if is_best:
            best_path = self.checkpoint_dir / "checkpoint_best.pth"
            torch.save(checkpoint, best_path)
            print(f"Saved best checkpoint: {best_path}")

    def train(self):
        """Full training loop"""
        print(f"\nStarting training for {self.config['epochs']} epochs...")
        print(f"Training samples: {len(self.train_loader.dataset)}")
        if self.val_loader:
            print(f"Validation samples: {len(self.val_loader.dataset)}")

        start_time = time.time()

        for epoch in range(self.config["epochs"]):
            self.epoch = epoch

            # Train
            train_loss, train_metrics = self.train_epoch()
            self.train_losses.append(train_loss)

            # Validate
            if self.val_loader:
                val_loss, val_metrics = self.validate()
                self.val_losses.append(val_loss)
            else:
                val_loss = float('nan')

            # Scheduler
            self.scheduler.step()

            # Log
            print(f"\nEpoch {epoch+1}/{self.config['epochs']}:")
            print(f"  Train loss: {train_loss:.4f}")
            if not torch.isnan(torch.tensor(val_loss)):
                print(f"  Val loss: {val_loss:.4f}")

            # Save
            if (epoch + 1) % self.config["save_every"] == 0:
                self.save_checkpoint(f"checkpoint_epoch_{epoch+1}.pth")

            # Best model
            if not torch.isnan(torch.tensor(val_loss)) and val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.save_checkpoint(f"checkpoint_epoch_{epoch+1}.pth", is_best=True)
                print(f"  New best validation loss: {val_loss:.4f}")

        # Final
        self.save_checkpoint("checkpoint_final.pth")

        elapsed = time.time() - start_time
        print(f"\nTraining completed in {elapsed/60:.1f} minutes")
        print(f"Best validation loss: {self.best_val_loss:.4f}")

        return {
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "best_val_loss": self.best_val_loss
        }
