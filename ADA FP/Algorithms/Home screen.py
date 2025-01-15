import pygame
import networkx as nx
import pandas as pd
import time as time_module
from pygame.locals import *
import random
import itertools


class DropDown:
    def __init__(self, rect, options, font):
        self.rect = rect
        self.options = ["None"] + options
        self.font = font
        self.active = False
        self.selected = "None"
        self.scroll_offset = 0
        self.visible_options = 5
        self.option_height = 30
        self.option_rects = []
        self._calculate_option_rects()

    def _calculate_option_rects(self):
        self.option_rects = []
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_options, len(self.options))
        
        for i in range(start_idx, end_idx):
            rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height + ((i - start_idx) * self.option_height),
                self.rect.width,
                self.option_height
            )
            self.option_rects.append(rect)

    def handle_scroll(self, event):
        if self.active and len(self.options) > self.visible_options:
            if event.button == 4:  
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:  
                self.scroll_offset = min(len(self.options) - self.visible_options, 
                                      self.scroll_offset + 1)
            self._calculate_option_rects()

    def draw(self, screen, colors):
        # Draw the main dropdown button
        pygame.draw.rect(screen, colors['blue'], self.rect)
        text = self.font.render(self.selected, True, colors['white'])
        screen.blit(text, (self.rect.x + 5, self.rect.y + 5))

        # Draw the dropdown list when active
        if self.active:
            # Draw background for dropdown area
            dropdown_height = min(len(self.options), self.visible_options) * self.option_height
            dropdown_bg = pygame.Rect(self.rect.x, self.rect.y + self.rect.height,
                                    self.rect.width, dropdown_height)
            pygame.draw.rect(screen, colors['blue'], dropdown_bg)
            
            # Draw options
            for i, rect in enumerate(self.option_rects):
                option_idx = i + self.scroll_offset
                if option_idx < len(self.options):
                    pygame.draw.rect(screen, colors['blue'], rect)
                    # Highlight on hover
                    mouse_pos = pygame.mouse.get_pos()
                    if rect.collidepoint(mouse_pos):
                        pygame.draw.rect(screen, (100, 100, 255), rect)  
                    
                    text = self.font.render(self.options[option_idx], True, colors['white'])
                    screen.blit(text, (rect.x + 5, rect.y + 5))
            
            # Draw scroll indicators if needed
            if len(self.options) > self.visible_options:
                if self.scroll_offset > 0:  # Up arrow
                    pygame.draw.polygon(screen, colors['white'],
                        [(self.rect.right - 20, self.rect.bottom + 10),
                         (self.rect.right - 10, self.rect.bottom + 20),
                         (self.rect.right - 30, self.rect.bottom + 20)])
                
                if self.scroll_offset < len(self.options) - self.visible_options:  
                    bottom_y = self.rect.bottom + dropdown_height
                    pygame.draw.polygon(screen, colors['white'],
                        [(self.rect.right - 20, bottom_y - 10),
                         (self.rect.right - 10, bottom_y - 20),
                         (self.rect.right - 30, bottom_y - 20)])

    def handle_click(self, pos):
        if self.active:
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(pos):
                    option_idx = i + self.scroll_offset
                    if option_idx < len(self.options):
                        self.selected = self.options[option_idx]
                        self.active = False
                        return True
            # Click outside the dropdown area
            dropdown_area = pygame.Rect(
                self.rect.x, 
                self.rect.y, 
                self.rect.width,
                self.rect.height + (len(self.option_rects) * self.option_height)
            )
            if not dropdown_area.collidepoint(pos):
                self.active = False
        elif self.rect.collidepoint(pos):
            self.active = not self.active
            self._calculate_option_rects()
            return True
        else:
            self.active = False
        return False


