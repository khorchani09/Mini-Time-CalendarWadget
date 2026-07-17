#!/usr/bin/env python3
"""
Mini Time & Calendar Gadget (gold & sky-blue edition)
--------------------------------------------------------
Compact desktop widget (Tkinter, stdlib only) with the user's chosen
golden photo as background and sky-blue calendar/clock text.

By default only the calendar and the live clock are shown. Click the
small switch under the clock to reveal the extra panel: Julian
day-of-year, GPS time, Local/UTC side by side, Sunrise/Sunset.

No external dependencies at runtime - only tkinter, datetime, calendar,
math (the background photo is embedded as base64 PNG data below, so
there is nothing extra to bundle or ship alongside this file).
"""

import tkinter as tk
import calendar
import datetime
import math
import json
import os
import threading
import urllib.request
import urllib.parse

# GPS time has been a constant 18 seconds ahead of UTC since the last
# leap second (31 Dec 2016). Update this if a new leap second is added.
GPS_UTC_OFFSET_SECONDS = 18

DEFAULT_LAT = -33.9249   # Cape Town
DEFAULT_LON = 18.4241

# Remembers the last coordinates you set, so the gadget re-opens with them
# instead of always resetting to the default location above.
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".mini_time_gadget.json")


def load_saved_location():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return float(data["lat"]), float(data["lon"])
    except Exception:
        return None


def save_location(lat, lon):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"lat": lat, "lon": lon}, f)
    except Exception:
        pass  # best-effort only; never let a save failure crash the gadget

BLACK = "#b8920f"        # panel colour, matched to the photo background tone
GOLD = "#140d02"          # dark black - main text / numbers
GOLD_DIM = "#3a2a10"      # dark brownish-black - secondary/dim text
GOLD_BRIGHT = "#000000"   # pure black - emphasis text
YELLOW = "#ffe14d"
RED_ACCENT = "#b3552f"
TRANSPARENT_KEY = "#fe01fe"   # chroma-key colour used to punch rounded corners
CORNER_RADIUS = 14

WIDTH = 200
COLLAPSED_H = 258
EXPANDED_EXTRA_H = 208

WEEKDAY_HEADERS = ["M", "T", "W", "T", "F", "S", "S"]

# Embedded background photo (base64 PNG), pre-sized for the collapsed
# and expanded window heights so no image resizing is needed at runtime.
BG_IMAGE_COLLAPSED_B64 = (
    "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"
    "bNU346D9+/8HHgL5tQq6gqsAAAAASUVORK5CYII="
)

BG_IMAGE_EXPANDED_B64 = (
    "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"
)



# --------------------------------------------------------------------------
# Sunrise / Sunset (classic Sun Rise/Set algorithm, Almanac for Computers)
# --------------------------------------------------------------------------
def _sun_event_utc_hours(day_of_year, lat, lon, rising, zenith=90.833):
    lng_hour = lon / 15.0
    t = day_of_year + ((6 - lng_hour) / 24.0 if rising else (18 - lng_hour) / 24.0)
    m = (0.9856 * t) - 3.289
    l = m + (1.916 * math.sin(math.radians(m))) + (0.020 * math.sin(math.radians(2 * m))) + 282.634
    l = l % 360
    ra = math.degrees(math.atan(0.91764 * math.tan(math.radians(l))))
    ra = ra % 360
    l_quad = (math.floor(l / 90.0)) * 90.0
    ra_quad = (math.floor(ra / 90.0)) * 90.0
    ra = ra + (l_quad - ra_quad)
    ra = ra / 15.0
    sin_dec = 0.39782 * math.sin(math.radians(l))
    cos_dec = math.cos(math.asin(sin_dec))
    cos_h = (math.cos(math.radians(zenith)) - (sin_dec * math.sin(math.radians(lat)))) / (
        cos_dec * math.cos(math.radians(lat))
    )
    if cos_h > 1 or cos_h < -1:
        return None
    if rising:
        h = 360 - math.degrees(math.acos(cos_h))
    else:
        h = math.degrees(math.acos(cos_h))
    h = h / 15.0
    T = h + ra - (0.06571 * t) - 6.622
    UT = (T - lng_hour) % 24
    return UT


