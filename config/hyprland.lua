-- Omarchy-style navigation for Hyprland 0.56 on Void.
local base = (os.getenv("XDG_CONFIG_HOME") or (os.getenv("HOME") .. "/.config")) .. "/hypr/"
local menu = "bash " .. string.format("%q", base .. "void-menu")
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = 1 })
hl.env("XCURSOR_SIZE", "24")
hl.config({
    general = {
        layout = "dwindle", gaps_in = 6, gaps_out = 12, border_size = 2,
        col = { active_border = { colors = {"rgba(a7c080ff)", "rgba(7fbbb3ff)"}, angle = 45 },
                inactive_border = "rgba(39463fff)" },
    },
    decoration = {
        rounding = 12,
        shadow = { enabled = true, range = 18, render_power = 3, color = 0x66000000 },
        blur = { enabled = true, size = 3, passes = 2 },
    },
    dwindle = { preserve_split = true },
    input = { kb_layout = "us", follow_mouse = 1 },
    misc = { disable_hyprland_logo = true, force_default_wallpaper = 0 },
})
hl.on("hyprland.start", function()
    hl.exec_cmd("dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_TYPE")
    hl.exec_cmd("/usr/libexec/xfce-polkit")
    hl.exec_cmd("bash " .. string.format("%q", base .. "desktop-start"))
end)
local function bind(keys, description, action)
    hl.bind(keys, action, { description = description })
end
bind("SUPER + SPACE", "Desktop menu", hl.dsp.exec_cmd(menu))
bind("SUPER + ALT + SPACE", "Applications", hl.dsp.exec_cmd("rofi -no-config -theme " .. string.format("%q", base .. "menu.rasi") .. " -show drun"))
bind("SUPER + K", "Keyboard shortcuts", hl.dsp.exec_cmd(menu .. " keys"))
bind("SUPER + ESCAPE", "System menu", hl.dsp.exec_cmd(menu .. " system"))
bind("SUPER + RETURN", "Terminal", hl.dsp.exec_cmd("ghostty"))
bind("SUPER + SHIFT + RETURN", "Browser", hl.dsp.exec_cmd("firefox"))
bind("SUPER + SHIFT + F", "Files", hl.dsp.exec_cmd("thunar"))
bind("SUPER + W", "Close window", hl.dsp.window.close())
bind("SUPER + Q", "Close window", hl.dsp.window.close())
bind("SUPER + T", "Terminal", hl.dsp.exec_cmd("ghostty"))
bind("SUPER + SHIFT + T", "Toggle floating", hl.dsp.window.float({ action = "toggle" }))
bind("SUPER + F", "Fullscreen", hl.dsp.window.fullscreen())
bind("SUPER + J", "Toggle split direction", hl.dsp.layout("togglesplit"))
bind("SUPER + P", "Toggle pseudo tiling", hl.dsp.window.pseudo())
bind("SUPER + G", "Toggle window group", hl.dsp.group.toggle())
bind("SUPER + CTRL + right", "Next grouped window", hl.dsp.group.next())
bind("SUPER + CTRL + left", "Previous grouped window", hl.dsp.group.prev())
for _, direction in ipairs({ "left", "right", "up", "down" }) do
    bind("SUPER + " .. direction, "Focus " .. direction, hl.dsp.focus({ direction = direction }))
    bind("SUPER + SHIFT + " .. direction, "Swap " .. direction, hl.dsp.window.swap({ direction = direction }))
end
for i = 1, 10 do
    bind("SUPER + " .. (i % 10), "Workspace " .. i, hl.dsp.focus({ workspace = i }))
    bind("SUPER + SHIFT + " .. (i % 10), "Move to workspace " .. i, hl.dsp.window.move({ workspace = i }))
end
bind("SUPER + S", "Scratchpad", hl.dsp.workspace.toggle_special("scratchpad"))
bind("SUPER + grave", "Scratchpad", hl.dsp.workspace.toggle_special("scratchpad"))
bind("SUPER + ALT + S", "Move to scratchpad", hl.dsp.window.move({ workspace = "special:scratchpad" }))
bind("SUPER + SHIFT + grave", "Move to scratchpad", hl.dsp.window.move({ workspace = "special:scratchpad" }))
hl.bind("SUPER + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind("SUPER + mouse:273", hl.dsp.window.resize(), { mouse = true })
hl.bind("XF86AudioRaiseVolume", hl.dsp.exec_cmd("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), { repeating = true })
hl.bind("XF86AudioLowerVolume", hl.dsp.exec_cmd("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"), { repeating = true })
hl.bind("XF86AudioMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"))

-- Laptop Fn/media keys (Fn Lock determines whether Fn must be held).
hl.bind("XF86MonBrightnessUp", hl.dsp.exec_cmd("python3 " .. string.format("%q", base .. "brightness") .. " up"), { repeating = true })
hl.bind("XF86MonBrightnessDown", hl.dsp.exec_cmd("python3 " .. string.format("%q", base .. "brightness") .. " down"), { repeating = true })
hl.bind("XF86AudioMicMute", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"))
hl.bind("XF86AudioPlay", hl.dsp.exec_cmd("playerctl play-pause"))
hl.bind("XF86AudioPause", hl.dsp.exec_cmd("playerctl play-pause"))
hl.bind("XF86AudioNext", hl.dsp.exec_cmd("playerctl next"))
hl.bind("XF86AudioPrev", hl.dsp.exec_cmd("playerctl previous"))

-- ThinkPad utility keys. Standard F1-F12 remain available through Fn Lock.
local controls = "python3 " .. string.format("%q", base .. "desktop-controls")
bind("XF86Display", "Display menu", hl.dsp.exec_cmd("python3 " .. string.format("%q", base .. "display-menu")))
bind("XF86WLAN", "Toggle Wi-Fi", hl.dsp.exec_cmd(controls .. " wifi"))
bind("XF86Tools", "Desktop settings", hl.dsp.exec_cmd(controls .. " settings"))
bind("XF86Bluetooth", "Bluetooth controls", hl.dsp.exec_cmd(controls .. " bluetooth"))
bind("XF86Favorites", "Desktop menu (star)", hl.dsp.exec_cmd(menu))

-- Desktop essentials.
bind("SUPER + L", "Lock screen", hl.dsp.exec_cmd("bash " .. string.format("%q", base .. "lock-screen")))
bind("PRINT", "Screenshot region", hl.dsp.exec_cmd("python3 " .. string.format("%q", base .. "screenshot") .. " region"))
bind("SHIFT + PRINT", "Screenshot all displays", hl.dsp.exec_cmd("python3 " .. string.format("%q", base .. "screenshot") .. " screen"))
bind("SUPER + PRINT", "Screenshot active window", hl.dsp.exec_cmd("python3 " .. string.format("%q", base .. "screenshot") .. " window"))
bind("SUPER + V", "Clipboard history", hl.dsp.exec_cmd("bash " .. string.format("%q", base .. "clipboard-menu")))

dofile(base .. "touchpad.lua")
