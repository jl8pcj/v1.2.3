import board
import digitalio
import storage
import usb_cdc

# ===== 開発用スイッチ =====
sw = digitalio.DigitalInOut(board.GP10)
sw.direction = digitalio.Direction.INPUT
sw.pull = digitalio.Pull.UP

# スイッチON（GND接続）= 開発モード
if not sw.value:
    print("DEV MODE")
    storage.enable_usb_drive()
    usb_cdc.enable(console=True, data=True)

# スイッチOFF = 実行モード（安全）
else:
    print("RUN MODE")
    storage.disable_usb_drive()
    storage.remount("/", readonly=False)
    usb_cdc.enable(console=False, data=True)
