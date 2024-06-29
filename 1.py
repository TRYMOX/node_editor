import pygame
import pygame.freetype
import pygame_gui
import json

# Initialize Pygame and Pygame GUI
pygame.init()

# Constants
WIDTH, HEIGHT = 1200, 800
BG_COLOR = (30, 30, 30)
NODE_COLOR = (50, 50, 50)
NODE_BORDER_COLOR = (200, 200, 200)
NODE_TEXT_COLOR = (255, 255, 255)
SOCKET_COLOR = (0, 200, 255)
LINE_COLOR = (0, 255, 255)
SOCKET_RADIUS = 8
FONT_SIZE = 9  # Smaller font size

# Set up the screen and UI manager
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Draggable Nodes with Connections")
ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT))

# Load the font
font = pygame.freetype.SysFont(None, FONT_SIZE)

# Helper function to render text
def render_text(text, pos, color=NODE_TEXT_COLOR):
    font.render_to(screen, pos, text, color)

class Socket:
    def __init__(self, node, is_input, index=0):
        self.node = node
        self.is_input = is_input
        self.index = index
        self.connected = False
        self.connection = None  # Store the connection reference
        self.update_position()

    def update_position(self):
        if self.is_input:
            self.x = self.node.rect.left - SOCKET_RADIUS * 2
        else:
            self.x = self.node.rect.right + SOCKET_RADIUS * 2
        self.y = self.node.rect.top + 20 + self.index * 30

    def draw(self, screen):
        color = SOCKET_COLOR if not self.connected else LINE_COLOR
        pygame.draw.circle(screen, color, (self.x, self.y), SOCKET_RADIUS)

class Node:
    def __init__(self, x, y, width, height, text, input_labels, output_labels):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.input_labels = input_labels
        self.output_labels = output_labels
        self.input_sockets = [Socket(self, True, i) for i in range(len(input_labels))]
        self.output_sockets = [Socket(self, False, i) for i in range(len(output_labels))]
        self.result = None

    def draw(self, screen):
        pygame.draw.rect(screen, NODE_COLOR, self.rect, border_radius=5)
        pygame.draw.rect(screen, NODE_BORDER_COLOR, self.rect, 2, border_radius=5)
        render_text(self.text, (self.rect.x + 10, self.rect.y + 5))
        for i, label in enumerate(self.input_labels):
            render_text(label, (self.rect.x + 5, self.rect.y + 20 + i * 30))
        for i, label in enumerate(self.output_labels):
            render_text(label, (self.rect.x + self.rect.width - 50, self.rect.y + 20 + i * 30))
        for socket in self.input_sockets + self.output_sockets:
            socket.draw(screen)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right mouse button
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.offset_x = self.rect.x - event.pos[0]
                self.offset_y = self.rect.y - event.pos[1]
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:  # Right mouse button
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.rect.x = event.pos[0] + self.offset_x
                self.rect.y = event.pos[1] + self.offset_y
                for socket in self.input_sockets + self.output_sockets:
                    socket.update_position()

    def get_socket_at_pos(self, pos):
        for socket in self.input_sockets + self.output_sockets:
            if ((socket.x - pos[0]) ** 2 + (socket.y - pos[1]) ** 2) ** 0.5 < SOCKET_RADIUS:
                return socket
        return None

    def compute(self):
        pass

    def propagate(self):
        for socket in self.output_sockets:
            if socket.connected:
                connected_node = socket.connection.node
                connected_node.compute()
                connected_node.propagate()

