import time
from network_manager import NetworkManager
import WIFI_CONFIG
from consts import INKY_BUTTONS

from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_INKY_PACK
from rotary_irq_rp2 import RotaryIRQ
from machine import Pin

import ujson

# from urllib import urequest
import uasyncio
import urequests

graphics = PicoGraphics(DISPLAY_INKY_PACK)
graphics.set_font("bitmap8")
WIDTH, HEIGHT = graphics.get_bounds()


"""
Connects to wifi and queries either the `generate_problem`("/") or the `make_estimations`("/estimate") endpoint depending on the state of the app.
"""

button_a = Button(12)
button_b = Button(13)
button_c = Button(14)
rot_enc_button = Pin(7, Pin.IN, Pin.PULL_UP)
rot_enc = RotaryIRQ(
    pin_num_clk=8,
    pin_num_dt=9,
    min_val=0,
    max_val=20,
    incr=1,
    reverse=False,
    range_mode=RotaryIRQ.RANGE_BOUNDED,
)


# a handy function we can call to clear the screen
# display.set_pen(15) is white and display.set_pen(0) is black
def clear():
    graphics.set_pen(15)
    graphics.clear()


"""
This is a dictionary that maps the current page to the next and previous pages along with the available page controls.
{
    CURRENT_PAGE: (NEXT_PAGE, PREVIOUS_PAGE, SHOW_CLOSE_BUTTON, SHOW_BACK_BUTTON, SHOW_FORWARD_BUTTON),
}
"""
PAGE_CONFIG = {
    "TITLE": ("QUESTION", None, 0, 0, 1),
    "QUESTION": ("ANSWER", None, 1, 0, 1),
    "ANSWER": ("RESULT", "QUESTION", 1, 1, 1),
    "RESULT": (None, None, 1, 0, 0),
}


class LoadingPage:
    def __init__(self, graphics, WIDTH, HEIGHT):
        self.graphics = graphics
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.render()

    def render(self):
        clear()
        self.graphics.set_pen(0)
        self.graphics.text("Loading...", 10, 10, wordwrap=self.WIDTH - 20, scale=2)
        self.graphics.update()


class TitlePage:
    def __init__(self, graphics, WIDTH, HEIGHT):
        self.graphics = graphics
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.render()

    def render(self):
        clear()
        self.graphics.set_pen(0)
        self.graphics.text("Baaaaaallpark", 10, 10, wordwrap=self.WIDTH - 20, scale=2)
        set_page_controls(self, "TITLE")
        self.graphics.update()


class QuestionPage:
    def __init__(self, graphics, WIDTH, HEIGHT):
        self.graphics = graphics
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.render()

    def render(self):
        clear()
        self.graphics.set_pen(0)
        self.graphics.text("Question", 10, 5, wordwrap=self.WIDTH - 20, scale=1)
        self.graphics.text(
            app_state.question, 10, 24, wordwrap=self.WIDTH - 25, scale=2
        )
        set_page_controls(self, "QUESTION")
        self.graphics.update()


class AnswerInputPage:
    def __init__(self, graphics, WIDTH, HEIGHT):
        self.graphics = graphics
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        graphics.set_update_speed(3)

        self.msd = 0  # most_significant_digit (1-9)
        self.num_digits = 1  # number of digits
        self.updating_digit_count = False
        self.value = self.calculate_final_number()
        self.render()

    def calculate_final_number(self):
        # Subtract 1 from digits because msd is already the first digit
        return self.msd * (10 ** (self.num_digits - 1))

    def page_layout(self):
        clear()
        self.graphics.set_pen(0)
        self.graphics.text("Answer", 10, 5, wordwrap=self.WIDTH - 20, scale=1)
        self.graphics.text("Your estimate", 10, 24, scale=2)
        set_page_controls(self, "ANSWER")

    def render(self):
        self.page_layout()
        self.graphics.text("_", 10, 48, scale=3)
        self.graphics.update()

        while True:
            try:
                val_new = rot_enc.value()
                if rot_enc_button.value() == 0:
                    # Rot encoder button pressed
                    print("called button press")
                    number_to_display = str(self.calculate_final_number()) + "_"
                    self.page_layout()
                    self.graphics.text(number_to_display, 10, 48, scale=3)
                    self.graphics.update()

                    if self.updating_digit_count:
                        self.value = self.calculate_final_number()

                    else:
                        rot_enc.set(value=self.num_digits)
                        val_new = self.num_digits
                        self.updating_digit_count = True
                    while rot_enc_button.value() == 0:
                        continue

                if not self.updating_digit_count:
                    # updating the first digit
                    # first digit must be 1-9
                    if val_new != self.msd and val_new > 0 and val_new < 10:
                        self.msd = val_new
                        number_to_display = str(self.calculate_final_number())
                        self.page_layout()
                        self.graphics.text(number_to_display, 10, 48, scale=3)
                        self.graphics.update()

                else:
                    # updating the number of digits
                    if val_new != self.num_digits and val_new > 0:
                        self.num_digits = val_new
                        number_to_display = str(self.calculate_final_number()) + "_"
                        self.page_layout()
                        self.graphics.text(number_to_display, 10, 48, scale=3)
                        self.graphics.update()

                    if val_new <= 0:
                        # if the user has scrolled down to 0, go back to editing the first digit
                        self.updating_digit_count = False
                        rot_enc.set(value=self.msd)
                        print("switching to first digit...")

                time.sleep_ms(50)
            except KeyboardInterrupt:
                break


