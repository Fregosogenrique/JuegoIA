    def calculate_path(self):
        # Busco el mejor camino usando A* y RandomRoute
        try:
            start = self.game_state.player_pos
            goal = self.game_state.house_pos
            obstacles = self.game_state.obstacles

            # Obtener las iteraciones visibles e invisibles de la interfaz
            self.visible_iterations = self.renderer.get_visible_iterations()
            self.invisible_iterations = self.renderer.get_invisible_iterations()
            
            # Ejecutar siempre el A* para tener un punto de referencia
            self.astar_path = self.astar.find_path(start, goal, obstacles)
            
            # Usar el método apropiado para RandomRoute según el modo seleccionado
            if self.selected_path == 'random' or self.random_route_learning:
                self.random_route_learning = True
                
                # Primero ejecutar las iteraciones invisibles (sin actualizar la interfaz)
                if self.invisible_iterations > 0:
                    print(f"Ejecutando {self.invisible_iterations} iteraciones invisibles...")
                    self.is_learning_in_progress = True
                    # Las iteraciones invisibles solo actualizan la matriz de aprendizaje
                    self.ucs.find_path_with_learning(start, goal, obstacles, iterations=self.invisible_iterations)
                    self.is_learning_in_progress = False
                
                # Luego ejecutar las iteraciones visibles
                if self.visible_iterations > 0:
                    print(f"Ejecutando {self.visible_iterations} iteraciones visibles...")
                    self.ucs_path = self.ucs.find_path_with_learning(start, goal, obstacles, iterations=self.visible_iterations)
                else:
                    # Si no hay iteraciones visibles, solo ejecutar una vez para obtener el camino
                    self.ucs_path = self.ucs.find_path_with_learning(start, goal, obstacles, iterations=1)
            else:
                # Modo normal (sin aprendizaje)
                self.ucs_path = self.ucs.find_path(start, goal, obstacles)

            if not self.astar_path and not self.ucs_path:
                self.game_state.no_path_error = True
                self.game_state.error_timer = 0
                self.game_state.game_started = False
                self.is_running = False
                return False

            # Aseguramos que los costos sean enteros
            self.astar_cost = self.calculate_path_cost(self.astar_path)
            self.ucs_cost = self.calculate_path_cost(self.ucs_path)
            
            if self.selected_path == 'astar':
                self.current_path = self.astar_path
            else:
                self.current_path = self.ucs_path
            self.path_index = 1 if self.current_path else 0
            return True
        except Exception as e:
            print(f"Error al calcular las rutas: {e}")
            return False
    def visualize_movement_matrix(self):
        """Visualiza la matriz de movimientos de RandomRoute usando el método interno de la clase"""
        try:
            # Use the plot_analysis method from RandomRoute class for comprehensive visualization
            if hasattr(self.ucs, 'plot_analysis'):
                # Mostrar un análisis completo que incluye:
                # - Mapa de calor de movimientos
                # - Matriz de aprendizaje
                # - Estadísticas comparativas
                self.ucs.plot_analysis(save_fig
    def run(self):
        """Bucle principal del juego"""
        running = True
        while running:
            try:
                # No actualizar la pantalla durante el aprendizaje invisible
                if not self.is_learning_in_progress:
                    if self.game_state.victory:
                        self._handle_victory_state()
                    elif self.game_state.no_path_error:
                        self._handle_no_path_error()
                    else:
                        self.renderer.screen.fill(GameConfig.BLACK)
                        self._update_display()

                running = self._process_events()
                pygame.time.delay(GameConfig.GAME_SPEED)
            except Exception as e:
                print(f"Error en el bucle principal: {e}")
                running = False
    def _process_events(self):
        """Procesa todos los eventos del juego"""
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif not self.game_state.victory and event.type == pygame.MOUSEBUTTONDOWN:
                    if event.pos[0] < GameConfig.GRID_WIDTH * GameConfig.SQUARE_SIZE:
                        self._handle_grid_click(event.pos[0], event.pos[1], event.button)
                    else:
                        self._handle_sidebar_click(event.pos[0], event.pos[1])
                elif not self.game_state.victory and event.type == pygame.KEYDOWN:
                    self.handle_keyboard(event.key)
                
                # Procesar eventos de los campos de texto
                self.renderer.handle_input_event(event)

            # No procesar movimientos durante el aprendizaje invisible
            if not self.is_learning_in_progress and not self.game_state.victory and self.game_state.game_started and \
                    self.current_path and self.is_running:
                self.update_player_movement()

            return True
        except Exception as e:
            print(f"Error en el procesamiento de eventos: {e}")
            return False
