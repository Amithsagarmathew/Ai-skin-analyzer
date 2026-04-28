# Skin Progress Tracking Module - Implementation Plan

## 1. Overview
We will leverage the existing Computer Vision analysis to track skin health changes over time. By storing each analysis result in the `SkinScan` database, we can build a historical timeline and visualize improvements.

## 2. Core Architecture
The system relies on the existing `SkinScan` model which already captures the necessary data points:
- **Image Evidence**: `image` field.
- **Quantitative Metrics**: `acne_score`, `oiliness_score`, `wrinkle_score`, `hydration_score`.
- **Timeline**: `scan_date`.

## 3. Implementation Steps

### Step 1: Ensure Data Persistence
**Status:** ✅ Existing (`SkinScan` model).
- Every time a user runs an analysis in `analysis_view`, we must ensure a new `SkinScan` record is saved.

### Step 2: Progress Dashboard (Backend)
**Action:** Create `views.progress_view`.
- **Query:** Fetch all `SkinScan` records for the logged-in user, ordered by `scan_date`.
- **Data Serialization:** Convert the query set into JSON-serializable lists for the frontend graph:
    - `dates`: List of scan timestamps.
    - `acne_trend`: List of acne scores.
    - `wrinkle_trend`: List of wrinkle scores.
    - `images`: List of image URLs for the gallery.

### Step 3: Graphical Visualization (Frontend)
**Action:** Create `progress.html` using **Chart.js**.
- **Line Chart**: Plot the metrics over time.
    - X-Axis: Date.
    - Y-Axis: Severity Score (0-100).
- **Interactive**: Hovering over a data point shows the specific scores.
- **Filters**: Buttons for "Last 7 Days" (Weekly) and "Last 30 Days" (Monthly).

### Step 4: Visual Comparison (Computer Vision Results)
**Action:** Implement "Before vs After" Mode.
- **UI**: Side-by-side comparison of two selected scans.
- **Delta Calculation**: Automatically calculate the percentage change.
    - *Example*: "Acne Score reduced by 15% since Jan 1st."
- **CV Validation**: Display the original analyzed images (with bounding boxes if stored, or raw images) to visually prove the improvement.

### Step 5: Insights & Reports
- **Logic**: Simple heuristic analysis.
    - If `current_score < previous_score` (for negative traits like Acne): **"Improvement Detected"**.
    - If `current_score > previous_score`: **"Condition Worsened - Check Routine"**.

## 4. Why this is "Simple"
- **No New Models**: We use the existing database structure.
- **No New CV Training**: We strictly compare the *outputs* of the existing rigorous CV engine.
- **Standard Libraries**: Chart.js handles the complex visualization lifting.
- **Automatic**: The user just scans their face; the tracking happens in the background automatically.
