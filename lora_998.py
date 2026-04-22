from machine import UART, Pin
import time
import config

cfg  = config.DEVICES[config.DEVICE]
uart = UART(cfg['uart_id'], baudrate=115200, tx=Pin(cfg['tx']), rx=Pin(cfg['rx']))

def send_at(cmd, delay=0.1):
    uart.write((cmd + '\r\n').encode())
    time.sleep(delay)
    if uart.any():
        return uart.read().decode()
    return ''

def setup():
    send_at(f'AT+ADDRESS={cfg["address"]}')
    send_at(f'AT+NETWORKID={config.NETWORK}')
    send_at(f'AT+BAND={config.BAND}')
    print(f'Ready. Device={config.DEVICE} Address={cfg["address"]}')

def send(msg):
    # sends to the other device automatically
    other = 2 if cfg['address'] == 1 else 1
    send_at(f'AT+SEND={other},{len(msg)},{msg}')
    print(f'>>> {msg}')

def parse(raw):
    try:
        parts = raw.strip().split(',')
        addr  = parts[0].split('=')[1]
        data  = parts[2]
        rssi  = parts[3]
        snr   = parts[4]
        return addr, data, rssi, snr
    except:
        return None, raw, None, None

def listen():
    print('Listening... Ctrl+C to stop')
    while True:
        if uart.any():
            raw = uart.read().decode()
            if raw.startswith('+RCV'):
                addr, data, rssi, snr = parse(raw)
                print(f'[from {addr}]: {data}  (RSSI:{rssi} SNR:{snr})')
        time.sleep(0.05)