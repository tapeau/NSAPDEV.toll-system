# TOLL SYSTEM
A simple command-line toll system implementation developed in Python as Final Project for DLSU NSAPDEV course (T2 2024-2025). Implements both server and client application.

## Members
- James Kielson Cipriaso
- John Lorenzo Tapia

## Running the server
Build and run the client with the necessary parameters.

- `port` (int): The port number to be used by the server.
```
py server.py <port>
```

## Running the client
Build and run the client with the necessary parameters.

- `address` (string): The address of the toll server. Must be a valid IPv4 or IPv6 address.
- `port` (int): The port number of the toll server application.
- `action` (string): The type of client action to the toll system. Must a string of strictly either `ENTRY` or `EXIT`.
- `plate` (string): The plate number used by the client for the interaction with the toll system.
- `point` (int): The toll point from which the client performed their action to the toll system.
```
py client.py <address> <port> <interaction> <plate> <point>
```

### Examples:
```
py server.py 8224
```
```
py client.py 127.0.0.1 12345 ENTRY ABC123 9
```

## User prompts
If no command-line arguments are provided, the script will prompt the user for each input.
