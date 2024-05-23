#!/usr/bin/env bash

# Function to check the current color scheme
check_color_scheme() {
    local theme
    theme=$(xfconf-query -c xsettings -p /Net/ThemeName)

    # Check if theme name contains 'dark'
    if [[ $theme == *"dark"* ]]; then
        echo "dark"
    else
        echo "light"
    fi
}

# Monitor by xfconf-query
xfconf-query -c xsettings -p /Net/ThemeName -m | while read -r; do
    check_color_scheme
done