class ResultPage:
    def __init__(self, graphics, WIDTH, HEIGHT):
        self.graphics = graphics
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.render()

    def render(self):
        clear()
        self.graphics.set_pen(0)
        self.graphics.text("Result", 10, 10, wordwrap=self.WIDTH - 20, scale=2)
        set_page_controls(self, "RESULT")
        self.graphics.update()


def set_page_controls(self, page):
    _, _, close, back, forward = PAGE_CONFIG[page]
    self.graphics.set_pen(1)
    if close:
        self.graphics.text(*INKY_BUTTONS["CLOSE"], 240, 3)
    if back:
        self.graphics.text(*INKY_BUTTONS["BCK"], 240, 3)
    if forward:
        self.graphics.text(*INKY_BUTTONS["FWD"], 240, 3)


PAGE_MAP = {
    "TITLE": TitlePage,
    "QUESTION": QuestionPage,
    "ANSWER": AnswerInputPage,
    "RESULT": ResultPage,
}


class AppState:

    def __init__(self):
        self.question = None
        self.answer = None
        self.current_page_key = "TITLE"
        self.current_page = self.current_page = PAGE_MAP[self.current_page_key](
            graphics, WIDTH, HEIGHT
        )
        self.loading_question = False
        self.loading_answer = False
        self.is_connected = False

    def reset_problem(self):
        self.question = None
        self.answer = None

    def fetch_question(self):
        print("Fetching question...")
        try:
            res = urequests.get(WIFI_CONFIG.ENDPOINT)
            self.question = res.text
        except Exception as e:
            print(f"Error fetching question: {e}")

    async def fetch_answer(self, *args, **kwargs):
        print("Starting fetch_answer...")
        if self.question == None or self.loading_answer:
            print("fetch_answer: No question available or already loading answer.")
            return
        self.loading_answer = True
        print("Waiting for answer...")
        MAX_RETRIES = 3
        retries = 0
        while retries < MAX_RETRIES:
            if self.answer:
                break
            try:
                res = urequests.post(
                    WIFI_CONFIG.ENDPOINT + "estimate",
                    data=ujson.dumps({"fermi_problem": self.question}),
                )
                print(f"Answer received: {res.text}")
                self.answer = res.text
            except Exception as e:
                print(f"Error fetching answer: {e}")
                retries += 1
            await uasyncio.sleep(0.3)

        self.loading_answer = False

    def set_page(self, page_key: str):
        print(f"Setting page to: {page_key}")
        if page_key == "TITLE":
            self.reset_problem()
            print("Problem reset.")

        if page_key == "QUESTION" and not self.question and not self.loading_question:
            self.loading_question = True
            del self.current_page
            self.current_page = LoadingPage(graphics, WIDTH, HEIGHT)
            self.fetch_question()
            self.loading_question = False

            loop = uasyncio.get_event_loop()
            print("Creating task to fetch answer...")
            loop.create_task(self.fetch_answer())

        del self.current_page
        self.current_page_key = page_key
        self.current_page = PAGE_MAP[page_key](graphics, WIDTH, HEIGHT)
        print(f"Page set to: {page_key}")


graphics.set_update_speed(2)  # 0 (slowest) to 3 (fastest)
app_state = AppState()


def connection_status_handler(mode, status, ip):
    print("Network: {}".format(WIFI_CONFIG.SSID))
    status_text = "Connecting..."
    if status is not None:
        if status:
            status_text = "Connection successful!"
            app_state.is_connected = True
        else:
            status_text = "Connection failed!"

    print(status_text)
    print("IP: {}")


network_manager = NetworkManager(
    WIFI_CONFIG.COUNTRY, status_handler=connection_status_handler
)


async def main_loop():
    await network_manager.client(WIFI_CONFIG.SSID, WIFI_CONFIG.PSK)
    while True:
        if button_a.read() and PAGE_CONFIG[app_state.current_page_key][2]:
            print("Button A pressed")
            app_state.set_page("TITLE")
            await uasyncio.sleep(0.5)
        elif button_b.read() and PAGE_CONFIG[app_state.current_page_key][3]:
            previous_page = PAGE_CONFIG[app_state.current_page_key][1]
            if previous_page:
                app_state.set_page(previous_page)
            await uasyncio.sleep(0.5)
        elif button_c.read() and PAGE_CONFIG[app_state.current_page_key][4]:
            next_page = PAGE_CONFIG[app_state.current_page_key][0]
            if next_page:
                app_state.set_page(next_page)
            await uasyncio.sleep(0.5)

        await uasyncio.sleep(
            0.1
        )  # this number is how frequently the Pico checks for button presses


# Run the event loop
loop = uasyncio.get_event_loop()
loop.create_task(main_loop())
loop.run_forever()
