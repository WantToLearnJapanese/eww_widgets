#!/usr/bin/env python3

import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

log_fp = open("/tmp/eww_ws.log", "a")
print_org = print
sys.stderr = log_fp

CLASS_BLACKLIST = set(
    [
        "kakaotalk.exe",
    ]
)


def print(*args, **kwargs):
    print_org(*args, **kwargs, file=log_fp)
    log_fp.flush()


DESKTOPS = dict()


class NodeException(Exception):
    pass


class NodeBlacklisted(NodeException):
    pass


class NodeFloating(NodeException):
    pass


class NodeSticky(NodeException):
    pass


class NodeHidden(NodeException):
    pass


class OrderNodes:
    """Depth First Search for Nodes"""

    @staticmethod
    def dfs(
        root: dict | None,  # "id", "firstChild", "secondChild"
    ) -> list[int]:  # returns ordered list of node IDs
        if root is None:
            return []

        visited = set()
        ordered = []

        def dfs_(node):
            nId = node.get("id", None)
            print("nId: ", nId)
            if node["id"] in visited:
                return
            visited.add(node["id"])
            if node.get("client", None) is not None:
                ordered.append(node["id"])
            if node["firstChild"]:
                dfs_(node["firstChild"])
            if node["secondChild"]:
                dfs_(node["secondChild"])

        dfs_(root)

        return ordered


class Icon:
    """
    Get
      * png file from _NET_WM_ICON by xprop
      * path to the icon under "/usr/share/icons" or "~/.local/share/icons"
    """

    _ICON_PATH_CACHE = dict()

    @staticmethod
    def icon_from_path(
        instanceName: str,
        className,
        exts=set([".png", ".svg"]),
        paths=[Path("/usr/share/icons"), Path.home() / ".local/share/icons"],
    ):
        for ext in exts:
            icon_path = Path.home() / f".cache/eww/{instanceName}-{className}{ext}"
            if icon_path.exists():
                Icon._ICON_PATH_CACHE[(instanceName, className)] = str(icon_path)
                return str(icon_path)
        target_stems = [
            instanceName,
            className,
            className.lower().replace(" ", "-"),
        ]
        if className == "Google-chrome" and instanceName.startswith("crx_"):
            target_stem = instanceName.replace("crx_", "chrome-") + "-Default"
            target_stems.append(target_stem)

        for path in paths:
            for d in path.rglob("*"):
                if not d.is_dir():
                    continue
                for ext in exts:
                    for s in target_stems:
                        f = d / f"{s}{ext}"
                        if f.exists():
                            p = (
                                Path.home()
                                / f".cache/eww/{instanceName}-{className}{ext}"
                            )
                            p.parent.mkdir(parents=True, exist_ok=True)
                            p.unlink(missing_ok=True)
                            p.symlink_to(f)
                            Icon._ICON_PATH_CACHE[(instanceName, className)] = str(p)
                            return str(p)
        return ""

    @staticmethod
    def icon_from_xprop(window_id, instanceName, className):
        icon_path = Path.home() / ".cache" / "eww" / f"{instanceName}-{className}.png"
        icon_path.parent.mkdir(parents=True, exist_ok=True)
        if icon_path.exists():
            Icon._ICON_PATH_CACHE[(instanceName, className)] = str(icon_path)
            return str(icon_path)

        if (
            className == "Google-chrome"
            and instanceName.startswith("crx_")
            and instanceName.startswith("jetbrains")
        ):
            # Chrome PWAs delay the setting of the icon
            time.sleep(1.5)

        xprop_cmd = f"xprop -id {window_id} -notype 32c _NET_WM_ICON"
        xprop_output = subprocess.check_output(xprop_cmd, shell=True).decode()

        # The output is in following format
        # """_NET_WM_DATA = height, width, uin32[, ...]""""
        # uint32 is the rgba value of the pixel in decimal
        # note that sepertor is comma.
        if not xprop_output.startswith("_NET_WM_ICON = "):
            return ""

        hw_rgbas = xprop_output.split("=")[1].strip().split(",")
        h, w = int(hw_rgbas[0]), int(hw_rgbas[1])
        argbs = [int(abgr) for abgr in hw_rgbas[2 : 2 + h * w]]

        if len(argbs) != h * w:
            return ""

        # Convert argb to rgba
        rgbas = []
        for argb in argbs:
            a = (argb >> 24) & 0xFF
            r = (argb >> 16) & 0xFF
            g = (argb >> 8) & 0xFF
            b = argb & 0xFF
            rgbas.append((r, g, b, a))

        # Create image
        img = Image.new("RGBA", (w, h))
        img.putdata(rgbas)

        # Save image
        img.save(icon_path)

        # Set cache
        Icon._ICON_PATH_CACHE[(instanceName, className)] = str(icon_path)

        return str(icon_path)

    @staticmethod
    def get_path2(w_id, instanceName, className):
        if (instanceName, className) in Icon._ICON_PATH_CACHE:
            return Icon._ICON_PATH_CACHE[(instanceName, className)]

        if className == "Google-chrome" and instanceName.startswith("crx_"):
            icon_path = Icon.icon_from_path(instanceName, className)
            if icon_path:
                return icon_path
            return Icon.icon_from_xprop(w_id, instanceName, className)
        else:
            icon_path = Icon.icon_from_xprop(w_id, instanceName, className)
            if icon_path:
                return icon_path
            return Icon.icon_from_path(instanceName, className)


