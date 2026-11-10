# Contributing to Moonbeam

Moonbeam is a GPL-3.0-or-later fork of Moonlight Qt. Preserve upstream copyright,
license notices, and attribution. Keep protocol and platform fixes easy to compare
with upstream; retain upstream project and dependency filenames where practical.

Use a branch, make a focused change, and run the relevant checks. Maintainers
integrate with ordinary direct pushes to `master`; pull requests are not required.
Never force-push or move a published release tag.

```sh
python3 tests/test_ci_runner.py
python3 tests/test_installer.py
python3 tests/test_release_promotion.py
python3 tests/test_release_artifacts.py
```

GitHub Actions runs reconnect and per-game profile tests with Qt. On Linux,
`bash scripts/build-moonbeam-container.sh` builds portable packages and runs these
Qt tests in an Ubuntu 22.04 Podman container. Build output belongs in `build/` and
`dist/`; neither is committed. See [releases](docs/RELEASES.md) for the full
platform matrix, versioning, validation, and promotion process.

Report fork-specific problems in the Moonbeam issue tracker. Include the full
version and package name, reproduction steps, and relevant reviewed logs. Do not
commit pairing keys, host configuration, private desktop recordings, or credentials.

Follow [the upstream replay policy](docs/UPSTREAM.md) when taking new Moonlight versions.
