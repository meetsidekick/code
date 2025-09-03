# Example Custom Code: Pomodoro Timer
# File name pattern MUST be custom_code_*.py so it appears in Execute menu.
# Required entry point: define a function run(env) -> None.
# Provided env keys: oled, mpu, open_menu (call to show main menu),
#   menu_button (Pin), settings (module), sleep_ms (func), Pin (class).
# EXIT: Return from run() to go back.
# MENU ACCESS: You can call env['open_menu']() anytime.
# IMPORTANT: Keep loops short and call sleep_ms to yield CPU.
# This example keeps things very short for demonstration on limited hardware.

from time import ticks_ms

def run(env):
    oled = env.get('oled')
    menu_btn = env.get('menu_button')
    sleep_ms = env.get('sleep_ms')
    open_menu = env.get('open_menu')

    # Two quick demo cycles (work=5s, break=3s)
    cycles = [(5000,'WORK'), (3000,'BREAK')]
    for duration, label in cycles:
        start = ticks_ms()
        while ticks_ms() - start < duration:
            # Exit early if user presses menu button
            if menu_btn and menu_btn.value()==0:
                return
            if oled:
                oled.fill(0)
                oled.text('POMODORO',0,0)
                oled.text(label,0,16)
                remain = (duration - (ticks_ms()-start))//1000
                oled.text('Left:'+str(remain)+'s',0,32)
                oled.text('(btn=exit)',0,48)
                try:
                    oled.show()
                except Exception:
                    pass
            sleep_ms(200)
    if oled:
        oled.fill(0)
        oled.text('DONE!',0,24)
        try:
            oled.show()
        except Exception:
            pass
    sleep_ms(1500)
