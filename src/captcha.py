import tempfile
from anticaptchaofficial.imagecaptcha import imagecaptcha
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import PySimpleGUI as sg
import re


def captcha_buider(resp, api_key):
    with tempfile.TemporaryDirectory() as tmpdir:
        captcha_file = f"{tmpdir}/captcha.svg"
        with open(captcha_file, "w") as f:
            f.write(resp["captcha"])

        imgfile = open(captcha_file, "r+")
        captcha_cleaned = re.sub('(<path d=)(.*?)(fill="none"/>)', "", imgfile.read())
        imgfile.seek(0)
        imgfile.write(captcha_cleaned)
        imgfile.truncate()
        imgfile.close()

        drawing = svg2rlg(captcha_file)
        png_file = f"{tmpdir}/captcha.png"
        renderPM.drawToFile(drawing, png_file, fmt="PNG")

        if api_key:
            renderPM.drawToFile(drawing, "captcha.png", fmt="PNG")
            solver = imagecaptcha()
            solver.set_verbose(1)
            solver.set_key(api_key)
            captcha_text = solver.solve_and_return_solution(png_file)

            if captcha_text != 0:
                print(f"Captcha text: {captcha_text}")
            else:
                print(f"Task finished with error: {solver.error_code}")

            return captcha_text
        else:
            layout = [
                [sg.Image(png_file)],
                [sg.Text("Enter Captcha Below")],
                [sg.Input(key="txtcaptcha")],
                [sg.Button("Submit", bind_return_key=True)],
            ]

            window = sg.Window("Enter Captcha", layout, finalize=True)
            window.TKroot.focus_force()  # focus on window
            window.Element("txtcaptcha").SetFocus()  # focus on field

            event, values = window.read()
            window.close()

            return values["txtcaptcha"]
