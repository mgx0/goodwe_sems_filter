#!/usr/bin/env python3
import os
import sys
import socket
import binascii
import threading
import dns.resolver
import logging
import signal
from datetime import datetime

# Configuration
LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 20001
REMOTE_PORT = 20001
BUFFER_SIZE = 4096
ENABLE_DOWNLOAD = bool(os.environ.get("ENABLE_DOWNLOAD", "False").lower() in ['true', '1', 'yes'])
DEBUG = bool(os.environ.get("DEBUG", "False").lower() in ['true', '1', 'yes'])
GOODWE_TCP_SERVER = os.environ.get("GOODWE_TCP_SERVER", 'tcp.goodwe-power.com')
LOG_FILE = os.environ.get("LOG_FILE", "")  # Empty string means log to console only
MAX_CONNECTIONS = int(os.environ.get("MAX_CONNECTIONS", "100"))

# Global variables
server_socket = None
connection_semaphore = threading.Semaphore(MAX_CONNECTIONS)
running = True

# Set up logging
def setup_logging():
    log_level = logging.DEBUG if DEBUG else logging.INFO
    log_format = '%(asctime)s - %(levelname)s - %(message)s'

    # Create logger
    logger = logging.getLogger('goodwe_sems_filter')
    logger.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)

    # Create file handler if LOG_FILE is specified
    if LOG_FILE:
        try:
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(log_format))
            logger.addHandler(file_handler)
        except Exception as e:
            logger.error(f"Failed to set up file logging to {LOG_FILE}: {e}")

    return logger

# Initialize logger
logger = setup_logging()

# Signal handler for graceful shutdown
def handle_sigterm(signum, frame):
    global running, server_socket
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False
    # Close the server socket to interrupt accept()
    if server_socket:
        try:
            server_socket.close()
        except Exception as e:
            logger.error(f"Error closing server socket: {e}")

    # Give threads a moment to close connections
    logger.info("Waiting for connections to close...")
    threading.Event().wait(3)
    logger.info("Exiting...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

def resolve_goodwe_ip():
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['8.8.8.8']
    try:
        answer = resolver.resolve(GOODWE_TCP_SERVER, 'A')
        return answer[0].to_text()
    except Exception as e:
        logger.error(f"DNS resolution failed: {e}")
        return None

def log_data(label, data):
    hex_data = binascii.hexlify(data).decode()
    if DEBUG:
        logger.debug(f"{label} HEX: {hex_data}")

    # If you want to log binary data to a separate file for analysis
    if DEBUG and LOG_FILE:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
        try:
            with open(f"data_{label.replace(' ', '_')}_{timestamp}.bin", "wb") as f:
                f.write(data)
        except Exception as e:
            logger.error(f"Failed to write binary data to file: {e}")

def forward_data(src, dst, label):
    try:
        while True:
            data = src.recv(BUFFER_SIZE)
            if not data:
                break
            log_data(label, data)
            dst.sendall(data)
    except Exception as e:
        logger.error(f"Error in {label}: {e}")
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass
        logger.info(f"Closed connection: {label}")

def handle_client(client_conn, client_addr):
    with connection_semaphore:
        logger.info(f"Connection from {client_addr} (active connections: {MAX_CONNECTIONS - connection_semaphore._value})")
        try:
            goodwe_ip = resolve_goodwe_ip()
            if not goodwe_ip:
                client_conn.close()
                return

            goodwe_conn = socket.create_connection((goodwe_ip, REMOTE_PORT), timeout=10)
            logger.info(f"Connected to GoodWe at {goodwe_ip}")

            client_conn.settimeout(30)
            goodwe_conn.settimeout(30)

            threading.Thread(target=forward_data, args=(client_conn, goodwe_conn, f"{client_addr} > GoodWe"), daemon=True).start()
            if ENABLE_DOWNLOAD:
                threading.Thread(target=forward_data, args=(goodwe_conn, client_conn, f"GoodWe > {client_addr}"), daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to handle client {client_addr}: {e}")
            client_conn.close()

def start_server():
    global server_socket, running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((LISTEN_HOST, LISTEN_PORT))
        server_socket.listen()
        logger.info(f"Debug mode: {DEBUG}")
        logger.info(f"Download enabled: {ENABLE_DOWNLOAD}")
        logger.info(f"Maximum concurrent connections: {MAX_CONNECTIONS}")
        logger.info(f"Proxy listening on {LISTEN_HOST}:{LISTEN_PORT}\n-----------------------------------------\n")

        while running:
            try:
                conn, addr = server_socket.accept()
                if running:  # Make sure we haven't been asked to shut down
                    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
            except socket.error as e:
                if running:  # Only log if it wasn't caused by shutdown
                    logger.error(f"Socket error: {e}")
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")

    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        if server_socket:
            server_socket.close()
        logger.info("Server shut down")

if __name__ == "__main__":
    start_server()