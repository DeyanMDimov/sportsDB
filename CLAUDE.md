# Project instructions

## Git workflow

- `main` is the local dev branch, not a protected release branch. When a change is
  done, commit it and merge it into the local `main` (the checkout at the repo root)
  without opening a pull request. Don't push unless asked.
- The `main` checkout often has uncommitted work in progress. Never stash, reset or
  overwrite it; if the merge would touch those files, stop and ask.
