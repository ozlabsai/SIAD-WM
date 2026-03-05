# SIAD Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-28

## Active Technologies
- Python 3.13+ (per constitution) + PyTorch 2.x, pytest (testing), Weights & Biases (monitoring) (002-anti-collapse)
- HDF5 datasets (h5py), checkpoints (PyTorch format) (002-anti-collapse)
- Python 3.13+ (per constitution requirement) + PyTorch 2.x (world model), rasterio + numpy (geospatial I/O), h5py (dataset storage), pytest (testing) (003-003-temporal-conditioning)
- HDF5 datasets (`*.h5`) for preprocessed satellite imagery tiles, metadata JSON for timestamp tracking (003-003-temporal-conditioning)

- Python 3.13+ (per constitution requirement) + `earthengine-api` (satellite data collection), PyTorch 2.x (world model training with `torch.compile()`), `rasterio` + `numpy` (geospatial I/O), `matplotlib` (visualization), `h5py` (dataset storage), `pytest` (testing) (001-siad-mvp)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.13+ (per constitution requirement): Follow standard conventions

## Recent Changes
- 003-003-temporal-conditioning: Added Python 3.13+ (per constitution requirement) + PyTorch 2.x (world model), rasterio + numpy (geospatial I/O), h5py (dataset storage), pytest (testing)
- 002-anti-collapse: Added Python 3.13+ (per constitution) + PyTorch 2.x, pytest (testing), Weights & Biases (monitoring)

- 001-siad-mvp: Added Python 3.13+ (per constitution requirement) + `earthengine-api` (satellite data collection), PyTorch 2.x (world model training with `torch.compile()`), `rasterio` + `numpy` (geospatial I/O), `matplotlib` (visualization), `h5py` (dataset storage), `pytest` (testing)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
