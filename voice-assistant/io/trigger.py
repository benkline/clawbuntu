"""
Trigger abstraction supporting two modes:
  - 'keyboard': press Enter to trigger (useful for development/testing)
  - 'button':   GPIO button connected to the ReSpeaker's pin header

The ReSpeaker Core v2.0 exposes GPIO pins on its 40-pin header.
The board uses Rockchip RK3229 SoC GPIO, accessible via /sys/class/gpio
or the mraa library (Seeed's preferred GPIO library for this board).

For simplicity we use gpiozero with the RPi pin factory shim,
which works on the ReSpeaker's Linux environment.
"""
import sys
from config.settings import settings


class TriggerSource:
    """Abstract trigger - blocks until user initiates a recording."""

    def wait_for_trigger(self) -> None:
        raise NotImplementedError


class KeyboardTrigger(TriggerSource):
    def wait_for_trigger(self) -> None:
        input("\n[Trigger] Press ENTER to speak (or Ctrl+C to quit)...")
        print("[Trigger] Activated.")


class GPIOButtonTrigger(TriggerSource):
    """
    GPIO push-to-talk button trigger.

    The button should be wired between the GPIO pin and GND.
    The pin is configured with internal pull-up, so it reads HIGH when open
    and LOW when the button is pressed.

    NOTE: The ReSpeaker Core v2.0 uses the Rockchip RK3229 SoC.
    gpiozero can be used with the lgpio or native pin factories.
    If gpiozero is unavailable, fall back to sysfs GPIO directly.
    """

    def __init__(self, pin: int):
        self.pin = pin
        self._button = self._init_button()

    def _init_button(self):
        try:
            from gpiozero import Button
            btn = Button(self.pin, pull_up=True)
            print(f"[Trigger] GPIO button initialized on pin {self.pin} (gpiozero)")
            return btn
        except (ImportError, Exception) as e:
            print(f"[Trigger] gpiozero unavailable ({e}), falling back to sysfs GPIO")
            return None

    def wait_for_trigger(self) -> None:
        if self._button is not None:
            print(f"[Trigger] Waiting for button press on GPIO {self.pin}...")
            self._button.wait_for_press()
            print("[Trigger] Button pressed.")
        else:
            # Fallback: poll /sys/class/gpio directly
            self._sysfs_wait()

    def _sysfs_wait(self) -> None:
        """Direct sysfs GPIO polling as a fallback."""
        import time
        gpio_path = f"/sys/class/gpio/gpio{self.pin}/value"
        print(f"[Trigger] Polling {gpio_path} for button press...")
        while True:
            try:
                with open(gpio_path, "r") as f:
                    value = f.read().strip()
                if value == "0":  # Active low (pulled high, button grounds it)
                    print("[Trigger] Button pressed (sysfs).")
                    return
                time.sleep(0.05)
            except FileNotFoundError:
                print(f"[Trigger] GPIO {self.pin} not exported. Trying to export...")
                try:
                    with open("/sys/class/gpio/export", "w") as f:
                        f.write(str(self.pin))
                    time.sleep(0.1)
                except Exception as ex:
                    print(f"[Trigger] Export failed: {ex}")
                    time.sleep(0.5)


def get_trigger() -> TriggerSource:
    """Factory: return the correct trigger based on configuration."""
    mode = settings.trigger.MODE
    if mode == "button":
        return GPIOButtonTrigger(pin=settings.trigger.BUTTON_GPIO_PIN)
    else:
        return KeyboardTrigger()
