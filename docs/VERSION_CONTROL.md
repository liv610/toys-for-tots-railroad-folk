# Version control

The project is a Git repository, set up on 4 November 2026. Git tracks:
- source code and page sources
- small inputs: coastlines, masks, reference images, and `usmap/out4/scene4.json`, which pass 5 reads
- documentation, and the JSON results of tests

Renders, viewer bundles and caches are not tracked; the tracked code rebuilds them (see `.gitignore`). Approved
renders are preserved separately, as described below. The older `usmap/checkpoints/` folders stay on disk, untouched.

## Branches

| Branch | What it holds | Rule |
|---|---|---|
| `main` | The approved map: the code that renders the published pass 5 map, plus changes proven not to alter its output. | Only verified work is merged. Every commit renders the published map pixel for pixel. |
| `develop` | `main` plus the three topic branches below. Day-to-day work happens here. | May contain unapproved changes. |
| `experiment/rendering` | Engine 10 (tiled, position-exact rendering, the edge presets, the tile cache with rekey), the lab8 and lab9 experiments, and the engine checks. | Never changes `main`'s output. |
| `toytown/hires` | High-resolution Toy Town: the storefront levels, toy library and figure study, and the pending, unapproved sign-fade fix in `tft7.py`. | Built on `experiment/rendering`. |
| `viewer/dev` | The prototype viewer with the 2× layer (source, builder, browser tests). | Built on `experiment/rendering`. |

## Tags (approved milestones)

Each tag's source tree was rebuilt from its checkpoint folder and re-rendered on 4 November 2026. The re-render
matched the checkpoint's saved images pixel for pixel; only leftover animation files from earlier runs differed.

| Tag | What it is |
|---|---|
| `pass4-approved` | Pass 4, approved baseline (3 Nov 2026) |
| `pass5-v13` | Pass 5 before the Florida work: Northwest, double butte, desert, grand station, moving landscape (page version 13) |
| `pass5-v15` | Pass 5 after Florida and the Southeast (page versions 14–15) |
| `pass5-v19` | Ocean margin, steamer on the Gulf, Toys for Tots branding. This is the published map (page versions 18–19). |
| `fastbrush-verified` | `main` with the band-limited brush and the station fix. It renders the published map exactly, about 2.6× faster. |

## Restoring an approved version

To look at it or render it without touching your work:

```
git worktree add ../tft-pass5-v19 pass5-v19      # a separate folder with that version's code
cd ../tft-pass5-v19/usmap && PYTHONPATH=../folk2:../styles2:. python3 usmap5.py --width 6400
git worktree remove ../tft-pass5-v19             # when finished
```

To make `main` match a tag again, for example after a bad merge:

```
git switch main
git revert --no-edit <bad-commit>                # undoes one commit and keeps the history
```

To bring back a single file from a tag:

```
git restore --source pass5-v19 -- usmap/tft7.py
```

Never `git reset --hard` or force-push `main`. Revert instead, so the history stays complete.

## Preserving approved renders without filling Git

The renders are deterministic: the same code renders the same pixels, as the tags above show. So the code tag is the
primary record, and the images are a convenience. For each approved milestone:

1. **A release bundle.** Zip the viewer bundle (`viewer5/`, about 32 MB), the still images and the scene file into
   `usmap/approved/<tag>.zip`. That folder is ignored by Git.
2. **A pixel manifest in Git.** `approved/<tag>.sha256` holds a SHA-256 of every approved image's decoded pixels
   (a few KB). Anyone can then prove a render matches the approved one, without the images being in Git.
3. **Off-machine copies.** Upload the bundle to the matching GitHub Release once a remote exists, because release
   files are not part of the repository's history. Keep the published claude.ai page versions as well.

This keeps the repository around 20 MB while every approved picture stays exactly reproducible and comparable.
Git LFS would also work, but it adds a server-side dependency for files that can be regenerated anyway.

## Day to day

```
git switch develop
# ... edit, render through tools/job.py, verify ...
git add -p && git commit -m "Toy Town: <what changed and how it was checked>"
git switch main && git merge --no-ff <topic>     # only after verification (see tools/WORKFLOW.md)
git tag -a pass5-v20 -m "..."                    # when a new version is approved
```
