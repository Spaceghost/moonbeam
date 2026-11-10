# Mirroring Moonlight releases

Moonbeam mirrors the **exact published Moonlight release tags and version numbers**,
with Moonbeam changes replayed on top. Moonlight v6.2.0 means Moonbeam v6.2.0;
Moonbeam does not invent v6.3.0 until Moonlight releases v6.3.0. There is no
independent feature/maintenance numbering and no fork or Git suffix in versions.

1. Fetch fresh origin/master and upstream release tags into a separate namespace:
   `git fetch upstream 'refs/tags/*:refs/moonlight/releases/*'`. Select an actual
   published stable Moonlight tag, such as `refs/moonlight/releases/v6.2.0`.
   Keep upstream tag refs separate from Moonbeam's identically named public tags.
   Start an isolated release branch/worktree from fresh origin/master.
2. Rebase and replay the focused Moonbeam changes onto that upstream version.
   Drop a patch only after upstream behavior is verified equivalent. Preserve
   deliberate upstream backports and record their integration revision separately.
3. Review `git range-diff OLD_BASE..OLD_FORK NEW_BASE..REPLAYED_FORK` and the full
   tree difference. Resolve conflicts without discarding Moonbeam features.
4. Preserve published master ancestry before ordinary integration; never
   force-push or move published tags. Merge newer master work when needed.
5. Set `app/moonbeam-version.txt` equal to upstream's `app/version.txt` and the
   selected tag without its `v`. Update `upstream.json` with the release tag,
   release commit and version; write matching release notes. Let CI verify the
   actual upstream release, rebuild all platforms, and promote the exact bytes.

Keep following upstream this way until Moonlight provides equivalent behavior.
The current v6.2.0 counterpart retains selected upstream fixes through4113dd26 in
addition to Moonbeam's improvements; the released upstream base is de2467e4.
Those additional fixes do not justify a different public version number.
