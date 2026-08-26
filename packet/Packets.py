import base64
from contextlib import contextmanager
import io
import json
from pathlib import Path
import struct
import time
import socket
import os
import uuid
from PIL import Image, ImageFilter
import av
import numpy as np

class Packet:
    def __init__(self, src_ip:str, dst_ip:str, src_port:int, dst_port:int, protocol:str, raw:bytes, timestamp:int=None):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.protocol = protocol
        self.raw = raw
        self.timestamp = timestamp or int(time.time() * 1000)
    
    @classmethod
    def deserialize(cls, json_data: dict):
        params = {
            **json_data, 
            "raw": base64.b64decode(json_data['raw'])
        }
        return Packet(**params)
        
    def serialize(self) -> dict:
        return {
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": self.src_port,
            "dst_port": self.dst_port,
            "protocol": self.protocol,
            "raw": base64.b64encode(self.raw).decode('utf-8'),
            "timestamp": self.timestamp
        }
        
    @property
    def identity(self) -> str:
        return f'{self.src_ip}:{self.src_port}->{self.dst_ip}:{self.dst_port}'

class PacketEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Packet):
            return obj.serialize()
        return super().default(obj)

class Sniffer:
    def __init__(self, host, promiscous_mode=False):
        self.host = host
        
        self.skt = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)
        self.skt.bind((host, 0))
        self.skt.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        self.skt.settimeout(1.0)
        
        self._promiscous_mode = promiscous_mode
        self._toggle_rcvall()
    
    @property
    def promiscous_mode(self) -> bool:
        return self._promiscous_mode
    
    @promiscous_mode.setter
    def promiscous_mode(self, value):
        self._promiscous_mode = value
        self._toggle_rcvall()
    
    def _toggle_rcvall(self):
        if os.name == "nt":
            rcvall_mode = socket.RCVALL_ON if self.promiscous_mode else socket.RCVALL_OFF
            self.skt.ioctl(socket.SIO_RCVALL, rcvall_mode)

    def _parse_packet(self, raw: bytes):
        try:
            ip_header = raw[:20]
            iph = struct.unpack('!BBHHHBBH4s4s', ip_header)
            
            ihl = (iph[0] & 0xF) * 4
            protocol = iph[6]
            src_ip = socket.inet_ntoa(iph[8])
            dst_ip = socket.inet_ntoa(iph[9])

            src_port = None
            dst_port = None
            proto_name = 'OTHER'

            if protocol == 6:  # TCP
                tcp_header = raw[ihl:ihl+20]
                tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                src_port, dst_port = tcph[0], tcph[1]
                proto_name = 'TCP'

            elif protocol == 17:  # UDP
                udp_header = raw[ihl:ihl+8]
                udph = struct.unpack('!HHHH', udp_header)
                src_port, dst_port = udph[0], udph[1]
                proto_name = 'UDP'

            return Packet(
                src_ip, dst_ip,
                src_port, dst_port,
                proto_name,
                raw
            )

        except Exception:
            return None
    
    def receive(self, parsed=True):
        try:
            data, _ = self.skt.recvfrom(65535)
            
            if not parsed:
                return data
            
            packet = self._parse_packet(data)
            
            return packet
        except socket.timeout:
            return None
    
    def close(self):
        self.promiscous_mode = False
        self.skt.close()
        
@contextmanager
def sniff(host: str, promiscous_mode: bool = False):
    sniffer = Sniffer(host, promiscous_mode)  
    try:  
        yield sniffer 
    finally:  
        sniffer.close()
    
def listen(host: str, time_limit: int = 10, promiscous_mode: bool = False):
    incoming_data = []
    
    start_t = time.time()
    end_t = start_t + time_limit
    
    print('Started Listening')
    
    with sniff(host, promiscous_mode) as sniffer:
        while time.time() < end_t:
            packet = sniffer.receive()

            if not packet:
                continue
            
            incoming_data.append(packet)
    
    print('Finished Listening')
    return incoming_data

