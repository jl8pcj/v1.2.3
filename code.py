import board
import analogio
import usb_cdc
import storage
import json
import time

usb = usb_cdc.data

# ---------- PIEZO ----------
piezos = [
    analogio.AnalogIn(board.A0),
    analogio.AnalogIn(board.A1),
    analogio.AnalogIn(board.A2),
    analogio.AnalogIn(board.A3),
]

# ---------- 設定 ----------
settings = {
    "gain":[1,1,1,1],
    "threshold":[15000,15000,15000,15000]
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
            settings=json.load(f)
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
        "threshold":settings["threshold"]
    })

# ---------- USB RECEIVE ----------
buffer=""

def check_usb():
    global buffer

    if not usb or not usb.connected:
        return

    data=usb.read(usb.in_waiting or 0)
    if not data:
        return

    buffer+=data.decode()

    while "\n" in buffer:
        line,buffer=buffer.split("\n",1)

        try:
            cmd=json.loads(line)

            if cmd["cmd"]=="set":
                settings[cmd["type"]][cmd["ch"]]=cmd["value"]

            elif cmd["cmd"]=="save":
                save_settings()

            elif cmd["cmd"]=="get_settings":
                send_settings()

        except:
            pass

# ---------- ADC ----------
def send_adc(ch,val):
    send({"type":"adc","ch":ch,"value":val})

# ---------- START ----------
load_settings()

print("READY")

while True:

    check_usb()

    for i,p in enumerate(piezos):
        send_adc(i,p.value)

    time.sleep(0.02)