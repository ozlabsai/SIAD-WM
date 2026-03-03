# SIAD Command Center

**Tactical Satellite Intelligence Interface** - Palantir/Anduril-style demo for SIAD World Model

![Status: In Development](https://img.shields.io/badge/status-in%20development-yellow)
![Model: Medium 374M](https://img.shields.io/badge/model-medium%20374M-blue)
![Val Loss: 0.0131](https://img.shields.io/badge/val%20loss-0.0131-green)

## 🎯 Vision

A command center-style interface showcasing the SIAD World Model's ability to predict satellite imagery 6 months into the future. Built with a Palantir/Anduril tactical aesthetic featuring:

- 🗺️ **Interactive hex grid map** of SF Bay Area tiles
- 📊 **Model quality gallery** (best/worst/average predictions)
- 🎮 **Real-time inference** via FastAPI backend
- 🎨 **Dark tactical UI** with hex grids and glowing accents
- 📈 **Metrics dashboard** with loss graphs and confidence heatmaps

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌────────────────┐
│   Frontend      │  HTTP   │   FastAPI        │  PyTorch│   SIAD Model   │
│   React + Three ├────────>│   Backend        ├────────>│   + Decoder    │
│   (Port 3000)   │<────────│   (Port 8000)    │<────────│   (GPU/CPU)    │
└─────────────────┘         └──────────────────┘         └────────────────┘
      │                            │                             │
      │ WebGL Hex Map              │ Model Loading               │ Checkpoints
      │ Timeline Scrubber          │ Inference Pipeline          │ - Medium 374M
      │ Metrics Display            │ Gallery Curation            │ - Decoder
      └────────────────────────────┴─────────────────────────────┘
```

## 📁 Project Structure

```
siad-command-center/
├── api/                          # FastAPI Backend
│   ├── main.py                   # API server + endpoints
│   ├── routes/
│   │   ├── tiles.py             # Tile management
│   │   ├── predict.py           # Model inference
│   │   └── gallery.py           # Curated predictions
│   └── services/
│       ├── model_loader.py      # Model management
│       ├── inference.py         # Inference pipeline
│       └── gallery.py           # Gallery curation
│
├── frontend/                     # React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Gallery/         # Prediction showcase
│   │   │   ├── HexMap/          # 3D hex tile map
│   │   │   ├── Timeline/        # 6-month scrubber
│   │   │   ├── Metrics/         # Loss/confidence dashboard
│   │   │   └── Layout/          # Tactical panels
│   │   ├── lib/
│   │   │   ├── api.ts           # Backend client
│   │   │   └── three-utils.ts   # WebGL helpers
│   │   └── styles/
│   │       ├── tokens.json      # Design system
│   │       └── tactical.css     # Palantir/Anduril theme
│   └── package.json
│
└── scripts/
    └── generate_gallery.py      # Pre-compute predictions
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+
- CUDA GPU (recommended) or CPU
- Trained SIAD medium model checkpoint
- Trained decoder checkpoint

### Backend Setup

```bash
cd siad-command-center/api

# Install dependencies
pip install fastapi uvicorn torch pyyaml rasterio numpy

# Set paths to checkpoints
export MODEL_CHECKPOINT=../../checkpoints/checkpoint_best.pth
export DECODER_CHECKPOINT=../../checkpoints/decoder_best.pth

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd siad-command-center/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Visit `http://localhost:3000` for the command center interface.

## 🎨 Design System

### Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Background Primary | `#0a0a0a` | Main background |
| Background Secondary | `#1a1a1a` | Panels/cards |
| Accent Cyan | `#14b8a6` | Hover states, highlights |
| Accent Amber | `#f59e0b` | Selected states, active |
| Text Primary | `#f5f5f5` | Main text |
| Text Dim | `#737373` | Secondary text |

### Typography

- **Mono**: JetBrains Mono (data, code, metrics)
- **UI**: Inter (labels, body text)
- **Display**: Rajdhani (headers, tactical text)

### Components

- **Hex Buttons**: Sharp corners, 1px cyan border, glow on hover
- **Panels**: Dark glass effect with backdrop blur
- **Cards**: Hover → cyan outline, Selected → amber fill
- **Badges**: Uppercase, wide letter-spacing, status colors

## 📊 Model Performance

| Metric | Value |
|--------|-------|
| Model Size | Medium (374M params) |
| Validation Loss | 0.0131 |
| Dataset | 21 tiles × 48 months |
| Training Time | ~20 minutes (A100 80GB) |
| Decoder PSNR | TBD (training) |

## 🔧 API Endpoints

### Tiles

- `GET /api/tiles` - List all available tiles
- `GET /api/tiles/{tile_id}` - Get tile metadata

### Inference

- `POST /api/predict` - Run 6-month prediction
  ```json
  {
    "tile_id": "tile_x000_y000",
    "start_month": "2024-01",
    "actions": [[0.0, 0.0], [0.1, 0.0], ...]  // Optional
  }
  ```

### Gallery

- `GET /api/gallery?category=best&limit=15` - Get curated predictions
- `POST /api/gallery/generate` - Generate gallery (long-running)

## 🎯 Roadmap

### Phase 1: Foundation ✅
- [x] Decoder architecture
- [x] FastAPI backend skeleton
- [x] Design system tokens
- [x] Model service

### Phase 2: Core Features 🚧
- [ ] Gallery curation service
- [ ] Inference pipeline
- [ ] Hex map visualization
- [ ] Timeline scrubber
- [ ] Metrics dashboard

### Phase 3: Polish & Deploy
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Docker deployment
- [ ] HuggingFace Spaces hosting

## 🤝 Multi-Agent Development

This project is built by a team of 8 specialized agents:

| Agent | Role | Status |
|-------|------|--------|
| Agent 1 | Decoder Architect | ✅ Complete |
| Agent 2 | Backend Engineer | 🚧 In Progress |
| Agent 3 | Frontend Architect | ✅ Design Complete |
| Agent 4 | Gallery Engineer | 🚧 In Progress |
| Agent 5 | Map Visualization | 🚧 In Progress |
| Agent 6 | Timeline Engineer | ⏳ Pending |
| Agent 7 | Metrics Dashboard | ⏳ Pending |
| Agent 8 | Integration Engineer | ⏳ Pending |

## 📝 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- SIAD World Model team
- Palantir/Anduril for UI inspiration
- HuggingFace for model hosting
