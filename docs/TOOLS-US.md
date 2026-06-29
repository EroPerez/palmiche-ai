# Tools guide — Palmiche J.A.R.V.I.S.

Complete reference for the **66 available tools**, with conversational usage examples and frequently asked questions (FAQ) for each category.

---

## Index

1. [System](#1-system)
2. [Applications and processes](#2-applications-and-processes)
3. [Files and directories](#3-files-and-directories)
4. [Network and connectivity](#4-network-and-connectivity)
5. [Media](#5-media)
6. [Screenshots](#6-screenshots)
7. [Web](#7-web)
8. [Clipboard and notifications](#8-clipboard-and-notifications)
9. [Weather](#9-weather)
10. [Notes](#10-notes)
11. [Timers and alarms](#11-timers-and-alarms)
12. [Calculator and unit conversion](#12-calculator-and-unit-conversion)
13. [Text tools](#13-text-tools)
14. [Calendar and events](#14-calendar-and-events)
15. [Developer](#15-developer)
16. [System — power and autostart](#16-system--power-and-autostart)
17. [Computer Use ★](#17-computer-use-)
18. [External tools (MCP and A2A agents)](#18-external-tools-mcp-and-a2a-agents)
19. [Camera Vision ★](#19-camera-vision-)

---

## 1. System

### `get_system_info`

Returns CPU usage, RAM, disk space and system uptime.

**Usage examples:**
```
How is the system doing?
How much RAM am I using?
Show me the CPU and disk status
How long has the computer been running?
```

**FAQ:**

**What data does it return exactly?**
CPU usage (global percentage), RAM (used/total/percentage), disk of root partition (used/total/percentage) and system uptime.

**Can I see the usage of a partition other than root?**
Not directly; use `run_shell_command` with `df -h /path` for specific partitions.

**How often does it update?**
Every time you make a query — there is no continuous monitoring.

---

### `get_battery_info`

Battery status: percentage, whether it's charging/discharging and estimated remaining time.

**Usage examples:**
```
How much battery do I have left?
Is the laptop charging?
How much battery time do I have?
```

**FAQ:**

**Does it work on desktop computers?**
On machines without a battery, it returns a message indicating no battery was detected.

**Is the remaining time accurate?**
It's an operating system estimate based on current consumption; it may vary if you change the workload.

---

### `control_volume`

Controls the system volume: get level, set an exact value, raise, lower, mute or unmute.

**Available actions:** `get` `set` `up` `down` `mute` `unmute`

**Usage examples:**
```
What's the system volume at?
Turn the volume up to 80%
Lower the volume 10 points
Mute the audio
Unmute
Set the volume to 50%
```

**FAQ:**

**Does it require any external program?**
On Linux it uses `pactl` (PulseAudio/PipeWire). On macOS it uses `osascript` (built-in). If `pactl` is not available, it returns an error with installation instructions.

**Do `up` and `down` accept a number?**
Yes, you can specify the increment: "turn the volume up 15 points" → `action=up, value=15`. If you don't specify a value, the default increment is 10.

**Can I mute just one application?**
No; this tool controls the system master volume.

---

### `control_brightness`

Controls screen brightness (Linux only with `brightnessctl` installed).

**Available actions:** `get` `set` `up` `down`

**Usage examples:**
```
What's the screen brightness?
Set brightness to 70%
Lower brightness 20 points
Maximum brightness
```

**FAQ:**

**Does it work on macOS?**
Not currently; `brightnessctl` is Linux-exclusive. On macOS it returns a not compatible message.

**Why doesn't it work even though I have `brightnessctl` installed?**
The user running Jarvis needs write permissions to the backlight device. Run `sudo usermod -aG video $USER` and restart the session.

**`set 100` doesn't reach maximum visual brightness**
Some external monitors have their own brightness control independent of the operating system. This tool only controls the integrated screen's backlight.

---

## 2. Applications and processes

### `open_application`

Opens an application or program by name or command.

**Usage examples:**
```
Open Firefox
Start the code editor
Open the system calculator
Launch Spotify
Open the file manager
```

**FAQ:**

**How does Jarvis know which command to use?**
It launches the name as you typed it. If the binary is in the system's `PATH`, it works. If not, the system returns an error.

**Can I pass arguments?**
Yes, for example: "open firefox with the URL google.com". Jarvis will include the argument when launching the process.

**The app opens but Jarvis says there was an error**
Some programs write to stderr on startup (Qt messages, GTK warnings...) without it being a real error. The tool uses `Popen` in the background — if the process starts, the app should appear.

---

### `close_application`

Terminates a process by name. By default sends SIGTERM (clean shutdown); with `force=true` sends SIGKILL.

**Usage examples:**
```
Close Firefox
Terminate the Spotify process
Force close vlc
Kill the python process
```

**FAQ:**

**Does it close all processes with that name?**
Yes, it terminates all processes whose name (partially) matches the one specified.

**When should I use `force`?**
When the process doesn't respond to SIGTERM. Use it carefully as it doesn't give time to save data.

**Can I close by PID?**
Not directly; use `run_shell_command` with `kill -9 <PID>` if you need PID precision.

---

### `list_running_apps`

Lists running processes with their memory usage.

**Usage examples:**
```
What applications are running?
What processes are consuming the most memory?
Is there any Python process active?
Show me the Firefox processes
```

**FAQ:**

**Does it show all system processes?**
It shows the most relevant processes sorted by memory usage. Kernel and system processes are usually filtered out.

**Can I filter by name?**
Yes: "is there any python process?" → `filter=python`.

---

## 3. Files and directories

### `search_files`

Searches for files or directories in the filesystem by name or glob pattern.

**Usage examples:**
```
Search for PDF files in ~/Documents
Where are the .log files on the system?
Find all files named "config.json"
Search for folders named "node_modules" in ~/projects
```

**FAQ:**

**How deep does the search go?**
Maximum 6 levels deep to avoid slow searches in large trees.

**Does it support wildcards?**
Yes, glob patterns like `*.pdf`, `config*`, `*.{js,ts}`.

**Does it search hidden files?**
Yes, it includes hidden directories and files (those starting with `.`).

---

### `read_file`

Reads the content of a text file (up to N lines, default 100).

**Usage examples:**
```
Read the file ~/notes.txt
Show me the first 50 lines of ~/config.py
What's in ~/.bashrc?
```

**FAQ:**

**Does it work with binary files?**
No; it's designed for text files. Binaries will show as illegible characters.

**Can I read more than 100 lines?**
Yes, specify the number: "read the first 500 lines of file.log".

**The file has thousands of lines, how do I search for something specific?**
Ask Jarvis to use `run_shell_command` with `grep "term" file.txt`.

---

### `write_file`

Writes or appends content to a text file.

**Modes:** `write` (overwrite) · `append` (add to end)

**Usage examples:**
```
Write "Hello world" to ~/test.txt
Append this line to the end of ~/diary.txt: "Today was a good day"
Create a file ~/script.sh with this content: ...
```

**FAQ:**

**Does it overwrite the file if it already exists?**
With `write` mode yes. If you only want to add, specify "append".

**Does it create parent directories if they don't exist?**
No; use `create_directory` first if the path doesn't exist.

---

### `list_directory`

Lists the content of a directory (up to 40 items, directories first).

**Usage examples:**
```
List the files in ~/Documents
What's on the desktop?
Show me the hidden files in my home
```

**FAQ:**

**Why do I only see 40 items?**
To avoid excessively long responses. If you need to see more, use `run_shell_command` with `ls -la ~/path | head -100`.

**Does it include hidden files?**
Not by default. Explicitly ask "show me the hidden files" to include them.

---

### `delete_file` · `move_file` · `copy_file` · `create_directory` · `open_file`

Standard file management operations.

**Usage examples:**
```
Delete ~/Downloads/old_file.zip
Move ~/Downloads/photo.jpg to ~/Images/vacation/
Copy the report.pdf to ~/Backups/
Create the folder ~/projects/new-app
Open the PDF ~/Documents/manual.pdf
```

**FAQ — `delete_file`:**
Can I recover a deleted file? No, deletion is permanent (doesn't go to trash). Confirm before asking Jarvis to delete something important.

**FAQ — `open_file`:**
Uses the system's default application (`xdg-open` on Linux, `open` on macOS). If there's no app associated with the file type, it may not open.

---

## 4. Network and connectivity

### `get_network_info`

Shows local IP, public IP, WiFi network SSID and signal level.

**Usage examples:**
```
What's my IP address?
What WiFi network am I connected to?
What's my public IP?
Give me network information
```

**FAQ:**

**Is the public IP obtained from the internet?**
Yes, it makes a request to an external service. It may fail without a connection.

**Does it work with wired (Ethernet) connections?**
Yes; in that case the SSID field will appear empty or as "cable".

---

### `ping_host`

Sends ICMP packets to a host and returns latency and packet loss.

**Usage examples:**
```
Ping google.com
Does the server 192.168.1.1 respond?
Check the connection to cloudflare.com with 10 packets
```

**FAQ:**

**How many packets does it send by default?**
4 packets. You can change it: "send 10 pings to google.com".

**It says the host doesn't respond but the website loads fine**
Some servers block ICMP via firewall. Lack of ping response doesn't mean the service is down.

---

## 5. Media

### `media_control`

Controls system media playback.

**Available actions:** `play` `pause` `next` `previous` `stop`

**Usage examples:**
```
Pause the music
Play the next song
Stop playback
Resume the music
Go back to the previous song
```

**FAQ:**

**What players does it work with?**
On Linux it uses `playerctl`, which is compatible with Spotify, VLC, Rhythmbox, mpv and any player that implements MPRIS. On macOS it controls Music.app via AppleScript.

**Can I control YouTube in the browser?**
Only if the browser exposes MPRIS controls (some don't by default).

---

### `get_media_status`

Returns the title and artist of the currently playing track.

**Usage examples:**
```
What song is playing?
What music am I listening to?
```

**FAQ:**

**Returns "no active playback" but there is music**
Make sure the player is active on the system. On Linux, `playerctl status` in terminal should show `Playing`.

---

## 6. Screenshots

### `take_screenshot`

Captures the full screen or allows selecting an area.

**Usage examples:**
```
Take a screenshot
Take a screenshot of the desktop
Capture only a zone of the screen
Save the screenshot to ~/Images/capture.png
```

**FAQ:**

**Where does it save the file?**
By default to `~/screenshot_YYYYMMDD_HHMMSS.png`. You can specify a different path.

**Does it require any external program?**
On Linux it uses `scrot` (`sudo apt install scrot`). On macOS it uses `screencapture` (built-in).

**Does it work in tray mode (without window focus)?**
Yes, `scrot` captures the full desktop regardless of which window is active.

---

## 7. Web

### `open_url`

Opens a URL in the system's default browser.

**Usage examples:**
```
Open github.com
Open https://news.ycombinator.com
Visit the Python documentation page
```

**FAQ:**

**Does it need the `https://` prefix?**
No; if you don't include a scheme, `https://` is added automatically.

---

### `web_search`

Opens a search in the browser in incognito/private mode.

**Available engines:** `google` (default) · `duckduckgo` · `youtube`

**Usage examples:**
```
Search Google for "pasta recipes"
Search YouTube for Python tutorials
Search DuckDuckGo without tracking "internet privacy"
```

**FAQ:**

**Does Jarvis return the search results?**
No; it opens the browser with the search. To read results directly, combine with `fetch_webpage`.

**Why incognito mode?**
To avoid saving browsing history from searches launched from Jarvis.

---

### `fetch_webpage` *(new)*

Downloads a webpage and extracts its readable text (removes HTML, scripts, styles and navigation).

**Usage examples:**
```
Read the article at https://example.com/news
What does this page say? https://docs.python.org/3/library/os.html
Extract the content from https://wikipedia.org/wiki/Artificial_intelligence
Search DuckDuckGo and read me the first result
```

**FAQ:**

**How much text does it return?**
Up to 3,000 characters by default. You can ask for more: "read up to 8000 characters from that page".

**It doesn't return the content I expected**
Some pages load content dynamically with JavaScript (React, Vue...). This tool downloads the initial static HTML. For pages with dynamic content, the result may be incomplete.

**Can it read pages behind a login?**
No; it doesn't manage sessions or authentication cookies.

**Does it work with online PDFs?**
No; it's designed for `text/html` and `text/plain`. For PDFs, download them first with `http_request` and then use `read_file`.

---

### `get_rss_feed` *(new)*

Gets the latest entries from an RSS 2.0 or Atom feed, returning title, link and date.

**Usage examples:**
```
Show me the latest news from https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada
Give me the 5 latest entries from the Hacker News feed
What's new on the Python blog? https://feeds.feedburner.com/PythonInsider
```

**FAQ:**

**How many entries does it show by default?**
10. You can change it: "show me the last 20 entries".

**What's the difference between RSS and Atom?**
They are two feed formats. Jarvis detects and parses both automatically.

**Can I subscribe for automatic updates?**
Not currently; each query makes a one-time request to the feed. For continuous monitoring, combine with a periodic timer.

---

## 8. Clipboard and notifications

### `get_clipboard` · `set_clipboard`

Reads and writes to the system clipboard.

**Usage examples:**
```
What do I have in the clipboard?
Copy this to the clipboard: npm install palmiche-jarvis
Save this text to the clipboard: [long text...]
```

**FAQ:**

**Does it work between applications?**
Yes, it modifies the system's global clipboard (the same one used by Ctrl+C / Ctrl+V).

**Is there a size limit?**
In practice no, although very large clipboards may take longer.

---

### `send_notification`

Sends a desktop notification with title, message and urgency level.

**Urgency levels:** `low` · `normal` (default) · `critical`

**Usage examples:**
```
Send a notification: "Meeting in 5 minutes"
Notify me with critical urgency: "Memory almost full!"
Send a low notification: "Download completed"
```

**FAQ:**

**Does it require any program on Linux?**
Yes, `notify-send` from the `libnotify-bin` package (`sudo apt install libnotify-bin`).

**Notifications don't appear even though `notify-send` is installed**
Verify that the notification service is active on your desktop. In minimal environments there may be no notification daemon.

---

## 9. Weather

> No API key required. Data via [wttr.in](https://wttr.in) (free public service).

### `get_weather` *(new)*

Current weather: temperature (with wind chill), humidity, wind, visibility, pressure and daily range.

**Usage examples:**
```
What's the weather like today?
How's the weather in Madrid?
How many degrees are there in Buenos Aires right now?
Give me the weather in Tokyo in Fahrenheit
Is it raining in London?
```

**FAQ:**

**What happens if I don't specify a city?**
It auto-detects the location by IP. Accuracy may correspond to your internet provider, not your exact location.

**What units does the temperature come in?**
Celsius by default (metric system). Type "in Fahrenheit" or "in imperial" to change.

**Does it work without internet connection?**
No; it needs to connect to `wttr.in` to get the data.

**The data doesn't match my exact city**
Try with the English name or include the country: "Madrid, Spain" or "Santiago, Chile".

---

### `get_forecast` *(new)*

1 to 3-day forecast: weather description, maximum/minimum temperature and total precipitation.

**Usage examples:**
```
What will the weather be like this week?
Give me the 3-day forecast for Barcelona
Is it going to rain tomorrow in Seville?
2-day forecast for New York in imperial
```

**FAQ:**

**Can it give more than 3 days?**
No; the free wttr.in API returns a maximum of 3 days.

**What does "rain: X mm" mean?**
It's the total accumulated precipitation for that day according to the forecast.

---

## 10. Notes

> Stored in `~/.jarvis_notes.json` (configurable with `JARVIS_NOTES_FILE`). Works offline.

### `create_note` *(new)*

Creates a new note or updates the content of an existing one with the same title.

**Usage examples:**
```
Create a note titled "Project ideas" with the content: ...
Save this as a note "Pasta recipe": ingredients...
Update the note "Project ideas" with this new content: ...
Create a note "Monday meeting" with tags: work, urgent
```

**FAQ:**

**What happens if a note with that title already exists?**
The content and tags are updated; the id and creation date are preserved.

**Are tags case-sensitive?**
No; tag searches are case-insensitive.

**Can I use markdown in the content?**
Yes, content is stored as plain text and Jarvis will display it formatted if the terminal supports it.

---

### `list_notes` *(new)*

Lists all notes sorted by update date (most recent first).

**Usage examples:**
```
What notes do I have saved?
Show me notes with the "work" tag
List my "recipe" notes
How many notes do I have?
```

**FAQ:**

**How many notes does it show?**
All existing ones. If you have many, the result may be long; use tag filters or `search_notes` to narrow it down.

---

### `read_note` *(new)*

Reads the full content of a note by title (partial search) or id.

**Usage examples:**
```
Read the note "Project ideas"
Show me the note about Monday's meeting
Open the note with id a1b2c3d4
```

**FAQ:**

**Is the search exact?**
No; it searches first by exact id, then by exact title, and finally by partial title match. The first match is returned.

**Can I see two notes at once?**
Not with a single command; make two separate requests.

---

### `search_notes` *(new)*

Searches in title and content of all notes (case-insensitive).

**Usage examples:**
```
Search my notes for "budget"
Do I have any notes that mention "API key"?
Search notes about "Python"
```

**FAQ:**

**Does it also search in tags?**
Not directly; use `list_notes` with tag filter for that.

**Does it support regular expressions?**
No; the search is literal text, case-insensitive.

---

### `delete_note` *(new)*

Permanently deletes a note by title or id.

**Usage examples:**
```
Delete the note "Old draft"
Delete the note with id a1b2c3d4
```

**FAQ:**

**Can it be undone?**
No; deletion is permanent. The JSON file is updated immediately.

**Can I delete all notes at once?**
There's no bulk command; do it note by note or directly delete `~/.jarvis_notes.json` from the terminal.

---

## 11. Timers and alarms

> Timers run in background threads and trigger desktop notifications on completion. They are volatile: lost if the process ends.

### `set_timer` *(new)*

Starts a timer by duration in seconds.

**Usage examples:**
```
Set a 25-minute timer for pomodoro
Remind me in 30 seconds
1-hour timer for the oven
Set a 90-second timer called "pasta al dente"
```

**FAQ:**

**What's the maximum duration?**
24 hours (86,400 seconds).

**What happens when it ends?**
It sends a desktop notification with the timer name. If no notification daemon is active, the notification won't appear (but the timer did finish).

**Does Jarvis keep responding while the timer runs?**
Yes; the timer runs in a background thread and doesn't block the conversation.

**Does the timer survive if I close Jarvis?**
No; timers are in-memory. If the process ends, they're lost. For persistent scheduled tasks, use the system's `cron`.

**How many timers can I have active simultaneously?**
There's no fixed limit, but each one uses a system thread.

---

### `set_alarm` *(new)*

Schedules an alarm for a specific time of day in HH:MM format (24h).

**Usage examples:**
```
Set an alarm for 08:30 to wake up
Alarm at 14:00 for the meeting
Remind me at 23:59 that I have something to do
```

**FAQ:**

**What happens if the time has already passed today?**
The alarm is scheduled for the same time the next day.

**Can I set an alarm for a specific date?**
Not directly; use `add_event` in the calendar if you need reminders on future dates.

**Does it work if the laptop is in sleep mode?**
No; the Python process must be active. If the system suspends, the timer won't fire at the correct time.

---

### `list_timers` *(new)*

Shows all active timers with remaining time in `HH:MM:SS` format.

**Usage examples:**
```
How much time is left on the timer?
What timers do I have active?
```

**FAQ:**

**Why doesn't the timer I set appear?**
If the Jarvis process restarted, the timers were lost. Create a new one.

---

### `cancel_timer` *(new)*

Cancels an active timer by its id (6 hexadecimal characters).

**Usage examples:**
```
Cancel timer abc123
Stop the pomodoro timer [id: f3a9c1]
```

**FAQ:**

**Where do I find the timer id?**
It's shown when creating it with `set_timer` or `set_alarm`, and also appears in `list_timers`.

---

## 12. Calculator and unit conversion

### `calculate` *(new)*

Safely evaluates math expressions using Python's `ast` module (no direct `eval`). Cannot execute arbitrary code.

**Operators:** `\+` `\-` `*` `/` `**` (power) `%` `//` (integer division)
**Functions:** `sqrt` `cbrt` `sin` `cos` `tan` `asin` `acos` `atan` `atan2` `log` `log2` `log10` `exp` `abs` `round` `floor` `ceil` `factorial` `gcd` `hypot` `degrees` `radians` `min` `max`
**Constants:** `pi` `e` `tau` `inf`
**Aliases:** `×` → `*` · `÷` → `/` · `^` → `**`

**Usage examples:**
```
What is sqrt(144) + 2^10?
Calculate the factorial of 10
What is sin(pi/2)?
What is log(e)?
Calculate 3.14159 × 5²
How many seconds are in a week? (7 * 24 * 60 * 60)
```

**FAQ:**

**Is it safe? Can it execute system commands?**
Yes, it's safe. The evaluator parses the expression as an AST tree and only allows number nodes, arithmetic operators and functions from the whitelist. No access to modules, imports or system calls.

**Does it support complex numbers?**
Not in the functions, but `sqrt(-1)` returns an error; use `1j` directly if you need complex numbers.

**Does it work with scientific notation?**
Yes: `1.5e3` equals `1500`.

**Can it solve equations?**
No; it only evaluates direct numeric expressions. For symbolic algebra, ask Jarvis to use `run_shell_command` with Python and sympy.

---

### `convert_units` *(new)*

Converts between units of measurement in the following categories.

| Category | Available units |
|---|---|
| Length | `m` `km` `cm` `mm` `mi` `yd` `ft` `in` `nm` |
| Mass | `kg` `g` `mg` `lb` `oz` `t` (ton) |
| Temperature | `°C` `celsius` `°F` `fahrenheit` `K` `kelvin` |
| Speed | `m/s` `km/h` `mph` `kt` (knots) |
| Area | `m²` `km²` `ha` `acre` `ft²` `in²` `mi²` |
| Volume | `l` `ml` `m³` `gal` `qt` `pt` `cup` |
| Digital storage | `B` `KB` `MB` `GB` `TB` `PB` `KiB` `MiB` `GiB` `TiB` |

**Usage examples:**
```
Convert 100 km to miles
How many feet is 1.80 meters?
Convert 37°C to Fahrenheit
How many knots are 100 km/h?
Convert 2.5 GB to MB
How many pounds is 75 kg?
Convert 1 acre to square meters
```

**FAQ:**

**The unit I need is not in the list**
Open an issue in the repository or add the conversion factor directly in `jarvis/tools/calculator.py` in the `_UNITS` dictionary.

**Why does temperature use formulas and not factors?**
Because temperature conversion is affine (involves addition/subtraction), not multiplicative like other units.

**Can I chain conversions?**
Not directly, but you can make two requests: "convert 5 miles to km, and that result to meters".

---

## 13. Text tools

### `text_stats` *(new)*

Analyzes a text and returns statistics: words, characters (total and without spaces), lines, paragraphs, sentences and estimated reading time.

**Usage examples:**
```
How many words does this text have? [text]
Analyze the statistics of my essay
How long would it take to read this?
```

**FAQ:**

**How does it calculate reading time?**
Uses an average speed of 200 words per minute, which is the standard adult reading speed.

**How does it count sentences?**
Looks for final punctuation marks (`.` `!` `?`). May not be exact with abbreviations or decimal points.

---

### `text_transform` *(new)*

Applies a transformation to the input text.

| Operation | Result |
|---|---|
| `upper` | UPPERCASE |
| `lower` | lowercase |
| `title` | First Letter Of Each Word Capitalized |
| `capitalize` | Only the first letter capitalized |
| `reverse` | Reverses the text |
| `trim` | Removes leading and trailing whitespace |
| `slug` | text-ready-for-url (removes accents, spaces → hyphens) |
| `snake` | text_in_snake_case_format |
| `camel` | textInCamelCaseFormat |
| `pascal` | TextInPascalCaseFormat |
| `strip_accents` | Removes diacritics (á→a, ñ→n...) |
| `count_vowels` | Counts the vowels in the text |
| `palindrome` | Checks if the text is a palindrome |

**Usage examples:**
```
Convert "Hello World" to snake_case
Is "racecar" a palindrome?
Convert this title to slug: "Ubuntu Installation Guide"
Convert this class name to camelCase: "my_important_variable"
Remove the accents from this text: "Ángel García Ramírez"
```

**FAQ:**

**`slug` vs `snake`: which one to use?**
`slug` generates identifiers for URLs (only letters, numbers and hyphens, no accents). `snake_case` uses underscores and maintains the original language.

**Does `palindrome` distinguish spaces and symbols?**
No; it removes everything except letters and numbers before comparing, so "A man a plan a canal Panama" is correctly recognized as a palindrome.

**Does `strip_accents` remove ñ?**
ñ is converted to `n`. If you only want to remove tildes (á→a) but keep characters like ñ, you'll need to post-process.

---

## 14. Calendar and events

> Stored in `~/.jarvis_events.json` (configurable with `JARVIS_EVENTS_FILE`). No connection or external accounts required.

### `add_event`

Creates an event in the local calendar.

**Parameters:** title (required), date `YYYY-MM-DD` or `today`/`tomorrow` (required), time `HH:MM` (optional), description (optional), location (optional).

**Usage examples:**
```
Add a dentist appointment tomorrow at 10:30
Create an event "Ana's birthday" on 2026-07-15
Add "Team meeting" today at 15:00 in room B
```

**FAQ:**

**Can I create recurring events?**
No; each event is one-time. For recurring events, create one for each date.

**Do they sync with Google Calendar?**
No; the calendar is completely local. For Google Calendar integration, contribute or use an external connector.

---

### `list_events` · `upcoming_events` · `delete_event`

**Usage examples:**
```
What events do I have this week?
Show me the next 14 days of my agenda
Do I have anything scheduled for July?
Delete event a3f2b1c4
```

**FAQ — `upcoming_events`:**
How many days does it show by default? 7. Change with: "show me the next 30 days".

**FAQ — `delete_event`:**
Where do I find the event id? It appears in brackets when listing events: `[a3f2b1c4]`.

---

## 15. Developer

### `format_json`

Validates and formats JSON with configurable indentation.

**Usage examples:**
```
Format this JSON: {"name":"test","value":42}
Indent this JSON with 4 spaces: [{"a":1},{"b":2}]
Is this JSON valid? {name: "test"}
```

**FAQ:**

**What happens if the JSON is invalid?**
Returns the parsing error with the problem position.

---

### `hash_text`

Computes the cryptographic hash of a text.

**Algorithms:** `md5` · `sha1` · `sha256` (default) · `sha512`

**Usage examples:**
```
Calculate the SHA256 of "hello world"
What's the MD5 of this string?
SHA512 hash of my password [text]
```

**FAQ:**

**Can I hash files?**
Not directly; use `read_file` to get the content and then `hash_text`. For large files, use `run_shell_command` with `sha256sum file`.

---

### `encode_decode`

Encodes or decodes text in base64, URL-encoding or hexadecimal.

**Usage examples:**
```
Encode in base64: "user:password"
Decode this base64: dXNlcjpwYXNzd29yZA==
Encode in URL: "search with spaces"
```

---

### `generate_uuid`

Generates one or more random UUID4s.

**Usage examples:**
```
Generate a UUID
Give me 5 UUIDs
I need 10 unique identifiers
```

---

### `convert_timestamp`

Converts between Unix epoch and ISO-8601 format, or returns the current time.

**Usage examples:**
```
What time is it now in epoch?
Convert timestamp 1719187200 to date
What epoch corresponds to 2026-06-24T12:00:00?
```

---

### `http_request`

Performs HTTP requests and returns status, key headers and body preview. Ideal for testing APIs.

**Methods:** `GET` (default) · `POST` · `PUT` · `DELETE` · `PATCH` · `HEAD`

**Usage examples:**
```
Do a GET to https://api.github.com/zen
Test this endpoint: POST https://httpbin.org/post with body {"test": true}
What does HEAD of https://example.com return?
```

**FAQ:**

**How many body characters does it show?**
Up to 1,000 characters. To see more, use `fetch_webpage` which is optimized for HTML content.

**Does it support authentication?**
Not directly; add the header manually using `run_shell_command` with `curl -H "Authorization: Bearer TOKEN" ...`.

---

### `git_status`

Shows current branch, working tree changes and the last 5 commits of a repository.

**Usage examples:**
```
What's the current repository status?
Status of the repo at ~/projects/my-app
What branch am I on?
Are there uncommitted changes?
```

**FAQ:**

**Why is the default path "."?**
It uses the working directory of the Jarvis process. If you launched Jarvis from your repo, it will work directly.

---

### `find_process_on_port`

Identifies which process is listening on a TCP port.

**Usage examples:**
```
What's running on port 3000?
What process is using port 8080?
Is port 5432 free?
```

**FAQ:**

**Does it need special permissions?**
To see other users' processes it may need `sudo`. Current user processes are always visible.

**Does it work with UDP?**
No; it only scans TCP connections in LISTEN state.

---

## 16. System — power and autostart

### `power_action`

Controls the system power state.

**Actions:** `shutdown` · `restart` · `sleep` · `lock`

**Usage examples:**
```
Lock the screen
Put the computer to sleep
Shut down the system
Restart the computer
```

> **Security note:** The `shutdown`, `restart` and `sleep` actions require explicit confirmation before executing. Jarvis will ask for confirmation and only proceed when you respond affirmatively.

**FAQ:**

**Why does Jarvis ask for confirmation before shutting down?**
These are destructive and irreversible actions. Confirmation is enforced in code (not just in the prompt) to prevent accidental executions.

**`shutdown` gives an authentication error on Linux**
It's a polkit permissions issue. Install the included rule:
```bash
sudo jarvis/scripts/install-power-rules.sh
```

---

### `setup_autostart`

Configures Jarvis to start automatically with the operating system.

**Usage examples:**
```
Enable Jarvis autostart
Disable autostart
Configure Jarvis to start with the Ollama backend
```

**FAQ:**

**Where does it install the autostart entry?**
On Linux it creates a `.desktop` file in `~/.config/autostart/`. On macOS it uses a LaunchAgent in `~/Library/LaunchAgents/`.

**Does it start in tray or terminal mode?**
By default in tray mode (`--tray`). You can change it with the `tray=false` parameter.

---

---

## 17. Computer Use ★

> Requires `pip install "palmiche-jarvis[computer-use]"` and `GOOGLE_API_KEY` in `.env`.

### `computer_use_task`

Visually controls a **Chromium browser** (backend `playwright`) or the **full desktop** (backend `desktop`) to complete tasks described in natural language. The agent uses Gemini to see the screen and decides which actions to execute at each step.

Inspired by [google-gemini/computer-use-preview](https://github.com/google-gemini/computer-use-preview).

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task` | string | — | Task in natural language |
| `backend` | string | `"playwright"` | `"playwright"` (browser) or `"desktop"` (desktop) |
| `initial_url` | string | `"https://www.google.com"` | Starting URL (playwright backend only) |
| `max_iterations` | integer | `30` | Visual agent step limit |

**Actions Gemini can execute:**

| Action | Description |
|---|---|
| `click` / `double_click` / `triple_click` | Single, double or triple click at coordinates |
| `right_click` / `middle_click` | Secondary or wheel click |
| `type` | Type text (with optional Enter) |
| `scroll` | Scroll in any direction with magnitude |
| `drag_and_drop` | Drag from source to destination |
| `navigate` | Navigate to a URL |
| `go_back` / `go_forward` | Browser history |
| `press_key` / `hotkey` | Individual key or combination (Ctrl+C, Alt+F4...) |
| `take_screenshot` | Explicit capture to see the state |
| `wait` | Wait N seconds |

**Usage examples:**
```
Search for the Bitcoin price today in the browser
Open YouTube and play jazz music
Navigate to wikipedia.org and search for "Cuban Revolution"
Fill out the contact form at example.com with name "John" and email "john@test.com"
Go to google.com, search for "best restaurants in Havana" and tell me the top 3 results
Download the cover image from the page https://example.com
```

**FAQ:**

**Do I need to have Chromium installed beforehand?**
No. Playwright downloads its own Chromium when running `playwright install chromium`. It doesn't interfere with the system browser.

**Does it work in headless mode? Does a window open?**
By default yes, it works in headless mode (no visible window). For debugging you can pass `headless=False` (only from Python directly).

**Which Gemini models support computer use?**
The recommended model is `gemini-2.5-flash`. Models that support the `ComputerUse` API are those from the `gemini-2.5` family and specific versions with computer use support enabled.

**Can the `desktop` backend control any application?**
Yes, it can control any application visible on the desktop: browsers, editors, native apps, etc. Requires a graphical environment (Xorg/Wayland).

**Is it safe?**
Gemini includes sensitive action detection and requests user confirmation before executing them. The agent also has a configurable iteration limit (`COMPUTER_USE_MAX_ITERATIONS`) to prevent infinite loops.

**What happens if the agent doesn't complete the task within the iteration limit?**
It returns the last available reasoning with a message indicating the limit was reached. Increase `max_iterations` or simplify the task.

**Can I combine computer use with other backends (Claude, native Gemini)?**
The `computer_use_task` tool always uses `google-genai` directly with `GOOGLE_API_KEY`, regardless of Jarvis's main backend. You can use `--backend anthropic` for chat while computer use uses Gemini internally.

---

## 18. External tools (MCP and A2A agents)

The 66 built-in tools are just the starting point. Jarvis can connect to **external MCP servers** and inject their tools dynamically, as well as delegate tasks to **remote A2A agents**. The model sees all these tools exactly like the built-in ones.

> Full guide with step-by-step examples: **[MCP-AGENTS-US.md](MCP-AGENTS-US.md)**

---

### External MCP tools (`mcp_*`)

When you connect an MCP server, all its tools are registered with the `mcp_` prefix.

**Enable:**

```bash
# stdio transport (local process — most common)
python -m jarvis --connect-mcp "npx -y @modelcontextprotocol/server-filesystem ~/projects"

# SSE/HTTP transport (server already running)
python -m jarvis --connect-mcp "http://localhost:3000"

# In .env (persistent, separated by ;)
JARVIS_MCP_SERVERS=npx -y @modelcontextprotocol/server-filesystem ~/projects;http://my-server:3000
```

**Example tools registered after connecting the MCP Filesystem server:**

| Tool in Jarvis | Description |
|---|---|
| `mcp_read_file` | Read file contents (via MCP) |
| `mcp_write_file` | Write content to a file (via MCP) |
| `mcp_list_directory` | List directory contents (via MCP) |
| `mcp_search_files` | Search files by pattern (via MCP) |
| `mcp_create_directory` | Create a directory (via MCP) |
| `mcp_get_file_info` | Return file metadata (via MCP) |

**Example usage in chat:**

```
You: Read the file ~/projects/main.py and explain what it does
Jarvis: [uses mcp_read_file] The file contains a class...
```

**FAQ:**

**Do I need the `mcp` package?**
Yes. Install with `pip install 'palmiche-jarvis[mcp]'`.

**Which MCP servers can I use?**
Any server compatible with the MCP protocol: official `@modelcontextprotocol` servers (filesystem, GitHub, SQLite, Brave Search, etc.), community servers, or custom ones.

**How many servers can I connect simultaneously?**
No technical limit. Each server can contribute multiple tools.

**Do MCP tools persist between sessions?**
No; they are discovered on each Jarvis startup by connecting to the server.

---

### Remote A2A agents (`delegate_to_*`)

When you connect an A2A agent, it is registered as a tool with the `delegate_to_` prefix followed by the agent name.

**Enable:**

```bash
# Via flag (repeatable)
python -m jarvis --connect-a2a http://specialized-agent:8080

# In .env (persistent, comma-separated)
JARVIS_A2A_AGENTS=http://agent1:8080,http://agent2:9090
```

**Registered tool:**

| Tool in Jarvis | Parameter | Description |
|---|---|---|
| `delegate_to_<name>` | `message: str` | Delegates the task to the remote agent and returns its response |

**Example:**

```
You: Analyze this code and tell me if there are any bugs
Jarvis: [uses delegate_to_analyst("Analyze this code...")] 
        The analyst found 2 potential issues...
```

**FAQ:**

**Which agents are A2A-compatible?**
Any agent that implements Google's A2A protocol (JSON-RPC 2.0 over HTTP). Another Jarvis instance with `--serve-a2a` is also compatible.

**Can I combine MCP and A2A in the same session?**
Yes; the model has access to all tools and decides which ones to use based on the context of each request.

---

## 19. Camera Vision ★

> Requires `pip install "palmiche-jarvis[vision]"` and a camera connected to the system.
> The model configured in `JARVIS_MODEL` must be multimodal (Claude 3.x, Gemini, GPT-4o, Llava…).

### `camera_capture`

Captures a photo from the camera and saves it to disk.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `save_path` | string | `~/Capturas/camera_TIMESTAMP.jpg` | Destination path |
| `camera_index` | integer | config | Device index (0 = default) |
| `show_preview` | bool | `false` | Show the captured frame in a window |

**Usage examples:**
```
Take a photo with the camera
Capture an image and save it to ~/Photos/selfie.jpg
Take a photo with the secondary camera (index 1)
```

**FAQ:**

**Where does it save photos by default?**
In `~/Capturas/` with name `camera_YYYYMMDD_HHMMSS.jpg`. The directory is created automatically.

**Camera not detected**
Verify the camera is connected and not in use by another application. Try `camera_index=1` if you have multiple cameras.

---

### `camera_describe`

Captures a photo and describes it using the configured AI model.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | general description | Custom question or instruction for the model |
| `camera_index` | integer | config | Device index |
| `save_path` | string | `~/Capturas/…` | Optional path to save the image |
| `show_preview` | bool | `false` | Show the image in a window during analysis |

**Usage examples:**
```
What does the camera see right now?
Describe what's in front of me
Is there anyone in the room?
Look through the camera and tell me if the desk is tidy
```

**FAQ:**

**Which model analyzes the image?**
The one configured in `JARVIS_MODEL`. Any multimodal model works: `claude-3-5-sonnet`, `gemini-2.5-flash`, `gpt-4o`, `llava` (Ollama), etc.

**How fast does it respond?**
Capture takes under 1 second. Analysis time depends on the model and connection.

---

### `camera_recognize_objects`

Captures a photo and identifies all objects present in the scene.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `camera_index` | integer | config | Device index |
| `save_path` | string | `~/Capturas/…` | Optional path to save the image |
| `show_preview` | bool | `false` | Show the image in a window during analysis |

**Usage examples:**
```
What objects are on my desk?
Identify everything in the room
List the objects you see with the camera
What's on the table?
```

**FAQ:**

**What format does the response have?**
Numbered list with: object name, position in frame (left/center/right, top/middle/bottom), relative size and confidence level (high/medium/low).

---

### `camera_recognize_gestures`

Captures a photo and recognizes hand gestures and body language.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `camera_index` | integer | config | Device index |
| `save_path` | string | `~/Capturas/…` | Optional path to save the image |
| `show_preview` | bool | `false` | Show the image in a window |

**Usage examples:**
```
What gesture am I making?
How many fingers am I holding up?
Am I making a thumbs up sign?
Recognize the gesture my hand is making
```

**FAQ:**

**What gestures can it recognize?**
Open palm, fist, pointing, thumbs up/down, peace sign, OK, pinch, wave and any other the multimodal model can visually identify.

**Does it work with both hands?**
Yes; analysis covers each hand visible in the frame separately.

---

### `camera_analyze`

Captures a photo and analyzes it with a custom prompt. The most flexible tool for any visual question.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `prompt` | string | **required** | Question or instruction for the model about the image |
| `camera_index` | integer | config | Device index |
| `save_path` | string | `~/Capturas/…` | Optional path to save the image |
| `show_preview` | bool | `false` | Show the image in a window |

**Usage examples:**
```
Look at the camera and tell me what color my shirt is
Is the door behind me open or closed?
Read the text on the paper I'm holding
How many people are in the room?
Does the workspace look tidy or chaotic?
Analyze the facial expression I have right now
```

**FAQ:**

**What's the difference from `camera_describe`?**
`camera_describe` uses a fixed general-description prompt. `camera_analyze` accepts any specific question or instruction you need.

---

### `camera_monitor`

Monitors the camera for a period, analyzing frames at regular intervals and returning a summary of all observations.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `task` | string | general changes | What to monitor: "count people", "detect movement", "alert if someone enters"… |
| `duration` | integer | `10` | Seconds to monitor (max 60) |
| `interval` | integer | `3` | Seconds between captures (min 2) |
| `camera_index` | integer | config | Device index |
| `show_preview` | bool | `false` | Show live preview while monitoring |

**Usage examples:**
```
Monitor the camera for 30 seconds and tell me if anyone enters
Watch the door for 1 minute
Monitor the desk for 20 seconds and alert me if anything changes
How many times did someone walk past the camera in 30 seconds?
```

**FAQ:**

**How many frames does it analyze?**
`frames = duration ÷ interval`. With default values (10 s, every 3 s): ~3 frames. Adjust based on the speed of movement you want to detect.

**Does it block the conversation while monitoring?**
Yes; the tool is synchronous and doesn't return until the period ends. For longer durations, use repeated short calls.

**What is the minimum interval?**
2 seconds (enforced in code). Shorter intervals would flood the model with too many calls.

---

### `camera_preview`

Opens a live camera view window with no AI analysis. Ideal for checking framing and focus before using other camera tools.

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `duration` | integer | `15` | Seconds of preview (max 120) |
| `camera_index` | integer | config | Device index |

Close the window by pressing **ESC** or **Q**.

**Usage examples:**
```
Open the camera preview
Show me what the camera sees live
Activate the camera for 30 seconds to verify it works
Is the camera focused correctly?
```

**FAQ:**

**No window appears**
Requires an active graphical environment (Xorg/Wayland). SSH sessions without X11 forwarding cannot display windows.

**The window shows Qt errors on open**
The camera module automatically sets `QT_QPA_PLATFORM=xcb` on import to prevent conflicts with Qt plugins not bundled with OpenCV.

**Can I close it before the time runs out?**
Yes, press **ESC** or **Q** in the window.

---

## Adding new tools

To contribute a new built-in tool:

1. Create a module in `jarvis/tools/module_name.py` with the functions
2. Register the tool in `jarvis/tools/registry.py`:
   - Import the functions at the top of the file
   - Add the JSON definition to the `TOOL_DEFINITIONS` array
   - Add the handler to the dictionary in `execute_tool`
3. Open a Pull Request describing the new tool

Follow the pattern of any existing module (for example `jarvis/tools/weather.py`).
