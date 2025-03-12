import numpy as np
import random
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import math
class RandomRoute:
    def __init__(self, width=40, height=30):
        # Inicialización con dimensiones configurables
        self.width = width
        self.height = height
        
        # Tabla Q para Q-learning [y, x, acción]
        self.q_table = np.zeros((height, width, 4), dtype=float)
        
        # Matriz de visitas para seguimiento
        self.visit_count = np.zeros((height, width), dtype=int)
        
        # Parámetros de Q-learning
        self.learning_rate = 0.1  # Alpha: tasa de aprendizaje
        self.discount_factor = 0.9  # Gamma: factor de descuento
        self.epsilon = 0.3  # Epsilon: probabilidad de exploración
        self.epsilon_decay = 0.995  # Tasa de decaimiento de epsilon
        self.epsilon_min = 0.01  # Valor mínimo de epsilon
        
        # Mapeo de direcciones a índices
        self.dir_indices = {
            (-1, 0): 0,  # arriba
            (0, 1): 1,   # derecha
            (1, 0): 2,   # abajo
            (0, -1): 3   # izquierda
        }
        
        # Direcciones de movimiento
        self.directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        self.direction_names = ["arriba", "derecha", "abajo", "izquierda"]
        
        # Almacenar el mejor camino encontrado
        self.best_path = None
        self.best_path_length = float('inf')
        self.best_reward = float('-inf')
        
        # Historial de entrenamiento
        self.training_history = {
            'path_lengths': [],
            'rewards': [],
            'epsilons': []
        }
        
        # Variables para entrenamiento en background
        self.training_thread = None
        self.stop_training = False
        self.training_iterations = 0
        self.max_training_iterations = 1000
    def calculate_reward(self, current, goal, steps_taken=1):
        """
        Calcula la recompensa para una acción basada en la distancia a la meta y otros factores
        
        Args:
            current: Posición actual (x, y)
            goal: Posición de la meta (x, y)
            steps_taken: Número de pasos dados hasta ahora
            
        Returns:
            Un valor de recompensa
        """
        # Recompensa base: negativa para motivar encontrar caminos cortos
        base_reward = -0.1
        
        # Calcular distancia Manhattan actual a la meta
        current_distance = abs(current[0] - goal[0]) + abs(current[1] - goal[1])
        
        # Si llegamos a la meta, dar una recompensa grande
        if current == goal:
            return 10.0
            
        # Recompensa inversa a la distancia (más cerca = mejor recompensa)
        proximity_reward = 1.0 / (current_distance + 1)
        
        # Penalización por caminos largos
        step_penalty = -0.01 * steps_taken
        
        # Combinar las recompensas
        total_reward = base_reward + proximity_reward + step_penalty
        
        return total_reward
        
    def choose_action(self, state, valid_moves, obstacles, goal, is_training=True):
        """
        Implementa la política epsilon-greedy para elegir una acción
        
        Args:
            state: Estado actual (x, y)
            valid_moves: Lista de movimientos válidos [(dir, new_pos), ...]
            obstacles: Conjunto de obstáculos
            goal: Posición de la meta
            is_training: Si estamos en modo entrenamiento (True) o inferencia (False)
            
        Returns:
            El movimiento elegido (dir, new_pos)
        """
        x, y = state
        
        # Si no hay movimientos válidos, retornar None
        if not valid_moves:
            return None
            
        # Exploración: elegir una acción aleatoria con probabilidad epsilon
        if is_training and random.random() < self.epsilon:
            return random.choice(valid_moves)
            
        # Explotación: elegir la acción con el mayor valor Q
        q_values = []
        for dir_move, new_pos in valid_moves:
            dir_idx = self.dir_indices[dir_move]
            q_value = self.q_table[y][x][dir_idx]
            q_values.append((q_value, (dir_move, new_pos)))
            
        # Ordenar por valor Q descendente
        q_values.sort(reverse=True, key=lambda x: x[0])
        
        # Si todos los valores Q son iguales (0), elegir basado en la heurística de distancia
        if all(q == 0 for q, _ in q_values):
            # Elegir basado en la menor distancia Manhattan a la meta
            distances = []
            for _, (dir_move, new_pos) in q_values:
                dist = abs(new_pos[0] - goal[0]) + abs(new_pos[1] - goal[1])
                distances.append((dist, (dir_move, new_pos)))
            distances.sort(key=lambda x: x[0])  # Ordenar por distancia ascendente
            return distances[0][1]  # Retornar el movimiento con menor distancia
            
        # Retornar el movimiento con el mayor valor Q
        return q_values[0][1]
        
    def update_q_value(self, state, action, next_state, reward, done):
        """
        Actualiza el valor Q para un par estado-acción usando la ecuación de Bellman
        
        Args:
            state: Estado actual (x, y)
            action: Acción tomada (dx, dy)
            next_state: Estado siguiente (x, y)
            reward: Recompensa recibida
            done: Si el episodio ha terminado
        """
        x, y = state
        action_idx = self.dir_indices[action]
        
        # Si llegamos a un estado terminal (meta), el valor futuro es 0
        if done:
            max_future_q = 0
        else:
            next_x, next_y = next_state
            # Obtenemos el máximo valor Q del siguiente estado
            max_future_q = np.max(self.q_table[next_y][next_x])
            
        # Fórmula de actualización Q-learning: Q(s,a) = Q(s,a) + α * [r + γ * max Q(s',a') - Q(s,a)]
        current_q = self.q_table[y][x][action_idx]
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_future_q - current_q)
        
        # Actualizar el valor Q
        self.q_table[y][x][action_idx] = new_q
    
    def find_path(self, start, goal, obstacles, is_training=False):
        """
        Busca un camino usando Q-learning con exploración epsilon-greedy
        
        Args:
            start: Posición inicial (x, y)
            goal: Posición de la meta (x, y)
            obstacles: Conjunto de obstáculos
            is_training: Si estamos en modo entrenamiento (True) o inferencia (False)
            
        Returns:
            El camino encontrado o None si no se encontró
        """
        start = tuple(start)
        goal = tuple(goal)
        current = start
        path = [current]
        visited = {current}
        max_steps = self.width * self.height * 2
        steps = 0
        total_reward = 0
        
        # Si no estamos entrenando, usar el valor mínimo de epsilon
        current_epsilon = self.epsilon if is_training else self.epsilon_min
        
        while current != goal and steps < max_steps:
            # Incrementar contador de visitas
            self.visit_count[current[1]][current[0]] += 1
            
            # Obtener vecinos válidos
            valid_neighbors = self.get_neighbors(current, obstacles)
            if not valid_neighbors:
                break
                
            # Filtrar vecinos no visitados (para evitar ciclos durante el entrenamiento)
            valid_moves = [(dir_move, new_pos) for dir_move, new_pos in valid_neighbors
                           if new_pos not in visited]
                           
            # Si no hay movimientos sin visitar, permitir revisitar (para evitar callejones sin salida)
            if not valid_moves and is_training:
                valid_moves = valid_neighbors
                
            if not valid_moves:
                break
                
            # Elegir acción usando epsilon-greedy
            chosen_move = self.choose_action(current, valid_moves, obstacles, goal, is_training)
            if chosen_move is None:
                break
                
            dir_move, next_pos = chosen_move
            
            # Calcular recompensa
            reward = self.calculate_reward(next_pos, goal, steps)
            total_reward += reward
            
            # Marcar como visitado y agregar al camino
            visited.add(next_pos)
            path.append(next_pos)
            
            # Actualizar valor Q si estamos entrenando
            if is_training:
                done = (next_pos == goal)
                self.update_q_value(current, dir_move, next_pos, reward, done)
                
            # Avanzar
            current = next_pos
            steps += 1
            
        # Registrar resultados del episodio si estamos entrenando
        if is_training:
            # Reducir epsilon (exploración) con el tiempo
            self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)
            
            # Registrar estadísticas
            self.training_history['path_lengths'].append(len(path))
            self.training_history['rewards'].append(total_reward)
            self.training_history['epsilons'].append(self.epsilon)
            
            # Actualizar mejor camino si corresponde
            if current == goal and (total_reward > self.best_reward or 
                                   (total_reward == self.best_reward and len(path) < self.best_path_length)):
                self.best_path = path.copy()
                self.best_path_length = len(path)
                self.best_reward = total_reward
                
        # Retornar el camino si llegamos a la meta, o None si no lo logramos
        if current == goal:
            return path
        return None
        
    def get_neighbors(self, position, obstacles):
        """
        Obtiene los vecinos válidos de una posición
        
        Args:
            position: Posición actual (x, y)
            obstacles: Conjunto de obstáculos
            
        Returns:
            Lista de movimientos válidos [(dir_move, new_pos), ...]
        """
        x, y = position
        valid_neighbors = []
        
        for dir_move in self.directions:
            dx, dy = dir_move
            new_x, new_y = x + dx, y + dy
            
            # Verificar límites del mapa
            if 0 <= new_x < self.width and 0 <= new_y < self.height:
                new_pos = (new_x, new_y)
                # Verificar que no sea un obstáculo
                if new_pos not in obstacles:
                    valid_neighbors.append((dir_move, new_pos))
                    
        return valid_neighbors
    
    def train_background(self, start, goal, obstacles, callback=None, update_interval=50):
        """
        Inicia un entrenamiento en segundo plano usando un hilo separado
        
        Args:
            start: Posición inicial (x, y)
            goal: Posición final (x, y)
            obstacles: Conjunto de obstáculos
            callback: Función a llamar después de cada actualización de intervalo
            update_interval: Número de iteraciones entre actualizaciones de progreso
        """
        # Detener cualquier entrenamiento existente
        self.stop_background_training = True
        if self.training_thread and self.training_thread.is_alive():
            self.training_thread.join()
        
        # Reiniciar variables de control
        self.stop_training = False
        self.training_iterations = 0
        
        # Función de entrenamiento que se ejecutará en segundo plano
        def training_worker():
            while not self.stop_training and self.training_iterations < self.max_training_iterations:
                # Ejecutar un episodio de entrenamiento
                path = self.find_path(start, goal, obstacles, is_training=True)
                self.training_iterations += 1
                
                # Llamar al callback en intervalos regulares si se proporcionó uno
                if callback and self.training_iterations % update_interval == 0:
                    callback(self.training_iterations, path, 
                             self.training_history, self.best_path)
                
                # Pequeña pausa para evitar sobrecargar la CPU
                time.sleep(0.001)
                
            # Llamada final al callback cuando el entrenamiento termina
            if callback:
                callback(self.training_iterations, None, 
                         self.training_history, self.best_path, is_final=True)
        
        # Iniciar hilo de entrenamiento
        self.training_thread = threading.Thread(target=training_worker)
        self.training_thread.daemon = True  # Hilo en segundo plano
        self.training_thread.start()
        
    def stop_background_training(self):
        """
        Detiene cualquier entrenamiento en segundo plano que esté en ejecución
        
        Returns:
            True si se detuvo un entrenamiento en curso, False si no había ninguno
        """
        if self.training_thread and self.training_thread.is_alive():
            self.stop_training = True
            self.training_thread.join(timeout=2.0)  # Esperar a que termine, con timeout
            return True
        return False
        
    def plot_learning_progress(self, save_path=None, show=True):
        """
        Visualiza el progreso del aprendizaje durante el entrenamiento
        
        Args:
            save_path: Ruta donde guardar la imagen, o None para no guardar
            show: Si se debe mostrar la visualización
            
        Returns:
            Figura de matplotlib
        """
        if not self.training_history['path_lengths']:
            print("No hay datos de entrenamiento para visualizar")
            return None
            
        fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
        episodes = range(1, len(self.training_history['path_lengths']) + 1)
        
        # Gráfico de longitud de camino
        axs[0].plot(episodes, self.training_history['path_lengths'], 'b-')
        axs[0].set_title('Longitud de Camino vs. Episodios')
        axs[0].set_ylabel('Longitud')
        axs[0].grid(True)
        
        # Gráfico de recompensa total
        axs[1].plot(episodes, self.training_history['rewards'], 'g-')
        axs[1].set_title('Recompensa Total vs. Episodios')
        axs[1].set_ylabel('Recompensa')
        axs[1].grid(True)
        
        # Gráfico de epsilon (exploración)
        axs[2].plot(episodes, self.training_history['epsilons'], 'r-')
        axs[2].set_title('Epsilon (Exploración) vs. Episodios')
        axs[2].set_xlabel('Episodios')
        axs[2].set_ylabel('Epsilon')
        axs[2].grid(True)
        
        plt.tight_layout()
        
        # Guardar figura si se especificó una ruta
        if save_path:
            plt.savefig(save_path)
            
        # Mostrar o no la figura
        if show:
            plt.show()
        else:
            plt.close(fig)
            
        return fig
        
    def plot_q_values_heatmap(self, save_path=None, show=True):
        """
        Visualiza los valores Q como mapas de calor para cada dirección
        
        Args:
            save_path: Ruta donde guardar la imagen, o None para no guardar
            show: Si se debe mostrar la visualización
            
        Returns:
            Figura de matplotlib
        """
        # Crear figura con subplots para cada dirección
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        axs = axs.flatten()
        
        # Crear un mapa de colores personalizado
        cmap = plt.cm.viridis
        
        # Calcular valor máximo para normalizar los mapas de calor
        max_q = np.max(self.q_table) if np.max(self.q_table) > 0 else 1
        
        # Generar mapa de calor para cada dirección
        for i, direction_name in enumerate(self.direction_names):
            # Extraer valores Q para esta dirección
            q_values = self.q_table[:, :, i]
            
            # Mostrar mapa de calor
            im = axs[i].imshow(q_values, cmap=cmap, vmin=0, vmax=max_q)
            axs[i].set_title(f'Valores Q: {direction_name}')
            axs[i].set_xlabel('X')
            axs[i].set_ylabel('Y')
            
            # Agregar barras de color para cada mapa
            plt.colorbar(im, ax=axs[i])
            
        plt.tight_layout()
        
        # Guardar figura si se especificó una ruta
        if save_path:
            plt.savefig(save_path)
            
        # Mostrar o no la figura
        if show:
            plt.show()
        else:
            plt.close(fig)
            
        return fig
        
    def plot_best_path(self, start, goal, obstacles, save_path=None, show=True):
        """
        Visualiza el mejor camino encontrado durante el entrenamiento
        
        Args:
            start: Posición inicial (x, y)
            goal: Posición de la meta (x, y)
            obstacles: Conjunto de obstáculos
            save_path: Ruta donde guardar la imagen, o None para no guardar
            show: Si se debe mostrar la visualización
            
        Returns:
            Figura de matplotlib
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Configuración de la cuadrícula
        ax.set_xlim(-0.5, self.width - 0.5)
        ax.set_ylim(self.height - 0.5, -0.5)  # Invertir eje Y para que (0,0) sea arriba a la izquierda
        ax.set_xticks(range(self.width))
        ax.set_yticks(range(self.height))
        ax.grid(True)
        
        # Dibujar obstáculos
        for obs in obstacles:
            x, y = obs
            ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, color='black'))
            
        # Dibujar mapa de calor de visitas
        visit_heatmap = np.ma.masked_where(self.visit_count == 0, self.visit_count)
        ax.imshow(visit_heatmap, cmap='Blues', alpha=0.6, vmin=1, vmax=np.max(self.visit_count))
        
        # Dibujar el mejor camino si existe
        if self.best_path:
            path_x = [pos[0] for pos in self.best_path]
            path_y = [pos[1] for pos in self.best_path]
            ax.plot(path_x, path_y, 'r-', linewidth=2, label=f'Mejor camino ({len(self.best_path)} pasos)')
            
            # Marcar dirección de movimiento con flechas
            for i in range(len(self.best_path) - 1):
                x1, y1 = self.best_path[i]
                x2, y2 = self.best_path[i + 1]
                dx, dy = x2 - x1, y2 - y1
                ax.arrow(x1, y1, dx * 0.6, dy * 0.6, head_width=0.2, head_length=0.2, 
                         fc='red', ec='red', alpha=0.7)
                
        # Marcar inicio y meta
        ax.plot(start[0], start[1], 'go', markersize=10, label='Inicio')
        ax.plot(goal[0], goal[1], 'bo', markersize=10, label='Meta')
        
        # Añadir leyenda y título
        ax.legend()
        ax.set_title(f'Mejor Camino Encontrado\nRecompensa: {self.best_reward:.2f}, Longitud: {self.best_path_length}')
        
        plt.tight_layout()
        
        # Guardar figura si se especificó una ruta
        if save_path:
            plt.savefig(save_path)
            
        # Mostrar o no la figura
        if show:
            plt.show()
        else:
            plt.close(fig)
            
        return fig
        
    def plot_comprehensive_analysis(self, start, goal, obstacles, save_path=None, show=True):
        """
        Genera un análisis completo del aprendizaje con múltiples visualizaciones
        
        Args:
            start: Posición inicial (x, y)
            goal: Posición de la meta (x, y)
            obstacles: Conjunto de obstáculos
            save_path: Ruta donde guardar la imagen, o None para no guardar
            show: Si se debe mostrar la visualización
            
        Returns:
            Figura de matplotlib
        """
        # Crear una figura grande con subfiguras
        fig = plt.figure(figsize=(18, 12))
        
        # Definir la distribución de subfiguras
        gs = fig.add_gridspec(2, 3)
        
        # 1. Gráfico de progreso de entrenamiento (primera fila, columnas 1-2)
        ax1 = fig.add_subplot(gs[0, 0:2])
        if self.training_history['path_lengths']:
            episodes = range(1, len(self.training_history['path_lengths']) + 1)
            ax1.plot(episodes, self.training_history['path_lengths'], 'b-', label='Longitud de camino')
            ax1.set_ylabel('Longitud', color='b')
            ax1.tick_params(axis='y', labelcolor='b')
            ax1.set_xlabel('Episodios')
            ax1.grid(True, alpha=0.3)
            
            # Segundo eje Y para recompensas
            ax1_twin = ax1.twinx()
            ax1_twin.plot(episodes, self.training_history['rewards'], 'g-', label='Recompensa')
            ax1_twin.set_ylabel('Recompensa', color='g')
            ax1_twin.tick_params(axis='y', labelcolor='g')
            
            # Título y leyenda combinados
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax1_twin.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center')
        
        ax1.set_title('Progreso del Entrenamiento')
        
        # 2. Mejor camino (primera fila, columna 3)
        ax2 = fig.add_subplot