class Node:

    def __init__(
        self,
        mId,
        dId,
        nId,
        mIdx,
        dIdx,
        nIdx,
        instanceName=None,
        className=None,
        title=None,
        focused=False,
        icon: str = "",
        pos_x: int | None = 0,  # tiled position
        pos_y: int | None = 0,
    ):
        self._mId = mId
        self._dId = dId
        self._id = nId
        self._mIdx = mIdx
        self._dIdx = dIdx
        self._idx = nIdx
        self._focussed = focused

        # Get wClass, wTitle
        if instanceName is None or title is None:
            bspc_cmd = f"bspc query -T -n {self._id}"
            print("bspc_cmd: ", bspc_cmd)
            try:
                bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
            except subprocess.CalledProcessError as e:
                raise NodeException(f"Node not found: {self._id}")
            node = json.loads(bspc_output)
            is_floating = node["client"]["state"] == "floating"
            is_sticky = node["sticky"]
            is_hidden = node["hidden"]
            instanceName = node["client"]["instanceName"]
            className = node["client"]["className"]
            pos_x = node["client"]["tiledRectangle"]["x"]
            pos_y = node["client"]["tiledRectangle"]["y"]

            xprop_cmd = f"xprop -id {self._id} _NET_WM_NAME"
            try:
                xprop_output = subprocess.check_output(xprop_cmd, shell=True).decode()
            except subprocess.CalledProcessError as e:
                raise NodeException(f"Node not found: {self._id}")
            title = xprop_output.split("=")[1].strip()

            if is_floating:
                raise NodeFloating(f"Floating class: {instanceName}-{className}")
            if is_sticky:
                raise NodeSticky(f"Sticky class: {instanceName}-{className}")
            if is_hidden:
                raise NodeHidden(f"Hidden class: {instanceName}-{className}")
            if instanceName in CLASS_BLACKLIST:
                raise NodeBlacklisted(f"Blacklisted class: {instanceName}-{className}")

        self._instanceName = instanceName
        self._className = className
        self._title = title
        self._pos_x = pos_x
        self._pos_y = pos_y

        # Set icon
        if icon == "":
            self._icon = Icon.get_path2(self._id, self._instanceName, self._className)
        else:
            self._icon = icon
        if nIdx is not None:
            self.set_eww()

    @property
    def mId(self):
        return self._mId

    @property
    def dId(self):
        return self._dId

    @property
    def id_(self):
        return self._id

    @property
    def mIdx(self):
        return self._mIdx

    @property
    def dIdx(self):
        return self._dIdx

    @property
    def idx(self):
        return self._idx

    @property
    def class_(self):
        return self._instanceName

    @property
    def class2(self):
        return self._className

    @property
    def title(self):
        return self._title

    @property
    def focussed(self):
        return self._focussed

    @property
    def icon(self):
        return self._icon

    @property
    def pos_x(self):
        return self._pos_x

    @property
    def pos_y(self):
        return self._pos_y

    @classmethod
    def new(cls: "Node", w: "Node") -> "Node":
        return cls(
            w.mId,
            w.dId,
            w.id_,
            w.mIdx,
            w.dIdx,
            w.idx,
            w.class_,
            w.class2,
            w.title,
            w.focussed,
            w.icon,
            w.pos_x,
            w.pos_y,
        )

    def setIdx(
        self,
        nIdx,
        forceRefresh=False,
        disableUnset=False,
        forceUnfocus=False,
    ):
        oldIdx = self._idx
        newIdx = nIdx
        # if newIdx == oldIdx and not forceRefresh:
        # return
        if not disableUnset and oldIdx and newIdx and newIdx < oldIdx:
            self.unset_eww()
        self.unfocus(force=forceUnfocus)
        self._idx = newIdx
        self.set_eww()

    def set_eww(self):
        eww_cmd_icon = "eww update "
        eww_cmd_icon += f"window_{self._mIdx}_{self._dIdx}_{self._idx}_icon="
        eww_cmd_icon += f'"{self._icon}"'
        print("eww_cmd_icon: ", eww_cmd_icon)
        subprocess.run(eww_cmd_icon, shell=True)

        # eww_cmd_label = "eww update "
        # eww_cmd_label += f"window_{self._dIdx}_{self._idx}_label="
        # eww_cmd_label += f"\"{self._title}\""
        # subprocess.run(eww_cmd_label, shell=True)

        eww_cmd_nid = "eww update "
        eww_cmd_nid += f"window_{self._mIdx}_{self._dIdx}_{self._idx}_id="
        eww_cmd_nid += f"{self._id}"
        subprocess.run(eww_cmd_nid, shell=True)

    def unset_eww(self):
        eww_cmd_icon = "eww update "
        eww_cmd_icon += f"window_{self._mIdx}_{self._dIdx}_{self._idx}_icon="
        eww_cmd_icon += '""'
        print("eww_cmd_icon: ", eww_cmd_icon)
        subprocess.run(eww_cmd_icon, shell=True)

        # eww_cmd_label = "eww update "
        # eww_cmd_label += f"window_{self._dIdx}_{self._idx}_label="
        # eww_cmd_label += '""'
        # subprocess.run(eww_cmd_label, shell=True)

        eww_cmd_nid = "eww update "
        eww_cmd_nid += f"window_{self._mIdx}_{self._dIdx}_{self._idx}_id="
        eww_cmd_nid += '""'
        subprocess.run(eww_cmd_nid, shell=True)

        self.unfocus()

    def focus(self):
        eww_cmd_focused = "eww update "
        eww_cmd_focused += f"focused_window_{self._mIdx}="
        eww_cmd_focused += f"{self._id}"

    def unfocus(self, force=False):
        pass


