# SIAD Command Center - Troubleshooting Guide

**Version 1.0.0** | Last Updated: 2025-03-04

This guide covers common issues and solutions for the SIAD Command Center application.

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Backend Issues](#backend-issues)
3. [Frontend Issues](#frontend-issues)
4. [Data Issues](#data-issues)
5. [Map Issues](#map-issues)
6. [Performance Issues](#performance-issues)
7. [Development Environment](#development-environment)
8. [Testing Issues](#testing-issues)

---

## Quick Diagnostics

### System Health Check

Run these commands to verify your setup:

```bash
# Check Python version (should be 3.13+)
python --version

# Check Node version (should be 18+)
node --version

# Check backend health
curl http://localhost:8001/health

# Check frontend is running
curl http://localhost:3000

# Verify data files exist
ls data/residuals_test.h5
ls data/aoi_sf_seed/hotspots_ranked.json
```

### Expected Output

**Backend health:**
```json
{
  "status": "healthy",
  "service": "SIAD Command Center API",
  "version": "1.0.0"
}
```

**Frontend:**
Should return HTML (Next.js page)

---

## Backend Issues

### Issue: Backend won't start

**Error:**
```
Error: command not found: uvicorn
```

**Solution:**
```bash
# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal and try again
uv run uvicorn api.main:app --reload --port 8001
```

---

### Issue: Port 8001 already in use

**Error:**
```
ERROR: [Errno 48] Address already in use
```

**Solution:**

**Option 1: Kill existing process**
```bash
# Find process using port 8001
lsof -ti:8001

# Kill it
kill -9 $(lsof -ti:8001)

# Or on Linux
sudo fuser -k 8001/tcp
```

**Option 2: Use different port**
```bash
uv run uvicorn api.main:app --reload --port 8002
```

Then update frontend API URL:
```typescript
// frontend/lib/api.ts
const API_BASE = "http://localhost:8002/api";
```

---

### Issue: HDF5 file not found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/residuals_test.h5'
```

**Solution:**

**Check file exists:**
```bash
ls -lh data/residuals_test.h5
```

**If missing, regenerate test data:**
```bash
uv run python scripts/create_test_hdf5.py
```

**Check file permissions:**
```bash
chmod 644 data/residuals_test.h5
```

---

### Issue: JSON metadata files not found

**Error:**
```
FileNotFoundError: data/aoi_sf_seed/hotspots_ranked.json
```

**Solution:**

**Regenerate seed dataset:**
```bash
uv run python scripts/create_seed_dataset.py
```

**Verify all files present:**
```bash
ls data/aoi_sf_seed/
# Should show: hotspots_ranked.json, metadata.json, months.json, tiles/
```

---

### Issue: CORS errors in browser console

**Error:**
```
Access to fetch at 'http://localhost:8001/api/aoi' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solution:**

**Check backend CORS config:**
```python
# api/config.py
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

**Verify middleware is enabled:**
```python
# api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Restart backend** after changes.

---

### Issue: Backend slow or hanging

**Symptoms:**
- API requests taking >5 seconds
- Backend becomes unresponsive

**Diagnosis:**
```bash
# Check HDF5 file is not corrupted
uv run python -c "import h5py; f = h5py.File('data/residuals_test.h5', 'r'); print(list(f.keys())); f.close()"

# Check file size is reasonable
ls -lh data/residuals_test.h5
# Should be <500MB for demo data
```

**Solution:**

**Restart backend:**
```bash
# Kill backend
pkill -f uvicorn

# Restart
uv run uvicorn api.main:app --reload --port 8001
```

**Check system resources:**
```bash
# macOS
top -l 1 | grep -E "^CPU|^Phys"

# Linux
htop
```

If memory usage >80%, close other applications.

---

## Frontend Issues

### Issue: Frontend won't start

**Error:**
```
Error: Cannot find module 'next'
```

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

---

### Issue: Port 3000 already in use

**Error:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Solution:**

**Option 1: Kill existing process**
```bash
lsof -ti:3000 | xargs kill -9
```

**Option 2: Use different port**
```bash
PORT=3001 npm run dev
```

---

### Issue: Build errors with Next.js

**Error:**
```
Error: Failed to compile
./components/MapView.tsx
Module not found: Can't resolve 'mapbox-gl'
```

**Solution:**

**Reinstall dependencies:**
```bash
cd frontend
npm install mapbox-gl @types/mapbox-gl
```

**Clear Next.js cache:**
```bash
rm -rf .next
npm run dev
```

---

### Issue: TypeScript errors

**Error:**
```
Type 'Hotspot' is not assignable to type 'never'
```

**Solution:**

**Check TypeScript version:**
```bash
cd frontend
npx tsc --version
# Should be 5.x
```

**Verify type definitions:**
```typescript
// frontend/types/index.ts
export interface Hotspot {
  tileId: string;
  score: number;
  lat: number;
  lon: number;
  month: string;
  changeType: string;
  region: string;
  onset?: string;
  confidence?: string;
  alert_type?: string;
}
```

**Restart TypeScript server in VS Code:**
- Command Palette (Cmd+Shift+P)
- "TypeScript: Restart TS Server"

---

### Issue: API requests failing

**Error (in browser console):**
```
Failed to fetch: TypeError: Failed to fetch
```

**Diagnosis:**
```bash
# Check backend is running
curl http://localhost:8001/health

# Check API endpoint directly
curl http://localhost:8001/api/aoi
```

**Solution:**

**Verify API base URL:**
```typescript
// frontend/lib/api.ts
const API_BASE = "http://localhost:8001/api";
```

**Check network tab in DevTools:**
- Open Chrome DevTools (F12)
- Network tab
- Look for failed requests (red)
- Click request to see error details

**Common causes:**
1. Backend not running → Start backend
2. Wrong port → Update API_BASE URL
3. CORS issue → Check backend CORS config
4. Firewall → Disable temporarily to test

---

## Data Issues

### Issue: No hotspots showing

**Symptoms:**
- Detection rail says "No hotspots detected"
- Map is empty (no markers)

**Diagnosis:**
```bash
# Check hotspots file has data
cat data/aoi_sf_seed/hotspots_ranked.json | grep -c '"tile_id"'
# Should show >0

# Test API directly
curl "http://localhost:8001/api/detect/hotspots?min_score=0.0&limit=100"
```

**Solution:**

**If API returns empty array:**
```bash
# Regenerate hotspots
uv run python scripts/generate_hotspots.py
```

**If API returns error:**
- Check backend logs for stack trace
- Verify HDF5 file integrity

**If frontend filter is too strict:**
- Lower minimum score threshold (slider in UI)
- Clear date range filters
- Set alert type to "All"

---

### Issue: Tile detail modal shows no data

**Symptoms:**
- Modal opens but shows "No data available"
- Timeline chart is empty

**Diagnosis:**
```bash
# Check tile directory exists
ls data/aoi_sf_seed/tiles/1/

# Should show timeline.json and imagery files
```

**Solution:**

**Regenerate tile timelines:**
```bash
uv run python scripts/generate_timelines.py
```

**Verify tile data:**
```bash
cat data/aoi_sf_seed/tiles/1/timeline.json
# Should show array of {month, score, timestamp}
```

---

### Issue: Corrupted HDF5 file

**Error:**
```
OSError: Unable to open file (file signature not found)
```

**Solution:**

**Backup old file:**
```bash
mv data/residuals_test.h5 data/residuals_test.h5.backup
```

**Regenerate HDF5:**
```bash
uv run python scripts/create_test_hdf5.py
```

**Verify new file:**
```bash
uv run python -c "import h5py; f = h5py.File('data/residuals_test.h5', 'r'); print('Groups:', list(f.keys())); print('Valid'); f.close()"
```

---

## Map Issues

### Issue: Map not rendering

**Symptoms:**
- Gray box where map should be
- Console error: "Mapbox GL JS: Error loading map"

**Solution:**

**Check Mapbox token:**
```bash
cat frontend/.env.local
# Should show: NEXT_PUBLIC_MAPBOX_TOKEN=pk.ey...
```

**If token missing:**
```bash
echo "NEXT_PUBLIC_MAPBOX_TOKEN=your_token_here" > frontend/.env.local
```

**Get free Mapbox token:**
1. Sign up at https://account.mapbox.com/
2. Copy default public token
3. Paste in `.env.local`

**Restart frontend** after adding token.

**Note:** Map will work without token (hotspots still visible, just no basemap).

---

### Issue: Markers not appearing

**Symptoms:**
- Map loads but no hotspot markers
- Hotspots visible in rail but not on map

**Diagnosis:**

**Check browser console:**
```javascript
// Should see no errors like:
// "Invalid GeoJSON"
// "Invalid coordinates"
```

**Check data format:**
```bash
curl http://localhost:8001/api/detect/hotspots | python -m json.tool
# Verify lat/lon are valid numbers
```

**Solution:**

**Verify coordinate format:**
- Latitude: -90 to 90
- Longitude: -180 to 180

**Check map bounds:**
```typescript
// MapView.tsx
// Ensure hotspots are within visible bounds
map.fitBounds([...]);
```

**Refresh page** after data changes.

---

### Issue: Map performance is slow

**Symptoms:**
- Laggy when panning/zooming
- Stuttering when playing timeline
- High CPU usage

**Solution:**

**Enable marker clustering** (future enhancement):
```javascript
// For 1000+ hotspots
map.addSource('hotspots', {
  type: 'geojson',
  data: geojson,
  cluster: true,
  clusterRadius: 50
});
```

**Reduce marker count:**
- Increase score threshold
- Apply date range filter
- Limit to top 100 hotspots

**Close other tabs/applications:**
- Map rendering is GPU-intensive

---

## Performance Issues

### Issue: Slow initial load

**Symptoms:**
- Page takes >5 seconds to show data
- "Loading hotspots..." spinner stays too long

**Diagnosis:**

**Time each step:**
```bash
# Backend response time
time curl http://localhost:8001/api/detect/hotspots

# Should be <500ms
```

**Solution:**

**Backend optimization:**
```python
# api/services/data_loader.py
# Ensure file is cached in memory
self.hdf5_file = h5py.File(hdf5_path, 'r')  # Keep open
```

**Frontend optimization:**
```typescript
// Reduce initial limit
fetchHotspots(0.5, 50)  // Instead of 100
```

**Network optimization:**
- Use localhost (not 127.0.0.1)
- Disable VPN if active

---

### Issue: Memory usage high

**Symptoms:**
- Backend using >1GB RAM
- Frontend tab using >500MB

**Solution:**

**Backend:**
```bash
# Close HDF5 file when done
# api/main.py lifespan context manager handles this
```

**Frontend:**
```javascript
// Clear TanStack Query cache
queryClient.clear()

// Or reduce cache time
queryClient.setDefaultOptions({
  queries: {
    cacheTime: 60000,  // 1 minute instead of 5
  }
})
```

**Restart both services** if memory leak suspected.

---

## Development Environment

### Issue: UV not found

**Error:**
```
bash: uv: command not found
```

**Solution:**

**Install UV:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart terminal
source ~/.bashrc  # or ~/.zshrc
```

**Verify installation:**
```bash
uv --version
```

---

### Issue: Python version mismatch

**Error:**
```
Python 3.11 found, but 3.13+ required
```

**Solution:**

**Check installed Python versions:**
```bash
ls /usr/local/bin/python*
```

**Install Python 3.13 via UV:**
```bash
uv python install 3.13
uv python pin 3.13
```

**Or use system package manager:**
```bash
# macOS
brew install python@3.13

# Ubuntu
sudo apt install python3.13
```

---

### Issue: Node/npm version too old

**Error:**
```
error: This version of npm is compatible with lockfileVersion@3
```

**Solution:**

**Update Node.js:**
```bash
# macOS
brew install node@18

# Or use nvm
nvm install 18
nvm use 18
```

**Update npm:**
```bash
npm install -g npm@latest
```

---

## Testing Issues

### Issue: Playwright tests failing

**Error:**
```
browserType.launch: Executable doesn't exist
```

**Solution:**

**Install browsers:**
```bash
cd frontend
npx playwright install chromium
```

**Run tests:**
```bash
npm run test:e2e
```

---

### Issue: E2E tests timing out

**Error:**
```
Test timeout of 30000ms exceeded
```

**Solution:**

**Ensure services are running:**
```bash
# Terminal 1: Backend
uv run uvicorn api.main:app --port 8001

# Terminal 2: Frontend
cd frontend && npm run dev
```

**Increase timeout:**
```typescript
// playwright.config.ts
timeout: 60000,  // 60 seconds
```

**Run single test:**
```bash
npx playwright test demo.spec.ts --headed
```

---

### Issue: Backend tests failing

**Error:**
```
ModuleNotFoundError: No module named 'api'
```

**Solution:**

**Run tests with UV:**
```bash
uv run pytest tests/test_integration.py -v
```

**Or set PYTHONPATH:**
```bash
export PYTHONPATH=.
pytest tests/test_integration.py -v
```

---

## Getting Help

### Collect Debug Information

Before asking for help, gather this info:

```bash
# System info
uname -a
python --version
node --version

# Backend logs
uv run uvicorn api.main:app --log-level debug

# Frontend logs
npm run dev
# (check terminal output)

# Browser console
# Open DevTools (F12), copy Console and Network tabs

# Data validation
uv run python scripts/validate_demo_data.py
```

### Check Logs

**Backend logs:**
- Terminal running `uvicorn` command
- Look for errors, warnings, tracebacks

**Frontend logs:**
- Terminal running `npm run dev`
- Browser DevTools Console (F12)

**Network logs:**
- Browser DevTools Network tab
- Check for failed requests (red)
- Inspect request/response payloads

---

## Common Error Messages

### "Module not found"
- **Cause:** Missing dependency
- **Fix:** `npm install` or `uv sync`

### "Address already in use"
- **Cause:** Port conflict
- **Fix:** Kill process or use different port

### "File not found"
- **Cause:** Missing data file
- **Fix:** Regenerate data with scripts

### "CORS policy"
- **Cause:** Backend CORS misconfiguration
- **Fix:** Check `api/config.py` CORS_ORIGINS

### "Failed to fetch"
- **Cause:** Backend not running or wrong URL
- **Fix:** Start backend, verify API_BASE URL

### "Invalid GeoJSON"
- **Cause:** Corrupted coordinate data
- **Fix:** Regenerate hotspots JSON

---

## Still Having Issues?

1. **Read error message carefully** - Often contains solution
2. **Check recent code changes** - Revert if needed
3. **Try "clean start"** - Delete caches, restart everything
4. **Search error message** - Likely others have seen it
5. **Ask for help** - Provide debug info above

---

**Troubleshooting Guide Version:** 1.0.0
**Last Updated:** 2025-03-04
**Next Review:** After user feedback from first demo
