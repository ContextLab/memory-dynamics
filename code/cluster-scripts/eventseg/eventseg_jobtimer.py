"""
CLI utility to monitor event segmentation SLURM jobs.

`eventseg_submit.py` submits many jobs, each writing stdout to `<job_name>.out`
in `eventseg_config.LOG_DIR`. `eventseg_cruncher.py` prints progress as `XX/YY`
each iteration. This script parses those logs and displays a live progress bar
for the aggregate progress across all jobs, with an optional per-job view.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


# Ensure we can import sibling `eventseg_config.py` when executed from anywhere.
THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import eventseg_config as config  # noqa: E402


PROGRESS_RE = re.compile(r"(?P<done>\d+)\s*/\s*(?P<total>\d+)")


@dataclass(frozen=True)
class JobInfo:
    name: str
    stdout_path: Path
    script_path: Optional[Path] = None
    total_from_script: Optional[int] = None


@dataclass(frozen=True)
class JobProgress:
    done: int
    total: Optional[int]
    # `True` if the log suggests the job is finished (done==total) *and* total known.
    is_complete: bool


def _read_tail_bytes(path: Path, max_bytes: int) -> bytes:
    """
    Read up to `max_bytes` from the end of a file.
    Returns b"" if file doesn't exist or can't be read.
    """
    try:
        with path.open("rb") as f:
            try:
                f.seek(0, 2)
                size = f.tell()
                f.seek(max(0, size - max_bytes), 0)
            except OSError:
                # Some filesystems may not support seek well; fall back.
                pass
            return f.read()
    except OSError:
        return b""


def _parse_progress_from_text(text: str) -> Optional[tuple[int, int]]:
    """
    Return (done, total) using the *last* occurrence of `XX/YY` in `text`.
    """
    matches = list(PROGRESS_RE.finditer(text))
    if not matches:
        return None
    m = matches[-1]
    done = int(m.group("done"))
    total = int(m.group("total"))
    return done, total


def read_job_progress(stdout_path: Path, tail_bytes: int = 32_768) -> JobProgress:
    """
    Parse the latest progress `XX/YY` from a job stdout file.
    """
    data = _read_tail_bytes(stdout_path, max_bytes=tail_bytes)
    if not data:
        return JobProgress(done=0, total=None, is_complete=False)

    # Be forgiving of encoding issues.
    text = data.decode("utf-8", errors="replace")
    parsed = _parse_progress_from_text(text)
    if parsed is None:
        return JobProgress(done=0, total=None, is_complete=False)

    done, total = parsed
    done = max(0, done)
    total = max(0, total)
    is_complete = bool(total) and done >= total
    return JobProgress(done=done, total=total if total > 0 else None, is_complete=is_complete)


def _parse_total_iters_from_script(script_text: str) -> Optional[int]:
    """
    Try to infer number of iterations from the cruncher args in the job script.

    We look for a line like:
      python .../eventseg_cruncher.py <PARTICIPANT> <RECTYPE> MIN_K MAX_K N
    and compute (MAX_K - MIN_K + 1).
    """
    # This regex is intentionally lenient with paths and whitespace.
    m = re.search(
        r"python\s+.*eventseg_cruncher\.py\s+\S+\s+\S+\s+(?P<min_k>\d+)\s+(?P<max_k>\d+)\s+\d+",
        script_text,
    )
    if not m:
        return None
    min_k = int(m.group("min_k"))
    max_k = int(m.group("max_k"))
    if max_k < min_k:
        return None
    return (max_k - min_k) + 1


def discover_jobs(
    script_dir: Path,
    log_dir: Path,
    script_glob: str = "eventseg_*.sh",
) -> list[JobInfo]:
    """
    Discover expected jobs based on generated SLURM job scripts.

    If no scripts are found, fall back to discovering jobs from `.out` logs in `log_dir`.
    """
    jobs: list[JobInfo] = []
    script_paths = sorted(script_dir.glob(script_glob))
    for script_path in script_paths:
        name = script_path.stem
        stdout_path = log_dir.joinpath(f"{name}.out")
        total_from_script: Optional[int] = None
        try:
            script_text = script_path.read_text()
            total_from_script = _parse_total_iters_from_script(script_text)
        except OSError:
            pass
        jobs.append(
            JobInfo(
                name=name,
                stdout_path=stdout_path,
                script_path=script_path,
                total_from_script=total_from_script,
            )
        )

    if jobs:
        return jobs

    # Fallback: discover directly from log files.
    for out_path in sorted(log_dir.glob("eventseg_*.out")):
        jobs.append(JobInfo(name=out_path.stem, stdout_path=out_path, script_path=None, total_from_script=None))

    return jobs


def _format_job_label(job: JobInfo) -> str:
    # Try to keep labels compact.
    return job.name.replace("eventseg_", "")


def _clamp_completed(done: int, total: Optional[int]) -> int:
    if total is None:
        return done
    return min(done, total)


def _compute_overall(jobs: Iterable[JobInfo], progresses: dict[str, JobProgress]) -> tuple[int, int]:
    """
    Return (overall_done, overall_total) using best available totals.
    Jobs without known totals are ignored in total, but their `done` is included
    only when a total is known (to keep the main bar meaningful).
    """
    overall_done = 0
    overall_total = 0
    for job in jobs:
        jp = progresses[job.name]
        total = jp.total if jp.total is not None else job.total_from_script
        if total is None or total <= 0:
            continue
        overall_total += total
        overall_done += _clamp_completed(jp.done, total)
    return overall_done, overall_total


def run_rich_ui(
    jobs: list[JobInfo],
    refresh_s: float,
    per_job: bool,
    once: bool,
    tail_bytes: int,
    max_job_bars: int,
    sort: str,
    grid_cols: int,
) -> int:
    from rich.console import Console
    from rich.console import Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    console = Console()

    if not jobs:
        console.print(
            Panel.fit(
                f"[bold]No jobs found.[/bold]\n\nSearched for scripts in:\n  {config.SCRIPT_DIR}\n\n"
                f"Tip: pass --script-dir/--log-dir if your paths differ.",
                title="eventseg_jobtimer",
            )
        )
        return 2

    def log_mtime(job: JobInfo) -> float:
        try:
            return job.stdout_path.stat().st_mtime
        except OSError:
            return 0.0

    def choose_grid_cols(term_width: int) -> int:
        """
        Pick a reasonable number of per-job columns given terminal width.
        Tuned for Rich progress columns: label + bar + percent + M/N.
        """
        if grid_cols and grid_cols > 0:
            return grid_cols
        # Auto mode.
        if term_width >= 190:
            return 3
        if term_width >= 130:
            return 2
        return 1

    overall_progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        BarColumn(bar_width=None),
        TaskProgressColumn(show_speed=False),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        expand=True,
    )

    overall_task = overall_progress.add_task("Overall", total=1)

    def build_summary_table(progresses: dict[str, JobProgress]) -> Table:
        completed = sum(1 for j in jobs if progresses[j.name].is_complete)
        with_total = sum(
            1 for j in jobs if (progresses[j.name].total is not None or j.total_from_script is not None)
        )
        table = Table.grid(expand=True)
        table.add_column(justify="left")
        table.add_column(justify="right")
        table.add_row(
            "[bold]Jobs[/bold]",
            f"{completed}/{len(jobs)} complete  •  {with_total}/{len(jobs)} have totals",
        )
        table.add_row("[bold]Scripts[/bold]", str(jobs[0].script_path.parent if jobs[0].script_path else "—"))
        table.add_row("[bold]Logs[/bold]", str(jobs[0].stdout_path.parent))
        return table

    def render(progresses: dict[str, JobProgress]):
        summary = build_summary_table(progresses)

        if not per_job:
            # In "normal" mode we still want to show the overall progress bar.
            grid = Table.grid(expand=True)
            grid.add_row(summary)
            grid.add_row(overall_progress)
            return Panel(grid, title="eventseg_jobtimer", border_style="cyan")

        # Filter out 100%-finished jobs from the per-job list.
        active_jobs = []
        for job in jobs:
            jp = progresses[job.name]
            total = jp.total if jp.total is not None else job.total_from_script
            if total is not None and total > 0 and jp.done >= total:
                continue
            active_jobs.append(job)

        if sort == "recent":
            active_jobs = sorted(active_jobs, key=lambda j: (-log_mtime(j), j.name))
        elif sort == "name":
            active_jobs = sorted(active_jobs, key=lambda j: j.name)
        elif sort == "remaining":
            def remaining(job: JobInfo) -> tuple[int, str]:
                jp = progresses[job.name]
                total = jp.total if jp.total is not None else job.total_from_script
                if total is None:
                    # Unknown totals last.
                    return (10**9, job.name)
                return (max(0, total - _clamp_completed(jp.done, total)), job.name)

            active_jobs = sorted(active_jobs, key=remaining)
        else:
            raise ValueError(f"Unknown sort mode: {sort}")

        if max_job_bars > 0:
            shown = active_jobs[:max_job_bars]
        else:
            shown = active_jobs

        # Render per-job progress bars in a grid (multiple columns).
        n_cols = min(max(1, choose_grid_cols(console.size.width)), max(1, len(shown)))
        # Distribute jobs into columns, top-to-bottom.
        col_jobs: list[list[JobInfo]] = [[] for _ in range(n_cols)]
        for idx, job in enumerate(shown):
            col_jobs[idx % n_cols].append(job)

        per_job_grid = Table.grid(expand=True)
        for _ in range(n_cols):
            per_job_grid.add_column(ratio=1)

        col_renderables = []
        for jobs_in_col in col_jobs:
            prog = Progress(
                TextColumn("{task.description}"),
                BarColumn(bar_width=None),
                TaskProgressColumn(show_speed=False),
                MofNCompleteColumn(),
                expand=True,
            )
            for job in jobs_in_col:
                jp = progresses[job.name]
                total = jp.total if jp.total is not None else job.total_from_script
                task_total = total if (total is not None and total > 0) else 1
                done = _clamp_completed(jp.done, total) if total else 0
                desc = _format_job_label(job)
                if total is None:
                    desc = f"{desc}  [dim](progress: {jp.done}/?)[/dim]"
                prog.add_task(desc, total=task_total, completed=done)
            col_renderables.append(prog)

        per_job_grid.add_row(*col_renderables)

        more_note: Optional[str] = None
        if len(active_jobs) > len(shown):
            more_note = f"[dim]…and {len(active_jobs) - len(shown)} more active jobs (use --max-job-bars to adjust)[/dim]"
        elif len(active_jobs) == 0:
            more_note = "[dim]No active (incomplete) jobs to display.[/dim]"

        items = [summary, overall_progress, per_job_grid]
        if more_note:
            items.append(more_note)
        return Panel(Group(*items), title="eventseg_jobtimer", border_style="cyan")

    def refresh_once() -> dict[str, JobProgress]:
        progresses: dict[str, JobProgress] = {}
        for job in jobs:
            jp = read_job_progress(job.stdout_path, tail_bytes=tail_bytes)
            # If we know the job's total from script, keep is_complete in sync.
            total = jp.total if jp.total is not None else job.total_from_script
            is_complete = bool(total) and jp.done >= (total or 0)
            progresses[job.name] = JobProgress(done=jp.done, total=jp.total, is_complete=is_complete)
        overall_done, overall_total = _compute_overall(jobs, progresses)
        overall_progress.update(overall_task, total=max(1, overall_total), completed=overall_done)
        return progresses

    progresses = refresh_once()
    with Live(render(progresses), console=console, refresh_per_second=max(1, int(1 / max(refresh_s, 1e-6)))) as live:
        if once:
            return 0
        try:
            while True:
                progresses = refresh_once()
                live.update(render(progresses))
                if all(progresses[j.name].is_complete for j in jobs if (progresses[j.name].total or j.total_from_script)):
                    # We only auto-exit when every job with a known total is complete.
                    break
                time.sleep(refresh_s)
        except KeyboardInterrupt:
            return 130
    return 0


def run_basic_ui(
    jobs: list[JobInfo],
    refresh_s: float,
    once: bool,
    tail_bytes: int,
) -> int:
    """
    Minimal fallback UI (single line), no external deps.
    """
    if not jobs:
        print("No jobs found. Try passing --script-dir and --log-dir.", file=sys.stderr)
        return 2

    def snapshot():
        progresses: dict[str, JobProgress] = {}
        for job in jobs:
            progresses[job.name] = read_job_progress(job.stdout_path, tail_bytes=tail_bytes)
        overall_done, overall_total = _compute_overall(jobs, progresses)
        completed = sum(1 for j in jobs if progresses[j.name].is_complete)
        return overall_done, overall_total, completed, len(jobs)

    def bar(done: int, total: int, width: int = 30) -> str:
        if total <= 0:
            return "[" + ("?" * width) + "]"
        frac = max(0.0, min(1.0, done / total))
        n = int(round(frac * width))
        return "[" + ("#" * n) + ("-" * (width - n)) + "]"

    if once:
        d, t, c, n = snapshot()
        if t > 0:
            print(f"{bar(d, t)}  {d}/{t}  ({100*d/t:5.1f}%)   jobs: {c}/{n} complete")
        else:
            print(f"{bar(0, 0)}  {d}/?   jobs: {c}/{n} complete")
        return 0

    try:
        while True:
            d, t, c, n = snapshot()
            if t > 0:
                line = f"{bar(d, t)}  {d}/{t}  ({100*d/t:5.1f}%)   jobs: {c}/{n} complete"
            else:
                line = f"{bar(0, 0)}  {d}/?   jobs: {c}/{n} complete"
            print("\r" + line + " " * 10, end="", flush=True)
            time.sleep(refresh_s)
    except KeyboardInterrupt:
        print()
        return 130


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="eventseg_jobtimer.py",
        description="Live progress monitoring for eventseg SLURM jobs (parses XX/YY from stdout logs).",
    )
    p.add_argument(
        "--script-dir",
        type=Path,
        default=config.SCRIPT_DIR,
        help="Directory containing generated job scripts (default: eventseg_config.SCRIPT_DIR).",
    )
    p.add_argument(
        "--log-dir",
        type=Path,
        default=config.LOG_DIR,
        help="Directory containing job stdout logs (default: eventseg_config.LOG_DIR).",
    )
    p.add_argument(
        "--script-glob",
        type=str,
        default="eventseg_*.sh",
        help="Glob pattern for job scripts to include (default: eventseg_*.sh).",
    )
    p.add_argument(
        "--refresh",
        type=float,
        default=1.0,
        help="Refresh interval in seconds (default: 1.0).",
    )
    p.add_argument(
        "--tail-bytes",
        type=int,
        default=32_768,
        help="How many bytes to read from the end of each .out file (default: 32768).",
    )
    p.add_argument(
        "--per-job",
        action="store_true",
        help="Show per-job progress bars in addition to the overall bar.",
    )
    p.add_argument(
        "--max-job-bars",
        type=int,
        default=60,
        help="Maximum per-job bars to display when --per-job is set (default: 60, 0 means unlimited).",
    )
    p.add_argument(
        "--grid-cols",
        type=int,
        default=0,
        help="Per-job grid columns in --per-job mode (0 = auto based on terminal width).",
    )
    p.add_argument(
        "--sort",
        type=str,
        choices=("recent", "name", "remaining"),
        default="recent",
        help="Order per-job bars by log recency, name, or remaining work (default: recent).",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Print a single snapshot and exit (no live updating).",
    )
    p.add_argument(
        "--no-rich",
        action="store_true",
        help="Disable rich UI even if installed (use basic fallback).",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    jobs = discover_jobs(args.script_dir, args.log_dir, script_glob=args.script_glob)

    use_rich = not args.no_rich
    if use_rich:
        try:
            import rich  # noqa: F401
        except Exception:
            use_rich = False

    if use_rich:
        return run_rich_ui(
            jobs=jobs,
            refresh_s=max(0.1, float(args.refresh)),
            per_job=bool(args.per_job),
            once=bool(args.once),
            tail_bytes=int(args.tail_bytes),
            max_job_bars=int(args.max_job_bars),
            sort=str(args.sort),
            grid_cols=int(args.grid_cols),
        )
    return run_basic_ui(
        jobs=jobs,
        refresh_s=max(0.1, float(args.refresh)),
        once=bool(args.once),
        tail_bytes=int(args.tail_bytes),
    )


if __name__ == "__main__":
    raise SystemExit(main())