class FlightOptimizer:
    def __init__(self):
        pygame.init()
        # Reduced window size
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Flight Route Optimizer")
        self.font = pygame.font.Font(None, 28)  
        self.colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'blue': (0, 0, 255),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'gray': (128, 128, 128)
        }
        self.load_data()
        self.reset_state()

        # Adjusted positions for dropdowns
        self.route_closure_dropdown = DropDown(
            pygame.Rect(400, 100, 150, 30),
            [f"{a}-{b}" for a, b in self.G.edges()],
            self.font
        )
        self.airport_closure_dropdown = DropDown(
            pygame.Rect(600, 100, 150, 30),
            list(self.G.nodes()),
            self.font
        )

 
        self.positions = {
        "LCE": (100, 200),    
        "GCM": (700, 200),    
        "GJA": (100, 400),    
        "PEU": (300, 150),    
        "TGU": (500, 150),    
        "RTB": (550, 250),    
        "SAP": (300, 350),    
        "UII": (50, 500),    
        "CLT": (650, 500),    
        "MIA": (400, 500)     
    }



    def format_time(self, hours):
        if hours is None:
            return "N/A"
        total_minutes = int(hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"

    def load_data(self):
        df = pd.read_csv(r'C:\Users\samue\OneDrive\Desktop\ADA FP\Preprocessing and scrapping\routes and distances.csv')
        df['FlightTime_Hours'] = df.apply(lambda x: int(x['FlightTime'].split('h')[0]) +
                                          int(x['FlightTime'].split('h')[1].split('m')[0])/60, axis=1)
        self.airports = ['LCE', 'GCM', 'GJA', 'PEU', 'RTB', 'SAP', 'TGU', 'UII', 'CLT', 'MIA']

        filtered_df = df[df['SourceAirport'].isin(self.airports) &
                         df['DestinationAirport'].isin(self.airports)]

        self.G = nx.Graph()
        for _, row in filtered_df.iterrows():
            self.G.add_edge(row['SourceAirport'], row['DestinationAirport'],
                            weight=row['FlightTime_Hours'])
    def brute_force_route_optimization_with_delays(self, graph, start_airport, end_airport):
        min_flight_time = float('inf')
        best_route = None

        airports_to_permute = [airport for airport in self.airports 
                            if airport != start_airport and airport != end_airport]

        for num_intermediates in range(len(airports_to_permute) + 1):
            # Store permutations explicitly
            all_routes = list(itertools.permutations(airports_to_permute, num_intermediates))

            for route in all_routes:
                full_route = [start_airport] + list(route) + [end_airport]
                total_time = 0
                valid_route = True

                for i in range(len(full_route) - 1):
                    if graph.has_edge(full_route[i], full_route[i + 1]):
                        total_time += graph[full_route[i]][full_route[i + 1]]['weight']
                    else:
                        valid_route = False
                        break

                if valid_route and total_time < min_flight_time:
                    min_flight_time = total_time
                    best_route = full_route

        return best_route, min_flight_time


    def dijkstra_route_optimization_with_delays(self, graph, start_airport, end_airport):
        try:
            shortest_path = nx.dijkstra_path(graph, source=start_airport, 
                                           target=end_airport, weight='weight')
            total_flight_time = nx.dijkstra_path_length(graph, source=start_airport, 
                                                      target=end_airport, weight='weight')
            return shortest_path, total_flight_time
        except nx.NetworkXNoPath:
            return None, None


    def reset_state(self):
        self.state = 'algorithm_select'
        self.algorithm = None
        self.start_airport = None
        self.end_airport = None
        self.enable_delays = False
        self.airport_closure = None
        self.route_closure = None

        if hasattr(self, 'route_closure_dropdown'):
            self.route_closure_dropdown.selected = "None"
            self.route_closure_dropdown.active = False
        if hasattr(self, 'airport_closure_dropdown'):
            self.airport_closure_dropdown.selected = "None"
            self.airport_closure_dropdown.active = False

    def draw_algorithm_select(self):
        self.screen.fill(self.colors['white'])
        buttons = {}

        # Main title
        main_title = self.font.render("Plane Route Optimizer", True, self.colors['black'])
        main_title_x = (self.width - main_title.get_width()) // 2
        main_title_y = 50
        self.screen.blit(main_title, (main_title_x, main_title_y))

        # Subtitle 
        subtitle = self.font.render("Select Algorithm", True, self.colors['black'])
        subtitle_x = (self.width - subtitle.get_width()) // 2
        subtitle_y = main_title_y + 150  
        self.screen.blit(subtitle, (subtitle_x, subtitle_y))

        # Make buttons wider and taller
        button_width = 300
        button_height = 80
        button_spacing = 40  
        
        # Calculate center positions for buttons to be side by side
        total_width = (button_width * 2) + button_spacing
        start_x = (self.width - total_width) // 2
        start_y = subtitle_y + 100  

        # Dijkstra button
        dijkstra_rect = pygame.Rect(start_x, start_y, button_width, button_height)
        pygame.draw.rect(self.screen, self.colors['blue'], dijkstra_rect)
        
        text = self.font.render("Greedy Algorithm", True, self.colors['white'])
        text_x = dijkstra_rect.x + (button_width - text.get_width()) // 2
        text_y = dijkstra_rect.y + (button_height - text.get_height()) // 2
        self.screen.blit(text, (text_x, text_y))

        # Brute Force button
        brute_force_rect = pygame.Rect(start_x + button_width + button_spacing, start_y, 
                                    button_width, button_height)
        pygame.draw.rect(self.screen, self.colors['blue'], brute_force_rect)
        
        text = self.font.render("Brute Force", True, self.colors['white'])
        text_x = brute_force_rect.x + (button_width - text.get_width()) // 2
        text_y = brute_force_rect.y + (button_height - text.get_height()) // 2
        self.screen.blit(text, (text_x, text_y))

        buttons['dijkstra'] = dijkstra_rect
        buttons['brute_force'] = brute_force_rect

        return buttons

    def draw_route_select(self):
        self.screen.fill(self.colors['white'])
        buttons = {}

        # Title
        title = self.font.render("Select Airports and Options", True, self.colors['black'])
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 10))

        # Error message for invalid airport closure
        if (self.airport_closure_dropdown.selected == self.start_airport or 
            self.airport_closure_dropdown.selected == self.end_airport):
            error_msg = self.font.render("Cannot close selected start/end airport!", True, self.colors['red'])
            self.screen.blit(error_msg, (self.width // 2 - error_msg.get_width() // 2, 40))
            # Reset the dropdown selection
            self.airport_closure_dropdown.selected = "None"

        # Airport selection area
        airports_label = self.font.render("Airports:", True, self.colors['black'])
        self.screen.blit(airports_label, (30, 70))

        # Create a more compact grid layout for airports
        y = 100
        x = 30
        button_width = 80
        button_height = 30
        airports_per_column = 5

        for i, airport in enumerate(self.airports):
            column = i // airports_per_column
            row = i % airports_per_column
            
            rect = pygame.Rect(x + (column * (button_width + 10)), 
                            y + (row * (button_height + 5)), 
                            button_width, button_height)
            
            color = self.colors['blue']
            if airport == self.start_airport:
                color = self.colors['green']
            elif airport == self.end_airport:
                color = self.colors['red']
            
            pygame.draw.rect(self.screen, color, rect)
            text = self.font.render(airport, True, self.colors['white'])
            self.screen.blit(text, (rect.x + 5, rect.y + 5))
            
            buttons[f'airport_{airport}'] = rect

        # Draw dropdowns
        self.route_closure_dropdown.draw(self.screen, self.colors)
        route_closure_text = self.font.render("Route Closure:", True, self.colors['black'])
        self.screen.blit(route_closure_text, (self.route_closure_dropdown.rect.x, 
                                            self.route_closure_dropdown.rect.y - 25))

        self.airport_closure_dropdown.draw(self.screen, self.colors)
        airport_closure_text = self.font.render("Airport Closure:", True, self.colors['black'])
        self.screen.blit(airport_closure_text, (self.airport_closure_dropdown.rect.x, 
                                            self.airport_closure_dropdown.rect.y - 25))

        # Control buttons at the bottom
        delay_rect = pygame.Rect(self.width//2 - 160, self.height - 50, 150, 35)
        color = self.colors['green'] if self.enable_delays else self.colors['blue']
        pygame.draw.rect(self.screen, color, delay_rect)
        text = self.font.render("Toggle Delays", True, self.colors['white'])
        self.screen.blit(text, (delay_rect.x + 5, delay_rect.y + 5))
        buttons['delay'] = delay_rect

        # Only enable simulate button if both airports are selected
        simulate_rect = pygame.Rect(self.width//2 + 10, self.height - 50, 150, 35)
        simulate_color = self.colors['blue'] if self.start_airport and self.end_airport else self.colors['gray']
        pygame.draw.rect(self.screen, simulate_color, simulate_rect)
        text = self.font.render("Simulate", True, self.colors['white'])
        self.screen.blit(text, (simulate_rect.x + 5, simulate_rect.y + 5))
        buttons['simulate'] = simulate_rect

        return buttons




    def draw_simulation(self):
        import tracemalloc
        import gc  # For garbage collection
        
        self.screen.fill(self.colors['white'])
        buttons = {}

        # Draw main menu button
        main_menu_rect = pygame.Rect(10, 10, 150, 40)
        pygame.draw.rect(self.screen, self.colors['red'], main_menu_rect)
        main_menu_text = self.font.render("Main Menu", True, self.colors['white'])
        self.screen.blit(main_menu_text, (main_menu_rect.x + 5, main_menu_rect.y + 5))
        buttons['main_menu'] = main_menu_rect

        adjusted_graph = self.G.copy()

        # Remove selected closed airport and routes
        if self.airport_closure_dropdown.selected != "None":
            if self.airport_closure_dropdown.selected in adjusted_graph:
                adjusted_graph.remove_node(self.airport_closure_dropdown.selected)

        if self.route_closure_dropdown.selected != "None":
            airports = self.route_closure_dropdown.selected.split("-")
            if adjusted_graph.has_edge(*airports):
                adjusted_graph.remove_edge(*airports)

        # Apply random delays if enabled
        if self.enable_delays:
            for u, v in adjusted_graph.edges():
                delay_factor = random.uniform(1.0, 1.5)
                adjusted_graph[u][v]['weight'] *= delay_factor

        try:
            # Clear memory before starting
            gc.collect()
            tracemalloc.start()
            
            start_time = time_module.time()
            
            if self.algorithm == 'dijkstra':
                path, flight_time = self.dijkstra_route_optimization_with_delays(
                    adjusted_graph, self.start_airport, self.end_airport)
            elif self.algorithm == 'brute_force':
                path, flight_time = self.brute_force_route_optimization_with_delays(
                    adjusted_graph, self.start_airport, self.end_airport)

            # Get memory usage
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Convert to MB
            memory_mb = peak / 1024 / 1024

            total_algorithm_time = time_module.time() - start_time
            total_algorithm_time_ms = total_algorithm_time * 1000

            if path is None or flight_time is None:
                raise nx.NetworkXNoPath()

            # Pre-render text
            delay_text = " (including delays)" if self.enable_delays else ""
            flight_time_text = f"Flight time: {self.format_time(flight_time)}{delay_text}"
            algorithm_time_text = f"Algorithm time: {total_algorithm_time_ms:.2f} ms"
            path_text = f"Optimal Path: {' -> '.join(path)}"
            memory_text = f"Memory Usage: {memory_mb:.2f} MB"
           

            text1 = self.font.render(flight_time_text, True, self.colors['black'])
            text2 = self.font.render(algorithm_time_text, True, self.colors['black'])
            text3 = self.font.render(path_text, True, self.colors['black'])
            text4 = self.font.render(memory_text, True, self.colors['black'])

            text1 = self.font.render(flight_time_text, True, self.colors['black'])
            text2 = self.font.render(algorithm_time_text, True, self.colors['black'])
            text3 = self.font.render(path_text, True, self.colors['black'])
            text4 = self.font.render(memory_text, True, self.colors['black'])
          

            # Load and scale plane image
            plane_image = pygame.image.load(r"C:\Users\samue\OneDrive\Desktop\ADA FP\vecteezy_flying-airplane-isolated-on-background-3d-rendering_37277866.png")
            scale_factor = 0.02
            new_width = int(plane_image.get_width() * scale_factor)
            new_height = int(plane_image.get_height() * scale_factor)
            plane_image = pygame.transform.scale(plane_image, (new_width, new_height))

            # Function to redraw the base visualization
            def redraw_base():
                self.screen.fill(self.colors['white'])
                pygame.draw.rect(self.screen, self.colors['red'], main_menu_rect)
                self.screen.blit(main_menu_text, (main_menu_rect.x + 5, main_menu_rect.y + 5))
                
                # Draw edges
                for (u, v) in adjusted_graph.edges():
                    start_pos = self.positions[u]
                    end_pos = self.positions[v]
                    pygame.draw.line(self.screen, self.colors['gray'], start_pos, end_pos, 2)
                    
                    # Calculate label position
                    mid_x = (start_pos[0] + end_pos[0]) // 2
                    mid_y = (start_pos[1] + end_pos[1]) // 2
                    edge_time = adjusted_graph[u][v]['weight']
                    time_text = self.font.render(self.format_time(edge_time), True, self.colors['black'])
                    
                    offset = 10
                    if abs(end_pos[1] - start_pos[1]) < 100:
                        mid_y += offset
                    
                    self.screen.blit(time_text, (mid_x - time_text.get_width()//2, 
                                            mid_y - time_text.get_height()//2))

                # Draw the optimal path in red
                for i in range(len(path) - 1):
                    u = path[i]
                    v = path[i + 1]
                    start_pos = self.positions[u]
                    end_pos = self.positions[v]
                    pygame.draw.line(self.screen, self.colors['red'], start_pos, end_pos, 2)

                # Draw nodes
                for node in adjusted_graph.nodes():
                    node_color = self.colors['blue']
                    if node in path:
                        node_color = self.colors['green']
                    if node == self.airport_closure_dropdown.selected:
                        node_color = self.colors['red']
                        
                    pygame.draw.circle(self.screen, node_color, self.positions[node], 15)
                    text = self.font.render(node, True, self.colors['black'])
                    self.screen.blit(text, (self.positions[node][0] - 20, self.positions[node][1] - 30))

                # Draw stats
                self.screen.blit(text1, (self.width // 2 - text1.get_width() // 2, 10))
                self.screen.blit(text2, (self.width // 2 - text2.get_width() // 2, 40))
                self.screen.blit(text3, (self.width // 2 - text3.get_width() // 2, 70))
                self.screen.blit(text4, (self.width // 2 - text4.get_width() // 2, 100))
              

            # Start animation
            plane_pos = self.positions[path[0]]
            for i in range(1, len(path)):
                next_pos = self.positions[path[i]]
                steps = 30
                
                for step in range(steps):
                    redraw_base()
                    
                    # Calculate current position
                    current_x = plane_pos[0] + (next_pos[0] - plane_pos[0]) * step / steps
                    current_y = plane_pos[1] + (next_pos[1] - plane_pos[1]) * step / steps
                    
                    # Draw plane
                    plane_rect = plane_image.get_rect(center=(int(current_x), int(current_y)))
                    self.screen.blit(plane_image, plane_rect.topleft)
                    
                    pygame.display.flip()
                    pygame.time.delay(50)
                
                plane_pos = next_pos

        except (nx.NetworkXNoPath):
            # Draw only error message without background graph
            self.screen.fill(self.colors['white'])
            
            # Redraw main menu button
            pygame.draw.rect(self.screen, self.colors['red'], main_menu_rect)
            self.screen.blit(main_menu_text, (main_menu_rect.x + 5, main_menu_rect.y + 5))
            
            error_text1 = self.font.render("No valid path available!", True, self.colors['red'])
            error_text2 = self.font.render("Please check:", True, self.colors['black'])
            error_text3 = self.font.render("- Airport closures", True, self.colors['black'])
            error_text4 = self.font.render("- Route closures", True, self.colors['black'])
            error_text5 = self.font.render("- Start/End airport selection", True, self.colors['black'])
            
            # Position error messages
            y_start = 150
            spacing = 30
            self.screen.blit(error_text1, (self.width // 2 - error_text1.get_width() // 2, y_start))
            self.screen.blit(error_text2, (self.width // 2 - error_text2.get_width() // 2, y_start + spacing))
            self.screen.blit(error_text3, (self.width // 2 - error_text3.get_width() // 2, y_start + spacing * 2))
            self.screen.blit(error_text4, (self.width // 2 - error_text4.get_width() // 2, y_start + spacing * 3))
            self.screen.blit(error_text5, (self.width // 2 - error_text5.get_width() // 2, y_start + spacing * 4))

        return buttons


    def handle_click(self, pos, buttons):
        if self.state == 'route_select':
            if self.route_closure_dropdown.handle_click(pos):
                return
            if self.airport_closure_dropdown.handle_click(pos):
                return

        for key, rect in buttons.items():
            if rect.collidepoint(pos):
                if self.state == 'algorithm_select':
                    self.algorithm = key
                    self.state = 'route_select'
                elif self.state == 'route_select':
                    if 'airport_' in key:
                        airport = key.split('_')[1]
                        if not self.start_airport:
                            self.start_airport = airport
                        elif not self.end_airport and airport != self.start_airport:
                            self.end_airport = airport
                    elif key == 'delay':
                        self.enable_delays = not self.enable_delays
                    elif key == 'simulate' and self.start_airport and self.end_airport:
                        self.state = 'simulation'
                elif self.state == 'simulation':
                    if key == 'main_menu':
                        self.reset_state()
                        self.state = 'algorithm_select' 
    

    def run(self):
        running = True
        while running:
            if self.state == 'algorithm_select':
                buttons = self.draw_algorithm_select()
            elif self.state == 'route_select':
                buttons = self.draw_route_select()
            elif self.state == 'simulation':
                buttons = self.draw_simulation()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    # Handle scrolling for dropdowns
                    if event.button in (4, 5):  
                        self.route_closure_dropdown.handle_scroll(event)
                        self.airport_closure_dropdown.handle_scroll(event)
                    else:
                        self.handle_click(pos, buttons)

            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    optimizer = FlightOptimizer()
    optimizer.run()
