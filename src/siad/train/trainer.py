"""Training loop for SIAD World Model

Implements:
- Multi-step rollout training with EMA target encoder
- Checkpointing (best + periodic)
- Gradient clipping
- Learning rate scheduling
- Reproducibility (seed management)
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from pathlib import Path
from typing import Dict, Optional, Tuple
import json
import time
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from siad.model import WorldModel


class Trainer:
    """SIAD World Model Trainer

    Handles:
        - Training loop with EMA updates
        - Validation
        - Checkpointing (best model + periodic saves)
        - Gradient clipping
        - Learning rate scheduling

    Args:
        model: WorldModel instance
        train_loader: DataLoader for training set
        val_loader: DataLoader for validation set
        config: Training configuration dict
        checkpoint_dir: Where to save checkpoints
        device: torch.device or str (default: auto-detect)
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

        # Device setup
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = device
        self.model.to(self.device)

        # Default config
        self.config = {
            "learning_rate": 1e-4,
            "weight_decay": 1e-5,
            "epochs": 50,
            "ema_momentum": 0.996,
            "grad_clip_norm": 1.0,
            "loss_type": "cosine",  # or "mse"
            "loss_weights": None,   # Uniform weights
            "save_every": 5,        # Save checkpoint every N epochs
            "seed": 42,
            "context_length": 6,
            "rollout_horizon": 6,
            "band_order_version": "v1"
        }
        if config:
            self.config.update(config)

        # Set seed for reproducibility (Principle V)
        self._set_seed(self.config["seed"])

        # Optimizer and scheduler
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config["learning_rate"],
            weight_decay=self.config["weight_decay"]
        )

        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=self.config["epochs"]
        )

        # Training state
        self.epoch = 0
        self.best_val_loss = float('inf')
        self.train_losses = []
        self.val_losses = []

        print(f"Trainer initialized:")
        print(f"  Device: {self.device}")
        print(f"  Learning rate: {self.config['learning_rate']}")
        print(f"  Epochs: {self.config['epochs']}")
        print(f"  EMA momentum: {self.config['ema_momentum']}")
        print(f"  Checkpoint dir: {self.checkpoint_dir}")

    def _set_seed(self, seed: int):
        """Set random seeds for reproducibility"""
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    def train_epoch(self) -> Tuple[float, Dict[str, float]]:
        """Train for one epoch

        Returns:
            avg_loss: Average training loss
            metrics: Dict of aggregated metrics
        """
        self.model.train()
        epoch_losses = []
        epoch_metrics = {}

        pbar = tqdm(self.train_loader, desc=f"Epoch {self.epoch+1}/{self.config['epochs']}")

        for batch_idx, batch in enumerate(pbar):
            # Move to device
            obs_context = batch["obs_context"].to(self.device)
            actions_rollout = batch["actions_rollout"].to(self.device)
            obs_targets = batch["obs_targets"].to(self.device)

            # Forward pass and compute loss
            loss, metrics = self.model.compute_rollout_loss(
                obs_context,
                actions_rollout,
                obs_targets,
                loss_weights=self.config["loss_weights"],
                loss_type=self.config["loss_type"]
            )

            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            if self.config["grad_clip_norm"] > 0:
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config["grad_clip_norm"]
                )

            self.optimizer.step()

            # Update target encoder via EMA
            self.model.update_target_encoder(momentum=self.config["ema_momentum"])

            # Track metrics
            epoch_losses.append(loss.item())
            for key, value in metrics.items():
                if key not in epoch_metrics:
                    epoch_metrics[key] = []
                epoch_metrics[key].append(value)

            # Update progress bar
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        # Aggregate metrics
        avg_loss = sum(epoch_losses) / len(epoch_losses)
        for key in epoch_metrics:
            epoch_metrics[key] = sum(epoch_metrics[key]) / len(epoch_metrics[key])

        return avg_loss, epoch_metrics

    @torch.no_grad()
    def validate(self) -> Tuple[float, Dict[str, float]]:
        """Validate on validation set

        Returns:
            avg_loss: Average validation loss
            metrics: Dict of aggregated metrics
        """
        if self.val_loader is None:
            return float('nan'), {}

        self.model.eval()
        val_losses = []
        val_metrics = {}

        for batch in tqdm(self.val_loader, desc="Validation"):
            # Move to device
            obs_context = batch["obs_context"].to(self.device)
            actions_rollout = batch["actions_rollout"].to(self.device)
            obs_targets = batch["obs_targets"].to(self.device)

            # Forward pass
            loss, metrics = self.model.compute_rollout_loss(
                obs_context,
                actions_rollout,
                obs_targets,
                loss_weights=self.config["loss_weights"],
                loss_type=self.config["loss_type"]
            )

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
        """Save model checkpoint

        Args:
            filename: Checkpoint filename
            is_best: Whether this is the best model so far
        """
        checkpoint = {
            "epoch": self.epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "train_loss": self.train_losses[-1] if self.train_losses else float('nan'),
            "val_loss": self.val_losses[-1] if self.val_losses else float('nan'),
            "best_val_loss": self.best_val_loss,
            "config": {**self.config, **self.model.get_config()},
            "seed": self.config["seed"]
        }

        checkpoint_path = self.checkpoint_dir / filename
        torch.save(checkpoint, checkpoint_path)
        print(f"Saved checkpoint: {checkpoint_path}")

        # Save best model separately
        if is_best:
            best_path = self.checkpoint_dir / "checkpoint_best.pth"
            torch.save(checkpoint, best_path)
            print(f"Saved best checkpoint: {best_path}")

    def load_checkpoint(self, checkpoint_path: str):
        """Load checkpoint and resume training

        Args:
            checkpoint_path: Path to checkpoint file
        """
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])
        self.epoch = checkpoint["epoch"]
        self.best_val_loss = checkpoint.get("best_val_loss", float('inf'))

        print(f"Loaded checkpoint from epoch {self.epoch}")

    def train(self):
        """Run full training loop

        Returns:
            history: Dict with train/val losses per epoch
        """
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
                val_metrics = {}

            # Update scheduler
            self.scheduler.step()

            # Log
            print(f"\nEpoch {epoch+1}/{self.config['epochs']}:")
            print(f"  Train loss: {train_loss:.4f}")
            if not torch.isnan(torch.tensor(val_loss)):
                print(f"  Val loss: {val_loss:.4f}")

            # Save checkpoint
            if (epoch + 1) % self.config["save_every"] == 0:
                self.save_checkpoint(f"checkpoint_epoch_{epoch+1}.pth")

            # Save best model
            if not torch.isnan(torch.tensor(val_loss)) and val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.save_checkpoint(f"checkpoint_epoch_{epoch+1}.pth", is_best=True)
                print(f"  New best validation loss: {val_loss:.4f}")

        # Final checkpoint
        self.save_checkpoint("checkpoint_final.pth")

        elapsed = time.time() - start_time
        print(f"\nTraining completed in {elapsed/60:.1f} minutes")
        print(f"Best validation loss: {self.best_val_loss:.4f}")

        return {
            "train_losses": self.train_losses,
            "val_losses": self.val_losses,
            "best_val_loss": self.best_val_loss
        }
