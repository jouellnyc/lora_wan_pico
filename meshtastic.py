#TBD - pi4
import meshtastic
import meshtastic.serial_interface
from pubsub import pub
import datetime
import time

def on_receive(packet, interface):
    from_id = packet.get('fromId')
    snr = packet.get('rxSnr')
    hops = packet.get('hopStart', 0) - packet.get('hopLimit', 0)
    decoded = packet.get('decoded', {})
    portnum = decoded.get('portnum')
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    line = f"{timestamp} | {from_id} | {portnum} | SNR:{snr} | hops:{hops}"
    print(line)
    with open("mesh_log.txt", "a") as f:
        f.write(line + "\n")

def on_connection(interface, topic=pub.AUTO_TOPIC):
    print("Connected — sending message")
    interface.sendText("hello from OptiPlex")
    print("Message sent")

def on_nodes(node, interface):
    user = node.get('user', {})
    pos = node.get('position', {})
    print(f"\n{user.get('longName')} | {user.get('hwModel')}")
    print(f"  SNR: {node.get('snr')}")
    print(f"  Last heard: {node.get('lastHeard')}")
    print(f"  Hops: {node.get('hopsAway')}")
    print(f"  Lat: {pos.get('latitude')} Lon: {pos.get('longitude')}")
    print(f"  Altitude: {pos.get('altitude')}")

pub.subscribe(on_receive, "meshtastic.receive")
pub.subscribe(on_connection, "meshtastic.connection.established")
pub.subscribe(on_nodes, "meshtastic.node.updated")

iface = meshtastic.serial_interface.SerialInterface("/dev/ttyUSB0")

time.sleep(300)  # 5 minutes, adjust as needed
iface.close()
