"""
Métodos adicionales para guardar y cargar el estado de entrenamiento de HybridPathfinder.
Estos métodos deben añadirse manualmente a la clase HybridPathfinder en el archivo hybrid_pathfinder.py
"""

# Método para guardar el estado de entrenamiento
def save_training_state(self, filename_prefix="training_state"):
    """
    Guarda el estado de entrenamiento actual.
    
    Args:
        filename_prefix (str): Prefijo para los archivos de estado
    
    Returns:
        bool: True si se guardó exitosamente, False en caso contrario
    """
    try:
        # Guardar el mapa de calor
        heat_map_file = f"{filename_prefix}_heat_map.npy"
        self.heat_map.save_heat_map(heat_map_file)
        
        # Guardar estadísticas de entrenamiento
        stats_file = f"{filename_prefix}_stats.npy"
        training_stats = {
            'success_count': self.success_path_count,
            'failure_count': self.failed_path_count,
            'execution_count': self.heat_map.execution_count
        }
        np.save(stats_file, training_stats)
        
        print(f"Estado de entrenamiento guardado en {filename_prefix}_*.npy")
        return True
    except Exception as e:
        print(f"Error al guardar el estado de entrenamiento: {e}")
        return False

# Método para cargar el estado de entrenamiento
def load_training_state(self, filename_prefix="training_state"):
    """
    Carga un estado de entrenamiento previo.
    
    Args:
        filename_prefix (str): Prefijo para los archivos de estado
    
    Returns:
        bool: True si se cargó exitosamente, False en caso contrario
    """
    try:
        # Cargar el mapa de calor
        heat_map_file = f"{filename_prefix}_heat_map.npy"
        heat_map_loaded = self.heat_map.load_heat_map(heat_map_file)
        
        if not heat_map_loaded:
            return False
        
        # Cargar estadísticas de entrenamiento
        stats_file = f"{filename_prefix}_stats.npy"
        training_stats = np.load(stats_file, allow_pickle=True).item()
        
        # Restaurar estadísticas
        self.success_path_count = training_stats['success_count']
        self.failed_path_count = training_stats['failure_count']
        
        print(f"Estado de entrenamiento cargado desde {filename_prefix}_*.npy")
        return True
    except Exception as e:
        print(f"Error al cargar el estado de entrenamiento: {e}")
        return False

"""
Instrucciones para añadir estos métodos a la clase HybridPathfinder:

1. Abrir el archivo hybrid_pathfinder.py
2. Copiar los dos métodos anteriores (save_training_state y load_training_state) 
3. Pegarlos al final de la clase HybridPathfinder, justo después del método check_victory_conditions
4. Guardar el archivo

Estos métodos permitirán mantener el estado de entrenamiento entre sesiones de juego,
preservando la proporción 2:1 de éxitos vs fallos para un mejor rendimiento del
pathfinding híbrido.
"""

