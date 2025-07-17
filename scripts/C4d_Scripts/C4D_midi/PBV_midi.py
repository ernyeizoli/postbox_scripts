import c4d
import rtmidi
import threading
import time
import traceback

"""
1. kell legyen egy MIDI nevu null a megfelelo User Data-val
-- todo egy script ami letrehozza a megfelelo User Datas MIDI objektumot
2. kell az rtmidi csomag a python kornyezetben
"""


# --- MIDI Configuration ---
MIDI_PORT = 0  # Change this to your MIDI port number
POLL_INTERVAL = 0.0001

# CC knobs/faders → User Data IDs
CC_MAP = {
    13: 2, 14: 3, 15: 4, 16: 5, 17: 6, 18: 7, 19: 8, 20: 9,
    29: 11, 30: 12, 31: 13, 32: 14, 33: 15, 34: 16, 35: 17, 36: 18,
    49: 20, 50: 21, 51: 22, 52: 23, 53: 24, 54: 25, 55: 26, 56: 27,
    77: 29, 78: 30, 79: 31, 80: 32, 81: 33, 82: 34, 83: 35, 84: 36,
}

# Note On buttons (track focus) → User Data IDs starting at 38
NOTE_MAP = {
    41: 38, 42: 39, 43: 40, 44: 41, 57: 42, 58: 43, 59: 44, 60: 45,
    73: 47, 74: 48, 75: 49, 76: 50, 89: 51, 90: 52, 91: 53, 92: 54,
}

running = True
midi_connection = None
midi_thread_ref = None
port_opened = False

def list_ports():
    midi = rtmidi.MidiIn()
    ports = midi.get_ports()
    print("️ Available MIDI Ports:")
    for i, p in enumerate(ports):
        print(f"  Port {i}: {p}")
    del midi

def connect_midi():
    global midi_connection, port_opened
    try:
        if midi_connection:
            midi_connection.close_port()
            del midi_connection
        midi_connection = rtmidi.MidiIn()
        ports = midi_connection.get_ports()
        if not ports or MIDI_PORT >= len(ports):
            print(f"❌ No MIDI ports or port index {MIDI_PORT} invalid.")
            return False
        midi_connection.open_port(MIDI_PORT)
        print(f"✅ Connected to MIDI port: {ports[MIDI_PORT]}")
        port_opened = True
        return True
    except Exception:
        print(f"⚠️ MIDI port {MIDI_PORT} already in use or cannot open.")
        port_opened = False
        return False

def midi_loop():
    global midi_connection, port_opened
    while running:
        try:
            if not port_opened:
                time.sleep(1)
                continue

            if not midi_connection or not midi_connection.is_port_open():
                print(" Attempting MIDI reconnect...")
                if not connect_midi():
                    time.sleep(1)
                    continue

            msg = midi_connection.get_message()
            if msg:
                midi_data, _ = msg
                status = midi_data[0]
                data1 = midi_data[1]
                data2 = midi_data[2] if len(midi_data) > 2 else 0

                obj = doc.SearchObject("MIDI")
                if not obj:
                    continue

                # Control Change (CC) 176–191
                if 176 <= status <= 191 and data1 in CC_MAP:
                    user_data_id = CC_MAP[data1]
                    normalized = (data2 / 127.0) * 100.0
                    obj[c4d.ID_USERDATA, user_data_id] = int(normalized)
                    c4d.EventAdd()

                # Note On (144–159), velocity 127 → toggle Boolean User Data
                elif 144 <= status <= 159 and data1 in NOTE_MAP and data2 == 127:
                    user_data_id = NOTE_MAP[data1]
                    current = obj[c4d.ID_USERDATA, user_data_id]
                    if current == 1:
                        obj[c4d.ID_USERDATA, user_data_id] = 0
                    else:
                        obj[c4d.ID_USERDATA, user_data_id] = 1
                    print(f" Toggled NOTE {data1}")
                    c4d.EventAdd()

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print("❌ Error in MIDI thread:")
            traceback.print_exc()
            time.sleep(1)

def main():
    global running, midi_thread_ref

    if not midi_thread_ref or not midi_thread_ref.is_alive():
        print(" Starting MIDI listener...")
        running = True
        connected = connect_midi()
        if not connected:
            print("❗ MIDI port busy or not available. Will not attempt reconnect until script restart.")
        midi_thread_ref = threading.Thread(target=midi_loop)
        midi_thread_ref.daemon = True
        midi_thread_ref.start()
    else:
        obj = op.GetObject()
        if not obj:
            return
        c4d.EventAdd()

def stop():
    global running, midi_connection, port_opened
    print(" Stopping MIDI listener...")
    running = False
    if midi_connection:
        try:
            midi_connection.close_port()
        except:
            pass
        midi_connection = None
    port_opened = False

def on_cleanup():
    stop()

# Uncomment to list available MIDI ports:
# list_ports()

main()