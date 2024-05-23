#!/usr/bin/env bash

# Print following information about battery in json by gojq
#  - charging status  (str without leading/trailing spaces)
#  - percentage  (int)
#  - remaining time (str without leading/trailing spaces)

# Grep the first battery info ("Battery 0:")
battery_info=$(acpi -b | head -n 1)
charging_status=$(echo "$battery_info" | awk '{print $3}' | tr -d ',')
percentage=$(echo "$battery_info" | awk '{print $4}' | tr -d '%,')
remaining_time=$(echo "$battery_info" | awk '{print $5}' | tr -d ',')
echo "{\"status\": \"$charging_status\", \"percentage\": $percentage, \"time\": \"$remaining_time\"}"
