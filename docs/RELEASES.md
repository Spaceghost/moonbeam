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
   `6.3.0`. Cherry-pick backports with `git cherry-pick -x`.
3. Push that commit to `release/**` (for example `release/6.3.0`).
   The **Moonbeam release candidate** workflow builds Linux, Windows x64/ARM64,
   universal macOS, and Steam Link. All builds use the same source commit.
4. Download the final `moonbeam-candidate-COMMIT` artifact from a successful run.
   Intermediate platform and debug-symbol artifacts are for diagnostics.
5. Verify `Moonbeam-SHA256SUMS` and validate these exact packages on target hardware
   before promotion. A successful cross-compile is not hardware validation.

Linux CI uses the existing isolated, ephemeral Fedora Ubuntu software pool when
`MOONBEAM_SELF_HOSTED=true` is enabled on this repository. Admission requires
both the owner actor and triggering actor; fork/other-actor work uses GitHub.
The pool's CPU, memory, network, nesting and cleanup protections remain in force.
Windows and macOS use GitHub-hosted runners because no matching local platforms
are admitted. Lightweight routing/version jobs also run on GitHub.

The admitted self-hosted pool runs native Ubuntu 24.04 for installer/release/Qt
tests, Steam Link cross-builds and artifact assembly. The portable Linux build
explicitly uses GitHub Ubuntu 22.04 to retain its glibc 2.35 compatibility baseline.
No nested containers, userspace filesystem emulation or extra worker privileges
are needed. `scripts/ci-ubuntu.sh` changes only official Ubuntu archive transport
to HTTPS for the pool's network policy, retaining suites and signing keys.
Downloads are cached, not release binaries. Local immutable-system builds
continue to use the existing Ubuntu 22.04 Podman builder.

Every master/release push rebuilds all platforms. A weekly scheduled run catches
build-environment drift. Both checks and candidate workflows accept `runner`:
`auto`, `self-hosted`, or `github`. A busy self-hosted pool queues work; the
`github` override starts an independent hosted build when local capacity is
unavailable. No automatic publication or hardware attestation occurs.

```sh
gh workflow run release-candidate.yml --repo Spaceghost/moonbeam --ref release/6.3.0 -f runner=auto
# Explicit hosted rebuild when the local pool cannot serve work:
gh workflow run release-candidate.yml --repo Spaceghost/moonbeam --ref release/6.3.0 -f runner=github
```

The Linux builder runs installer and Qt reconnect tests and checks portable
startup. The assembly job requires all eight package/source files, archives the
tracked source with recursive submodules, and generates checksums and provenance.
The source archive includes a source manifest so it can build without `.git`;
local source-archive rebuilds cannot be promoted as verified CI candidates.
If any platform fails, no complete candidate is produced and promotion is blocked.

Public versions, native versions and asset filenames use clean `MAJOR.MINOR.PATCH`,
starting at **6.3.0**. Feature releases advance the minor series; reserve patch
versions for focused maintenance. Do not add `-moonbeam.N`, `+gCOMMIT`, or candidate
suffixes. MSI supports major/minor up to 255 and patch up to 65535. Provenance is
in `candidate.json` and `SOURCE_MANIFEST.json`, bound to the successful run and
exact commit. Old published versions and tags remain immutable. Different bytes
cannot silently replace an installed bundle under the same version.

Follow [upstream replay](UPSTREAM.md) for future Moonlight rebases.

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