class InputNode(Node):
    def __init__(self, x, y, width, height, text):
        super().__init__(x, y, width, height, text, [], ["Number"])
        self.value = "0"
        self.value_type = "int"
        self.result = int(self.value)
        self.input_field = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(x + 10, y + 40, width - 20, 30),
            manager=ui_manager
        )
        self.input_field.set_text(self.value)
        self.type_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=["int", "float", "complex", "str", "bool"],
            starting_option="int",
            relative_rect=pygame.Rect(x + 10, y + 80, width - 20, 30),
            manager=ui_manager
        )
        self.bool_checkbox = pygame_gui.elements.UISelectionList(
            relative_rect=pygame.Rect(x + 10, y + 40, width - 20, 60),
            item_list=["True", "False"],
            manager=ui_manager
        )
        self.bool_checkbox.hide()

    def draw(self, screen):
        super().draw(screen)
        self.input_field.set_position((self.rect.x + 10, self.rect.y + 40))
        self.type_dropdown.set_position((self.rect.x + 10, self.rect.y + 80))
        self.bool_checkbox.set_position((self.rect.x + 10, self.rect.y + 40))

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.input_field:
                self.value = event.text
                self.compute()
                self.propagate()
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.type_dropdown:
                self.value_type = event.text
                self.update_input_type()
                self.compute()
                self.propagate()
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.bool_checkbox:
                self.value = event.text
                self.compute()
                self.propagate()

    def update_input_type(self):
        if self.value_type == "bool":
            self.input_field.hide()
            self.bool_checkbox.show()
        else:
            self.input_field.show()
            self.bool_checkbox.hide()

    def compute(self):
        try:
            if self.value_type == "int":
                self.result = int(self.value)
            elif self.value_type == "float":
                self.result = float(self.value)
            elif self.value_type == "complex":
                self.result = complex(self.value)
            elif self.value_type == "str":
                self.result = str(self.value)
            elif self.value_type == "bool":
                self.result = self.value == "True"
        except ValueError:
            self.result = None

    def update(self, time_delta):
        self.input_field.update(time_delta)
        self.type_dropdown.update(time_delta)
        self.bool_checkbox.update(time_delta)

class OperationNode(Node):
    def __init__(self, x, y, width, height, text, operation):
        super().__init__(x, y, width, height, text, ["Number", "Number"], ["Number"])
        self.operation = operation
        self.operation_dropdown = pygame_gui.elements.UIDropDownMenu(
            options_list=["add", "sub", "mul", "div"],
            starting_option=operation,
            relative_rect=pygame.Rect(x + 10, y + 40, width - 20, 30),
            manager=ui_manager
        )

    def draw(self, screen):
        super().draw(screen)
        self.operation_dropdown.set_position((self.rect.x + 10, self.rect.y + 40))

    def compute(self):
        try:
            input_values = []
            for socket in self.input_sockets:
                if socket.connected:
                    input_node = socket.connection.node
                    if input_node.result is not None:
                        input_values.append(input_node.result)
            if len(input_values) == 2:
                operation = self.operation_dropdown.selected_option
                if operation == "add":
                    self.result = input_values[0] + input_values[1]
                elif operation == "sub":
                    self.result = input_values[0] - input_values[1]
                elif operation == "mul":
                    self.result = input_values[0] * input_values[1]
                elif operation == "div":
                    self.result = input_values[0] / input_values[1] if input_values[1] != 0 else "Error: Div by 0"
        except Exception as e:
            self.result = None

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.operation_dropdown:
                self.operation = self.operation_dropdown.selected_option
                self.compute()
                self.propagate()

class PrintNode(Node):
    def __init__(self, x, y, width, height, text):
        super().__init__(x, y, width, height, text, ["Number"], [])

    def compute(self):
        for socket in self.input_sockets:
            if socket.connected:
                input_node = socket.connection.node
                self.result = input_node.result if input_node.result is not None else "None"

    def handle_event(self, event):
        super().handle_event(event)
        self.compute()

    def draw(self, screen):
        super().draw(screen)
        if self.result is not None:
            render_text(f"Print: {self.result}", (self.rect.x + 10, self.rect.y + self.rect.height - 30))

class ListNode(Node):
    def __init__(self, x, y, width, height, text):
        super().__init__(x, y, width, height, text, [], ["List"])
        self.list_data = []
        self.edit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x + 10, y + 40, width - 20, 30),
            text="Edit List",
            manager=ui_manager
        )

    def draw(self, screen):
        super().draw(screen)
        self.edit_button.set_position((self.rect.x + 10, self.rect.y + 40))

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.edit_button:
                self.open_list_editor()

    def open_list_editor(self):
        list_editor = ListEditor(self)

