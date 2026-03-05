# SIAD Command Center - Test Execution Guide

## Quick Test Summary

All tests have been implemented and are ready to run. This guide provides commands to execute the complete test suite.

---

## Prerequisites

Ensure both backend and frontend are running before executing tests:

**Terminal 1 - Backend:**
```bash
uv run uvicorn api.main:app --reload --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd frontend && npm run dev
```

---

## Test Commands

### 1. Data Validation

Verify all data files are present and valid:

```bash
# Quick validation (2 seconds)
uv run python scripts/quick_validate.py

# Expected output:
# ✓ VALIDATION PASSED - All required files present
```

---

### 2. Backend Integration Tests

Test all API endpoints:

```bash
# Run all integration tests
uv run pytest tests/test_integration.py -v

# Expected results:
# - 15+ tests pass
# - 0 failures
# - ~5 seconds execution time
```

**Individual test suites:**
```bash
# Health endpoints only
uv run pytest tests/test_integration.py::TestHealthEndpoints -v

# Hotspot endpoints only
uv run pytest tests/test_integration.py::TestHotspotEndpoints -v

# Data consistency only
uv run pytest tests/test_integration.py::TestDataConsistency -v
```

---

### 3. Performance Benchmarks

Run performance tests:

```bash
# All performance tests
uv run pytest tests/test_performance.py -v

# Expected results:
# - All benchmarks meet targets
# - Health check: <50ms
# - API endpoints: <500ms
# - User session: <2s
```

---

### 4. Frontend E2E Tests

**IMPORTANT:** Requires backend and frontend running first!

```bash
# Run all E2E tests (headless)
cd frontend && npm run test:e2e

# Run with UI (interactive mode)
cd frontend && npm run test:e2e:ui

# View test report
cd frontend && npm run test:e2e:report

# Expected results:
# - 15 tests pass
# - 0 failures
# - ~60 seconds execution time
```

**Individual test files:**
```bash
# Run specific test
npx playwright test demo.spec.ts

# Run in headed mode (see browser)
npx playwright test demo.spec.ts --headed

# Debug mode
npx playwright test demo.spec.ts --debug
```

---

### 5. Code Quality (Linting)

**Frontend linting:**
```bash
cd frontend && npm run lint

# Expected output:
# ✓ No errors
# ⚠ 1 warning (acceptable for demo)
```

**Backend linting:**
```bash
uv run ruff check api/

# Expected output:
# All checks passed!
```

---

## Complete Test Suite

Run all tests in sequence:

```bash
# 1. Validate data
uv run python scripts/quick_validate.py && \

# 2. Backend tests
uv run pytest tests/test_integration.py -v && \

# 3. Performance tests
uv run pytest tests/test_performance.py -v && \

# 4. Frontend linting
cd frontend && npm run lint && cd .. && \

# 5. Backend linting
uv run ruff check api/ && \

# 6. E2E tests (ensure services are running!)
cd frontend && npm run test:e2e

echo "✓ ALL TESTS COMPLETE"
```

---

## Test Results Checklist

After running all tests, verify:

- [ ] Data validation passes
- [ ] Backend integration tests: 15+ tests pass
- [ ] Performance benchmarks: All targets met
- [ ] Frontend linting: 0 errors (1 acceptable warning)
- [ ] Backend linting: All checks passed
- [ ] E2E tests: 15 tests pass

---

## Troubleshooting Test Failures

### E2E Tests Timeout

**Problem:** Tests timeout waiting for page load

**Solution:**
```bash
# Ensure backend is running
curl http://localhost:8001/health

# Ensure frontend is running
curl http://localhost:3000

# Restart services if needed
```

### Backend Tests Fail

**Problem:** API tests return errors

**Solution:**
```bash
# Check data files exist
ls data/residuals_test.h5
ls data/aoi_sf_seed/hotspots_ranked.json

# Regenerate if missing
uv run python scripts/create_seed_dataset.py
```

### Performance Tests Fail

**Problem:** Response times exceed targets

**Solution:**
- Close other applications (free up CPU/memory)
- Restart backend (clear any memory leaks)
- Run tests individually (reduce system load)

---

## CI/CD Integration (Future)

These tests are designed for CI/CD integration:

```yaml
# .github/workflows/test.yml (example)
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run validation
        run: uv run python scripts/quick_validate.py
      - name: Run backend tests
        run: uv run pytest tests/ -v
      - name: Run frontend tests
        run: cd frontend && npm run test:e2e
```

---

**Last Updated:** 2025-03-04
**Test Suite Version:** 1.0.0
