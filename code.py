import board
import analogio
import usb_cdc
import storage
import json
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

usb = usb_cdc.data
kbd = Keyboard(usb_hid.devices)

# ---------- PIEZO ----------
piezos = [
    analogio.AnalogIn(board.A0),  # D
    analogio.AnalogIn(board.A1),  # F
    analogio.AnalogIn(board.A2),  # J
    analogio.AnalogIn(board.A3),  # K
]

# ---------- 設定 ----------
settings = {
    "gain":[1,1,1,1],
    "threshold":[15000,15000,15000,15000],
    "mute_fj":10,   # F/J → D/K ミュート(ms)
    "mute_dk":12    # D/K → F/J ミュート(ms)
}

# ---------- USB SEND ----------
def send(obj):
    if usb and usb.connected:
        try:
            usb.write((json.dumps(obj)+"\n").encode())
        except:
            pass

# ---------- LOAD ----------
def load_settings():
    global settings
    try:
        with open("/setting.json","r") as f:
            settings = json.load(f)
        print("LOAD OK")
    except:
        print("DEFAULT SETTINGS")

# ---------- SAVE ----------
def save_settings():
    try:
        storage.remount("/", False)
        with open("/setting.json","w") as f:
            json.dump(settings,f)
        storage.remount("/", True)
        send({"type":"saved"})
    except Exception as e:
        print("SAVE ERROR",e)
        send({"type":"save_error"})

# ---------- SEND SETTINGS ----------
def send_settings():
    send({
        "type":"settings",
        "gain":settings["gain"],
        "threshold":settings["threshold"],
        "mute_fj":settings["mute_fj"],
        "mute_dk":settings["mute_dk"]
    })

# ---------- USB RECEIVE ----------
buffer=""

def check_usb():
    global buffer
    if not usb or not usb.connected:
        return

    data = usb.read(usb.in_waiting or 0)
    if not data:
        return

    buffer += data.decode()

    while "\n" in buffer:
        line, buffer = buffer.split("\n",1)
        try:
            cmd = json.loads(line)

            if cmd["cmd"]=="set":
                if cmd["type"] in ("mute_fj","mute_dk"):
                    settings[cmd["type"]] = cmd["value"]
                else:
                    settings[cmd["type"]][cmd["ch"]] = cmd["value"]

            elif cmd["cmd"]=="save":
                save_settings()

            elif cmd["cmd"]=="get_settings":
                send_settings()

        except:
            pass

# ---------- KEYBOARD MAP ----------
keymap = {
    0: Keycode.D,
    1: Keycode.F,
    2: Keycode.J,
    3: Keycode.K
}

prev_hit = [False, False, False, False]

last_fj_hit = 0
last_dk_hit = 0

# ---------- ADC ----------
def send_adc(ch,val):
    send({"type":"adc","ch":ch,"value":val})

# ---------- START ----------
load_settings()
print("READY")

while True:
    check_usb()

    now = time.monotonic_ns() // 1_000_000  # ms

    for i,p in enumerate(piezos):
        val = p.value * settings["gain"][i]

        # --- ミュート判定 ---
        if i in (0,3):  # D,K
            if now - last_fj_hit < settings["mute_fj"]:
                continue

        if i in (1,2):  # F,J
            if now - last_dk_hit < settings["mute_dk"]:
                continue

        # --- 閾値判定 ---
        if val > settings["threshold"][i]:
            if not prev_hit[i]:  # 叩き始めの瞬間だけ
                kbd.press(keymap[i])
                kbd.release(keymap[i])

                if i in (0,3):
                    last_dk_hit = now
                else:
                    last_fj_hit = now

            prev_hit[i] = True
        else:
            prev_hit[i] = False

        send_adc(i,val)

    time.sleep(0.002)

