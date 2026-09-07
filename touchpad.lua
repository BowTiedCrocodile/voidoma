-- Touchpad gestures; pinch is left to applications for native zoom.
local base = (os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")) .. "/hypr/"
hl.config({
    input = {
        touchpad = {
            natural_scroll = true,
            tap_to_click = true,
            clickfinger_behavior = true,
            tap_button_map = "lrm",
        },
    },
})
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 3, direction = "up", action = function() hl.exec_cmd(
    "rofi -no-config -theme " .. string.format("%q", base .. "menu.rasi") .. " -show drun") end })
hl.gesture({ fingers = 3, direction = "down", action = "special", workspace_name = "scratchpad" })
hl.gesture({ fingers = 4, direction = "up", action = function()
    hl.exec_cmd("hyprctl dispatch 'hl.dsp.window.fullscreen()'") end })
