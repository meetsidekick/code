# Sidekick v0
A very simple portable "Sidekick" Bot powered by an IMU(ADXL345) on ESP32 using MicroPython

## Info
A simple expressive home-made Open-Source Buddy made with lying-around hobbyist parts, powered by an ESP32 Development Board. Thanks to this, it will be infinitely hackable, allowing end users to install their own firmware or features if they wish.

Loosely inspired by tamagotchi and community-made desk toys, it will react to its surroundings through gyro movement, and expresses itself accordingly through the display and more!

> [!NOTE] 
> Project state: WIP `v0`

Project Homepage: https://meetsidekick.tech
Project Code: https://github.com/MeetSidekick/code


# Development Setup
## Automatic Setup/Flash

### Prepare this repo:
```bash
git clone https://github.com/MeetSidekick/code MeetSidekick-code
```

### Enter the Folder: 
```bash
cd MeetSidekick-code
```

### Setup Prerequisites:
Install `pixi` tool from the official link: https://pixi.sh/latest/#installation

Easy Setup Commands(Subject to change)
- Linux/MacOS (Close and Reopen shell after it's done installing)
    ```bash
    curl -fsSL https://pixi.sh/install.sh | sh
    ```
- Windows
    ```cmd
    powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"
    ```

    OR

    Releases(has installer packages): https://github.com/prefix-dev/pixi/releases/latest

    x86_64 Installer: https://github.com/prefix-dev/pixi/releases/latest/download/pixi-x86_64-pc-windows-msvc.msi

### Setup Environment:
```bash
pixi install
```
### Upload:
```bash
pixi run upload
```

## Manual Setup/Flash

### Prepare this repo:
```bash
git clone https://github.com/MeetSidekick/code MeetSidekick-code
```

### Enter the Folder: 
```bash
cd MeetSidekick-code
```

### Clone Libraries:
```bash 
git clone https://github.com/stlehmann/micropython-ssd1306 lib/
```

### Cleanup to save space: 
```
lib/.gitignore
lib/README.md
lib/sdist_upip.py
lib/setup.py
lib/.git
```

(adjust commands for other systems/shells)

Bash:
```bash 
rm -rf lib/.git lib/.gitignore lib/README.md lib/sdist_upip.py lib/setup.py
```

Cmd/Powershell: 
```
rmdir /s /q "lib\.git"
del "lib\.gitignore"
del "lib\README.md"
del "lib\sdist_upip.py"
del "lib\setup.py"
```

### Next Steps:
> [!TIP]
> Automating this with mpremote would be prudent. Check out upload-to-esp32.py in this folder, this is done automatically. Here are the steps to do it manually:

- Open Folder in Thonny
- Upload lib folder
- Upload `.py` files

## Modes
### Normal Mode 
<!-- TODO Attach Pic -->
Normal Sidekick! It will react to surroundings 

### Menu Mode 
<!-- TODO Attach Pic-->
This allows the user to:
- Mute/Unmute
- Switch Personality Cores
- Execute User Code
- Enter Dashboard Mode(Starts web server, first seen on first boot and when called)
- Wipe Stuff(User Code, Settings, etc)

<!-- Eventually will be able to launch user's custom code! Update: done!-->

### Code Loader Mode
With this, any user can place files called `custom_code_CodeTitle.py`, where the title of the program to be detected in the Code Loader is CodeTitle(change this to your liking). See next section for builtin examples.


# Custom Code

## Builtin
### Tools
<!-- - BLEStageControl
    - Bluetooth Presentation clicker. Needs to pair every time.
- WinBLERickroll
    - Same idea as above but rickrolls a windows user. -->
- DeviceTemp
    - Demo program to output the builtin temp sensor on the chip. NOT ACCURATE!
- Pomodoro Timer
    - A simple pomodoro timer to keep breaks.
- Stopwatch
    - A simple stopwatch for temporary counting.
- WifiScan
    - Scan nearby Wifi SSIDs
### Games
- Rhythm Game using two buttons 
- Flappy Clone
- Dino 
<!-- TODO Expand -->

# Wiring

### IIC/I2C
Pin assignment for ESP32 and IMU/Display:\
VCC -> 3v3\
GND -> GND\
SCL -> GPIO 5\
SDA -> GPIO 4

> [!TIP]
> (You can change SCL pin and SDA pin in file [main.py line 36](main.py#L36))


### Buzzer
Pin assignment for ESP32 and Buzzer:\
GPIO 8 -> Buzzer Terminal\
GND -> Buzzer Terminal
> [!TIP]
> (You can change buzzer pin in file [pin_values.py line 5](pin_values.py#L5))


### Touch
> [!WARNING]
> Touch Pin is disabled for now! This needs more testing and work...
Pin assignment for ESP32 and Touch Pin(For registering hold data):\
GND --(Resistor with 10kOhm)--> Pin A3 -> Metal Contact

> [!TIP]
> (You can change touch pin in file [pin_values.py line 4](pin_values.py#L4)) 

### Buttons
Pin assignment for ESP32 to Menu Pin:\
GPIO 1 -> GND
> [!TIP]
> (You can change enable pin in file [pin_values.py line 3](pin_values.py#L3))

Pin assignment for ESP32 to OK Pin:\
GPIO 0 -> GND
> [!TIP]
> (You can change enable pin in file [pin_values.py line 4](pin_values.py#L4))

