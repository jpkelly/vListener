import socket
import json
import keyboard
import signal
import sys
import time
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variable to hold the server socket
server_socket = None

# Function to handle client connections
def handle_client(client_socket):
    try:
        while True:
            # Receive data from the client
            data = client_socket.recv(1024)
            if not data:
                break
            
            # Process the received data (parse and execute command)
            command = data.decode('utf-8').strip()
            logging.info(f"Received command: {command}")
            
            # Parse the command and execute appropriate action
            response = parse_command(command)
            
            # Send a response back to the client
            client_socket.sendall(response.encode('utf-8'))
    finally:
        # Close the client connection
        client_socket.close()

# Function to parse and execute commands
def parse_command(command):
    try:
        command_dict = json.loads(command)
        
        if 'key' in command_dict and 'type' in command_dict:
            if command_dict['type'] in ['press', 'pressSpecial', 'combination', 'trio']:
                if 'password' in command_dict and command_dict['password'] == 'd41d8cd98f00b204e9800998ecf8427e':
                    key = command_dict['key']
                    
                    if command_dict['type'] == 'press':
                        logging.info(f"Simulating key press: {key}")
                        time.sleep(2)  # Introduce a 2-second delay
                        # Simulate key press using keyboard library
                        keyboard.press(key)
                        keyboard.release(key)
                        return f"Key press simulated: {key}"
                    
                    elif command_dict['type'] == 'pressSpecial':
                        logging.info(f"Simulating special key press: {key}")
                        time.sleep(2)  # Introduce a 2-second delay
                        # Simulate key press using keyboard library
                        keyboard.press_and_release(key)  # Use keyboard.press_and_release for special characters
                        return f"Special key press simulated: {key}"
                    
                    elif command_dict['type'] == 'combination':
                        if 'modifiers' in command_dict:
                            modifiers = command_dict['modifiers']
                            combo = '+'.join(modifiers) + '+' + key
                            logging.info(f"Simulating key combination: {combo}")
                            time.sleep(2)  # Introduce a 2-second delay
                            # Simulate key combination using keyboard library
                            keyboard.press_and_release(combo)
                            return f"Key combination simulated: {combo}"
                        else:
                            return "Missing modifiers for key combination"
                    
                    elif command_dict['type'] == 'trio':
                        if 'modifiers' in command_dict and len(command_dict['modifiers']) == 2:
                            modifiers = command_dict['modifiers']
                            combo = '+'.join(modifiers) + '+' + key
                            logging.info(f"Simulating key trio: {combo}")
                            time.sleep(2)  # Introduce a 2-second delay
                            # Simulate key combination using keyboard library
                            keyboard.press_and_release(combo)
                            return f"Key trio simulated: {combo}"
                        else:
                            return "Trio command requires exactly two modifiers"
                else:
                    return "Unauthorized access: Incorrect password"
            else:
                return "Unsupported command type"
        else:
            return "Invalid command format"

    except json.JSONDecodeError:
        return "Invalid JSON format"

# Signal handler function to handle Ctrl+C (SIGINT)
def signal_handler(sig, frame):
    logging.info("Server is shutting down...")
    global server_socket
    if server_socket:
        server_socket.close()
    sys.exit(0)

# Main server function
def start_server(host, port):
    global server_socket
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Bind the socket to the host and port
    server_socket.bind((host, port))
    
    # Listen for incoming connections
    server_socket.listen(5)
    logging.info(f"Server listening on {host}:{port}...")
    
    # Register signal handler for Ctrl+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while True:
            # Wait for a connection
            client_socket, client_address = server_socket.accept()
            logging.info(f"Accepted connection from {client_address}")
            
            # Handle client communication in a separate thread
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True  # Ensure threads exit when the main program exits
            client_thread.start()
    except KeyboardInterrupt:
        logging.info("Server terminated by user.")
    finally:
        if server_socket:
            server_socket.close()

# Start the server
if __name__ == "__main__":
    HOST = '127.0.0.1'  # Localhost
    PORT = 12345        # Port number (choose an available port)

    start_server(HOST, PORT)
