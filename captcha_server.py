from captcha.image import ImageCaptcha
import string
import random

CAPTCHA_PREFIX = b'Gui/captcha='
AVAILABLE_CHARACTERS = string.ascii_lowercase
CAPTCHA_LENGTH = 6
CAPTCHA_FORMAT = 'jpeg'

def captcha_server(input_queue, output_queue, captcha_solution_mamager):
    image = ImageCaptcha(width=280, height=90)
    while True:
        curr_req, cli_sock = input_queue.get()
        captcha, solution = generate_captcha(image)
        captcha_solution_mamager.register_captcha(cli_sock, solution)
        output_queue.put((CAPTCHA_PREFIX + captcha, cli_sock))


def generate_captcha(image):
    solution = ''.join(random.choices(AVAILABLE_CHARACTERS, k=6))
    captcha = image.generate(solution, CAPTCHA_FORMAT).read()
    return captcha, solution
