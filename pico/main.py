import time
from network_manager import NetworkManager
import WIFI_CONFIG
from consts import INKY_BUTTONS

from pimoroni import Button
from picographics import PicoGraphics, DISPLAY_INKY_PACK

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
# rot_enc = Button(15)
# rot_enc_button = Button(16)


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

        self.value = 1000
        self.render()

    def render(self):
        clear()
        self.graphics.set_pen(0)
        self.graphics.text("Answer", 10, 5, wordwrap=self.WIDTH - 20, scale=1)
        self.graphics.text("Your estimate", 10, 24, scale=2)
        self.graphics.text(str(self.value), 10, 48, scale=3)

        set_page_controls(self, "ANSWER")
        self.graphics.update()


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


class AppState:
    def __init__(self):
        self.question = None
        self.answer = None
        self.current_page = TitlePage(graphics, WIDTH, HEIGHT)
        self.current_page_key = "TITLE"
        self.loading_question = False
        self.loading_answer = False
        self.is_connected = False

    def reset_problem(self):
        self.question = None
        self.answer = None

    def fetch_question(self):
        print("Fetching question...")
        res = urequests.get(WIFI_CONFIG.ENDPOINT)
        self.question = res.text
        print(f"Question fetched: {self.question}")

    async def fetch_answer(self, *args, **kwargs):
        print("Starting fetch_answer...")
        if self.question == None or self.loading_answer:
            print("fetch_answer: No question available or already loading answer.")
            return
        self.loading_answer = True
        print("Waiting for answer...")
        res = urequests.post(
            WIFI_CONFIG.ENDPOINT + "estimate",
            data=ujson.dumps({"fermi_problem": self.question}),
        )
        print(f"Answer received: {res.text}")
        self.answer = res.text
        self.loading_answer = False

    def set_page(self, page_key: str):
        PAGE_MAP = {
            "TITLE": TitlePage,
            "QUESTION": QuestionPage,
            "ANSWER": AnswerInputPage,
            "RESULT": ResultPage,
        }

        print(f"Setting page to: {page_key}")
        if page_key == "TITLE":
            self.reset_problem()
            print("Problem reset.")

        if page_key == "QUESTION" and not self.question and not self.loading_question:
            self.loading_question = True
            del self.current_page
            self.current_page = LoadingPage(graphics, WIDTH, HEIGHT)
            print("Loading question...")
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
    clear()
    graphics.set_pen(0)
    graphics.text("Network: {}".format(WIFI_CONFIG.SSID), 10, 10, scale=2)
    status_text = "Connecting..."
    if status is not None:
        if status:
            status_text = "Connection successful!"
            app_state.is_connected = True
        else:
            status_text = "Connection failed!"

    graphics.text(status_text, 10, 30, scale=2)
    graphics.text("IP: {}".format(ip), 10, 60, scale=2)
    graphics.update()


network_manager = NetworkManager(
    WIFI_CONFIG.COUNTRY, status_handler=connection_status_handler
)


async def main_loop():
    while True:
        if button_a.read() and PAGE_CONFIG[app_state.current_page_key][2]:
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
