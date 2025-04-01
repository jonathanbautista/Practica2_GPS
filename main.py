import tkinter as tk 
from tkinter import ttk 
from PIL import Image, ImageDraw, ImageTk 
import threading 
import queue 
import serial 
import pyproj 
import datetime 
 
def gga_to_utm(lat, lon): 
    lat_deg = float(lat[:2]) + float(lat[2:])/60 
    lon_deg = -1 * (float(lon[:3]) + float(lon[3:])/60) 
    wgs84 = pyproj.CRS('EPSG:4326') 
    utm = pyproj.CRS.from_epsg(32630) 
    transformer = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True) 
    easting, northing = transformer.transform(lon_deg, lat_deg) 
    return easting, northing, '30T' 
 
def mapear_coordenadas(coordenada, imagen): 
    x, y = coordenada 
    coordenada_superior_izquierda = (40.38805556,-3.72805556) 
    coordenada_inferior_derecha = (40.38666667,-3.73416667) 
    x_mapped = (x - coordenada_superior_izquierda[0]) / (coordenada_inferior_derecha[0] - coordenada_superior_izquierda[0]) * imagen.width 
    y_mapped = (y - coordenada_superior_izquierda[1]) / (coordenada_inferior_derecha[1] - coordenada_superior_izquierda[1]) * imagen.height 
    return x_mapped, y_mapped 
 
def actualizar_punto_en_imagen(coordenada, imagen_acumulativa): 
    dibujo = ImageDraw.Draw(imagen_acumulativa) 
    tamaño_punto = 10 
    x_mapped, y_mapped = mapear_coordenadas(coordenada, imagen_acumulativa) 
    dibujo.ellipse([x_mapped - tamaño_punto, y_mapped - tamaño_punto, x_mapped + tamaño_punto, y_mapped + tamaño_punto], fill="red", outline="red") 
    return imagen_acumulativa 
 
def leer_datos_gps(q, ser): 
    while True: 
        line = ser.readline().decode('utf-8').strip() 
        if 'GPGGA' in line: 
        #trama_gps = "$GPGGA,152930.00,4023.334340,N,00337.68317,W,1,07,1.13,688.4,M,50.3,M,,*48"    
            parts = line.split(',') 
             # print("Hola, mundo!")
            if len(parts) > 5 and parts[2] and parts[4]:  # Verificar datos mínimos 
                lat = parts[2] 
                lon = parts[4] 
                easting, northing, zone = gga_to_utm(lat, lon) 
                q.put((easting, northing)) 
 
def actualizar_gui(root, q, imagen_original, etiqueta_imagen): 
    try: 
        while True:  # Procesar todos los elementos en la cola 
            easting, northing = q.get_nowait() 
            imagen_actualizada = actualizar_punto_en_imagen((easting, northing), imagen_original) 
            mostrar_imagen_en_gui(imagen_actualizada, etiqueta_imagen) 
    except queue.Empty: 
        pass 
    finally: 
        root.after(100, actualizar_gui, root, q, imagen_original, etiqueta_imagen) 
 
def mostrar_imagen_en_gui(imagen, etiqueta_imagen): 
    imagen_tk = ImageTk.PhotoImage(imagen) 
    etiqueta_imagen.configure(image=imagen_tk) 
    etiqueta_imagen.image = imagen_tk 
 
# Configuración inicial de la GUI 
root = tk.Tk() 
root.title("Visualización de Coordenadas GPS") 
 
imagen_acumulativa_path = "imagenes/pruebapng.png" 
imagen_acumulativa = Image.open(imagen_acumulativa_path) 
imagen_tk = ImageTk.PhotoImage(imagen_acumulativa) 
 
etiqueta_imagen = ttk.Label(root, image=imagen_tk) 
etiqueta_imagen.pack() 
 
# Configurar la cola y el puerto serie 
q = queue.Queue() 
ser = serial.Serial('COM7', 4800, timeout=1) 
 
# Iniciar hilo para leer datos GPS 
thread = threading.Thread(target=leer_datos_gps, args=(q, ser), daemon=True) 
thread.start() 
 
# Iniciar actualización de la GUI 
actualizar_gui(root, q, imagen_acumulativa, etiqueta_imagen) 
 
root.mainloop()