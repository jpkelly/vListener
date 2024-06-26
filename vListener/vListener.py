import json
import time
import keyboard
import socket
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.core.window import Window
import threading
import logging
import os
from pathlib import Path
from kivy.graphics import Color, Rectangle

# Define app version
APP_VERSION = "0.2"
CONFIG_DIR = Path.home() / "Library/Application Support/vlistener"
CONFIG_FILE = CONFIG_DIR / "vlistener_settings.json"

# Default configuration values
DEFAULT_IP_ADDRESS = "127.0.0.1"
DEFAULT_PORT = 12345
DEFAULT_DELAY_MS = 2500
DEFAULT_DEBUG_MODE = False
STARTUP_MESSAGE = "\n***** vListener started ***** \nYou can close this window and it will run in background.\nUse menu extra (ear icon) to show this window again or to quit vListener.\n****************************"

# Configure the logging
log_file_path = os.path.join(CONFIG_DIR, "vlistener.log")
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()])

# Function to create an icon image
def create_image():
    try:
        return Image.open('icon.png')
    except IOError:
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), 'white')
        dc = ImageDraw.Draw(image)
        dc.rectangle(
            (width // 4, height // 4, width // 4 * 3, height // 4 * 3),
            fill='black')
        return image

# Function to parse and execute commands
def parse_command(command, delay_ms):
    try:
        command_dict = json.loads(command)
        if 'key' in command_dict and 'type' in command_dict:
            if command_dict['type'] == 'press':
                if 'password' in command_dict and command_dict['password'] == 'd41d8cd98f00b204e9800998ecf8427e':
                    key = command_dict['key']
                    logging.debug(f"Simulating key press: {key}")
                    time.sleep(delay_ms / 1000.0)  # Convert milliseconds to seconds
                    keyboard.press(key)
                    keyboard.release(key)
                    return f"Key press simulated: {key}"
                else:
                    return "Unauthorized access: Incorrect password"
            elif command_dict['type'] == 'pressSpecial':
                if 'password' in command_dict and command_dict['password'] == 'd41d8cd98f00b204e9800998ecf8427e':
                    key = command_dict['key']
                    logging.debug(f"Simulating special key press: {key}")
                    time.sleep(delay_ms / 1000.0)  # Convert milliseconds to seconds
                    keyboard.press_and_release(key)
                    return f"Special key press simulated: {key}"
                else:
                    return "Unauthorized access: Incorrect password"
            elif command_dict['type'] == 'combination':
                if 'password' in command_dict and command_dict['password'] == 'd41d8cd98f00b204e9800998ecf8427e':
                    if 'modifiers' in command_dict:
                        modifiers = command_dict['modifiers']
                        key = command_dict['key']
                        combo = '+'.join(modifiers) + '+' + key
                        logging.debug(f"Simulating key combination: {combo}")
                        time.sleep(delay_ms / 1000.0)  # Convert milliseconds to seconds
                        keyboard.press_and_release(combo)
                        return f"Key combination simulated: {combo}"
                    else:
                        return "Missing modifiers for key combination"
                else:
                    return "Unauthorized access: Incorrect password"
            elif command_dict['type'] == 'trio':
                if 'password' in command_dict and command_dict['password'] == 'd41d8cd98f00b204e9800998ecf8427e':
                    if 'modifiers' in command_dict and len(command_dict['modifiers']) == 2:
                        modifiers = command_dict['modifiers']
                        key = command_dict['key']
                        combo = '+'.join(modifiers) + '+' + key
                        logging.debug(f"Simulating key trio: {combo}")
                        time.sleep(delay_ms / 1000.0)  # Convert milliseconds to seconds
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
    except json.JSONDecodeError as e:
        logging.debug(f"JSON Decode Error: {str(e)}")
        return "Invalid JSON format"

# Custom BoxLayout to handle background color
class ColoredBoxLayout(BoxLayout):
    def __init__(self, **kwargs):
        background_color = kwargs.pop('background_color', (1, 1, 1, 1))  # Default white
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*background_color)  # Set the background color
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class VicreoListenerApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_socket = None
        self.active_connections = []
        self.is_running = True
        self.debug_mode = DEFAULT_DEBUG_MODE
        self.delay_ms = DEFAULT_DELAY_MS  # Default delay in milliseconds
        self.listen_ip = DEFAULT_IP_ADDRESS  # Default IP address
        self.port = DEFAULT_PORT  # Default port number
        self.tray_icon = None  # To keep reference to the pystray icon

    def build(self):
        if self.debug_mode:
            logging.debug("Building the Kivy application UI")
        self.root = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Horizontal layout for port number, IP address, and corresponding buttons
        config_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60)
        
        self.ip_input = TextInput(text=self.listen_ip, hint_text="Enter IP address", multiline=False, size_hint_y=None, height=60)
        config_layout.add_widget(self.ip_input)
        
        self.set_ip_button = Button(text="Set IP", on_press=self.set_ip, size_hint_y=None, height=60)
        config_layout.add_widget(self.set_ip_button)
        
        self.port_input = TextInput(text=str(self.port), hint_text="Enter port number", multiline=False, size_hint_y=None, height=60)
        config_layout.add_widget(self.port_input)
        
        self.set_port_button = Button(text="Set Port", on_press=self.set_port, size_hint_y=None, height=60)
        config_layout.add_widget(self.set_port_button)
        
        self.delay_input = TextInput(text=str(self.delay_ms), hint_text="Enter delay (ms)", multiline=False, size_hint_y=None, height=60)
        config_layout.add_widget(self.delay_input)
        
        self.set_delay_button = Button(text="Set Delay", on_press=self.set_delay, size_hint_y=None, height=60)
        config_layout.add_widget(self.set_delay_button)
        
        self.root.add_widget(config_layout)
        
        # Horizontal layout for control buttons and debugging
        self.control_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=60)
        
        self.start_server_button = Button(text="Start Server", on_press=self.start_server, disabled=True, size_hint=(0.25, None), height=60)
        self.control_layout.add_widget(self.start_server_button)
        
        self.disconnect_button = Button(text="Disconnect", on_press=self.disconnect, disabled=True, size_hint=(0.25, None), height=60)
        self.control_layout.add_widget(self.disconnect_button)
        
        self.debug_toggle = ToggleButton(text="Debugging Off", size_hint=(0.25, None), height=60, background_color=(0.5, 0.5, 0.5, 1))
        self.debug_toggle.bind(on_press=self.toggle_debug)
        self.control_layout.add_widget(self.debug_toggle)
        
        self.quit_button = Button(text="Quit", on_press=self.quit_app, size_hint=(0.25, None), height=60)
        self.control_layout.add_widget(self.quit_button)
        
        self.hide_window_button = Button(text="HIDE (use menu to show)", on_press=self.hide_window, size_hint=(0.51, None), height=60, background_color=(0, 1, 0, 1))  # Green background
        self.control_layout.add_widget(self.hide_window_button)
        
        # New layout to control vertical spacing
        self.vertical_layout = BoxLayout(orientation='vertical', spacing=10)
        self.vertical_layout.add_widget(self.control_layout)

        # Add a redraw button below the control buttons
        self.redraw_button = Button(text="Redraw UI", on_press=self.redraw_ui, size_hint_y=None, height=40)
        self.redraw_button.opacity = 0  # Start hidden
        self.redraw_button.disabled = True  # Start disabled
        self.vertical_layout.add_widget(self.redraw_button)

        self.output = TextInput(readonly=True, size_hint=(1, 1), background_color=(0.9, 0.9, 0.9, 1), padding_y=(0, 10))  # Set top padding to 0
        self.vertical_layout.add_widget(self.output)
        
        self.root.add_widget(self.vertical_layout)

        self.update_text_alignment(self.ip_input)
        self.update_text_alignment(self.port_input)
        self.update_text_alignment(self.delay_input)

        # Add bottom bar for app version
        bottom_bar = ColoredBoxLayout(size_hint_y=None, height=30, background_color=(0.2, 0.2, 0.2, 1))  # Dark grey
        version_label = Label(text=f"Version: {APP_VERSION}", color=(0.7, 0.7, 0.7, 1), font_size='10sp', halign='left')  # Lighter text and smaller size
        bottom_bar.add_widget(version_label)
        self.root.add_widget(bottom_bar)

        Window.bind(on_request_close=self.hide_window)

        # Schedule configuration loading after the UI is fully set up
        Clock.schedule_once(self.post_build_init, 0)

        return self.root

    def update_text_alignment(self, text_input):
        if self.debug_mode:
            logging.debug(f"Updating text alignment for {text_input}")
        text_input.halign = 'center'
        text_input.bind(size=self._align_text)
        text_input.bind(focus=self._align_text)

    def _align_text(self, instance, value):
        if self.debug_mode:
            logging.debug(f"Aligning text for {instance}")
        instance.text_size = instance.size
        instance.padding_y = (instance.height - instance.line_height) / 2

    def toggle_debug(self, instance):
        if self.debug_mode:
            logging.debug("Toggling debug mode")
        self.debug_mode = not self.debug_mode
        self.debug_toggle.text = "Debugging On" if self.debug_mode else "Debugging Off"
        self.debug_toggle.background_color = (0.5, 0.5, 0.5, 1)
        self.log_message(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")
        self.update_redraw_button_visibility()
        self.update_vertical_spacing()
        self.save_config()

    def update_redraw_button_visibility(self):
        if self.debug_mode:
            logging.debug("Updating redraw button visibility")
        if self.debug_mode:
            self.redraw_button.opacity = 1
            self.redraw_button.disabled = False
        else:
            self.redraw_button.opacity = 0
            self.redraw_button.disabled = True

    def update_vertical_spacing(self):
        if self.debug_mode:
            logging.debug("Updating vertical spacing")
        # Adjust vertical spacing around the redraw button
        if self.debug_mode:
            self.vertical_layout.spacing = 10
            self.redraw_button.height = 40
        else:
            self.vertical_layout.spacing = 5
            self.redraw_button.height = 0

    def set_ip(self, instance):
        if self.debug_mode:
            logging.debug("Setting IP address")
        self.listen_ip = self.ip_input.text
        self.log_message(f"IP address set to {self.listen_ip}")
        if self.debug_mode:
            self.log_message(f"[DEBUG] IP address set to {self.listen_ip}")
        self.save_config()

    def set_port(self, instance):
        if self.debug_mode:
            logging.debug("Setting port number")
        if self.port_input.text.isdigit() and 0 <= int(self.port_input.text) <= 65535:
            self.start_server_button.disabled = False
            self.port = int(self.port_input.text)
            self.log_message(f"Port set to {self.port}")
            if self.debug_mode:
                self.log_message(f"[DEBUG] Port set to {self.port}")
            self.save_config()
        else:
            self.log_message("Invalid port number")
            if self.debug_mode:
                self.log_message("[DEBUG] Invalid port number entered")

    def set_delay(self, instance):
        if self.debug_mode:
            logging.debug("Setting delay value")
        if self.delay_input.text.isdigit() and int(self.delay_input.text) >= 0:
            self.delay_ms = int(self.delay_input.text)
            self.log_message(f"Delay set to {self.delay_ms} milliseconds")
            if self.debug_mode:
                self.log_message(f"[DEBUG] Delay set to {self.delay_ms} milliseconds")
            self.save_config()
        else:
            self.log_message("Invalid delay value")
            if self.debug_mode:
                self.log_message("[DEBUG] Invalid delay value entered")

    def start_server(self, instance):
        if self.debug_mode:
            logging.debug("Starting server")
        self.start_server_button.disabled = True
        self.disconnect_button.disabled = False
        self.is_running = True
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.start()
        if self.debug_mode:
            self.log_message("[DEBUG] Server start button pressed. Running on thread: " + threading.current_thread().name)

    def run_server(self):
        if self.debug_mode:
            logging.debug("Running server thread")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.listen_ip, self.port))
        self.server_socket.listen(5)
        self.log_message(f"Server started on {self.listen_ip}:{self.port}. Waiting for connections...")
        if self.debug_mode:
            self.log_message(f"[DEBUG] Server listening on {self.listen_ip}:{self.port}. Running on thread: " + threading.current_thread().name)
        while self.is_running:
            try:
                client_socket, addr = self.server_socket.accept()
                if self.debug_mode:
                    self.log_message(f"[DEBUG] Accepted connection from {addr}. Running on thread: " + threading.current_thread().name)
                if self.is_running:
                    self.active_connections.append(client_socket)
                    threading.Thread(target=self.handle_client, args=(client_socket,)).start()
            except Exception as e:
                if self.is_running:
                    self.log_message(f"Exception: {str(e)}")
                if self.debug_mode:
                    self.log_message(f"[DEBUG] Exception in run_server: {str(e)}")
                break

    def handle_client(self, client_socket):
        if self.debug_mode:
            logging.debug("Handling client connection")
        try:
            while self.is_running:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break
                    self.log_message(f"Incoming message: {data}")
                    if self.debug_mode:
                        self.log_message(f"[DEBUG] Received data: {data}")
                    response = parse_command(data, self.delay_ms)
                    self.log_message(response)
                except socket.error as e:
                    self.log_message(f"Socket error during client handling: {str(e)}")
                    if self.debug_mode:
                        self.log_message(f"[DEBUG] Socket error: {str(e)}")
                    break
        finally:
            client_socket.close()
            self.active_connections.remove(client_socket)
            self.log_message("Client disconnected.")
            if self.debug_mode:
                self.log_message("[DEBUG] Client socket closed and removed from active connections")

    def disconnect(self, instance):
        if self.debug_mode:
            logging.debug("Disconnecting server")
        self.is_running = False
        for client_socket in self.active_connections:
            client_socket.close()
        self.active_connections.clear()
        if self.server_socket:
            self.server_socket.close()
        self.start_server_button.disabled = False
        self.disconnect_button.disabled = True
        self.log_message("Server disconnected.")
        if self.debug_mode:
            self.log_message("[DEBUG] Server disconnect button pressed and server socket closed")

    def quit_app(self, instance):
        if self.debug_mode:
            logging.debug("Quitting application")
        self.disconnect(instance)
        self.stop()
        logging.info("Application has been closed cleanly.")
        if self.debug_mode:
            logging.debug("[DEBUG] Application closed by user.")
        if self.tray_icon:
            self.tray_icon.stop()

    def log_message(self, message):
        def append_text(dt):
            current_text = self.output.text
            self.output.text = f"{current_text}{message}\n"
            logging.info(message)  # Print to console
        Clock.schedule_once(append_text)

    def show_window(self):
        if self.debug_mode:
            logging.debug("Showing window")
        Window.show()
        Window.raise_window()
        if self.debug_mode:
            self.log_message("[DEBUG] Window shown")

    def hide_window(self, *args):
        if self.debug_mode:
            logging.debug("Hiding window")
        Window.hide()
        if self.debug_mode:
            self.log_message("[DEBUG] Window hidden")
        return True  # Returning True prevents the window from being closed

    def redraw_ui(self, instance):
        logging.info("[INFO] Redrawing UI")
        if self.debug_mode:
            self.log_message("[DEBUG] Redrawing UI")
        # Refresh the UI by updating existing widgets
        self.update_text_alignment(self.ip_input)
        self.update_text_alignment(self.port_input)
        self.update_text_alignment(self.delay_input)
        if self.debug_mode:
            self.log_message("[DEBUG] UI redrawn")

    def post_build_init(self, dt):
        if self.debug_mode:
            logging.debug("Post build initialization")
        # This method is called after build to ensure UI is initialized
        self.load_config()
        self.log_message(STARTUP_MESSAGE)  # Display startup message

    def load_config(self, dt=None):
        if self.debug_mode:
            logging.debug("Loading configuration")
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            if CONFIG_FILE.exists():
                with CONFIG_FILE.open("r") as f:
                    config = json.load(f)
                self.listen_ip = config.get('ip_address', DEFAULT_IP_ADDRESS)
                self.port = config.get('port', DEFAULT_PORT)
                self.delay_ms = config.get('delay', DEFAULT_DELAY_MS)
                self.debug_mode = config.get('debug', DEFAULT_DEBUG_MODE)
                # Update UI elements with loaded config
                if hasattr(self, 'ip_input'):
                    self.ip_input.text = self.listen_ip
                if hasattr(self, 'port_input'):
                    self.port_input.text = str(self.port)
                if hasattr(self, 'delay_input'):
                    self.delay_input.text = str(self.delay_ms)
                if hasattr(self, 'debug_toggle'):
                    self.debug_toggle.state = 'down' if self.debug_mode else 'normal'
                    self.debug_toggle.text = "Debugging On" if self.debug_mode else "Debugging Off"
                    self.update_redraw_button_visibility()  # Update visibility based on loaded debug mode
                    self.update_vertical_spacing()  # Update spacing based on loaded debug mode
                logging.info(f"[INFO] Configuration loaded: {config}")
                if self.debug_mode:
                    self.log_message(f"[DEBUG] Configuration loaded: {config}")
            else:
                self.log_message("[INFO] No configuration file found, using defaults.")
                if self.debug_mode:
                    self.log_message("[DEBUG] No configuration file found, using defaults.")
        except Exception as e:
            logging.error(f"[ERROR] Failed to load configuration: {str(e)}")
            if self.debug_mode:
                self.log_message(f"[DEBUG] Failed to load configuration: {str(e)}")

    def save_config(self):
        if self.debug_mode:
            logging.debug("Saving configuration")
        try:
            config = {
                'ip_address': self.listen_ip,
                'port': self.port,
                'delay': self.delay_ms,
                'debug': self.debug_mode
            }
            with CONFIG_FILE.open("w") as f:
                json.dump(config, f, indent=4)
            logging.info(f"[INFO] Configuration saved: {config}")
            if self.debug_mode:
                self.log_message(f"[DEBUG] Configuration saved: {config}")
        except Exception as e:
            logging.error(f"[ERROR] Failed to save configuration: {str(e)}")
            if self.debug_mode:
                self.log_message(f"[DEBUG] Failed to save configuration: {str(e)}")

def quit_app(icon, item):
    logging.info("Quitting application from tray icon")
    app = App.get_running_app()
    if app:
        app.quit_app(None)

def show_window(icon, item):
    logging.info("Showing window from tray icon")
    app = App.get_running_app()
    if app:
        app.show_window()

def run_tray():
    logging.info("Starting tray icon")
    menu = (item('Show Window', show_window), item('Quit', quit_app))
    icon = pystray.Icon("VicreoListener", create_image(), "Vicreo Listener", menu)
    icon.run_detached()

if __name__ == "__main__":
    run_tray()  # Start pystray menu
    VicreoListenerApp().run()  # Run the Kivy application on the main thread
