

## PARTE 2: DESARROLLO PRÁCTICO EN ENTORNO VIRTUAL 

### La Consigna del Alumno: "Módulo de Robustez y Telemetría para DevOps"
# **Contexto de Infraestructura:** El equipo de administración de servidores de la universidad te ha entregado un script base de Python (`srv_telemetry_base.py`) que implementa un shell remoto TCP multihilo en el puerto `9090`. Actualmente, el script funciona en condiciones ideales, pero es **muy inestable**: si un cliente se desconecta sin escribir `EXIT` (ej. si se le corta internet o presiona Ctrl+C), el servidor lanza excepciones en el hilo que saturan los logs y no liberan los descriptores adecuadamente.

# Tu tarea como desarrollador de aplicaciones es modificar **exclusivamente el servidor** para cumplir con los siguientes tres requerimientos de producción:

# 1. **Robustez ante Desconexiones Abruptas:** Capturar de forma precisa las excepciones de sockets (`ConnectionResetError`, `socket.error`) dentro del hilo del cliente. Si el cliente desaparece de la red de forma imprevista, el hilo no debe romper el servidor; debe cerrar el socket limpiamente (`conn.close()`) y registrar en la consola del servidor: `[ALERTA] Cliente <IP:Puerto> desconectado abruptamente.`
# 2. **Comando de Telemetría (`STATS`):** Agregar soporte para el comando `STATS` (en mayúsculas o minúsculas). Cuando un cliente conectado envíe este comando, el servidor **no debe ejecutar nada en el sistema operativo**. Debe responderle al cliente con un string de texto plano estructurado que informe:
#    * La cantidad de hilos activos totales en ese instante.
#    * La ruta del directorio de trabajo actual (utilizando el módulo `os`).
# 3. **Control de Saturación Activo (Capa de Aplicación):** Actualmente, si se supera el límite de `MAX_CLIENTS = 5`, las conexiones extras se quedan colgadas en un hilo secundario sin hacer nada. Debes modificar la lógica de aceptación para que, si el servidor ya llegó al máximo de clientes permitidos, acepte la conexión entrante, le envíe inmediatamente al cliente el mensaje: `[ERROR] Servidor saturado. Intente más tarde.\n`, y **cierre la conexión inmediatamente sin crear un hilo** para él, protegiendo los recursos de la VM.



import socket
import threading
import os

HOST = '0.0.0.0'  # Escucha en todas las interfaces de la VM
PORT = 9090
MAX_CLIENTS = 5

def manejar_cliente(conn, addr):
    print(f"[NUEVA CONEXIÓN] {addr} conectado exitosamente.")
    conn.send("Bienvenido al Servidor de Telemetría UNTDF.\nComandos disponibles: LS, PWD, STATS, EXIT\n> ".encode())

    while True:
        try:
            # Recibir datos del buffer del socket
            data = conn.recv(1024).decode().strip()
            
            # Si no hay datos, el cliente cerró el socket de su lado de forma limpia
            if not data:
                break

            partes = data.split(" ", 1)
            comando = partes[0].upper()
            
            if comando == "EXIT":
                break
            
            elif comando == "LS":
                archivos = os.listdir('.')
                respuesta = "\n".join(archivos)
            
            elif comando == "PWD":
                respuesta = os.getcwd()

            # =========================================================
            # TO-DO 2: IMPLEMENTAR AQUÍ EL COMANDO 'STATS'
            # =========================================================
            elif comando == "STATS":
                hilos_totales = threading.active_count()
                ruta_actual = os.getcwd()
                respuesta = f"Telemetría:\n- Hilos activos totales: {hilos_totales}\n- Directorio actual: {ruta_actual}"
            # =========================================================

            else:
                respuesta = "Comando no reconocido."

            # Enviar la respuesta agregando el prompt del shell
            conn.send((respuesta + "\n> ").encode())

        except (ConnectionResetError, socket.error):
            print(f"[ALERTA] Cliente {addr} desconectado abruptamente.")
        except Exception as e:
            print(f"Error general con el cliente {addr}: {e}")
        finally:
            # cierre limpio 
            print(f"[DESCONEXIÓN] {addr} finalizó sesión.")
            conn.close()

def iniciar_servidor():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Evitar el error: Address already in use
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server.bind((HOST, PORT))
    server.listen(MAX_CLIENTS)
    print(f"[LISTO] Servidor de infraestructura escuchando en puerto {PORT}...")

    while True:
        conn, addr = server.accept()
        
        # =========================================================
        # TO-DO 3: MODIFICAR ESTA LÓGICA PARA CONTROL DE SATURACIÓN
        # =========================================================
        # Contabilizar hilos activos (Nota: el hilo principal cuenta como 1)
        if threading.active_count() - 1 < MAX_CLIENTS:
            thread = threading.Thread(target=manejar_cliente, args=(conn, addr))
            thread.start()
            print(f"[HILOS ACTIVOS] Clientes concurrentes: {threading.active_count() - 1}")
        else:
            conn.send("[ERROR] Servidor saturado. Intente más tarde.\n".encode())
            # cierro la conexion inmediatamente sin crear un hilo
            conn.close()
            print(f"[RECHAZADO] Conexión desde {addr} denegada por saturación.")

if __name__ == "__main__":
    iniciar_servidor()