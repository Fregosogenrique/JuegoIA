import numpy as np
import random
import matplotlib.pyplot as plt

# Dimensiones de la matriz
filas, columnas = 40, 30
valores_por_celda = 4  # Cada celda contiene un arreglo de 4 valores
cantidad_negativos = 50  # Cantidad de celdas con [-1, -1, -1, -1]

# Crear la matriz con arreglos inicializados en [0, 0, 0, 0]
matriz = np.array([[[0] * valores_por_celda for _ in range(columnas)] for _ in range(filas)], dtype=object)

# Seleccionar posiciones aleatorias para asignar [-1, -1, -1, -1]
posiciones = set()
while len(posiciones) < cantidad_negativos:
    i, j = random.randint(0, filas - 1), random.randint(0, columnas - 1)
    posiciones.add((i, j))

# Asignar los valores -1 en las posiciones seleccionadas
for i, j in posiciones:
    matriz[i, j] = [-1] * valores_por_celda

# Convertir la matriz en una representación numérica para graficar
matriz_numerica = np.zeros((filas, columnas))  # 0 para azul
for i, j in posiciones:
    matriz_numerica[i, j] = 1  # 1 para rojo

# Mostrar la matriz gráficamente
plt.figure(figsize=(10, 10))
plt.imshow(matriz_numerica, cmap="coolwarm", interpolation="nearest")  # coolwarm: azul y rojo
plt.colorbar(label="Estado de la celda")
plt.xticks([])  # Ocultar etiquetas de los ejes
plt.yticks([])
plt.title("Matriz de arreglos (visualización gráfica)")
plt.show()