def sunrise_sunset(date_obj, lat, lon, utc_offset_hours):
    doy = date_obj.timetuple().tm_yday

    def fmt(ut_hours):
        if ut_hours is None:
            return None
        local_h = (ut_hours + utc_offset_hours) % 24
        hh = int(local_h)
        mm = int(round((local_h - hh) * 60))
        if mm == 60:
            mm = 0
            hh = (hh + 1) % 24
        return f"{hh:02d}:{mm:02d}"

    sunrise = fmt(_sun_event_utc_hours(doy, lat, lon, rising=True))
    sunset = fmt(_sun_event_utc_hours(doy, lat, lon, rising=False))
    return (sunrise or "none", sunset or "none")


def local_utc_offset_hours():
    offset = datetime.datetime.now().astimezone().utcoffset()
    return offset.total_seconds() / 3600.0


# --------------------------------------------------------------------------
# Reverse geocoding (coordinates -> place name), via OpenStreetMap Nominatim.
# Requires internet access; fails gracefully (returns None) when offline.
# Usage policy: nominatim.openstreetmap.org/reverse, max 1 req/s, needs a
# descriptive User-Agent, and results must credit OpenStreetMap.
# --------------------------------------------------------------------------
def reverse_geocode(lat, lon, timeout=5):
    try:
        params = urllib.parse.urlencode({
            "format": "jsonv2",
            "lat": f"{lat:.5f}",
            "lon": f"{lon:.5f}",
            "zoom": "10",
            "addressdetails": "1",
        })
        url = f"https://nominatim.openstreetmap.org/reverse?{params}"
        req = urllib.request.Request(
            url, headers={"User-Agent": "MiniTimeGadget/1.0 (personal desktop widget)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
        address = data.get("address", {})
        place = (address.get("city"))
        country = address.get("country")
        if place :
            return f"{place}"
        return place or data.get("display_name")
    except Exception:
        return None


# --------------------------------------------------------------------------
# Degrees/Minutes/Seconds coordinate helpers
# --------------------------------------------------------------------------
def parse_dms(text, positive_hemi, negative_hemi):
    """Parse a coordinate typed as DMS, e.g. 33 55 30 S / 33°55'30"S /
    18d25m27sE, or a plain decimal like -33.9249. Returns decimal degrees."""
    s = text.strip().upper()
    if not s:
        raise ValueError("empty coordinate")

    sign = 1
    if s[-1] in (positive_hemi, negative_hemi):
        if s[-1] == negative_hemi:
            sign = -1
        s = s[:-1].strip()
    elif s.startswith("-"):
        sign = -1
        s = s[1:]
    elif s.startswith("+"):
        s = s[1:]

    for ch in "°'\"DMS":
        s = s.replace(ch, " ")
    parts = [p for p in s.replace(",", " ").split() if p]
    if not parts:
        raise ValueError("no numbers found")

    deg = float(parts[0])
    minutes = float(parts[1]) if len(parts) > 1 else 0.0
    seconds = float(parts[2]) if len(parts) > 2 else 0.0
    decimal = deg + minutes / 60.0 + seconds / 3600.0
    return sign * decimal


def decimal_to_dms(value, positive_hemi, negative_hemi):
    """Format decimal degrees as a DMS string, e.g. 33°55'30"S."""
    hemi = positive_hemi if value >= 0 else negative_hemi
    value = abs(value)
    deg = int(value)
    minutes_full = (value - deg) * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60
    return f"{deg}\u00b0{minutes}'{seconds:.0f}\"{hemi}"


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------
class MiniGadget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gadget")
        self.resizable(False, False)
        self.overrideredirect(True)   # hide the OS title bar (close/min/max buttons)
        # window stays in normal desktop stacking order (not forced always-on-top)

        # Rounded corners rely on a Windows-only chroma-key transparency trick:
        # any pixel drawn in TRANSPARENT_KEY becomes a see-through hole in the
        # window. Falls back to plain square corners where unsupported.
        self._can_round = True
        try:
            self.wm_attributes("-transparentcolor", TRANSPARENT_KEY)
        except tk.TclError:
            self._can_round = False
        self.configure(bg=TRANSPARENT_KEY if self._can_round else BLACK)

        today = datetime.date.today()
        self.view_year = today.year
        self.view_month = today.month
        self.selected_date = today
        saved = load_saved_location()
        self.lat, self.lon = saved if saved else (DEFAULT_LAT, DEFAULT_LON)
        self._geocoded_coords = None
        self.expanded = False

        self.canvas = tk.Canvas(self, width=WIDTH, height=COLLAPSED_H,
                                 bg=TRANSPARENT_KEY if self._can_round else BLACK,
                                 highlightthickness=0)
        self.canvas.pack()

        self._bg_img_collapsed = tk.PhotoImage(data=BG_IMAGE_COLLAPSED_B64)
        self._bg_img_expanded = tk.PhotoImage(data=BG_IMAGE_EXPANDED_B64)
        self._draw_background(COLLAPSED_H)

        # ---- drag-to-move (no title bar means no default way to drag) ----
        self.canvas.bind("<ButtonPress-1>", self._start_drag)
        self.canvas.bind("<B1-Motion>", self._do_drag)

        # ---- close button (no title bar means no default close button) ---
        self._draw_close_button()
        self.canvas.tag_bind("close_btn", "<Button-1>", lambda e: self.destroy())
        self.canvas.tag_bind("close_btn", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("close_btn", "<Leave>", lambda e: self.canvas.config(cursor=""))
        self.bind("<Escape>", lambda e: self.destroy())

        # ---- content (always visible): nav + calendar + clock ----------
        self.content = tk.Frame(self.canvas, bg=BLACK)
        self.canvas.create_window(WIDTH // 2, 6, window=self.content, anchor="n")
        self._build_nav(self.content)
        self._build_calendar_grid(self.content)
        self._build_clock(self.content)

        # ---- switch (toggle) drawn on canvas -----------------------------
        self.switch_y = COLLAPSED_H - 20
        self._draw_switch()
        self.canvas.tag_bind("switch", "<Button-1>", self._toggle_extra)
        self.canvas.tag_bind("switch", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("switch", "<Leave>", lambda e: self.canvas.config(cursor=""))

        # ---- extra panel (hidden by default) ------------------------------
        self.extra = tk.Frame(self.canvas, bg=BLACK)
        self._build_extra(self.extra)
        self.extra_win = self.canvas.create_window(
            WIDTH // 2, COLLAPSED_H, window=self.extra, anchor="n", state="hidden"
        )

        self._redraw_calendar()
        self._update_extra_info()
        self._tick()

    # ---- window dragging (frameless window has no title bar to drag) ----
    def _start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _do_drag(self, event):
        x = self.winfo_pointerx() - self._drag_x
        y = self.winfo_pointery() - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _draw_close_button(self):
        self.canvas.delete("close_btn")
        r = 8
        cx, cy = WIDTH - 14, 14
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                 fill=BLACK, outline="", tags="close_btn")
        self.canvas.create_line(cx - 4, cy - 4, cx + 4, cy + 4,
                                 fill=GOLD_BRIGHT, width=2, tags="close_btn")
        self.canvas.create_line(cx - 4, cy + 4, cx + 4, cy - 4,
                                 fill=GOLD_BRIGHT, width=2, tags="close_btn")

    # ---- photo background ----------------------------------------------
    def _draw_background(self, height):
        self.canvas.config(height=height)
        self.canvas.delete("bgdeco")
        img = self._bg_img_expanded if height > COLLAPSED_H else self._bg_img_collapsed
        self.canvas.create_image(0, 0, image=img, anchor="nw", tags="bgdeco")
        self.canvas.tag_lower("bgdeco")
        self._draw_corner_mask(height)

    def _draw_corner_mask(self, height):
        self.canvas.delete("corner_mask")
        if not self._can_round:
            return
        r = CORNER_RADIUS
        corners = [
            (0, 0, 1, 1),                    # top-left
            (WIDTH, 0, -1, 1),                # top-right
            (0, height, 1, -1),               # bottom-left
            (WIDTH, height, -1, -1),          # bottom-right
        ]
        for cx, cy, sx, sy in corners:
            sq_x0, sq_x1 = sorted((cx, cx + sx * r))
            sq_y0, sq_y1 = sorted((cy, cy + sy * r))
            self.canvas.create_rectangle(sq_x0, sq_y0, sq_x1, sq_y1,
                                          fill=TRANSPARENT_KEY, outline="", tags="corner_mask")
            ov_x0, ov_x1 = sorted((cx, cx + sx * 2 * r))
            ov_y0, ov_y1 = sorted((cy, cy + sy * 2 * r))
            self.canvas.create_oval(ov_x0, ov_y0, ov_x1, ov_y1,
                                     fill=BLACK, outline="", tags="corner_mask")

    def _draw_switch(self):
        self.canvas.delete("switch")
        cx = WIDTH // 2
        y = self.switch_y
        pill_w, pill_h = 42, 16
        x0, y0 = cx - pill_w // 2, y - pill_h // 2
        x1, y1 = cx + pill_w // 2, y + pill_h // 2
        pill_color = GOLD_BRIGHT if self.expanded else GOLD_DIM
        self.canvas.create_oval(x0, y0, x0 + pill_h, y1, fill=pill_color, outline="", tags="switch")
        self.canvas.create_oval(x1 - pill_h, y0, x1, y1, fill=pill_color, outline="", tags="switch")
        self.canvas.create_rectangle(x0 + pill_h / 2, y0, x1 - pill_h / 2, y1,
                                      fill=pill_color, outline="", tags="switch")
        knob_x = (x1 - pill_h / 2) if self.expanded else (x0 + pill_h / 2)
        self.canvas.create_oval(knob_x - 6, y - 6, knob_x + 6, y + 6,
                                 fill=BLACK, outline=GOLD_BRIGHT, width=1, tags="switch")
        self.canvas.create_text(cx, y + 16, text="more info", fill=GOLD_DIM,
                                 font=("Segoe UI", 7, "bold"), tags="switch")

    # ---- content builders ----------------------------------------------
    def _gold_label(self, parent, **kw):
        kw.setdefault("bg", BLACK)
        kw.setdefault("fg", GOLD)
        return tk.Label(parent, **kw)

    def _build_nav(self, parent):
        nav = tk.Frame(parent, bg=BLACK)
        nav.pack(fill="x", pady=(0, 2))
        tk.Button(nav, text="‹", width=2, command=self._prev_month,
                   bg=BLACK, fg=GOLD, relief="flat", activebackground=BLACK,
                   activeforeground=GOLD_BRIGHT, bd=0, font=("Segoe UI", 8, "bold")).pack(side="left")
        self.month_year_lbl = self._gold_label(nav, font=("Segoe UI", 9, "bold"), width=12, anchor="center")
        self.month_year_lbl.pack(side="left", expand=True)
        tk.Button(nav, text="›", width=2, command=self._next_month,
                   bg=BLACK, fg=GOLD, relief="flat", activebackground=BLACK,
                   activeforeground=GOLD_BRIGHT, bd=0, font=("Segoe UI", 8, "bold")).pack(side="right")

        yr = tk.Frame(parent, bg=BLACK)
        yr.pack(fill="x", pady=(0, 4))
        tk.Button(yr, text="«", width=2, command=self._prev_year,
                   bg=BLACK, fg=GOLD_DIM, relief="flat", activebackground=BLACK,
                   activeforeground=GOLD_BRIGHT, bd=0, font=("Segoe UI", 7, "bold")).pack(side="left")
        self._gold_label(yr, text="", width=8).pack(side="left", expand=True)
        tk.Button(yr, text="»", width=2, command=self._next_year,
                   bg=BLACK, fg=GOLD_DIM, relief="flat", activebackground=BLACK,
                   activeforeground=GOLD_BRIGHT, bd=0, font=("Segoe UI", 7, "bold")).pack(side="right")

    def _build_calendar_grid(self, parent):
        grid = tk.Frame(parent, bg=BLACK)
        grid.pack()
        for i, wd in enumerate(WEEKDAY_HEADERS):
            self._gold_label(grid, text=wd, font=("Segoe UI", 6, "bold"), fg=GOLD_DIM).grid(
                row=0, column=i, padx=1, pady=1
            )
        self.day_buttons = []
        for r in range(6):
            row_btns = []
            for c in range(7):
                b = tk.Button(
                    grid, text="", width=2, height=1, relief="flat",
                    bg=BLACK, fg=GOLD, activebackground=GOLD_DIM, activeforeground=BLACK,
                    bd=0, font=("Segoe UI", 7, "bold"),
                    command=lambda rr=r, cc=c: self._on_day_click(rr, cc),
                )
                b.grid(row=r + 1, column=c, padx=0, pady=0)
                row_btns.append(b)
            self.day_buttons.append(row_btns)

    def _build_clock(self, parent):
        self.clock_lbl = self._gold_label(parent, font=("Consolas", 12, "bold"),
                                           fg=GOLD_BRIGHT, pady=6)
        self.clock_lbl.pack()

    def _build_extra(self, parent):
        self.julian_lbl = self._gold_label(parent, font=("Segoe UI", 9, "bold"), fg=GOLD_DIM)
        self.julian_lbl.pack(anchor="w", pady=(4, 2))

        self.gps_lbl = self._gold_label(parent, font=("Consolas", 8, "bold"), fg=GOLD)
        self.gps_lbl.pack(anchor="w")

        side = tk.Frame(parent, bg=BLACK)
        side.pack(fill="x", pady=(4, 2))
        local_box = tk.Frame(side, bg=BLACK)
        local_box.pack(side="left", expand=True, fill="x")
        self._gold_label(local_box, text="LOCAL", font=("Segoe UI", 6, "bold"), fg=GOLD_DIM).pack(anchor="w")
        self.local_time_lbl = self._gold_label(local_box, font=("Consolas", 9, "bold"), fg=GOLD_BRIGHT)
        self.local_time_lbl.pack(anchor="w")

        utc_box = tk.Frame(side, bg=BLACK)
        utc_box.pack(side="left", expand=True, fill="x")
        self._gold_label(utc_box, text="UTC", font=("Segoe UI", 6, "bold"), fg=GOLD_DIM).pack(anchor="w")
        self.utc_time_lbl = self._gold_label(utc_box, font=("Consolas", 9, "bold"), fg=GOLD_BRIGHT)
        self.utc_time_lbl.pack(anchor="w")

        self.sun_lbl = self._gold_label(parent, font=("Segoe UI", 8, "bold"), fg=YELLOW)
        self.sun_lbl.pack(anchor="w", pady=(4, 0))

        self.place_lbl = self._gold_label(parent, text="", font=("Segoe UI", 7, "bold"), fg=GOLD)
        self.place_lbl.pack(anchor="w", pady=(2, 0))

        self.lat_var = tk.StringVar(value=decimal_to_dms(self.lat, "N", "S"))
        self.lon_var = tk.StringVar(value=decimal_to_dms(self.lon, "E", "W"))

        entry_kw = dict(bg="#f5ecd0", fg=GOLD, insertbackground=GOLD,
                         relief="flat", highlightthickness=0, font=("Segoe UI", 7, "bold"))

        loc_grid = tk.Frame(parent, bg=BLACK)
        loc_grid.pack(fill="x", pady=(4, 2))

        self._gold_label(loc_grid, text="Lat", font=("Segoe UI", 6, "bold")).grid(
            row=0, column=0, sticky="w")
        tk.Entry(loc_grid, textvariable=self.lat_var, width=12, **entry_kw).grid(
            row=0, column=1, sticky="w", padx=(3, 0), pady=1)

        self._gold_label(loc_grid, text="Lon", font=("Segoe UI", 6, "bold")).grid(
            row=1, column=0, sticky="w")
        tk.Entry(loc_grid, textvariable=self.lon_var, width=12, **entry_kw).grid(
            row=1, column=1, sticky="w", padx=(3, 4), pady=1)
        tk.Button(loc_grid, text="Set", command=self._apply_location,
                   bg=GOLD_DIM, fg=BLACK, relief="flat", bd=0,
                   font=("Segoe UI", 6, "bold")).grid(row=1, column=2, sticky="w")

        self._gold_label(parent, text="e.g. 33\u00b055'30\"S",
                          font=("Segoe UI", 6, "bold"), fg=GOLD_DIM).pack(anchor="w")
        self._gold_label(parent, text="place data \u00a9 OpenStreetMap",
                          font=("Segoe UI", 5), fg=GOLD_DIM).pack(anchor="w")

    # ---- calendar logic --------------------------------------------------
    def _prev_month(self):
        self.view_month -= 1
        if self.view_month < 1:
            self.view_month, self.view_year = 12, self.view_year - 1
        self._redraw_calendar()

    def _next_month(self):
        self.view_month += 1
        if self.view_month > 12:
            self.view_month, self.view_year = 1, self.view_year + 1
        self._redraw_calendar()

    def _prev_year(self):
        self.view_year -= 1
        self._redraw_calendar()

    def _next_year(self):
        self.view_year += 1
        self._redraw_calendar()

    def _redraw_calendar(self):
        self.month_year_lbl.config(text=f"{calendar.month_abbr[self.view_month]} {self.view_year}")
        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.view_year, self.view_month)
        while len(weeks) < 6:
            weeks.append([0, 0, 0, 0, 0, 0, 0])
        today = datetime.date.today()
        for r in range(6):
            for c in range(7):
                day = weeks[r][c]
                btn = self.day_buttons[r][c]
                if day == 0:
                    btn.config(text="", state="disabled", bg=BLACK)
                else:
                    is_today = (day == today.day and self.view_month == today.month
                                and self.view_year == today.year)
                    is_selected = (day == self.selected_date.day and self.view_month == self.selected_date.month
                                   and self.view_year == self.selected_date.year)
                    bg = RED_ACCENT if is_selected else (GOLD_DIM if is_today else BLACK)
                    btn.config(text=str(day), state="normal", bg=bg)

    def _on_day_click(self, r, c):
        day_text = self.day_buttons[r][c].cget("text")
        if not day_text:
            return
        self.selected_date = datetime.date(self.view_year, self.view_month, int(day_text))
        self._redraw_calendar()
        self._update_extra_info()

    # ---- toggle ------------------------------------------------------
    def _toggle_extra(self, event=None):
        self.expanded = not self.expanded
        new_h = COLLAPSED_H + EXPANDED_EXTRA_H if self.expanded else COLLAPSED_H
        self._draw_background(new_h)

        # re-place the extra panel on top of the freshly drawn background
        self.canvas.itemconfigure(self.extra_win, state="normal" if self.expanded else "hidden")
        self.canvas.coords(self.extra_win, WIDTH // 2, COLLAPSED_H)
        self.switch_y = COLLAPSED_H - 20
        self._draw_switch()
        self.canvas.tag_bind("switch", "<Button-1>", self._toggle_extra)
        self.canvas.tag_bind("switch", "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
        self.canvas.tag_bind("switch", "<Leave>", lambda e: self.canvas.config(cursor=""))

        if self.expanded:
            self._update_extra_info()

    # ---- live clock ----------------------------------------------------
    def _tick(self):
        now_local = datetime.datetime.now()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        gps_time = now_utc + datetime.timedelta(seconds=GPS_UTC_OFFSET_SECONDS)

        self.clock_lbl.config(text=now_local.strftime("%A %d %H:%M"))
        if self.expanded:
            self.gps_lbl.config(text=f"GPS  {gps_time.strftime('%H:%M:%S')}")
            self.local_time_lbl.config(text=now_local.strftime("%H:%M:%S"))
            self.utc_time_lbl.config(text=now_utc.strftime("%H:%M:%S"))

        self.after(1000, self._tick)

    def _update_extra_info(self):
        doy = self.selected_date.timetuple().tm_yday
        year_len = 366 if calendar.isleap(self.selected_date.year) else 365
        self.julian_lbl.config(text=f"Day {doy}/{year_len} · {self.selected_date.strftime('%d %b %Y')}")

        offset = local_utc_offset_hours()
        sunrise, sunset = sunrise_sunset(self.selected_date, self.lat, self.lon, offset)
        self.sun_lbl.config(text=f"☀ {sunrise}   🌙 {sunset}")
        self._maybe_geocode()

    def _apply_location(self):
        try:
            lat = parse_dms(self.lat_var.get(), "N", "S")
            lon = parse_dms(self.lon_var.get(), "E", "W")
        except ValueError:
            self.sun_lbl.config(text="Invalid coordinates")
            return
        self.lat, self.lon = lat, lon
        save_location(lat, lon)
        self.lat_var.set(decimal_to_dms(lat, "N", "S"))
        self.lon_var.set(decimal_to_dms(lon, "E", "W"))
        self._update_extra_info()

    # ---- reverse geocoding (place name lookup, runs in a background thread) --
    def _maybe_geocode(self):
        coords = (round(self.lat, 5), round(self.lon, 5))
        if coords == self._geocoded_coords:
            return  # already have a name for this exact location
        self._geocoded_coords = coords
        self.place_lbl.config(text="Locating\u2026")
        threading.Thread(target=self._geocode_worker, args=coords, daemon=True).start()

    def _geocode_worker(self, lat, lon):
        name = reverse_geocode(lat, lon)
        self.after(0, lambda: self._on_geocode_done(lat, lon, name))

    def _on_geocode_done(self, lat, lon, name):
        # ignore a stale result if the location has since changed again
        if (lat, lon) != self._geocoded_coords:
            return
        self.place_lbl.config(text=name if name else "Location name unavailable")


if __name__ == "__main__":
    app = MiniGadget()
    app.mainloop()
