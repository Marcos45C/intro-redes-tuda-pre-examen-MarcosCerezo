Explicación técnica de la resolución
1 )
Robustez y Gestión de Descriptores de Archivo: Se envolvió el bucle principal en un bloque try-except capturando específicamente ConnectionResetError y socket.error
. Al usar un bloque finally para el comando conn.close(), aseguramos que el Descriptor de Archivo (File Descriptor) asociado al socket se libere correctamente en el sistema operativo, evitando que el puerto quede "colgado" o saturado de conexiones fantasma
.
2)
Comando de Telemetría: Implementamos el comando STATS utilizando la función threading.active_count(), que permite al administrador conocer cuántos procesos ligeros (hilos) están consumiendo recursos de la CPU en tiempo real
. Además, usamos os.getcwd() para informar sobre el entorno de ejecución del servidor en la jerarquía de directorios de Linux
.
3)
Control de Saturación en Capa de Aplicación: Modificamos la lógica de aceptación para proteger los recursos de la máquina virtual. Anteriormente, el servidor ignoraba las conexiones extra, dejándolas en la cola del kernel [Source 2 del historial]. Ahora, el servidor finaliza la conexión activamente si se supera el límite de MAX_CLIENTS. Esto es fundamental en entornos de producción para evitar ataques de denegación de servicio o degradación del rendimiento por exceso de hilos abiertos
.
