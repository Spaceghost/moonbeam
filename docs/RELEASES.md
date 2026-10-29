# Release branches, validation, and backports

Work uses ordinary branches and direct pushes. No pull requests are required or
created by this process. `master` receives integration changes. A maintained
`release/6.2` branch receives validated fixes and selected backports.

Pushing `release/**` runs the **Moonbeam release candidate** action. It compiles
the complete portable client, runs installer and reconnect tests, checks portable
startup and SHA-256 hashes, and uploads candidate artifacts. Every build includes
its commit in its binary version and `candidate.json`. Building never creates a tag.

Download a successful candidate run, install that exact tarball on the target
desktop, run `moonbeam selftest`, and check a real 1080p stream, audio, and decoder
recreation. The self-test uses Moonbeam's renderer, hardware decoder, test frame,
and three teardown/recreation cycles. A standalone FFmpeg decode is insufficient.
Do not publish screenshots containing personal desktop content as release assets.

After validation, run **Tag validated Moonbeam release** with the successful
candidate run ID and hardware validation marked complete. Promotion verifies the
workflow, successful conclusion, release branch, source commit, clean checkout,
run ID, and every artifact hash. It publishes those same bytes without rebuilding,
then creates a new version tag. Existing tags are never moved or replaced.

For a backport:

```sh
git switch release/6.2
git pull --ff-only origin release/6.2
git cherry-pick -x <fix-commit>
# Bump app/moonbeam-version.txt to the next Moonbeam patch before promotion.
git push origin release/6.2
```

Validate the new candidate and promote it to a new tag. The `-x` trailer links the
backport to its original commit. Keep fixes on `master` as well, using a normal
merge or a traced cherry-pick as appropriate. A failed build, decoder test, or live
stream check leaves the candidate untagged.
