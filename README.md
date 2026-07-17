# Mini-Time-CalendarWadget
Compact desktop widget (Tkinter, stdlib only) with the user's chosen golden photo as background  calendar/clock text.  By default only the calendar and the live clock are shown. Click the small switch under the clock to reveal the extra panel: Julian day-of-year, GPS time, Local/UTC side by side, Sunrise/Sunset.
how it works:
Here's the simplest way, using the `.pyw` file you already have:

**Step 1 — Find where `pythonw.exe` lives on your machine**
Open Command Prompt and run:
```
where pythonw
```
It'll print a path like `C:\Users\*******\AppData\Local\Programs\Python\Python312\pythonw.exe`. Copy that path.

**Step 2 — Open your Startup folder**
Press `Win + R`, type:
```
shell:startup
```
and hit Enter. This opens your personal Startup folder — anything here launches automatically when you log in.

**Step 3 — Create a shortcut**
1. Right-click inside that folder → **New → Shortcut**
2. In the location box, paste both the pythonw path and your script path together, in quotes, like this:
```
"C:\Users\********\AppData\Local\Programs\Python\Python312\pythonw.exe" "C:\Users\********\Downloads\New folder\mini_time_gadget.pyw"
```
   (use your actual pythonw path from Step 1, and wherever you saved the `.pyw` file)
3. Click Next, name it something like "Mini Time Gadget", click Finish

**Step 4 — Test it**
Double-click that new shortcut. If the gadget appears with no console window, it's working — it'll now also launch automatically every time you log into Windows.

One tip: keep the `.pyw` file in a permanent location (not a folder you might delete or rename later, like a temp Downloads subfolder) since the shortcut points to that exact path.


How it works: whenever you type new coordinates and hit Set, they're saved to a small file at C:\Users\khorchani\.mini_time_gadget.json (in your user folder). The next time you open the gadget — whether that's a manual relaunch or the automatic startup one — it reads that file first and uses those coordinates instead of the Cape Town default.
If you ever want to reset back to the default location, just delete that file and it'll fall back to Cape Town on the next launch.