class ListEditor:
    def __init__(self, list_node):
        self.list_node = list_node
        self.window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect((400, 200), (400, 400)),
            manager=ui_manager,
            window_display_title="List Editor",
            object_id="#list_editor"
        )
        self.list_entry = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect((20, 20), (360, 30)),
            manager=ui_manager,
            container=self.window
        )
        self.add_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((20, 60), (100, 30)),
            text="Add",
            manager=ui_manager,
            container=self.window
        )
        self.list_display = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect((20, 100), (360, 260)),
            html_text=self.format_list(),
            manager=ui_manager,
            container=self.window
        )
        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((140, 360), (120, 30)),
            text="Save",
            manager=ui_manager,
            container=self.window
        )
        self.list_data = list(self.list_node.list_data)

    def format_list(self):
        return "<br>".join(json.dumps(item) for item in self.list_data)

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.add_button:
                self.add_item()
            elif event.ui_element == self.save_button:
                self.save_list()

    def add_item(self):
        item = self.list_entry.get_text()
        if item:
            self.list_data.append(item)
            self.list_entry.set_text("")
            self.list_display.set_text(self.format_list())

    def save_list(self):
        self.list_node.list_data = self.list_data
        self.window.kill()

# Create nodes
nodes = []

# Store connections
connections = []

def remove_connection(socket):
    global connections
    new_connections = []
    for start, end in connections:
        if start == socket or end == socket:
            start.connected = False
            start.connection = None
            end.connected = False
            end.connection = None
        else:
            new_connections.append((start, end))
    connections = new_connections

# Function to add nodes
def add_node(node_type):
    if node_type == "Input":
        nodes.append(InputNode(100, 100, 200, 180, f"Input {len(nodes) + 1}"))
    elif node_type == "Operation":
        nodes.append(OperationNode(300, 100, 160, 100, f"Operation {len(nodes) + 1}", "add"))
    elif node_type == "Print":
        nodes.append(PrintNode(500, 100, 200, 80, f"Print {len(nodes) + 1}"))
    elif node_type == "List":
        nodes.append(ListNode(100, 400, 200, 80, f"List {len(nodes) + 1}"))

# Create buttons to add nodes
input_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((10, 10), (100, 50)),
    text='Add Input',
    manager=ui_manager
)

operation_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((120, 10), (100, 50)),
    text='Add Operation',
    manager=ui_manager
)

print_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((230, 10), (100, 50)),
    text='Add Print',
    manager=ui_manager
)

list_button = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((340, 10), (100, 50)),
    text='Add List',
    manager=ui_manager
)

# Main loop
running = True
selected_socket = None
current_mouse_pos = (0, 0)
clock = pygame.time.Clock()

while running:
    time_delta = clock.tick(60) / 1000.0
    screen.fill(BG_COLOR)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        ui_manager.process_events(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == input_button:
                add_node("Input")
            elif event.ui_element == operation_button:
                add_node("Operation")
            elif event.ui_element == print_button:
                add_node("Print")
            elif event.ui_element == list_button:
                add_node("List")
        for node in nodes:
            node.handle_event(event)
        for node in nodes:
            if isinstance(node, ListNode):
                node.edit_button.update(time_delta)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                for node in nodes:
                    socket = node.get_socket_at_pos(event.pos)
                    if socket:
                        if socket.connected:
                            # Remove the existing connection
                            remove_connection(socket.connection if socket.is_input else socket)
                        selected_socket = socket
                        break
            elif event.button == 3:  # Right mouse button
                for node in nodes:
                    if node.rect.collidepoint(event.pos):
                        node.handle_event(event)
                        break
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and selected_socket:  # Left mouse button
                for node in nodes:
                    socket = node.get_socket_at_pos(event.pos)
                    if socket and not socket.connected and (selected_socket.is_input != socket.is_input):
                        connections.append((selected_socket, socket))
                        selected_socket.connected = True
                        selected_socket.connection = socket
                        socket.connected = True
                        socket.connection = selected_socket
                        break
                selected_socket = None
            elif event.button == 3:  # Right mouse button
                for node in nodes:
                    node.handle_event(event)
        elif event.type == pygame.MOUSEMOTION:
            current_mouse_pos = event.pos
            for node in nodes:
                node.handle_event(event)

    # Draw connections
    for start_socket, end_socket in connections:
        pygame.draw.line(screen, LINE_COLOR, (start_socket.x, start_socket.y), (end_socket.x, end_socket.y), 2)

    # Draw current connection being dragged
    if selected_socket:
        pygame.draw.line(screen, LINE_COLOR, (selected_socket.x, selected_socket.y), current_mouse_pos, 2)

    # Draw nodes
    for node in nodes:
        node.draw(screen)
        if isinstance(node, InputNode):
            node.update(time_delta)
        node.compute()

    # Update the UI manager
    ui_manager.update(time_delta)
    ui_manager.draw_ui(screen)

    pygame.display.flip()

pygame.quit()
