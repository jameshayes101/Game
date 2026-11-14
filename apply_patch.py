#!/usr/bin/env python3
"""Patch upstream GridWars (mmatyas/GridWars) for the Miyoo Flip port.
Usage: python3 apply_patch.py <path-to-upstream-source>
Fails loudly if the upstream text does not match what we expect."""
import sys, os

src = sys.argv[1]

def edit(name, fn):
    p = os.path.join(src, name)
    with open(p, encoding="latin-1", newline="") as f:
        s = f.read()
    s = fn(s)
    with open(p, "w", encoding="latin-1", newline="") as f:
        f.write(s)

def must_replace(s, old, new):
    if old not in s:
        raise SystemExit("PATCH FAILED: expected text not found:\n" + old)
    return s.replace(old, new, 1)

# 1) gridwars.bmx: on Linux always use the SDL GL2 driver (window + GL context from SDL,
#    not X11/GLX). The game's desktop-OpenGL drawing then runs through gl4es on the handheld.
def gw(s):
    old = "?Linux\n?OpenGLES\nFramework SDL.GL2SDLMax2D\n?not OpenGLES\nFramework BRL.GLMax2D\n?\n"
    new = ("?Linux\n"
           "' Miyoo Flip port: window + GL context come from SDL (KMSDRM/EGL via gl4es on the handheld)\n"
           "Framework SDL.GL2SDLMax2D\n?\n")
    return must_replace(s, old, new)
edit("gridwars.bmx", gw)

# 2) sound.bmx: Linux had no music code at all. Play pre-rendered WAV copies of the .it songs.
def snd(s):
    s = must_replace(s, "?Linux\nGlobal musicchannel:TChannel = Null\n?\n",
                        "?Linux\nGlobal musicchannel:TChannel = Null\nGlobal musicsound:TSound = Null\n?\n")
    def sub_after(s, func, repl):
        i = s.index("Function " + func)
        marker = "?Linux\n\n?"
        j = s.index(marker, i)
        return s[:j] + repl + s[j + len(marker):]
    s = sub_after(s, "StartMusic(song:Int)",
"""?Linux
	If musicchannel <> Null Then Return

	Local f$ = ""

	Select song
		Case 0 'intro
			f$ = "music/Theme0.wav"
		Case 1 'in game
			f$ = "music/Theme1.wav"
		Case 2 'hi score
			f$ = "music/Theme2.wav"
	End Select

	musicsound = LoadSound(f$, SOUND_LOOP)
	If musicsound <> Null
		musicchannel = CueSound(musicsound)
		SetChannelVolume(musicchannel, musicvol)
		ResumeChannel(musicchannel)
	EndIf
?""")
    s = sub_after(s, "StopMusic()",
"""?Linux
	If musicchannel <> Null
		StopChannel(musicchannel)
		musicchannel = Null
	EndIf
	musicsound = Null
?""")
    s = sub_after(s, "SetMusicVolume()",
"""?Linux
	If musicchannel <> Null
		SetChannelVolume(musicchannel, musicvol)
	EndIf
?""")
    return s
edit("sound.bmx", snd)
# 3) The game defines its own global Function named Rect (utils.bmx). With the SDL graphics module
#    that name is already taken, so the compiler reports "Duplicate identifier rect". Rename it.
import re
for name in ("utils.bmx", "control.bmx"):
    p2 = os.path.join(src, name)
    with open(p2, encoding="latin-1", newline="") as f:
        t = f.read()
    t, n = re.subn(r"\brect\b", "GwRect", t, flags=re.IGNORECASE)
    print("renamed %d uses of Rect in %s" % (n, name))
    with open(p2, "w", encoding="latin-1", newline="") as f:
        f.write(t)

# 4) Linking failed with "undefined reference to JoyCount / JoyCName / JoyButtonCaps / JoyAxisCaps / ReadJoy":
#    BlitzMax's joystick back-end has no ARM64 Linux implementation. On the Flip all input arrives through
#    gptokeyb (pad -> keyboard), so provide do-nothing versions that report "no joysticks connected".
JOYSTUBS = """/* Miyoo Flip port: stand-ins for BlitzMax's joystick back-end, which has no ARM64 Linux version.
   Input comes from gptokeyb (pad -> keyboard), so these simply report that no joysticks exist. */
int JoyCount(void) { return 0; }
const char *JoyCName(int port) { (void)port; return ""; }
int JoyButtonCaps(int port) { (void)port; return 0; }
int JoyAxisCaps(int port) { (void)port; return 0; }
int ReadJoy() { return 0; }
"""
with open(os.path.join(src, "joystubs.c"), "w", newline="\n") as f:
    f.write(JOYSTUBS)

def add_import(s):
    old = 'Import "control.bmx"\n'
    new = 'Import "control.bmx"\n\n?Linux\nImport "joystubs.c"\n?\n'
    return must_replace(s, old, new)
edit("gridwars.bmx", add_import)
print("Added joystick stubs")

print("Patched OK")
