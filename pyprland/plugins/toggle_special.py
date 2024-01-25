""" toggle_special allows having an "expose" like selection of windows in a special group
"""

from typing import cast

from ..ipc import hyprctl, hyprctlJSON
from .interface import Plugin


class Extension(Plugin):  # pylint: disable=missing-class-docstring
    exposed: list[dict] = []

    async def run_toggle_special(self, special_workspace="minimized"):
        """[name] Toggles switching the focused window to the special workspace "name" (default: minimized)"""
        aw = cast(dict, await hyprctlJSON("activewindow"))
        wid = aw["workspace"]["id"]
        assert isinstance(wid, int)
        if wid < 1:  # special workspace: unminimize
            wrk = cast(dict, await hyprctlJSON("activeworkspace"))
            await hyprctl(
                [
                    f"togglespecialworkspace {special_workspace}",
                    f"movetoworkspacesilent {wrk['id']},address:{aw['address']}",
                    f"focuswindow address:{aw['address']}",
                ]
            )
        else:
            await hyprctl(
                f"movetoworkspacesilent special:{special_workspace},address:{aw['address']}"
            )
