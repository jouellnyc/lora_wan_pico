# REYAX RYLR998 & RYLR993 LoRa Modules with MicroPython

A practical guide based on real-world testing with Raspberry Pi Pico.

---

## Overview

| | RYLR998 | RYLR993 |
|---|---|---|
| Protocol | Proprietary point-to-point only | Proprietary + LoRaWAN |
| Default baud | 115200 | 9600 |
| Reset command | `AT+RESET` | `ATZ` |
| Address command | `AT+ADDRESS` | N/A (LoRaWAN uses DevEUI) |
| Send command | `AT+SEND=addr,len,data` | `AT+SEND=port:ack:hexdata` |
| AppKey command | `AT+APPKEY` | `AT+NWKKEY` |
| DevEUI command | `AT+DEVEUI` | `AT+DEUI` |
| Key format | No separator | Colon separated (AA:BB:CC...) |
| LoRaWAN | ❌ (AT+MODE=1 does not work) | ✅ |
| Price | ~$12 | ~$18 |
| Best for | Direct device-to-device comms | TTN / LoRaWAN IoT |

---

## RYLR998 — Point-to-Point

### What it does
Two modules talk directly to each other over LoRa. No internet, no gateway, no infrastructure. Range up to 5km line of sight.

### Breadboard wiring (Raspberry Pi Pico)

```
RYLR998          Pico
-------          ----
VDD      →       3.3V (Pin 36)
GND      →       GND
TXD      →       GP1 (UART0 RX)
RXD      →       GP0 (UART0 TX)
RST      →       (optional GPIO)
```

> Note: RYLR998 TXD connects to Pico RX and vice versa. Easy to mix up.

### MicroPython setup

```python
from machine import UART, Pin
import time

uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

def send_at(cmd, delay=0.1):
    uart.write((cmd + '\r\n').encode())
    time.sleep(delay)
    if uart.any():
        return uart.read().decode()
    return ''

# Configure
send_at('AT')                    # should return +OK
send_at('AT+ADDRESS=1')          # this device address
send_at('AT+NETWORKID=6')        # shared with other device
send_at('AT+BAND=915000000')     # 915MHz US / 868000000 EU

# Send to address 2
send_at('AT+SEND=2,5,hello')

# Receive
while True:
    if uart.any():
        print(uart.read().decode())
    time.sleep(0.05)
```

Incoming message format:
```
+RCV=1,5,hello,-67,8
       ^   ^    ^   ^
     addr len  rssi snr
```

### Key AT commands

| Command | Description |
|---|---|
| `AT` | Ping — returns `+OK` |
| `AT+ADDRESS=n` | Set device address (0-65535) |
| `AT+NETWORKID=n` | Set network ID (3-15), must match peer |
| `AT+BAND=915000000` | Set frequency |
| `AT+SEND=addr,len,data` | Send message |
| `AT+PARAMETER=12,4,1,7` | Max range mode (SF12) |
| `AT+RESET` | Soft reset |
| `AT+VER?` | Firmware version |

### Pros
- Simple, reliable, well documented
- No account or infrastructure needed
- Proven 5km range line of sight
- Settings persist in flash

### Cons
- Point-to-point only — no LoRaWAN despite what the datasheet implies
- `AT+MODE=1` does not work — LoRaWAN mode is not implemented

---

## RYLR993 — LoRaWAN

### What it does
Full LoRaWAN support. Connects to gateways on The Things Network (TTN), Helium, or any LoRaWAN network server. Data goes from module → gateway → internet → your app.

### Breadboard wiring (Raspberry Pi Pico)

Same as RYLR998 — VDD, GND, TXD→RX, RXD→TX. Module runs on 3.3V.

### TTN setup

1. Create account at [console.cloud.thethings.network](https://console.cloud.thethings.network)
2. Select **North America 1** cluster
3. Create application
4. Register end device — manual entry:
   - LoRaWAN version: **1.0.2**
   - Regional parameters: **RP001 1.0.2**
   - Frequency plan: **United States 902-928 MHz, FSB 2**
   - Activation: **OTAA**
5. Generate DevEUI and AppKey
6. Set JoinEUI to `0000000000000000`

### MicroPython setup

```python
from machine import UART, Pin
import time

uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

DEV_EUI  = 'XX:YY'   # colon format
JOIN_EUI = '00:00:00:00:00:00:00:00'
APP_KEY  = 'XX:YY'

def send_at(cmd, delay=0.5):
    uart.write((cmd + '\r\n').encode())
    time.sleep(delay)
    if uart.any():
        return uart.read().decode()
    return ''

def setup():
    send_at('ATZ', delay=3)              # reset — also confirms US915 band
    send_at(f'AT+DEUI={DEV_EUI}')
    send_at(f'AT+APPEUI={JOIN_EUI}')
    send_at(f'AT+NWKKEY={APP_KEY}')

def join():
    uart.write(b'AT+JOIN=1\r\n')
    start = time.time()
    while time.time() - start < 12:
        if uart.any() and 'JOINED' in uart.read().decode():
            return True
        time.sleep(0.1)
    return False

def send(msg):
    payload = msg.encode().hex()
    send_at(f'AT+SEND=2:0:{payload}', delay=3)

setup()
while not join():
    time.sleep(15)
send('hello from brooklyn')
```

### Key AT commands

| Command | Description |
|---|---|
| `ATZ` | Reset — returns firmware info + `+READY` |
| `AT+DEUI=xx:xx:...` | Set DevEUI (colon format) |
| `AT+APPEUI=xx:xx:...` | Set JoinEUI |
| `AT+NWKKEY=xx:xx:...` | Set AppKey |
| `AT+JOIN=1` | OTAA join — listen for `+EVT:JOINED` |
| `AT+SEND=port:ack:hexdata` | Send payload (hex encoded) |
| `AT+SEND?` | Show send syntax |

### Payload decoding on TTN

Add this JavaScript formatter under **Payload formatters → Uplink**:

```javascript
function decodeUplink(input) {
  var bytes = input.bytes;
  var str = String.fromCharCode.apply(null, bytes);
  return { decoded: { message: str } };
}
```

### Pros
- Real LoRaWAN — connects to TTN, Helium, etc.
- Data accessible anywhere via internet
- Proven working on NYC FloodNet gateway infrastructure
- Band pre-configured for US915 — no band command needed

### Cons
- Requires gateway coverage — indoors can be hit or miss
- Join timing is finicky — module can miss the join-accept window
- Different command syntax from RYLR998 — not a drop-in replacement
- Default 9600 baud (slower than 998)
- Payload must be hex encoded

---

## Coverage

- Check TTN gateway coverage: [ttnmapper.org](https://ttnmapper.org)
- In NYC, FloodNet and community gateways provide decent coverage
- Rooftop or elevated positions dramatically improve reliability
- Indoors coverage is unreliable in most areas

---

## Range (RYLR998 point-to-point)

| Environment | Range |
|---|---|
| Indoors | 50-200m |
| Urban street level | 200-500m |
| Rooftop line of sight | 1-3km |
| Max settings (SF12) rooftop | 5-10km |

Boost range with: `AT+PARAMETER=12,4,1,7` — both devices must match.

## Acknowledgements
Developed with assistance from [Claude](https://claude.ai) (Anthropic).

---

## Related projects
- [Meshtastic](https://meshtastic.org) — mesh networking on LoRa, no infrastructure needed
- [MeshCore](https://meshcore.co) — alternative mesh firmware, compatible with Heltec V3
- [The Things Network](https://thethingsnetwork.org) — free LoRaWAN network server

