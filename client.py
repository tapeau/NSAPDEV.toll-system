import socket
import sys

def send_transaction(server_host, server_port, transaction_type, plate, toll_point):
    """
    Connects to the server, sends the transaction message, and prints the server's response.
    
    Message format: "TYPE,plate,toll_point"
    Example: "ENTRY,ABC123,3" or "EXIT,ABC123,10"
    """
    message = f"{transaction_type},{plate},{toll_point}"
    
    try:
        # Create a TCP socket connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_host, server_port))
            s.sendall(message.encode())
            
            # Wait for a response from the server (up to 1024 bytes)
            response = s.recv(1024).decode()
            print("Server response:", response)
    except Exception as e:
        print("Error communicating with the server:", e)

def main():
    # If command-line arguments are provided, use them.
    if len(sys.argv) == 6:
        server_host = sys.argv[1]
        try:
            server_port = int(sys.argv[2])
        except ValueError:
            print("Error: Server port must be an integer.")
            sys.exit(1)
        transaction_type = sys.argv[3].upper()  # Normalize to uppercase
        plate = sys.argv[4]
        toll_point = sys.argv[5]
    else:
        # Otherwise, run in interactive mode.
        print("No command line arguments provided; entering interactive mode.")
        server_host = input("Enter server host (e.g. 127.0.0.1): ")
        try:
            server_port = int(input("Enter server port (e.g. 12345): "))
        except ValueError:
            print("Error: Server port must be an integer.")
            return
        transaction_type = input("Enter transaction type (ENTRY/EXIT): ").upper()
        plate = input("Enter vehicle plate number: ")
        toll_point = input("Enter toll point number: ")
    
    send_transaction(server_host, server_port, transaction_type, plate, toll_point)

if __name__ == "__main__":
    main()
