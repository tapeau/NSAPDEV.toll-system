import socket
import multiprocessing
import time
import logging
import sys

# Define a fixed toll fee rate per unit distance (here, per toll point difference)
RATE = 1.0

def setup_logging():
    """Configure logging to log to both console and a file."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    
    # File handler writes logs to server.log
    fh = logging.FileHandler("server.log", mode='a')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    
    # Console handler writes logs to stdout
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    
    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    else:
        logger.handlers.clear()
        logger.addHandler(fh)
        logger.addHandler(ch)

def handle_client(conn, address, vehicles, total_vehicles, total_fees, lock):
    """
    Handle a single client (toll booth) connection.
    Message format: "TYPE,plate,point"
    Where TYPE is either "ENTRY" or "EXIT", plate is the vehicle plate number,
    and point is the toll booth number.
    """
    setup_logging()  # Ensure logging is configured in this child process
    with conn:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                return
            parts = data.split(',')
            if len(parts) != 3:
                error_msg = "ERROR: Invalid message format"
                conn.sendall(error_msg.encode())
                logging.error(f"From {address}: {error_msg}")
                return

            transaction_type, plate, point_str = parts
            try:
                point = int(point_str)
            except ValueError:
                error_msg = "ERROR: Invalid toll point"
                conn.sendall(error_msg.encode())
                logging.error(f"From {address}: {error_msg}")
                return

            if transaction_type.upper() == "ENTRY":
                with lock:
                    if plate in vehicles:
                        response = f"ERROR: Vehicle {plate} already in highway"
                        conn.sendall(response.encode())
                        logging.error(f"CLIENT ENTRY ERROR: Plate {plate} attempted re-entry at toll point {point}.")
                        return
                    else:
                        vehicles[plate] = point
                        response = f"Vehicle {plate} entered at point {point}"
                conn.sendall(response.encode())
                logging.info(f"CLIENT ENTRY: Plate {plate} entered at toll point {point}.")
            
            elif transaction_type.upper() == "EXIT":
                with lock:
                    if plate not in vehicles:
                        response = f"ERROR: Vehicle {plate} not found in highway"
                        conn.sendall(response.encode())
                        logging.error(f"CLIENT EXIT ERROR: Plate {plate} not found when attempting exit at toll point {point}.")
                        return
                    else:
                        entry_point = vehicles.pop(plate)
                        distance = abs(point - entry_point)
                        fee = distance * RATE
                        total_fees.value += fee
                        total_vehicles.value += 1
                        response = f"Vehicle {plate} exited at point {point}. Fee: {fee}"
                conn.sendall(response.encode())
                logging.info(f"CLIENT EXIT: Plate {plate} exited at toll point {point} with fee collected {fee}.")
            
            else:
                error_msg = "ERROR: Unknown transaction type"
                conn.sendall(error_msg.encode())
                logging.error(f"From {address}: {error_msg}")
        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            conn.sendall(error_msg.encode())
            logging.exception(f"Exception handling client {address}: {error_msg}")

def stats_display(vehicles, total_vehicles, total_fees, stop_event):
    """
    Display highway statistics in real time every 5 seconds.
    Shows:
      - Current number of vehicles in the highway
      - Total number of vehicles that have used the highway
      - Total fees collected
    """
    setup_logging()
    while not stop_event.is_set():
        current_count = len(vehicles)
        stats_message = (f"Current vehicles in highway: {current_count} | "
                         f"Total vehicles used highway: {total_vehicles.value} | "
                         f"Total fees collected: {total_fees.value}")
        logging.info(stats_message)
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            break
    logging.info("Stats display process terminating.")

def main():
    setup_logging()
    
    # Determine the port number from command-line argument or user input.
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number provided. Please enter a valid integer.")
            sys.exit(1)
    else:
        port_input = input("Enter the port number to use for the server: ")
        try:
            port = int(port_input)
        except ValueError:
            print("Invalid port number entered. Exiting.")
            sys.exit(1)
    
    host = '0.0.0.0'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.settimeout(1.0)  # Set timeout so accept() is not blocking indefinitely
    server_socket.bind((host, port))
    server_socket.listen(10)
    logging.info(f"Server listening on {host}:{port}")
    logging.info("Booting up. Press Ctrl+C to exit the server program.")

    manager = multiprocessing.Manager()
    vehicles = manager.dict()              # { plate: entry_point }
    total_vehicles = manager.Value('i', 0)   # count of vehicles that have exited
    total_fees = manager.Value('d', 0.0)     # total fees collected
    lock = manager.Lock()
    stop_event = manager.Event()           # Used to signal the stats_display process to stop

    # Start a separate process to display stats in real time
    stats_process = multiprocessing.Process(
        target=stats_display, args=(vehicles, total_vehicles, total_fees, stop_event)
    )
    stats_process.start()

    # Keep track of client handler processes for a graceful shutdown
    processes = []
    try:
        while True:
            try:
                conn, address = server_socket.accept()
            except socket.timeout:
                continue
            process = multiprocessing.Process(
                target=handle_client,
                args=(conn, address, vehicles, total_vehicles, total_fees, lock)
            )
            process.start()
            processes.append(process)
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt detected. Server shutting down.")
    finally:
        stop_event.set()  # Signal the stats display process to exit
        server_socket.close()
        logging.info("Server socket closed. Waiting for child processes to finish.")
        # Join all child processes
        for process in processes:
            process.join(timeout=5)
        stats_process.join(timeout=5)
        logging.info("All processes terminated. Exiting server.")

if __name__ == "__main__":
    main()
