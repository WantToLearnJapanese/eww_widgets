#!/usr/bin/env bash

# Function to get battery information and print it in JSON format
get_battery_info() {
  local battery_info
  battery_info=$(upower -i $(upower -e | grep battery))

  local charging_status
  charging_status=$(echo "$battery_info" | grep "state:" | awk '{print $2}')

  local percentage
  percentage=$(echo "$battery_info" | grep "percentage:" | awk '{print $2}' | tr -d '%')

  local remaining_time
  remaining_time=$(echo "$battery_info" | grep "time to empty:" | awk '{print $4, $5}')
  if [ -z "$remaining_time" ]; then
    remaining_time=$(echo "$battery_info" | grep "time to full:" | awk '{print $4, $5}')
  fi

  # Print the information in JSON format
  echo "{\"status\": \"$charging_status\", \"percentage\": $percentage, \"time\": \"$remaining_time\"}"
}

get_battery_info

# Monitor battery status changes using upower events
upower --monitor-detail | while read -r line; do
  if echo "$line" | grep -q "battery"; then
    get_battery_info
  fi
done
