from machine import UART, Pin
import time
import configl as config

uart = UART(config.UART_ID, baudrate=9600,
            tx=Pin(config.TX_PIN), rx=Pin(config.RX_PIN))

def send_at(cmd, delay=0.5):
    uart.write((cmd + '\r\n').encode())
    time.sleep(delay)
    if uart.any():
        return uart.read().decode()
    return ''

def setup():
    send_at('ATZ', delay=3)
    send_at(f'AT+DEUI={config.DEV_EUI}')
    send_at(f'AT+APPEUI={config.JOIN_EUI}')
    send_at(f'AT+NWKKEY={config.APP_KEY}')

def join():
    uart.write(b'AT+JOIN=1\r\n')
    start = time.time()
    while time.time() - start < 12:
        if uart.any() and 'JOINED' in uart.read().decode():
            return True
        time.sleep(0.1)
    return False

def send(msg):
    send_at(f'AT+SEND=2:0:{msg.encode().hex()}', delay=3)

def run():
    setup()
    time.sleep(2)
    while not join():
        time.sleep(15)
    while True:
        send('hello from brooklyn roof')
        time.sleep(60)

#run()