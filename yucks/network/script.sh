#!/usr/bin/env bash

# Function to get network details
get_network_details() {
  local device=$(nmcli -t -f DEVICE,STATE d | grep ':connected$' | cut -d: -f1 | head -n 1)
  if [ -n "$device" ]; then
    nmcli -t -f GENERAL.STATE,GENERAL.DEVICE,GENERAL.CONNECTION,IP4.ADDRESS,IP4.GATEWAY,IP4.DNS dev show "$device"
  else
    echo ""
  fi
}

# Function to parse network details
parse_network_details() {
  local details="$1"
  local state=$(echo "$details" | grep -E '^GENERAL.STATE:' | cut -d: -f2)
  local device=$(echo "$details" | grep -E '^GENERAL.DEVICE:' | cut -d: -f2)
  local ssid=$(echo "$details" | grep -E '^GENERAL.CONNECTION:' | cut -d: -f2)
  local ip_address=$(echo "$details" | grep -E '^IP4.ADDRESS\[1\]:' | cut -d: -f2 | cut -d/ -f1)
  local default_gateway=$(echo "$details" | grep -E '^IP4.GATEWAY:' | cut -d: -f2)
  local dns_servers=$(echo "$details" | grep -E '^IP4.DNS\[[0-9]+\]:' | cut -d: -f2 | paste -s -d, -)

  local is_wifi="true"
  if [ -z "$ssid" ]; then
    is_wifi="false"
  fi

  local json_output=$(
    cat <<EOF
{
  "ssid": "$ssid",
  "ip": "$ip_address",
  "default_gateway": "$default_gateway",
  "dns_servers": "$dns_servers",
  "is_wifi": "$is_wifi"
}
EOF
  )

  # Print in a single line
  echo "$json_output" | jq -c .
}

# Function to print network status
print_network_status() {
  local details=$(get_network_details)
  if [ -n "$details" ]; then
    parse_network_details "$details"
  else
    echo '{"ssid": "", "ip": "", "default_gateway": "", "dns_servers": "", "is_wifi": "false"}' | jq -c .
  fi
}

# Function to monitor network changes using nmcli
monitor_network_changes() {
  print_network_status
  nmcli monitor | while read -r line; do
    print_network_status
  done
}

# Main function
main() {
  monitor_network_changes
}

# Run the main function
main

