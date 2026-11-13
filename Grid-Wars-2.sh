#!/bin/bash
# PORTMASTER: gridwars2.zip, Grid Wars 2.sh

XDG_DATA_HOME=${XDG_DATA_HOME:-$HOME/.local/share}

if [ -d "/opt/system/Tools/PortMaster/" ]; then
  controlfolder="/opt/system/Tools/PortMaster"
elif [ -d "/opt/tools/PortMaster/" ]; then
  controlfolder="/opt/tools/PortMaster"
elif [ -d "$XDG_DATA_HOME/PortMaster/" ]; then
  controlfolder="$XDG_DATA_HOME/PortMaster"
else
  controlfolder="/roms/ports/PortMaster"
fi

source $controlfolder/control.txt
[ -f "${controlfolder}/mod_${CFW_NAME}.txt" ] && source "${controlfolder}/mod_${CFW_NAME}.txt"
get_controls

GAMEDIR="/$directory/ports/gridwars2"
cd "$GAMEDIR" || exit 1

# Log everything (overwritten each launch) - send me this file if something goes wrong
> "$GAMEDIR/log.txt" && exec > >(tee "$GAMEDIR/log.txt") 2>&1
echo "Grid Wars 2 launch: $(date)  CFW=$CFW_NAME  ARCH=$DEVICE_ARCH  GAMEDIR=$GAMEDIR"

# The game stores Config.txt and hiscores.dat in $HOME/.config/gridwars -> keep them inside the port folder
export HOME="$GAMEDIR/home"
mkdir -p "$HOME/.config/gridwars"
[ -f "$HOME/.config/gridwars/Config.txt" ]   || cp "$GAMEDIR/Config.txt"   "$HOME/.config/gridwars/Config.txt"
[ -f "$HOME/.config/gridwars/hiscores.dat" ] || cp "$GAMEDIR/hiscores.dat" "$HOME/.config/gridwars/hiscores.dat"

# gl4es: the game uses desktop OpenGL; gl4es translates it to GLES for the Mali GPU
export LD_LIBRARY_PATH="$GAMEDIR/gl4es.${DEVICE_ARCH}:$GAMEDIR/libs.${DEVICE_ARCH}:$LD_LIBRARY_PATH"
if [ -f "${controlfolder}/libgl_${CFW_NAME}.txt" ]; then
  source "${controlfolder}/libgl_${CFW_NAME}.txt"
else
  source "${controlfolder}/libgl_default.txt"
fi
export LIBGL_ES=${LIBGL_ES:-2}
export LIBGL_GL=${LIBGL_GL:-21}
export LIBGL_FB=${LIBGL_FB:-4}

export SDL_GAMECONTROLLERCONFIG="$sdl_controllerconfig"
chmod +x "$GAMEDIR/gridwars2.${DEVICE_ARCH}"

# Pad -> keyboard mapping (see gridwars2.gptk)
$GPTOKEYB "gridwars2.${DEVICE_ARCH}" -c "./gridwars2.gptk" &
if type pm_platform_helper >/dev/null 2>&1; then
  pm_platform_helper "$GAMEDIR/gridwars2.${DEVICE_ARCH}"
fi

./gridwars2.${DEVICE_ARCH}

if type pm_finish >/dev/null 2>&1; then
  pm_finish
else
  $ESUDO kill -9 $(pidof gptokeyb) 2>/dev/null
  unset LD_LIBRARY_PATH
  printf "\033c" > /dev/tty0
fi