def draw(packets: list[Packet], width: int, height: int, scale: int, bytes_per_frame: int = 1):
    print('Started Drawing')

    frames = []

    if not packets:
        return frames

    # Sort packets by timestamp
    packets = sorted(packets, key=lambda p: p.timestamp)

    # Map identity → row
    identity_to_row = {}
    next_row = 0

    # Rolling buffers per row
    buffers = {}

    # Active packet streams
    active = []

    # Time tracking
    t = packets[0].timestamp
    end_t = packets[-1].timestamp
    i = 0

    while t <= end_t or active:
        # === ADD NEW PACKETS ===
        while i < len(packets) and packets[i].timestamp <= t:
            p = packets[i]
            ident = p.identity

            if ident not in identity_to_row:
                if next_row >= height:
                    i += 1
                    continue
                identity_to_row[ident] = next_row
                buffers[ident] = [0] * width
                next_row += 1

            active.append({
                "identity": ident,
                "data": p.raw,
                "index": 0
            })

            i += 1

        # === SHIFT LEFT ===
        for buf in buffers.values():
            buf.pop(0)
            buf.append(0)

        # === STREAM BYTES ===
        still_active = []
        for stream in active:
            ident = stream["identity"]

            for _ in range(bytes_per_frame):
                if stream["index"] >= len(stream["data"]):
                    break

                byte_val = stream["data"][stream["index"]]

                # Write to newest pixel
                buffers[ident][-1] = byte_val

                stream["index"] += 1

            if stream["index"] < len(stream["data"]):
                still_active.append(stream)

        active = still_active

        # === RENDER FRAME ===
        frame = Image.new('RGB', (width, height))
        px = frame.load()

        for ident, row in identity_to_row.items():
            buf = buffers[ident]
            for x in range(width):
                if buf:
                    v = buf[x]
                    px[x, row] = (v, v, v)
                else:
                    px[x, row] = (255, 0, 0)

        frame = frame.resize((width * scale, height * scale), Image.Resampling.NEAREST)
        frame = frame.filter(ImageFilter.GaussianBlur(0.25))
        frames.append(frame)

        t += 1  # simulated time step

    print('Finished Drawing')
    return frames

def write_to_json(path, incoming_data):
    with open(path, 'w') as f:
        json.dump(incoming_data, f, indent=2, cls=PacketEncoder)
        
def read_from_json(path):
    with open(path, 'r') as f:
        data = json.load(f) 
        
    # rehydrate byte data
    data = [Packet.deserialize(pkt) for pkt in data]
            
    return data

def pil_gif_to_mp4_bytes(frames, fps=24):
    print("Started Rendering")
    
    buf = io.BytesIO()
    container = av.open(buf, mode="w", format="mp4")
    
    # Use the first frame to set dimensions
    w, h = frames[0].width, frames[0].height
    even_w = w if w % 2 == 0 else w - 1
    even_h = h if h % 2 == 0 else h - 1

    stream = container.add_stream("libx264", rate=fps)
    stream.width = even_w
    stream.height = even_h
    stream.pix_fmt = "yuv420p" # Standard for MP4 compatibility
    
    for frame in frames:
        # 1. Ensure it's grayscale ('L')
        # 2. Crop/Resize to even dimensions if necessary
        img = frame.copy()
        if w != even_w or h != even_h:
            img = img.crop((0, 0, even_w, even_h))
            
        img_array = np.array(img)
        
        av_frame = av.VideoFrame.from_ndarray(img_array, format="rgb24")
        
        for packet in stream.encode(av_frame):
            container.mux(packet)

    for packet in stream.encode():
        container.mux(packet)
    
    container.close()
    buf.seek(0)
    print("Finished Rendering")
    return buf

FPS = 30

#uuid4 = '6326cc3a-b8d7-43e5-86c7-984c991fac3f'
uuid4 = uuid.uuid4()

base_path = Path(__file__).parent / 'output'
base_path.mkdir(exist_ok=True)

json_export_path = base_path / f'net_traffic_{uuid4}.json'

data = listen('192.168.3.103', 15, True)
write_to_json(json_export_path, data)

json_import_path = base_path / f'net_traffic_{uuid4}.json'
mp4_export_path = base_path / f'net_traffic_{uuid4}.mp4'

#data = read_from_json(json_import_path)
frames = draw(data, 240, 135, 8, 4)
buf = pil_gif_to_mp4_bytes(frames)
mp4_export_path.write_bytes(buf.getvalue())

#draw rows of bits offset by a rolling time value