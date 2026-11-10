# Following Moonlight

Moonbeam follows Moonlight's version series, with clean Moonbeam releases starting
at v6.3.0. Continue rebasing and replaying Moonbeam's work on upstream versions
until upstream implements equivalent behavior. Keep fixes small and attributable;
drop a patch only after its behavior is verified in upstream.

1. Fetch origin and upstream; start a new release branch from fresh origin/master.
2. Record the previous upstream base from `upstream.json`. Rebase the fork's
   focused runtime changes onto the selected upstream version in an isolated
   branch/worktree. Preserve packaging and Moonbeam-specific integration commits.
3. Review `git range-diff OLD_BASE..OLD_FORK NEW_BASE..REPLAYED_FORK`; resolve
   upstream equivalents deliberately. Update `upstream.json` and release notes.
4. Preserve published master ancestry before integrating with an ordinary push.
   Review any history-preserving integration merge against both trees; never
   force-push published branches or move tags. Merge newer master work if needed.
5. Let CI rebuild all platforms. Compare the complete source/package manifests,
   run required hardware/live-stream checks, and promote the exact candidate bytes.

Upstream's application protocol version remains in `app/version.txt`; Moonbeam's
public release version lives in `app/moonbeam-version.txt`. They may differ while
the fork carries features ahead of upstream. Published release metadata records
the actual source commit, independent of the clean public version number.
