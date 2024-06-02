#!/usr/bin/env bash

#!/bin/bash

# Function to get the now playing information
get_now_playing_info() {
    local player_status=$(playerctl status 2>/dev/null)
    local rest_info=$(playerctl metadata --format ', "artist": "{{ artist }}", "title": "{{ title }}", "thumbnail": "{{ mpris:artUrl }}"' 2>/dev/null)
    echo {\"status\": \"$player_status\"$rest_info}
}

# Monitor for changes and print the now playing information in JSON format
monitor_now_playing_changes() {
    playerctl --follow status | while read -r line; do
        sleep 1.0
        get_now_playing_info
    done
}

# Run the monitor function
monitor_now_playing_changes
