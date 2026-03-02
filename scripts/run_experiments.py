#!/usr/bin/env python3
"""High-level experiment runner for SIAD World Model

Runs comprehensive experiments with different model sizes, context lengths, and training configs.
Supports sequential and parallel execution, checkpoint recovery, and wandb tracking.

Usage:
    # Run a predefined experiment suite
    uv run scripts/run_experiments.py --suite baseline
    uv run scripts/run_experiments.py --suite scaling
    uv run scripts/run_experiments.py --suite temporal

    # Run custom experiment config
    uv run scripts/run_experiments.py --config configs/my_experiments.yaml

    # Resume interrupted experiments
    uv run scripts/run_experiments.py --suite scaling --resume

    # Run experiments in parallel (requires multiple GPUs)
    uv run scripts/run_experiments.py --suite scaling --parallel --gpus 0,1,2,3
"""

import argparse
import subprocess
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import shutil


class ExperimentRunner:
    """Manages and runs multiple training experiments"""

    def __init__(
        self,
        experiments_config: Dict[str, Any],
        manifest_path: str,
        data_root: Optional[str] = None,
        base_checkpoint_dir: str = "checkpoints",
        parallel: bool = False,
        gpus: Optional[List[int]] = None,
        resume: bool = False,
        dry_run: bool = False
    ):
        self.config = experiments_config
        self.manifest_path = manifest_path
        self.data_root = data_root
        self.base_checkpoint_dir = Path(base_checkpoint_dir)
        self.parallel = parallel
        self.gpus = gpus or [0]
        self.resume = resume
        self.dry_run = dry_run

        # Create results directory
        self.results_dir = Path("experiment_results")
        self.results_dir.mkdir(exist_ok=True)

        # Track experiment state
        self.state_file = self.results_dir / "experiment_state.json"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load experiment state for resume capability"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return {"completed": [], "failed": [], "in_progress": None}

    def _save_state(self):
        """Save experiment state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _is_experiment_complete(self, exp_name: str) -> bool:
        """Check if experiment has already completed"""
        checkpoint_dir = self.base_checkpoint_dir / exp_name
        final_checkpoint = checkpoint_dir / "checkpoint_final.pth"
        return final_checkpoint.exists()

    def _get_experiment_name(self, config: Dict[str, Any]) -> str:
        """Generate descriptive experiment name"""
        model_size = config.get("model_size", "tiny")
        context = config.get("context_length", 1)
        epochs = config.get("epochs", 50)
        batch_size = config.get("batch_size", 32)

        # Include timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{model_size}_ctx{context}_e{epochs}_bs{batch_size}_{timestamp}"

    def _estimate_training_time(self, config: Dict[str, Any]) -> float:
        """Estimate training time in minutes based on model size and epochs"""
        # Time estimates from model_sizes.yaml (per 50 epochs)
        base_times = {
            "tiny": 9,
            "small": 20,
            "medium": 45,
            "large": 120,
            "xlarge": 360
        }

        model_size = config.get("model_size", "tiny")
        epochs = config.get("epochs", 50)
        context = config.get("context_length", 1)

        base_time = base_times.get(model_size, 9)

        # Scale by epochs
        time_estimate = base_time * (epochs / 50)

        # Context length increases memory and compute per sample
        # Roughly: ctx=3 -> 1.5x, ctx=6 -> 2x
        context_multiplier = 1 + (context - 1) * 0.25
        time_estimate *= context_multiplier

        return time_estimate

    def _build_train_command(
        self,
        exp_name: str,
        config: Dict[str, Any],
        gpu_id: int = 0
    ) -> List[str]:
        """Build training command for an experiment"""
        checkpoint_dir = self.base_checkpoint_dir / exp_name

        # Base command
        cmd = [
            "uv", "run",
            "scripts/train.py",
            "--manifest", self.manifest_path,
        ]

        # Add data root if specified
        if self.data_root:
            cmd.extend(["--data-root", self.data_root])

        # Model config
        cmd.extend([
            "--model-size", config.get("model_size", "tiny"),
            "--context-length", str(config.get("context_length", 1)),
            "--batch-size", str(config.get("batch_size", 32)),
            "--epochs", str(config.get("epochs", 50)),
            "--lr", str(config.get("learning_rate", 1e-4)),
            "--checkpoint-dir", str(checkpoint_dir),
            "--num-workers", str(config.get("num_workers", 16)),
        ])

        # Wandb logging (always enabled for experiments)
        cmd.append("--wandb")
        wandb_project = config.get("wandb_project", "siad-experiments")
        cmd.extend(["--wandb-project", wandb_project])
        cmd.extend(["--wandb-name", exp_name])

        return cmd

    def _run_experiment(
        self,
        exp_name: str,
        config: Dict[str, Any],
        gpu_id: int = 0
    ) -> Dict[str, Any]:
        """Run a single experiment"""

        # Check if already complete
        if self.resume and self._is_experiment_complete(exp_name):
            print(f"✓ Experiment '{exp_name}' already complete, skipping")
            return {
                "name": exp_name,
                "status": "skipped",
                "message": "Already completed"
            }

        # Build command
        cmd = self._build_train_command(exp_name, config, gpu_id)

        # Set GPU environment
        env = {"CUDA_VISIBLE_DEVICES": str(gpu_id)}

        print(f"\n{'='*80}")
        print(f"Running experiment: {exp_name}")
        print(f"{'='*80}")
        print(f"Config: {json.dumps(config, indent=2)}")
        print(f"GPU: {gpu_id}")
        print(f"Estimated time: {self._estimate_training_time(config):.1f} minutes")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*80}\n")

        if self.dry_run:
            return {
                "name": exp_name,
                "status": "dry_run",
                "command": " ".join(cmd)
            }

        # Update state
        self.state["in_progress"] = exp_name
        self._save_state()

        # Run training
        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                env={**subprocess.os.environ, **env},
                check=True,
                capture_output=False  # Stream output to console
            )

            elapsed = (time.time() - start_time) / 60

            # Mark as complete
            self.state["completed"].append(exp_name)
            self.state["in_progress"] = None
            self._save_state()

            print(f"\n✓ Experiment '{exp_name}' completed in {elapsed:.1f} minutes")

            return {
                "name": exp_name,
                "status": "success",
                "elapsed_minutes": elapsed,
                "config": config
            }

        except subprocess.CalledProcessError as e:
            elapsed = (time.time() - start_time) / 60

            # Mark as failed
            self.state["failed"].append(exp_name)
            self.state["in_progress"] = None
            self._save_state()

            print(f"\n✗ Experiment '{exp_name}' failed after {elapsed:.1f} minutes")

            return {
                "name": exp_name,
                "status": "failed",
                "elapsed_minutes": elapsed,
                "error": str(e),
                "config": config
            }

    def run_sequential(self, experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run experiments sequentially"""
        results = []

        total_time = sum(self._estimate_training_time(exp) for exp in experiments)
        print(f"\n{'='*80}")
        print(f"Running {len(experiments)} experiments sequentially")
        print(f"Estimated total time: {total_time:.1f} minutes ({total_time/60:.1f} hours)")
        print(f"{'='*80}\n")

        for i, exp_config in enumerate(experiments, 1):
            exp_name = self._get_experiment_name(exp_config)

            print(f"\nExperiment {i}/{len(experiments)}: {exp_name}")

            result = self._run_experiment(exp_name, exp_config, gpu_id=self.gpus[0])
            results.append(result)

            # Save intermediate results
            self._save_results(results)

        return results

    def run_parallel(self, experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run experiments in parallel across multiple GPUs"""
        if len(self.gpus) < 2:
            print("Warning: Parallel mode requires multiple GPUs. Falling back to sequential.")
            return self.run_sequential(experiments)

        # TODO: Implement parallel execution using multiprocessing
        # For now, fall back to sequential
        print("Note: Parallel execution not yet implemented. Running sequentially.")
        return self.run_sequential(experiments)

    def _save_results(self, results: List[Dict[str, Any]]):
        """Save experiment results to JSON"""
        results_file = self.results_dir / "results.json"

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_experiments": len(results),
            "successful": sum(1 for r in results if r["status"] == "success"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "experiments": results
        }

        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nResults saved to: {results_file}")

    def run(self, experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run all experiments"""
        if self.parallel:
            results = self.run_parallel(experiments)
        else:
            results = self.run_sequential(experiments)

        # Print summary
        print(f"\n{'='*80}")
        print("Experiment Summary")
        print(f"{'='*80}")
        print(f"Total experiments: {len(results)}")
        print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
        print(f"Failed: {sum(1 for r in results if r['status'] == 'failed')}")
        print(f"Skipped: {sum(1 for r in results if r['status'] == 'skipped')}")

        # Show successful experiments
        successful = [r for r in results if r['status'] == 'success']
        if successful:
            print(f"\nSuccessful experiments:")
            for r in successful:
                elapsed = r.get('elapsed_minutes', 0)
                print(f"  - {r['name']} ({elapsed:.1f} min)")

        # Show failed experiments
        failed = [r for r in results if r['status'] == 'failed']
        if failed:
            print(f"\nFailed experiments:")
            for r in failed:
                print(f"  - {r['name']}: {r.get('error', 'Unknown error')}")

        print(f"{'='*80}\n")

        return results


def load_experiment_suite(suite_name: str) -> Dict[str, Any]:
    """Load predefined experiment suite"""
    config_path = Path(__file__).parent.parent / "configs" / "experiments.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Experiments config not found: {config_path}")

    with open(config_path) as f:
        all_suites = yaml.safe_load(f)

    if suite_name not in all_suites:
        available = ", ".join(all_suites.keys())
        raise ValueError(f"Unknown suite '{suite_name}'. Available: {available}")

    return all_suites[suite_name]


