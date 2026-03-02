"""
Persistence filtering for acceleration detections.

Retains only tiles with >= N consecutive months above threshold.
"""

from typing import List, Tuple


def find_consecutive_runs(indices: List[int], min_length: int) -> List[Tuple[int, int]]:
    """
    Find runs of consecutive integers with length >= min_length.

    Args:
        indices: Sorted list of integer indices
        min_length: Minimum run length

    Returns:
        List of (start_idx, end_idx) tuples for valid runs

    Example:
        >>> find_consecutive_runs([1, 2, 3, 5, 6, 10, 11, 12, 13], min_length=3)
        [(1, 3), (10, 13)]
    """
    if not indices:
        return []

    runs = []
    current_run = [indices[0]]

    for idx in indices[1:]:
        if idx == current_run[-1] + 1:
            current_run.append(idx)
        else:
            if len(current_run) >= min_length:
                runs.append((current_run[0], current_run[-1]))
            current_run = [idx]

    # Check final run
    if len(current_run) >= min_length:
        runs.append((current_run[0], current_run[-1]))

    return runs


def filter_by_persistence(
    flagged_tiles: dict, min_consecutive: int = 2
) -> dict:
    """
    Filter tiles to retain only those with >= N consecutive flagged months.

    Args:
        flagged_tiles: {
            tile_id: {
                "flagged_months": [month_indices],
                "max_score": float
            }
        }
        min_consecutive: Minimum consecutive months (default 2 per spec)

    Returns:
        {
            tile_id: {
                "persistent_spans": [(start_idx, end_idx), ...],
                "persistence_count": int,  # Max span length
                "max_score": float
            }
        }
    """
    persistent = {}

    for tile_id, data in flagged_tiles.items():
        flagged_months = data["flagged_months"]

        # Find consecutive runs
        spans = find_consecutive_runs(flagged_months, min_length=min_consecutive)

        if spans:
            # Compute max span length
            persistence_count = max((end - start + 1) for start, end in spans)

            persistent[tile_id] = {
                "persistent_spans": spans,
                "persistence_count": persistence_count,
                "max_score": data["max_score"],
            }

    return persistent
