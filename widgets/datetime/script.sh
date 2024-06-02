!#/usr/bin/env bash

# Datetime script.sh
# Print following information about datetime in JSON
#  - date (format: %Y-%m-%d)
#  - time in 24-hour format (format: %H:%M:%S)
#  - day (format: %a)
date=$(date +'%y/%m/%d')
time=$(date +'%H:%M:%S')
day=$(date +'%a')
echo "{\"date\": \"$date\", \"time\": \"$time\", \"day\": \"$day\"}"