# J.A.R.V.I.S. HUD

A Jarvis command center. Arc reactor, a live 3D globe, and a British voice that briefs you when you sit down.

It's the fun side of my Jarvis project. Not a productivity tool. Just cool.

## What it does

- **Global overwatch.** A spinning night-side Earth that shows home, the International Space Station live with its orbit trail, and every plane in the air around Minneapolis.
- **Briefing.** On wake Jarvis says good morning, the time, the weather, where the ISS is, and the fact of the day.
- **Talk to it.** Tap the arc reactor (or hit space) and ask for things. Or type them.
- **Panels.** Clock with sunrise and sunset, weather, ISS stats, nearby aircraft, fact of the day, on this day in history, top tech headlines, and a protocols board showing which feeds are live.

Everything runs on free public data. No logins, no API keys, nothing personal.

## Two ways to run it

**On any device (iPhone too).** Open the GitHub Pages link. Tap to wake Jarvis. On iPhone, Share > Add to Home Screen makes it feel like an app.

**On the Mac.** This gets you the real macOS "Daniel" voice and Jarvis greets you on his own, no tap needed.

```bash
python3 jarvis.py              # start it
python3 jarvis.py --install    # greet me every time I log in
python3 jarvis.py --uninstall  # stop that
python3 jarvis.py --say "Good evening, sir."
```

No installs. Just Python 3, which every Mac already has.

## Commands

| Say or type | Jarvis does |
|---|---|
| status report | full briefing |
| weather | conditions and what to wear |
| where's the ISS | flies the globe to the station |
| planes | closest aircraft overhead |
| fact | fact of the day |
| history | something that happened on this day |
| headlines | top stories |
| joke | questionable humor |
| spin / stop | globe rotation |
| home | zoom to Minneapolis |

## Make it yours

Top of the script in `docs/index.html`:

```js
const CONFIG = {
  name: "Carson",
  title: "sir",
  city: "Minneapolis",
  lat: 44.98,
  lon: -93.27,
};
```

New voice lines go in `COMMANDS` right below. Each one is a pattern and what Jarvis says back.

## Data sources

Open-Meteo (weather), Where the ISS at (space station), OpenSky Network (aircraft), Useless Facts (daily fact), Wikipedia On This Day, Hacker News. Globe by globe.gl.

## Ideas for Mark IV

- Sports scores for the Vikings and Wild
- Market open/close ticker
- Hook into the Obsidian vault to show the Jarvis Inbox
- "Jarvis, light show" mode
