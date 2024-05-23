#!/usr/bin/env bash

# N_MONITORS=1
N_DESKTOPS=10
N_WINDOWS=10

HALIGN="\"center\""
VALIGN="\"center\""

function generate_desktops {
    # num_desktops = $1 if $1 is set, else $NUM_DESKTOPS
    # num_windows = $2 if $2 is set, else $NUM_WINDOWS
    local n_desktops=${1:-$N_DESKTOPS}
    local n_windows=${2:-$N_WINDOWS}

    local desktops_yuck=""
    desktops_yuck+="(defvar focused_desktop -1)\n"
    desktops_yuck+="(defvar focused_window -1)\n"
    for i in $(seq 1 $n_desktops); do
        local desktop_yuck=""
        desktop_yuck+="(defvar desktop_${i}_focused false)\n"
        desktop_yuck+="(defvar desktop_${i}_class \"\")\n"
        desktop_yuck+="(defvar desktop_${i}_icon \"\")\n"
        desktop_yuck+="(defvar desktop_${i}_label \"\")\n"
        desktop_yuck+="(defvar desktop_${i}_did -2)\n"
        desktop_yuck+="(defvar desktop_${i}_ts 0)\n"
        desktop_yuck+="(defvar desktop_${i}_visible false)\n"
        for j in $(seq 1 $n_windows); do
            local window_yuck=""
            window_yuck+="(defvar window_${i}_${j}_focused false)\n"
            window_yuck+="(defvar window_${i}_${j}_class \"\")\n"
            window_yuck+="(defvar window_${i}_${j}_icon \"\")\n"
            window_yuck+="(defvar window_${i}_${j}_label \"\")\n"
            window_yuck+="(defvar window_${i}_${j}_visible true)\n"
            window_yuck+="(defvar window_${i}_${j}_nid \"\")\n"
            window_yuck+="(defwidget widget_window_${i}_${j} []\n"
            window_yuck+="(revealer\n"
            window_yuck+="  :reveal {window_${i}_${j}_icon != \"\" || window_${i}_${j}_label != \"\"}\n"
            window_yuck+="  :duration \"1000ms\"\n"
            window_yuck+="  :transition \"slideright\"\n"
            window_yuck+="  :halign ${HALIGN}\n"
            # window_yuck+="  :valign ${VALIGN}\n"
            window_yuck+="  (box\n"
            # window_yuck+="    :class \"ws_window \${window_${i}_${j}_class} \${window_${i}_${j}_focused?\"focused\":\"defocused\"}\"\n"
            window_yuck+="    :class \"ws_window \${window_${i}_${j}_class} \${focused_window == window_${i}_${j}_nid ? \"focused\" : \"defocused\"}\"\n"
            # window_yuck+="    :visible {window_${i}_${j}_icon != \"\" || window_${i}_${j}_label != \"\"}\n"
            window_yuck+="    :spacing 0\n"
            # window_yuck+="    :valign ${VALIGN}\n"
            window_yuck+="    :width 40\n"
            window_yuck+="    :height 40\n"
            window_yuck+="    (eventbox\n"
            window_yuck+="      :onclick \"bspc node \${window_${i}_${j}_nid} --flag hidden=off; bspc node -f \${window_${i}_${j}_nid}\"\n"
            window_yuck+="      (box(image\n"
            window_yuck+="      :path window_${i}_${j}_icon\n"
            window_yuck+="      :image-width 36\n"
            window_yuck+="      :image-height 36\n"
            window_yuck+="      :class \"ws_icon\"\n"
            # window_yuck+="      :visible {window_${i}_${j}_icon != \"\"}\n"
            window_yuck+="      :halign ${HALIGN}\n"
            # window_yuck+="      :valign ${VALIGN}\n"
            window_yuck+="    )\n"
            window_yuck+="    (label\n"
            window_yuck+="      :text window_${i}_${j}_label\n"
            window_yuck+="      :halign ${HALIGN}\n"
            window_yuck+="      :valign ${VALIGN}\n"
            window_yuck+="      :class \"ws_label\"\n"
            window_yuck+="      :visible {window_${i}_${j}_label != \"\"}\n"
            window_yuck+="    )))\n"
            window_yuck+="  ))\n"
            window_yuck+=")\n"

            desktop_yuck+="${window_yuck}"
        done
        desktops_yuck+="${desktop_yuck}"

        desktops_yuck+="(defwidget desktop_${i} []\n"
        desktops_yuck+="(revealer\n"
        desktops_yuck+="  :reveal {desktop_${i}_visible}\n"
        # desktops_yuck+="  :reveal {desktop_${i}_icon != \"\" || desktop_${i}_label != \"\"}\n"
        # desktops_yuck+="  :visible {desktop_${i}_icon != \"\" || desktop_${i}_label != \"\"}\n"
        desktops_yuck+="  :duration \"500ms\"\n"
        desktops_yuck+="  :transition \"slideright\"\n"
        desktops_yuck+="  :halign ${HALIGN}\n"
        desktops_yuck+="  (box\n"
        # desktops_yuck+="    :class \"ws_desktop \${desktop_${i}_class} \${desktop_${i}_focused?\"focused\":\"defocused\"}\"\n"
        desktops_yuck+="    :class \"ws_desktop \${desktop_${i}_class} \${focused_desktop == desktop_${i}_did ? \"focused\" : \"defocused\"} \${desktop_${i}_icon != \"\" || desktop_${i}_label != \"\" ? \"visible\" : \"invisible\"}\"\n"
        # desktops_yuck+="    :visible {desktop_${i}_icon != \"\" || desktop_${i}_label != \"\"}\n"
        desktops_yuck+="    :spacing 0\n"
        desktops_yuck+="    :space-evenly false\n"
        desktops_yuck+="    :halign ${HALIGN}\n"
        # desktops_yuck+="    :valign ${VALIGN}\n"
        # desktops_yuck+="    :width {desktop_${i}_ts + 2 > EWW_TIME? 100 : -1}\n"
        # desktops_yuck+="    :height 44\n"
        desktops_yuck+="    (eventbox\n"
        desktops_yuck+="      :onclick \"bspc desktop -f ^${i}\"\n"
        desktops_yuck+="      (box\n"
        desktops_yuck+="        (image\n"
        desktops_yuck+="          :path desktop_${i}_icon\n"
        desktops_yuck+="          :image-width {desktop_${i}_icon == \"\" ? 0 : 36}\n"
        desktops_yuck+="          :image-height {desktop_${i}_icon == \"\" ? 0 : 36}\n"
        desktops_yuck+="          :class \"ws_icon\"\n"
        desktops_yuck+="          :visible {desktop_${i}_icon != \"\"}\n"
        desktops_yuck+="          :halign ${HALIGN}\n"
        # desktops_yuck+="          :valign ${VALIGN}\n"
        desktops_yuck+="        )\n"
        desktops_yuck+="        (label\n"
        desktops_yuck+="          :text desktop_${i}_label\n"
        desktops_yuck+="          :class \"ws_label\"\n"
        desktops_yuck+="          :halign ${HALIGN}\n"
        desktops_yuck+="          :valign ${VALIGN}\n"
        # desktops_yuck+="          :visible {desktop_${i}_label != \"\"}\n"
        desktops_yuck+="        )\n"
        desktops_yuck+="      )\n"
        desktops_yuck+="    )\n"
        for j in $(seq 1 $n_windows); do
            desktops_yuck+="    (widget_window_${i}_${j})\n"
        done
        desktops_yuck+="  ))\n"
        desktops_yuck+=")\n"
    done

    desktops_yuck+="(defwidget widget_desktops []\n"
    desktops_yuck+="  (box\n"
    desktops_yuck+="    :spacing 0\n"
    desktops_yuck+="    :halign ${HALIGN}\n"
    desktops_yuck+="    :valign ${VALIGN}\n"
    desktops_yuck+="    :space-evenly false\n"
    desktops_yuck+="    :class \"workspaces\"\n"
    for i in $(seq 1 $n_desktops); do
        desktops_yuck+="    (desktop_${i})\n"
    done
    desktops_yuck+="  )\n"
    desktops_yuck+=")\n"

    printf "%b" "${desktops_yuck}" >"workspaces.yuck"
}

generate_desktops