def load_custom_config(config_path: str) -> Dict[str, Any]:
    """Load custom experiment config"""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Run comprehensive SIAD training experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Experiment selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--suite", type=str,
                      help="Predefined experiment suite (baseline, scaling, temporal, production, ablation)")
    group.add_argument("--config", type=str,
                      help="Custom experiment config YAML file")

    # Data paths
    parser.add_argument("--manifest", type=str,
                       default="data/manifest.jsonl",
                       help="Path to manifest.jsonl")
    parser.add_argument("--data-root", type=str, default=None,
                       help="Root directory for data files")

    # Execution options
    parser.add_argument("--parallel", action="store_true",
                       help="Run experiments in parallel (requires multiple GPUs)")
    parser.add_argument("--gpus", type=str, default="0",
                       help="Comma-separated GPU IDs (e.g., '0,1,2,3')")
    parser.add_argument("--checkpoint-dir", type=str, default="checkpoints",
                       help="Base checkpoint directory")
    parser.add_argument("--resume", action="store_true",
                       help="Resume interrupted experiments (skip completed ones)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print commands without running")

    args = parser.parse_args()

    # Load experiment config
    if args.suite:
        print(f"Loading experiment suite: {args.suite}")
        config = load_experiment_suite(args.suite)
    else:
        print(f"Loading custom config: {args.config}")
        config = load_custom_config(args.config)

    # Parse GPU IDs
    gpu_ids = [int(x.strip()) for x in args.gpus.split(",")]

    # Extract experiments list
    experiments = config.get("experiments", [])
    if not experiments:
        print("Error: No experiments defined in config")
        sys.exit(1)

    print(f"\nLoaded {len(experiments)} experiments:")
    for i, exp in enumerate(experiments, 1):
        model_size = exp.get("model_size", "tiny")
        context = exp.get("context_length", 1)
        epochs = exp.get("epochs", 50)
        print(f"  {i}. {model_size} (ctx={context}, epochs={epochs})")

    # Create runner
    runner = ExperimentRunner(
        experiments_config=config,
        manifest_path=args.manifest,
        data_root=args.data_root,
        base_checkpoint_dir=args.checkpoint_dir,
        parallel=args.parallel,
        gpus=gpu_ids,
        resume=args.resume,
        dry_run=args.dry_run
    )

    # Run experiments
    results = runner.run(experiments)

    # Exit with error code if any failed
    if any(r["status"] == "failed" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
