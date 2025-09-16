import oled_functions
import settings_store
from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff
from pin_values import code_debug_pin_value, code_ok_pin_value

def run_first_boot(oled, upside_down):
    """
    Manages the first boot setup process, showing a menu for Web Setup or Skip setup.
    """
    menu_items = [
        {"name": "Web Setup", "key": "web"},
        {"name": "Skip Setup", "key": "skip"},
    ]
    selected_index = 0

    # Initialize buttons
    menu_button = Pin(code_debug_pin_value, Pin.IN, Pin.PULL_UP)
    ok_button = Pin(code_ok_pin_value, Pin.IN, Pin.PULL_UP)

    while True:
        # Render menu
        oled.fill(0)
        oled_functions.update_oled(oled, "text", "First Time Setup", upside_down)
        for i, item in enumerate(menu_items):
            prefix = "> " if i == selected_index else "  "
            oled_functions.update_oled(oled, "text", f"{prefix}{item['name']}", upside_down, line=i+2)
        oled.show()

        # Handle input
        if menu_button.value() == 0:
            sleep_ms(100) # Debounce
            selected_index = (selected_index + 1) % len(menu_items)
            while menu_button.value() == 0:
                sleep_ms(20)

        if ok_button.value() == 0:
            sleep_ms(100) # Debounce
            
            press_start_time = ticks_ms()
            is_long_press = False
            while ok_button.value() == 0:
                if ticks_diff(ticks_ms(), press_start_time) > 1000: # 1 second
                    is_long_press = True
                    break
                sleep_ms(20)

            if is_long_press:
                oled.fill(0)
                oled_functions.update_oled(oled, "text", "Using Defaults...", upside_down, line=2)
                oled.show()
                sleep_ms(1000)
                user_name = "User"
                sidekick_name = "Sidekick"
                break

            # Short press logic
            selection = menu_items[selected_index]['key']
            
            if selection == "web":
                import web_setup
                web_setup.start_web_setup(oled, upside_down)
                # After setup is complete, the script will continue and reboot.
                break
            elif selection == "skip":
                user_name = "User"
                sidekick_name = "Sidekick"
                break

    # After web setup returns, we reboot
    print("DEBUG: Reached reboot point in first_boot.py.")
    from machine import reset
    reset()