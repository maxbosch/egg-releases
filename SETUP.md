# Setting up Egg — the agent contract

Everything Egg needs to be fully working, written for a coding agent (or a
human with a terminal). The in-app path is **Set Up Egg…** (menu bar egg →
Set Up Egg…, or the button on the empty library); this file is the same
contract for automation. The checklist window's **Copy Agent Instructions**
button emits a condensed version of this document with the machine's actual
paths filled in.

Nothing here is required before using Egg — drop an image and it works.
Each item unlocks one capability.

## Verification first

Egg verifies setup itself:

```sh
/Applications/Egg.app/Contents/MacOS/Egg --doctor
```

Prints a JSON report and exits 0 when nothing is left to do, 1 otherwise.
Every check has a stable `id`, a `state` (`ready` / `action_required` /
`off`), a `detail`, and a `remedy`. `off` means "not enabled" and is fine.
Checks with `"human_only": true` need a person at the machine — list them
for your user instead of retrying.

Flags: `--human` for text output, `--test` to also spend one API call
verifying the Anthropic key, `--probe-automation` to probe the Messages
Automation grant (raises the system prompt on first probe).

One caveat the doctor states itself: Full Disk Access is granted per app, so
a doctor run from a terminal cannot observe Egg's own grant. The app records
its view on every launch; the doctor substitutes it and notes when it did.

## Where configuration lives

| What | Where | How to set |
|---|---|---|
| Anthropic API key | login Keychain, service `com.feedegg.egg`, account `anthropic` | `security add-generic-password -U -s com.feedegg.egg -a anthropic -w '<key>'` |
| Everything else | `com.feedegg.egg` defaults domain | `defaults write com.feedegg.egg <key> <value>` |
| Library folder | `defaults read com.feedegg.egg LibraryPath`, else `~/Library/Application Support/Egg/Library` | set from the app (Settings → Library) |
| X OAuth tokens | `<library>/.tokens.json` | written by `scripts/fetch_bookmarks.py` |

Restart Egg after writing settings so every surface picks them up:
`osascript -e 'quit app "Egg"'; sleep 2; open -a Egg`

## The checks, in doctor order

### `anthropic-key`
One key powers scanning, search filters, Ideas, the taste skill, and is the
metered fallback for sandbox agents. Keychain command above; the key comes
from console.anthropic.com and should never be echoed or committed anywhere.
The app also accepts `ANTHROPIC_API_KEY` from the environment, but a GUI app
launched from Finder inherits no shell environment — prefer the Keychain.

### `agent-token`
Optional. `claude setup-token` in a terminal, then
`defaults write com.feedegg.egg agentOAuthToken '<sk-ant-oat…>'`.
With it, sandbox edits ride the Claude subscription; without it they bill
the API key. The value must start with `sk-ant-oat` — an API key pasted
here is the classic mistake and the doctor flags it.

### `messages` — phone capture
Three parts, two of them human-only:

1. **HUMAN**: add a second address to the Apple ID — Messages → Settings →
   iMessage → Send & Receive. Egg watches only this address.
2. `defaults write com.feedegg.egg messagesAlias '<that address>'`
3. **HUMAN**: grant Egg Full Disk Access (System Settings → Privacy &
   Security → Full Disk Access), then relaunch Egg. There is no API and no
   prompt for this grant; denied, chat.db reads as empty forever.

Optional: `messagesReplyEnabled` (bool) makes Egg answer in the thread —
it additionally needs the Automation grant, whose first probe is the prompt.

### `sandboxes`
Off by default (`heyoSandboxesEnabled`). Local mode (`heyoUseLocalVM`,
default true) needs a heyvm daemon on the Mac; cloud mode needs `heyoAPIKey`
(or `HEYO_API_KEY`). The doctor health-checks the local daemon the same way
a sandbox boot would.

### `scanning`
Fills search and the sidebar filters. Two equivalent paths:
- In-app: **Scan Library…** in the library sidebar (uses the Keychain key).
- Terminal: `ANTHROPIC_API_KEY=… python3 scan.py` from `scripts/` (in this
  repo or the egg-releases clone), against the same library folder.
Re-runs only pick up what's new. ~1¢ per hundred images — tell your user
before running it.

### `x-import`
Optional. Needs the user's own free X app — Egg ships no client id of its
own, because X counts reads per project and a shared one would pool every
user's imports into a single quota.

1. **HUMAN**: create an app at console.x.com → OAuth 2.0, type **Native App**,
   callback `http://127.0.0.1:8765/callback`, scopes
   `tweet.read users.read bookmark.read offline.access`.
2. `defaults write com.feedegg.egg xClientID '<client id>'`
3. **HUMAN**: authorize. In the app that's Set Up Egg → X bookmarks →
   Connect X; from a terminal it's `python3 scripts/fetch_bookmarks.py`
   (which now reads the same `xClientID` default, so no env var is needed).
   Either way X's consent screen opens in a browser and a person has to
   approve it.

Tokens land in `<library>/.tokens.json`, are written 0600, and refresh
locally. The app and the script share that file and the same item ids, so
you can connect in one and import from the other.

Importing afterwards: **Import Bookmarks** in the same window, or
`python3 scripts/fetch_bookmarks.py` again. Both are safe to re-run — items
already in the library keep their scans, tags and notes, and deleted items
are not resurrected.

No X app at all? The same window has an **experimental** reader that opens
your bookmarks page in Egg, scrolls it, and imports what it can see — no
client id and no API quota. It depends on X's page markup, so treat it as a
fallback rather than the supported path.

## Importing content

`skills/egg-ingest/SKILL.md` is the write contract for the library folder —
load it before writing items. Any folder of images, an export, or a URL list
can become items; anything that writes valid items is an importer.