class Desktop:

    def __init__(
        self,
        mId,
        dId,
        mIdx,
        dIdx=None,
        focused=False,
    ):
        self._mId = mId
        self._mIdx = mIdx
        self._id = dId
        self._focused = focused
        self._nId2Node = dict()  # type: dict[int, Node]

        # Get desktopIdx from "bspc query -D"
        if dIdx is None:
            dIdx = self.getLiveIndex()
        self._idx = dIdx

        self.set_eww()

    def getLiveIndex(self) -> int:
        bspc_cmd = f"bspc query -D -m {self._mId}"
        bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
        dIdxes = bspc_output.split("\n")
        dIdxes = [int(dIdx, 0) for dIdx in dIdxes if dIdx]
        return dIdxes.index(self._id) + 1

    def updateIdx(self, forceRefresh=False):
        newIdx = self.getLiveIndex()
        oldIdx = self._idx
        if newIdx == oldIdx and not forceRefresh:
            return
        self.unset_eww()
        for n in self.nodes:
            n.unset_eww()
        self._idx = newIdx
        self.set_eww()

        if forceRefresh:
            self.refresh_nodes()

        for n in self.nodes:
            n._dIdx = newIdx
            n.set_eww()

    @classmethod
    def new(cls: "Desktop", d: "Desktop") -> "Desktop":
        return cls(d.mId, d.id_, d.mIdx, d.idx, d.focused)

    @property
    def mId(self):
        return self._mId

    @property
    def mIdx(self):
        return self._mIdx

    @property
    def focused(self):
        return self._focused

    @property
    def id_(self):
        return self._id

    @property
    def idx(self):
        return self._idx

    @property
    def nodes(self) -> list[Node]:
        return self._nId2Node.values()

    def node_add_new(self, nId) -> Node:
        n = Node(self._mId, self._id, nId, self._mIdx, self._idx, None)
        self._nId2Node[nId] = n
        return n

    def node_add(self, n: Node, disableRefresh=False) -> Node:
        n_ = Node.new(n)

        self._nId2Node[n.id_] = n_
        print("node_add: ", n.id_, n.class_)

        if not disableRefresh:
            self.refresh_nodes()

        return n_

    def node_remove(
        self,
        nId,
        disableUnset=False,
        disableRefresh=False,
        forceUnfocus=False,
    ) -> Node:
        print("--node remove--")
        print("  * d nodes: ")
        for n in self.nodes:
            print(n.id_, n.class_)
        n = self._nId2Node.pop(nId, None)
        if n is None:
            print(" * node not found")
            return

        if not disableUnset:
            n.unset_eww()
        if forceUnfocus:
            n.unfocus(force=True)

        print("node_remove: ", n.id_, n.class_)

        if not disableRefresh and len(self._nId2Node) > 0:
            self.refresh_nodes()

        return n

    def refresh_nodes(self, disableUnset=False, forceRefresh=True):
        # bspc query -T -d <desktop_id> returns the tree of the desktop
        bspc_cmd = f"bspc query -T -d {self._id}"
        bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
        tree = json.loads(bspc_output)
        root = tree["root"]
        node_order = OrderNodes.dfs(root)  # list[int]  # list of node Ids

        i = 1
        for nId in node_order:
            n_ = self._nId2Node.get(nId, None)
            if n_ is None:
                continue
            print(f"{i}: {nId}, {n_.class_}")
            n_.setIdx(i, forceRefresh=forceRefresh, disableUnset=disableUnset)
            i += 1

    def __getitem__(self, nId) -> Node:
        return self._nId2Node.get(nId, None)

    def focus(self):
        eww_cmd = "eww update "
        eww_cmd += f"focused_desktop_{self._mIdx}="
        eww_cmd += f"{self._id}"
        subprocess.run(eww_cmd, shell=True)
        self._focused = True

    def unfocus(self):
        pass

    def set_eww(self):
        eww_cmd_label = "eww update "
        eww_cmd_label += f"desktop_{self._mIdx}_{self._idx}_label="
        eww_cmd_label += f'"{self._idx}"'
        subprocess.run(eww_cmd_label, shell=True)

        eww_cmd_dId = "eww update "
        eww_cmd_dId += f"desktop_{self._mIdx}_{self._idx}_id="
        eww_cmd_dId += f'"{self._id}"'
        subprocess.run(eww_cmd_dId, shell=True)

        eww_cmd_visible = "eww update "
        eww_cmd_visible += f"desktop_{self._mIdx}_{self._idx}_visible="
        eww_cmd_visible += "true"
        subprocess.run(eww_cmd_visible, shell=True)

    def unset_eww(self):
        # eww_cmd_label = "eww update "
        # eww_cmd_label += f"desktop_{self._idx}_label="
        # eww_cmd_label += '""'

        eww_cmd_visible = "eww update "
        eww_cmd_visible += f"desktop_{self._idx}_visible="
        eww_cmd_visible += "false"
        subprocess.run(eww_cmd_visible, shell=True)


