# Release process

Moonbeam mirrors the files attached to [Moonlight Qt releases](https://github.com/moonlight-stream/moonlight-qt/releases),
with an additional Linux installer bundle, checksums, and build provenance.

| Platform | Candidate / release asset |
| --- | --- |
| Windows x64 and ARM64 | `MoonbeamSetup-VERSION.exe` universal installer; `MoonbeamPortable-x64-VERSION.zip` and `MoonbeamPortable-arm64-VERSION.zip` |
| macOS Intel and Apple Silicon | `Moonbeam-VERSION.dmg` universal app |
| Linux x86_64, glibc 2.35+ | `Moonbeam-VERSION-x86_64.AppImage`; `moonbeam-VERSION-linux-x86_64.tar.gz` with `install.sh` |
| Valve Steam Link device | `Moonbeam-SteamLink-VERSION.zip` |
| Source and verification | `moonbeam-VERSION-source.tar.gz`, `Moonbeam-SHA256SUMS`, `candidate.json` |

Moonlight's Snap, Flatpak, Raspberry Pi, generic ARM/RISC-V Debian, and L4T links
use separate publishing projects and repositories. They are not GitHub release
assets and do not install Moonbeam. Moonbeam does not currently publish these
channels. Do not link an upstream Moonlight package as a Moonbeam download.
Windows/macOS candidates are unsigned; signing/notarization requires the fork's
own certificates and provisioning. Upstream signing credentials are not reused.

## Build one complete candidate

1. Integrate focused changes onto `master` using ordinary branches and direct pushes.
   Preserve upstream notices. Do not force-push or replace existing tags.
2. Set `app/moonbeam-version.txt` to the next unused version, for example
   `6.2.0-moonbeam.5`. Cherry-pick backports with `git cherry-pick -x`.
3. Push that commit to `release/**` (for example `release/6.2-platforms`).
   The **Moonbeam release candidate** workflow builds Linux, Windows x64/ARM64,
   universal macOS, and Steam Link. All builds use the same source commit.
4. Download the final `moonbeam-candidate-COMMIT` artifact from a successful run.
   Intermediate platform and debug-symbol artifacts are for diagnostics.
5. Verify `Moonbeam-SHA256SUMS` and validate these exact packages on target hardware
   before promotion. A successful cross-compile is not hardware validation.

Linux CI builds directly on its Ubuntu 22.04 runner; local immutable-system
builds use the Ubuntu 22.04 Podman container. Both call the same Linux build
script with the same dependencies and packaging.

The Linux builder runs installer and Qt reconnect tests and checks portable
startup. The assembly job requires all eight package/source files, archives the
tracked source with recursive submodules, and generates checksums and provenance.
The source archive includes a source manifest so it can build without `.git`;
local source-archive rebuilds cannot be promoted as verified CI candidates.
If any platform fails, no complete candidate is produced and promotion is blocked.

Artifact versions are `BASE+gCOMMIT` (12 commit digits). Native installer versions
must be numeric: `MAJOR.MINOR.(PATCH * 1000 + REVISION)`, for example
`6.2.0-moonbeam.5` becomes `6.2.5`. This gives MSI upgrades a monotonically
increasing third component; a fourth component would be ignored by MSI.
Revision must be below 1000, major/minor at most 255, and the computed patch at most
65535. Always bump the fork revision before a new release, including backports.
The full fork version is still reported by the client and used in asset names.

## Validate and promote the exact bytes

Install the downloaded packages. On a graphical desktop run `moonbeam selftest`
(or the native executable's `selftest` command) to exercise the selected video
path through three teardown/recreation cycles. Also inspect a real stream for
correct pixels, audio, renderer recreation, and reconnect/cancellation behavior.
Validate the supported target platforms; record hardware, OS, package, and results
in the release validation record. A standalone FFmpeg test is insufficient.
Never interrupt a user's existing game to validate a candidate, and never publish
pairing configs or screenshots containing personal desktop content.

After validation, run **Tag validated Moonbeam release** on `master` with the
successful candidate run ID and `video_validated=true`. This attests that the
candidate packages passed the required hardware and live-stream checks.

Promotion downloads only the final candidate artifact and verifies the workflow,
successful conclusion, branch, commit, run ID, full platform file set, clean source,
version, manifest, and SHA-256 hashes. It creates the new tag and GitHub Release
with the exact candidate bytes and platform download links; it never rebuilds.
Existing tags are rejected. Failed or incomplete candidates stay untagged.

```sh
gh workflow run promote-release.yml --repo Spaceghost/moonbeam --ref master \
  -f run_id=SUCCESSFUL_RUN_ID -f video_validated=true
```

## Local platform builds

Use a recursive clone. Linux: `bash scripts/build-moonbeam-container.sh` with
Podman and slirp4netns installed. Each checkout/worktree gets its own builder;
`MOONBEAM_BUILD_CONTAINER` and `MOONBEAM_BUILD_NETWORK` can override its name
and network mode. Existing builder containers are preserved.
Windows: run `setup-deps.ps1`, then `scripts\build-arch.bat Release` from the
appropriate x64 and ARM64 Qt prompts, then `scripts\generate-bundle.bat Release`.
macOS: `bash scripts/generate-dmg.sh Release` with Qt and `create-dmg` installed.
Steam Link: set `STEAMLINK_SDK_PATH` and run `bash scripts/build-steamlink-app.sh`.
CI configures `MOONBEAM_BUILD_VERSION` and `MOONBEAM_NATIVE_VERSION` centrally with
`scripts/release-version.py`; set these for equivalent local native builds.
All reproducible outputs live in ignored `build/`, `libs/`, and `dist/` directories.
