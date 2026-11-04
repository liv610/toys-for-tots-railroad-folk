# Running renders and builds

These rules took effect on 4 November 2026, after a workflow review. That review found long renders blocking work,
renders repeated for no reason, and one wait that could never finish.

## The rules

1. **Every long job goes through the job runner:**
   ```
   python3 tools/job.py run NAME --cpu [--mem GB] -- COMMAND
   ```
   Anything longer than a minute counts as long. Start the runner from a background shell, so the shell's exit is
   the completion notice. Nothing waits in the foreground for more than 9 minutes:
   `job.py wait NAME --max 540` returns as soon as the job ends, and earlier if it crashes.
2. **No duplicates.** A second job with the same name is refused while the first is running.
3. **At most two CPU-heavy jobs at once**, because the workspace has two cores. A third is refused.
4. **A memory budget of 5.5 GB.** The workspace allows 5,979 MB in total, and the kernel kills the biggest process
   when that is exceeded. That happened on 4 November, when two 6400-wide full-map renders ran together (about 3.2 GB
   each).
   - Full-map renders reserve `--mem 3.5`, so only one runs at a time.
   - Engine tiles reserve the default 1 GB.
   - The viewer build reserves 2 GB.
5. **No rendering code is edited while a job runs.** Run `python3 tools/job.py guard` first: it exits with an error
   while anything is running. The runner also fingerprints all rendering code when a job starts and again when it
   ends, and marks the result "CODE CHANGED" if the two differ. That job's output must not be trusted or cached.
6. **Finished means a `.done` marker.** `.jobs/NAME.done` is written atomically, holding the exit code and end time,
   only when the process has ended. The states are:
   - `running`: the process is alive
   - `done`: exit code 0
   - `failed`: non-zero exit code
   - `crashed`: the process is gone and no marker was written

   A finished render can't be mistaken for an unfinished one, and a dead one can't be mistaken for one still
   running. Never use `pgrep -f` with the job's own command text, which matches itself.
7. **Unchanged outputs don't rebuild.** Tile keys hash the scene elements and the code. When code changes but the
   output provably does not, re-key the cache instead of repainting it (`engine10/cache10.py rekey`). "Provably"
   means one of:
   - an A/B test of every affected tile, as in Phase 1
   - `rekey --verify`, which re-paints a sample of tiles and refuses on any difference

## Commands

```
python3 tools/job.py run NAME [--cpu] [--mem GB] -- CMD   # start (from a background shell)
python3 tools/job.py wait NAME ... [--max S]              # returns when they end; exit 0 ok, 1 failed, 2 still running
python3 tools/job.py status NAME | list | tail NAME [n]
python3 tools/job.py guard                                # before editing rendering code
python3 tools/compare_outputs.py DIR_A DIR_B              # pixel-exact comparison of two output folders
```

Job records live in `usmap/.jobs/`, and the previous run of a name is kept as `.prev`.
