#!/usr/bin/env python3

"""
Generate the workspaces.yuck file.
"""

from argparse import ArgumentParser
from pathlib import Path


class RawExp(str):
    pass


class DefWidget:
    def __init__(self, name, *args, children=None, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.children = children

    # defwidget widgetName [arg1 ...]
    #   :key1 value1s
    #   :... ...
    #   child1
    #   ...

    def print(self, indent=0):
        indentStr = " " * 2 * indent
        out = []
        out.append(f"{indentStr}(defwidget {self.name} [{' '.join(self.args)}]")
        for key, value in self.kwargs.items():
            out.append(f"{indentStr}  :{key} {value}")
        if self.children:
            for cName in self.children:
                if isinstance(cName, RawExp):
                    out.append(f"{indentStr}  ({cName})")
                elif isinstance(cName, str):
                    out.append(f'{indentStr}  "{cName}"')
                elif isinstance(cName, UseWidget):
                    out.extend(cName.print(indent + 1))

        out.append(f"{indentStr})")

        return out


class DefVar:
    def __init__(self, name, defaultVal):
        self.name = name
        self.defaultVal = defaultVal

        if isinstance(defaultVal, str):
            self.defaultVal = f'"{defaultVal}"'
        elif isinstance(defaultVal, bool):
            self.defaultVal = "true " if defaultVal else "false"
        elif isinstance(defaultVal, int):
            self.defaultVal = str(defaultVal)
        else:
            raise ValueError(f"Unsupported type for defaultVal: {type(defaultVal)}")

    def print(self, indent=0):
        indentStr = " " * 2 * indent
        return f"{indentStr}(defvar {self.name} {self.defaultVal})"


class UseWidget:
    def __init__(self, name, children=None, **kwargs):
        kwargs_ = kwargs.copy()
        for k, v in kwargs.items():
            if k == "class_":
                kwargs_["class"] = v
                del kwargs_[k]
            elif "_" in k:
                kwargs_[k.replace("_", "-")] = v
                del kwargs_[k]

        kwargs = kwargs_

        self.name = name
        self.kwargs = kwargs
        self.children = children

    def print(self, indent=0):
        indentStr = " " * 2 * indent
        out = []
        out.append(f"{indentStr}({self.name}")
        for key, value in self.kwargs.items():
            if isinstance(value, RawExp):
                out.append(f"{indentStr}  :{key} {value}")
            elif isinstance(value, str):
                out.append(f'{indentStr}  :{key} "{value}"')
            elif isinstance(value, bool):
                b = "true" if value else "false"
                out.append(f"{indentStr}  :{key} {b}")
            elif isinstance(value, int):
                out.append(f"{indentStr}  :{key} {value}")

        if self.children:
            for cName in self.children:
                if isinstance(cName, RawExp):
                    out.append(f"{indentStr}  ({cName})")
                elif isinstance(cName, str):
                    out.append(f"{indentStr}  {cName}")
                elif isinstance(cName, UseWidget):
                    out.extend(cName.print(indent + 1))
                else:
                    raise ValueError(f"Unsupported type for child: {type(cName)}")
        out.append(f"{indentStr})")

        return out


def defWindow(mi, di, wi):
    icon = UseWidget(
        "image",
        class_="icon",
        path=RawExp(f"window_{mi}_{di}_{wi}_icon"),
        image_width=36,
        image_height=36,
        halign="center",
        valign="center",
    )
    label = UseWidget(
        "label",
        class_="label",
        text=RawExp(f"window_{mi}_{di}_{wi}_label"),
        halign="center",
        valign="center",
    )

    iconLabel_box = UseWidget(
        "box",
        class_=(
            f"ws_window ${{window_{mi}_{di}_{wi}_class}} " +
            f'${{focused_window_{mi} == window_{mi}_{di}_{wi}_id? "focused" : "unfocused"}}'
        ),
        spacing=0,
        space_evenly=False,
        halign="center",
        valign="center",
        width=40,
        height=40,
        children=[
            icon,
            label,
        ],
    )

    iconLabel_evBox = UseWidget(
        "eventbox",
        onclick=f"bspc node -f ${{window_{mi}_{di}_{wi}_id}}",
        onrightclick=f"bspc node -c ${{window_{mi}_{di}_{wi}_id}}",
        children=[
            iconLabel_box,
        ],
    )

    iconLabel_revealer = UseWidget(
        "revealer",
        reveal=f'window_{mi}_{di}_{wi}_icon!="" || window_{mi}_{di}_{wi}_label!=""',
        duration="1000ms",
        transition="slideright",
        halign="center",
        valign="center",
        children=[
            iconLabel_evBox,
        ],
    )

    widget_window = DefWidget(
        f"ws_window_{mi}_{di}_{wi}",
        children=[
            iconLabel_revealer,
        ],
    )

    return widget_window


def defDesktop(mi, di, nWindows):
    icon = UseWidget(
        "image",
        class_="icon",
        path=RawExp(f"desktop_{mi}_{di}_icon"),
        image_width=36,
        image_height=36,
        halign="center",
        valign="center",
    )
    label = UseWidget(
        "label",
        class_="label",
        text=RawExp(f"desktop_{mi}_{di}_label"),
        halign="center",
        valign="center",
    )

    iconLabel_box = UseWidget(
        "box",
        class_=(
            f'ws_desktop ${{desktop_{mi}_{di}_class}} '
            + f'${{focused_desktop_{mi} == desktop_{mi}_{di}_id? "focused" : "unfocused"}} '
            + f'${{desktop_{mi}_{di}_visible ? "visible" : "invisible"}}'
        ),
        spacing=0,
        space_evenly=False,
        halign="center",
        valign="center",
        width=40,
        height=40,
        children=[
            icon,
            label,
        ],
    )

    iconLabel_evBox = UseWidget(
        "eventbox",
        onclick=f"bspc desktop -f {{desktop_{mi}_{di}_id}}",
        onrightclick=f"bspc desktop -r -f {{desktop_{mi}_{di}_id}}",
        children=[
            iconLabel_box,
        ],
    )

    iconLabel_revealer = UseWidget(
        "revealer",
        reveal=RawExp(f'{{desktop_{mi}_{di}_icon != "" || desktop_{mi}_{di}_label != ""}}'),
        duration="1000ms",
        transition="slideright",
        halign="center",
        valign="center",
        children=[
            iconLabel_evBox,
        ],
    )
    children = [iconLabel_revealer]
    children += [RawExp(f"ws_window_{mi}_{di}_{wi}") for wi in range(1, nWindows + 1)]

    widget_desktop = DefWidget(
        RawExp(f"(ws_desktop_{mi}_{di})"),
        children=children,
    )

    return widget_desktop


def defMonitor(mi, numDesktops=10):
    desktops = [RawExp(f"ws_desktop_{mi}_{di}") for di in range(1, numDesktops + 1)]
    box = UseWidget(
        "box",
        class_="ws_monitor",
        spacing=0,
        halign="center",
        valign="center",
        space_evenly=False,
        children=desktops,
    )

    return DefWidget(
        f"ws_monitor_{mi}",
        children=[box],
    )


def main():
    N_MONITORS = 2
    N_DESKTOPS = 10
    N_WINDOWS = 10
    OUTFILE = "workspaces2.yuck"

    parser = ArgumentParser()

    parser.add_argument("--n-monitors", type=int, default=N_MONITORS)
    parser.add_argument("--n-desktops", type=int, default=N_DESKTOPS)
    parser.add_argument("--n-windows", type=int, default=N_WINDOWS)
    parser.add_argument("--output", type=str, default=OUTFILE)

    args = parser.parse_args()

    N_MONITORS = args.n_monitors
    N_DESKTOPS = args.n_desktops
    N_WINDOWS = args.n_windows
    OUTFILE = Path(args.output)

    outs = []
    for mi in range(1, N_MONITORS + 1):
        outs.append(DefVar(f"focused_window_{mi}", -2))
        outs.append(DefVar(f"focused_desktop_{mi}", -2))
        for di in range(1, N_DESKTOPS + 1):
            for wi in range(1, N_WINDOWS + 1):
                outs.append(DefVar(f"window_{mi}_{di}_{wi}_id", -1))
                outs.append(DefVar(f"window_{mi}_{di}_{wi}_class", ""))
                outs.append(DefVar(f"window_{mi}_{di}_{wi}_icon", ""))
                outs.append(DefVar(f"window_{mi}_{di}_{wi}_label", ""))
                w = defWindow(mi, di, wi)
                outs.append(w)
            outs.append(DefVar(f"desktop_{mi}_{di}_id", -1))
            outs.append(DefVar(f"desktop_{mi}_{di}_class", ""))
            outs.append(DefVar(f"desktop_{mi}_{di}_icon", ""))
            outs.append(DefVar(f"desktop_{mi}_{di}_label", ""))
            outs.append(DefVar(f"desktop_{mi}_{di}_visible", False))

            d = defDesktop(mi, di, N_WINDOWS)
            outs.append(d)

        m = defMonitor(mi, N_DESKTOPS)
        outs.append(m)

    outs_ = []
    for o in outs:
        if isinstance(o, DefVar):
            outs_.append(o.print())
        elif isinstance(o, DefWidget):
            outs_.extend(o.print())
        elif isinstance(o, UseWidget):
            outs_.extend(o.print())
        else:
            raise ValueError(f"Unsupported type for o: {type(o)}")

    outs_ = "\n".join(outs_)

    with OUTFILE.open("w") as f:
        f.write(outs_)


if __name__ == "__main__":
    main()