class Monitor:

    def __init__(
        self,
        mId,
        mIdx=None,
    ):
        self._dId2Desktop = dict()
        self._id = mId

        # Get monitorIdx from "bspc query -M"
        if mIdx is None:
            mIdx = self.getLiveIndex()
        self._idx = mIdx

    @property
    def id_(self):
        return self._id

    @property
    def idx(self):
        return self._idx

    @property
    def desktops(self) -> list[Desktop]:
        return self._dId2Desktop.values()

    def getLiveIndex(self) -> int:
        bspc_cmd = "bspc query -M"
        bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
        mIdxes = bspc_output.split("\n")
        mIdx = mIdxes.index(self._id)
        return mIdx + 1

    def updateIdx(self):
        newIdx = self.getLiveIndex()
        oldIdx = self._idx
        if newIdx == oldIdx:
            return
        self.unset_eww()
        self._idx = newIdx
        self.set_eww()

    @classmethod
    def new(cls: "Monitor", m: "Monitor") -> "Monitor":
        return cls(m.id_, m.idx)

    def desktop_add_new(self, dId) -> Desktop:
        d = Desktop(self._id, dId, self._idx)
        self._dId2Desktop[dId] = d
        return d

    def desktop_add(self, d: Desktop) -> Desktop:
        d_ = Desktop.new(d)
        d_.updateIdx()
        self._dId2Desktop[d.id_] = d_
        return d_

    @staticmethod
    def _query_nodes(dJson):
        nodes = []

        def dfs(node):
            if node.get("firstChild", None) is not None:
                dfs(node["firstChild"])
            if node.get("secondChild", None) is not None:
                dfs(node["secondChild"])
            if node.get("client", None) is not None:
                nodes.append(node)

        if dJson.get("root", None) is None:
            return []
        dfs(dJson["root"])

        nIds = [n["id"] for n in nodes]
        return nIds

    @staticmethod
    def query_nodes(dId):
        bspc_cmd = f"bspc query -T -d {dId}"
        bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
        dJson = json.loads(bspc_output)
        nIds = Monitor._query_nodes(dJson)
        return nIds

    def desktop_remove(self, dId) -> Desktop:
        d = self._dId2Desktop.pop(dId, None)  # type: Desktop
        if d is None:
            return

        has_trailingDs = False
        for d_ in self._dId2Desktop.values():
            if d_.idx > d.idx:
                has_trailingDs = True
                break
        if not has_trailingDs:
            for n_ in d.nodes:
                n_.unset_eww()
            d.unset_eww()
        transfer_nId2dId = {n.id_: -1 for n in d.nodes}

        if len(transfer_nId2dId) == 0:
            for d_2 in self._dId2Desktop.values():
                if d_2.idx > d.idx:
                    d_2.updateIdx(forceRefresh=False)
                # d_2.updateIdx(forceRefresh=True)
            return d

        for d_ in self._dId2Desktop.values():
            destruct_nIds = Monitor.query_nodes(d_.id_)

            for nId in destruct_nIds:
                if nId in transfer_nId2dId:
                    transfer_nId2dId[nId] = d_.id_

        d_ = None
        for nId, dId in transfer_nId2dId.items():
            d_ = self._dId2Desktop[dId]  # type: Desktop
            try:
                d_.node_add_new(nId)
            except NodeException as e:
                print("NodeException: ", e)
                continue

        if d_:
            d_.updateIdx(forceRefresh=False)
            d_.updateIdx(forceRefresh=True)

        for d_2 in self._dId2Desktop.values():
            if d_2.idx > d.idx:
                d_2.updateIdx(forceRefresh=False)
                d_2.updateIdx(forceRefresh=True)
        return d

    def __getitem__(self, desktopId) -> Desktop:
        return self._dId2Desktop.get(desktopId, None)

    def eww_set(self):
        pass

    def eww_unset(self):
        pass


