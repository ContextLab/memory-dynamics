#!/usr/bin/env python3
"""
Monitor progress of transform_recalls-llm.py.

Reads the status JSON written by the main script and displays a live
progress bar with ETA, current task, and per-participant breakdown.

Usage:
    python monitor_recalls-llm.py            # update every 2s (default)
    python monitor_recalls-llm.py --interval 5   # update every 5s
"""
import argparse
import json
import shutil
import sys
import time
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path('/home/f0028ph/memory-dynamics')
STATUS_FILE = BASE_DIR / 'scripts' / '.transform_recalls_status.json'
OUTPUT_DIR = BASE_DIR / 'data' / 'processed' / 'participants'


def fmt_duration(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    td = timedelta(seconds=round(seconds))
    total_secs = int(td.total_seconds())
    hours, remainder = divmod(total_secs, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f'{hours}:{minutes:02d}:{secs:02d}'
    return f'{minutes}:{secs:02d}'


def count_completed_files(tasks: list[dict]) -> int:
    """Count tasks whose output files already exist on disk."""
    done = 0
    for t in tasks:
        subid, rectype = t['subid'], t['rectype']
        p_dir = OUTPUT_DIR / subid
        traj = p_dir / f'{rectype}_recall_trajectory.npy'
        wins = p_dir / f'{rectype}_recall_windows.npy'
        if traj.exists() and wins.exists():
            done += 1
    return done


def render(status: dict, term_width: int) -> str:
    """Build the full display string from current status."""
    lines = []

    state = status['state']
    total = status['total']
    completed = status['completed']
    skipped = status['skipped']
    start_time = status.get('start_time')
    update_time = status.get('update_time')
    current = status.get('current')
    stage = status.get('stage', '')
    n_windows = status.get('n_windows')
    tasks = status.get('tasks', [])

    # If we have the task list, do an independent file-based count
    # (more reliable if the status file is slightly stale)
    if tasks:
        file_completed = count_completed_files(tasks)
    else:
        file_completed = completed

    actually_done = max(completed, file_completed)
    embedded = actually_done - skipped

    now = time.time()
    elapsed = now - start_time if start_time else 0

    # Header
    lines.append(f'  State: {state}')
    lines.append(f'  Elapsed: {fmt_duration(elapsed)}')

    # Progress bar
    frac = actually_done / total if total else 0
    bar_width = min(term_width - 30, 60)
    filled = int(bar_width * frac)
    bar = '\u2588' * filled + '\u2591' * (bar_width - filled)
    lines.append(f'  [{bar}] {actually_done}/{total} ({frac:.0%})')

    # Breakdown
    lines.append(f'  Embedded: {embedded}  |  Skipped: {skipped}')

    # ETA (based on non-skipped work done so far)
    remaining = total - actually_done
    if embedded > 0 and remaining > 0:
        # Estimate time per embedded task from elapsed time,
        # but subtract a rough estimate of time spent on skips (negligible)
        secs_per_task = elapsed / embedded
        eta = secs_per_task * remaining
        lines.append(f'  ETA: ~{fmt_duration(eta)}')
    elif remaining == 0:
        lines.append(f'  ETA: done!')
    else:
        lines.append(f'  ETA: estimating...')

    # Current task
    if current:
        detail = f'  Current: {current} — {stage}'
        if n_windows and stage == 'embedding':
            detail += f' ({n_windows} windows)'
        lines.append(detail)

    # Staleness warning
    if update_time and (now - update_time) > 120:
        mins_ago = (now - update_time) / 60
        lines.append(f'  \u26a0  Status file last updated {mins_ago:.0f}m ago')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Monitor recall embedding progress')
    parser.add_argument(
        '--interval', type=float, default=2,
        help='Refresh interval in seconds (default: 2)'
    )
    args = parser.parse_args()

    term_width = shutil.get_terminal_size().columns
    prev_lines = 0

    print('Waiting for status file...' if not STATUS_FILE.exists() else '')

    try:
        while True:
            if not STATUS_FILE.exists():
                time.sleep(args.interval)
                continue

            try:
                status = json.loads(STATUS_FILE.read_text())
            except (json.JSONDecodeError, FileNotFoundError):
                # File being written; retry next tick
                time.sleep(args.interval)
                continue

            # Clear previous output
            if prev_lines:
                sys.stdout.write(f'\033[{prev_lines}A\033[J')

            output = render(status, term_width)
            sys.stdout.write(output + '\n')
            sys.stdout.flush()
            prev_lines = output.count('\n') + 1

            if status.get('state') == 'done':
                print('\nMain script finished.')
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print('\nMonitor stopped.')


if __name__ == '__main__':
    main()
