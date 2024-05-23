#!/usr/bin/env bash

# Function to get the active interface
get_active_interface() {
  local interface=$(nmcli -t -f DEVICE,STATE d | grep ':connected$' | cut -d: -f1 | head -n 1)
  echo "$interface"
}

# Function to get the SSID
get_ssid() {
  local ssid=$(nmcli -t -f ACTIVE,SSID dev wifi | grep '^yes' | cut -d: -f2)
  echo "$ssid"
}

# Function to get the IP address
get_ip_address() {
  local interface=$1
  if [ -z "$interface" ]; then
    echo ""
    return
  fi
  local ip=$(nmcli -t -f IP4.ADDRESS dev show "$interface" | grep -oP '\d+(\.\d+){3}')
  echo "$ip"
}

# Function to get the default gateway
get_default_gateway() {
  local interface=$1
  if [ -z "$interface" ]; then
    echo ""
    return
  fi
  local gateway=$(nmcli -t -f IP4.GATEWAY dev show "$interface" | cut -d: -f2)
  echo "$gateway"
}

# Function to get the DNS servers
get_dns_servers() {
  local interface=$1
  if [ -z "$interface" ]; then
    echo ""
    return
  fi
  local dns=$(nmcli -t -f IP4.DNS dev show "$interface" | cut -d: -f2 | paste -s -d, -)
  echo "$dns"
}

# Function to print network status in JSON
print_network_status() {
  local interface=$(get_active_interface)
  local ssid=$(get_ssid)
  local ip_address=$(get_ip_address "$interface")
  local default_gateway=$(get_default_gateway "$interface")
  local dns_servers=$(get_dns_servers "$interface")
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