class WM:

    def __init__(self):
        self._mId2Monitor = dict()  # type: dict[str, Monitor]

    def monitor_add(self, mId) -> Monitor:
        m = self._mId2Monitor[mId] = Monitor(mId)
        m.updateIdx()
        return m

    def monitor_remove(self, mId) -> Monitor:
        print("--monitor remove--")
        m = self._mId2Monitor.pop(mId)
        m.eww_unset()
        for m_ in self._mId2Monitor.values():
            m_.updateIdx()
        return m

    def monitor_focus(self, mId) -> Monitor:
        m = self._mId2Monitor[mId]
        if m is None:
            return
        m.focus()
        for m_ in self._mId2Monitor.values():
            if m_ is not m:
                m_.unfocus()
        return m

    def desktop_add(self, mId, dId) -> Desktop:
        m = self._mId2Monitor[mId]  # type: Monitor | None
        if m is None:
            return
        d = m.desktop_add_new(dId)
        return d

    def desktop_remove(self, mId, dId) -> Desktop:
        m = self._mId2Monitor[mId]  # type: Monitor
        if m is None:
            return
        m.desktop_remove(dId)
        # for d_ in m.desktops:
        # d_.updateIdx(forceRefresh=True)
        return m

    def desktop_swap(
        self, src_mId, src_dId, dst_mId, dst_dId
    ) -> tuple[Desktop, Desktop]:
        src_m = self._mId2Monitor[src_mId]  # type: Monitor
        dst_m = self._mId2Monitor[dst_mId]  # type: Monitor
        if src_m is None or dst_m is None:
            return None, None
        src_d = src_m.desktop_remove(src_dId)  # type: Desktop
        dst_d = dst_m.desktop_remove(dst_dId)  # type: Desktop
        if src_d is None or dst_d is None:
            return None, None
        src_m.desktop_add(dst_d)
        dst_m.desktop_add(src_d)

        return src_d, dst_d

    def desktop_transfer(self, src_mId, dId, dst_mId) -> Desktop:
        src_m = self._mId2Monitor[src_mId]
        dst_m = self._mId2Monitor[dst_mId]
        if src_m is None or dst_m is None:
            return
        d = src_m.desktop_remove(dId)
        if d is None:
            return
        d_ = dst_m.desktop_add(d)
        return d_

    def desktop_focus(self, mId, dId):
        m = self._mId2Monitor[mId]
        if m is None:
            return
        d = m[dId]
        if d is None:
            return
        d.focus()

    def node_add(self, mId, dId, nId) -> Node | None:
        m = self._mId2Monitor[mId]
        if m is None:
            return
        d = m[dId]
        if d is None:
            return
        try:
            n = d.node_add_new(nId)
            d.refresh_nodes(disableUnset=True)
            return n
        except NodeException as e:
            print("NodeException: ", e)
            return

    def node_remove(self, mId, dId, nId):
        m = self._mId2Monitor[mId]
        if m is None:
            return
        d = m[dId]  # type: Desktop
        if d is None:
            return
        d.node_remove(nId, disableRefresh=False)
        # d.node_remove(nId, disableRefresh=True)
        # d.refresh_nodes()

    def node_swap(self, src_mId, src_dId, src_nId, dst_mId, dst_dId, dst_nId):
        print("--node swap--")
        src_m = self._mId2Monitor[src_mId]
        dst_m = self._mId2Monitor[dst_mId]
        if src_m is None or dst_m is None:
            return
        src_d = src_m[src_dId]  # type: Desktop
        dst_d = dst_m[dst_dId]  # type: Desktop
        if src_d is None or dst_d is None:
            return
        src_n = src_d[src_nId]
        dst_n = dst_d[dst_nId]
        if src_n is None or dst_n is None:
            return
        src_focused = src_n.focussed
        dst_focused = dst_n.focussed
        print("  * remove nodes")
        print("  * src_d nodes: ")
        for n in src_d.nodes:
            print(n.id_, type(n.id_), n.class_)
        print("    * src_n: ", src_n.id_, type(src_n.id_), src_n.class_)
        src_d.node_remove(
            src_n.id_, disableUnset=True, disableRefresh=True, forceUnfocus=True
        )
        dst_d.node_remove(
            dst_n.id_, disableUnset=True, disableRefresh=True, forceUnfocus=True
        )

        print("  * add nodes")
        dst_n = src_d.node_add_new(dst_nId)
        src_n = dst_d.node_add_new(src_nId)

        print("  * refresh nodes")
        src_d.refresh_nodes()
        if src_d != dst_d:
            dst_d.refresh_nodes()

        if src_focused:
            src_n.focus()
        if dst_focused:
            dst_n.focus()

    def node_transfer(self, src_mId, src_dId, src_nId, dst_mId, dst_dId, dst_nId):
        src_monitor = self._mId2Monitor[src_mId]
        dst_monitor = self._mId2Monitor[dst_mId]
        if src_monitor is None or dst_monitor is None:
            return
        src_desktop = src_monitor[src_dId]
        dst_desktop = dst_monitor[dst_dId]
        if src_desktop is None or dst_desktop is None:
            return
        src_window = src_desktop[src_nId]
        if src_window is None:
            return
        print(f"--node transfer {src_nId} to {dst_nId}--")
        print("  -src node: ", src_window.id_, src_window.class_)
        print("  -dst node: ", dst_nId)
        n = src_desktop.node_remove(src_nId)
        if n is None:
            return
        dst_desktop.node_add_new(src_nId)
        print("  -srcDesktop nodes: ")
        for n in src_desktop.nodes:
            print(n.id_, n.class_)
        print("  -dstDesktop nodes: ")
        for n in dst_desktop.nodes:
            print(n.id_, n.class_)

        print("--refresh nodes--")
        if len(src_desktop.nodes) > 0:
            src_desktop.refresh_nodes(disableUnset=True)
        if len(dst_desktop.nodes) > 0:
            dst_desktop.refresh_nodes(disableUnset=True)

    def node_focus(self, mId, dId, nId):
        m = self._mId2Monitor[mId]
        if m is None:
            return
        d = m[dId]
        if d is None:
            return
        n = d[nId]
        if n is None:
            return
        n.focus()

        return

    def ev_monitor_add(self, mId, _mName, _mGeometry):
        self.monitor_add(mId)

    def ev_monitor_remove(self, mId):
        self.monitor_remove(mId)

    def ev_desktop_add(self, mId, dId, _dName):
        dId = int(dId, 0)
        self.desktop_add(mId, dId)

    def ev_desktop_remove(self, mId, dId):
        dId = int(dId, 0)
        self.desktop_remove(mId, dId)

    def ev_desktop_swap(self, src_mId, src_dId, dst_mId, dst_dId):
        src_dId, dst_dId = int(src_dId, 0), int(dst_dId, 0)
        self.desktop_swap(src_mId, src_dId, dst_mId, dst_dId)

    def ev_desktop_transfer(self, src_mId, dId, dst_mId):
        dId = int(dId, 0)
        self.desktop_transfer(src_mId, dId, dst_mId)

    def ev_desktop_focus(self, mId, dId):
        dId = int(dId, 0)
        self.desktop_focus(mId, dId)

    def ev_node_add(self, mId, dId, _iId, nId):
        nId = int(nId, 0)
        dId = int(dId, 0)
        self.node_add(mId, dId, nId)

    def ev_node_remove(self, mId, dId, nId):
        nId = int(nId, 0)
        dId = int(dId, 0)
        self.node_remove(mId, dId, nId)

    def ev_node_swap(self, src_mId, src_dId, src_nId, dst_mId, dst_dId, dst_nId):
        src_nId, dst_nId = int(src_nId, 0), int(dst_nId, 0)
        src_dId, dst_dId = int(src_dId, 0), int(dst_dId, 0)
        self.node_swap(src_mId, src_dId, src_nId, dst_mId, dst_dId, dst_nId)

    def ev_node_transfer(self, src_mId, src_dId, src_nId, dst_mId, dst_dId, dst_nId):
        src_nId, dst_nId = int(src_nId, 0), int(dst_nId, 0)
        src_dId, dst_dId = int(src_dId, 0), int(dst_dId, 0)
        self.node_transfer(src_mId, src_dId, src_nId, dst_mId, dst_dId, dst_nId)

    def ev_node_focus(self, mId, dId, nId):
        nId = int(nId, 0)
        dId = int(dId, 0)
        self.node_focus(mId, dId, nId)

    def ev_node_state(self, mId, dId, nId, state, onOff):
        dId, nId = int(dId, 0), int(nId, 0)

        floating_on = state == "floating" and onOff == "on"
        tiled_on = (state == "tiled" or state == "pseudo_tiled") and onOff == "on"

        if floating_on:
            self.node_remove(mId, dId, nId)
        elif tiled_on:
            self.node_add(mId, dId, nId)

    def ev_node_flag(self, mId, dId, nId, flag, onOff):
        dId, nId = int(dId, 0), int(nId, 0)
        is_sticky = flag == "sticky" and onOff == "on"
        is_hidden = flag == "hidden" and onOff == "on"
        print("flag: ", flag, onOff, is_sticky, is_hidden)
        if is_sticky or is_hidden:
            self.node_remove(mId, dId, nId)
        else:
            self.node_add(mId, dId, nId)

    def _init_monitors(self):
        bspc_cmd = "bspc query -M"
        bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
        mIds = bspc_output.strip().split("\n")
        for mId in mIds:
            self.monitor_add(mId)

    def _init_desktops(self):
        for m in self._mId2Monitor.values():
            bspc_cmd = f"bspc query -D -m {m.id_}"
            bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
            dIds = bspc_output.strip().split("\n")
            dIds = [int(dId, 0) for dId in dIds]
            for dId in dIds:
                m.desktop_add_new(dId)

    def _init_nodes(self):
        for m in self._mId2Monitor.values():
            for d in m.desktops:
                bspc_cmd = f"bspc query -N -n .leaf -d {d.id_}"
                try:
                    bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
                except subprocess.CalledProcessError:
                    continue
                nIds = bspc_output.strip().split("\n")
                for nId in nIds:
                    # d.node_add_new(nId)
                    try:
                        d.node_add_new(int(nId, 0))
                    except NodeException as e:
                        print("NodeException: ", e)
                        continue
                d.refresh_nodes()

    def _init_from_dump(self):
        bspc_cmd = "bspc wm -d"
        bspc_output = subprocess.check_output(bspc_cmd, shell=True).decode()
        dump = json.loads(bspc_output)
        focused_dId = None
        focused_nId = None
        for mi, m in enumerate(dump["monitors"], 1):
            focused_dId = m["focusedDesktopId"]
            eww_cmd = "eww update "
            eww_cmd += f"focused_desktop_{mi}="
            eww_cmd += f"{focused_dId}"
            
            subprocess.run(eww_cmd, shell=True)
            for _di, d in enumerate(m["desktops"], 1):
                if d["id"] == focused_dId:
                    focused_nId = d["focusedNodeId"]
                    eww_cmd += f"focused_window_{mi}="
                    eww_cmd += f"{focused_nId}"
                    
                    subprocess.run(eww_cmd, shell=True)
                    break

    def init(self):
        self._init_monitors()
        self._init_desktops()
        self._init_nodes()
        self._init_from_dump()


