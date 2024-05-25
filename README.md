#### Widgets

- Workspaces
- Now-Playing
- Network
- Battery
- DateTime
- Color-scheme

#### Todo
- [ ] Rewrite every widget to be dynamically sized depending on the screen size. (by `xrandr` command)
- [ ] Make the new widget for `Trays`.
- [ ] `Workspaces`
  - [x] Enable logging on file.
  - [x] Add the button to add the new workspace.
  - [x] Add Ignore specific window.
  - [x] Apply the animation by using `reveal` on `ws_desktop` and `ws_window`s.
  - [ ] Add DnD support between `ws_desktop` and `ws_window`s.
  - [x] Changes the size of the window icons or hiding them depends on the flags of the window. (i.e., sticky, hidden, etc.)
  - [ ] Multi-monitor support.
    - [ ] Run an individual `EWW window` on each monitor.
- [ ] `Network`
  - [ ] Make the popup for the `Network` widget.
    - [ ] Show the SSID of the connected network.
    - [ ] Show the IP address of the connected network.
    - [ ] Show the download and upload speed of the connected network.
  - [ ] Make the up/down labels for the `Network` widget.
- [ ] Make the popup for the `Battery` widget.
  - [ ] Show the graph of the battery percentage.
  - [ ] Show the remaining battery time or charging time.
- [ ] Make the popup for the `DateTime` widget.
  - [ ] Show the schedules up to the next `x` days.
  - [ ] Show the World Clock.
  - [ ] Show the calendar.
