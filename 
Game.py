            # Actualizar visualización
            self.renderer.render()
            
            # Mostrar indicador de progreso de entrenamiento si está activo
            if self.is_training or self.learning_complete:
                # Dibujar fondo para la información de entrenamiento
                pygame.draw.rect(self.screen, (30, 30, 30), 
                                (0, GameConfig.SCREEN_HEIGHT - 100, GameConfig.SCREEN_WIDTH, 100))
                
                # Dibujar barra de progreso en la parte inferior
                progress_color = (0, 255, 0) if self.learning_complete else (
                    min(255, int(255 * (1 - self.training_progress / 100))),  # R: disminuye con el progreso
                    min(255, int(255 * (self.training_progress / 100))),       # G: aumenta con el progreso
                    50  # B: constante
                )
                
                progress_width = int((GameConfig.SCREEN_WIDTH - 40) * (100 if self.learning_complete else self.training_progress) / 100)
                pygame.draw.rect(self.screen, (50, 50, 50), (20, GameConfig.SCREEN_HEIGHT - 40, GameConfig.SCREEN_WIDTH - 40, 20))
                # Dibujamos la barra de progreso con el color calculado
                pygame.draw.rect(self.screen, progress_color, (20, GameConfig.SCREEN_HEIGHT - 40, progress_width, 20))

                # Añadir texto de porcentaje en la barra
                percentage_font = pygame.font.Font(None, 18)
                percentage_text = percentage_font.render(
                    f"{100 if self.learning_complete else self.training_progress:.1f}%", 
                    True, (255, 255, 255)
                )
                percentage_rect = percentage_text.get_rect(
                    center=(20 + progress_width/2, GameConfig.SCREEN_HEIGHT - 30)
                )
                self.screen.blit(percentage_text, percentage_rect)
                # Crear sombra para el texto (mejora legibilidad)
                status_text = "Aprendizaje completado" if self.learning_complete else f"Aprendizaje: {self.training_progress:.1f}%"
                text_shadow = font.render(f"{status_text} - {self.learning_status}", True, (0, 0, 0))
                self.screen.blit(text_shadow, (22, GameConfig.SCREEN_HEIGHT - 72))
                
                # Texto principal
                text_color = (255, 255, 0) if self.learning_complete else (255, 255, 255)
                text = font.render(f"{status_text} - {self.learning_status}", True, text_color)
                self.screen.blit(text, (20, GameConfig.SCREEN_HEIGHT - 70))
                # Si el aprendizaje ha completado, mostrar mensaje de finalización
                if self.learning_complete and self.best_path:
                    # Mensaje con detalles de la ruta
                    complete_text = font.render(
        self.renderer = GameRenderer(self.screen, self)
        
        # Inicializar estado del entrenamiento
        self.training_complete = False
        self.training_status = ""
                        True, (255, 255, 0)
                    )
                    self.screen.blit(complete_text, (20, GameConfig.SCREEN_HEIGHT - 95))
                    
                    # Mostrar instrucción para el usuario
                    if not self.is_running:
                        instruction_text = font.render(
                            "Haz clic en 'Iniciar' para ver la mejor ruta", 
                            True, (255, 200, 0)
                        )
                        self.screen.blit(instruction_text, (GameConfig.SCREEN_WIDTH // 2 - 150, GameConfig.SCREEN_HEIGHT - 95))
    def show_best_path(self):
        """
        Muestra el mejor camino encontrado durante el entrenamiento.
        """
        if not self.best_path:
            print("No hay un mejor camino disponible. Inicie entren
                print(f"Aprendizaje completado. Mejor ruta: {len(best_path) if best_path else 'No encontrada'} pasos")
                self.is_training = False
                self.training_complete = True
                        self.agent.plot_analysis(
                            path=best_path,
                            history=history,
                            title="Análisis Final de Entrenamiento",
                            show_heatmap=True
                        )
                font = pygame.font.Font(None, 24)
                
                # Crear sombra para el texto (mejora legibilidad)
                text_shadow = font.render(f"Aprendizaje: {self.training_progress:.1f}% {self.training_status}", True, (0, 0, 0))
                self.screen.blit(text_shadow, (22, GameConfig.SCREEN_HEIGHT - 72))
                
                # Texto principal
                text = font.render(f"Aprendizaje: {self.training_progress:.1f}% {self.training_status}", True, (255, 255, 255))
                self.screen.blit(text, (20, GameConfig.SCREEN_HEIGHT - 70))
                # Si el aprendizaje ha completado, mostrar mensaje de finalización
                if self.training_complete and self.best_path:
            self.best_path = self.agent.best_path
        else:
            print("No se encontró una ruta óptima durante el entrenamiento")
            self.training_status = "No se encontró ruta óptima"
        if best_path:
            self.best_path = best_path
            self.training_status = f"Mejor ruta: {len(best_path)} pasos"
        else:
            self.training_status = "Buscando ruta óptima..."
            # Actualizar estado con métricas recientes
            self.training_status = f"Éxito reciente: {recent_success_rate:.1f}%"
                    if recent_avg < earlier_avg:
                        improvement = ((earlier_avg - recent_avg) / earlier_avg) * 100
                        self.training_status = f"Mejorando: {improvement:.1f}% (caminos más cortos)"
                    elif recent_avg > earlier_avg:
                        decline = ((recent_avg - earlier_avg) / earlier_avg) * 100
                        self.training_status = f"Explorando: {decline:.1f}% (caminos más largos)"
                    else:
                        self.training_status = f"Estable: {recent_avg:.1f} pasos promedio"
        # Cuando finaliza el entrenamiento, mostrar la mejor ruta
        if is_final:
            self.is_training = False
            self.training_complete = True
            if best_path:
                print(f"Entrenamiento completo. Mejor ruta: {len(best_path)} pasos")
                self.training_status = f"¡Completado! Mejor ruta: {len(best_path)} pasos"
            else:
                print("Entrenamiento completo. No se encontró una ruta óptima.")
                self.training_status = "No se encontró ruta óptima"