def main():
    # redirect stdout to /tmp/eww_ws.log

    print("eww_ws started")

    wm = WM()
    wm.init()

    event_cbs = {
        "monitor_add": wm.ev_monitor_add,
        "monitor_remove": wm.ev_monitor_remove,
        "desktop_add": wm.ev_desktop_add,
        "desktop_remove": wm.ev_desktop_remove,
        "desktop_swap": wm.ev_desktop_swap,
        "desktop_transfer": wm.ev_desktop_transfer,
        "desktop_focus": wm.ev_desktop_focus,
        "node_add": wm.ev_node_add,
        "node_remove": wm.ev_node_remove,
        "node_swap": wm.ev_node_swap,
        "node_transfer": wm.ev_node_transfer,
        "node_focus": wm.ev_node_focus,
        "node_state": wm.ev_node_state,
        "node_flag": wm.ev_node_flag,
    }

    process = subprocess.Popen(
        ["bspc", "subscribe"] + list(event_cbs.keys()), stdout=subprocess.PIPE
    )

    for line in iter(process.stdout.readline, b""):
        event_infos = line.decode().strip().split()
        event_type = event_infos[0]
        event_infos = event_infos[1:]

        event_cb = event_cbs.get(event_type, None)
        if event_cb is None:
            continue
        print("!event:", event_type)
        event_cb(*event_infos)


if __name__ == "__main__":
    main()
