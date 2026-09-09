# DIESE Screen View

Wall displays for The Australian Ballet that re-draw DIESE schedule reports
so they can be read from across a room.

DIESE's own screen report pins every booking to the hour it starts, so a
studio booked from 11:45 to 18:30 appears as one small block at 11:00 and
the rest of the afternoon looks free. This redraws the same data with
blocks sized by their real duration, a marker on the current time, and
type large enough to read at distance.

---

## How it works

One Render web service does two jobs:

| Path | What it does |
| --- | --- |
| `/` | Serves `board.html`, the display itself |
| `/schedule` | Fetches a DIESE report server-side and returns it |
| `/health` | Returns `ok` — useful for checking the service is awake |

The page and its data come from the same origin, so the browser never
applies CORS rules. That matters: DIESE does not send CORS headers and
IT4Culture declined to add them. Fetching server-side sidesteps the
question entirely.

```
TV / browser  ──►  Render service  ──►  audocuments.diesesoftware.com
                   (board.html)          (the 903 report)
```

## Files

| File | Purpose |
| --- | --- |
| `diese_proxy.py` | The Flask app. Serves the page, proxies the reports. |
| `board.html` | The display. One file serves every board. |
| `requirements.txt` | flask, flask-cors, requests, gunicorn |

All three sit together in the repository root. `diese_proxy.py` looks for
`board.html` next to itself.

## Deployment

Hosted on Render, auto-deploying from `main`. Commit and it redeploys in
two or three minutes.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn diese_proxy:app`
- Region: Singapore
- Plan: free — sleeps after 15 minutes idle, 30–60 seconds to wake

---

## The boards

Which report a page shows is decided by its own URL, so there is only one
copy of `board.html` to maintain.

**Studios** — `/`

**Health team** — `/?report=calendar&title=Health+team`

Reports are registered in the `REPORTS` dictionary in `diese_proxy.py`. To
add another, paste its DIESE URL there under a new key and use
`?report=<key>`.

### URL settings

| Setting | Does what | Example |
| --- | --- | --- |
| `report` | Which registered report to show | `?report=calendar` |
| `title` | Heading in the top left | `?title=Health+team` |
| `theme` | `studio` (default), `light`, `dark` | `?theme=light` |
| `start` | First hour drawn, or `none` | `?start=9` |
| `end` | Last hour drawn, or `none` | `?end=22` |
| `names` | `off` hides the person on each entry | `?names=off` |
| `min` | Minimum block height, in title-line units | `?min=4` |

### Settings in the file

Near the top of the `<script>` block in `board.html`:

- `VENUE_GROUPS` — colours keyed to column names. Colours follow the name,
  not the position, so a studio keeps its hue on days when others drop out
  of the report. Unmatched columns get spare hues in order of appearance.
- `BACKGROUND_TITLES` — entries treated as absence rather than appointments.
  The health report fills empty time with "Not Available", often spanning
  00:00–23:59; these are drawn as quiet bands, excluded from the day's span
  and from lane layout.
- `MIN_BLOCK_UNITS` — height every entry is guaranteed. The timeline runs at
  a variable rate: quiet stretches compress so busy ones keep their room.
- `AUTO_NARROW` — on a day too crowded to draw legibly, the board shows a
  window around the current time instead of shrinking everything past
  reading. The status line says "(narrowed)" when this happens.

---

## Constraints worth knowing

**The players run Chromium 56.** The foyer screen is a Samsung Tizen 4.0
panel. No CSS Grid, no `clamp()`, no `String.padStart`, no flex `gap` — all
of which broke it silently on the first attempt. Layout is flexbox and
absolute positioning; sizes scale through two variables the script sets at
runtime. Test any change on the screen, not only on a laptop.

**The report format is not a contract.** These pages are scraped from
DIESE's 903 template. Editing the 903's text layout in DIESE will change
what arrives here — that has already happened once and silently emptied the
board. The parser now handles the layouts seen so far and finds the time
anywhere in an entry, but a large enough change will still break it. If the
board becomes something people depend on, customising the report inside
DIESE (Brindisi) rather than scraping it is the version that survives.

**The board reports its own failures.** If the script throws, the screen
shows the error and line number rather than sitting on "Loading". If a
request hangs, it says so after 30 seconds. The status line at the bottom
right shows the visible window and when the data was last refreshed.

**Network.** The signage segment blocks general outbound traffic; the
service host had to be added to an allow list before the player could reach
it.

---

## Open questions

These are unresolved rather than decided, and are the first things anyone
inheriting this should look at.

**The URL is public.** No login. Anyone with the link can read TAB's
schedule, including cast names. The health board additionally pairs named
individuals with named treatments, which is health information — use
`?names=off` unless there is a decision to show them, and put a password on
it before circulating the link. HTTP basic auth in the proxy is about
fifteen lines.

**It is hosted on a personal account.** Render, in Sam Gray's name, on a
personal card. Fine while it is being built; not where a display the
company relies on should live. It is two small files and would run on an
internal server unchanged, which would also resolve the network and public
URL questions at once.

**Nobody else knows how it works.** Hence this file.
