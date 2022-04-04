#####################################################

# todas las importaciones

from turtle import width
import cv2
from cv2 import resize
from matplotlib.pyplot import connect
import numpy as np
import imutils
import mysql.connector
from mysql.connector import Error
#############################################################################

entrada_pcounter = 0
salida_pcounter = 0
cap = cv2.VideoCapture('videoprueba.avi') # video que se usa de ejemplo

#############################################################################

# contador de personas que suben y bajan

video_subs = cv2.bgsegm.createBackgroundSubtractorMOG() # algoritmo de substraccion de fondo
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)) # mejorar la imagen binaria

while True: 
    ret, frame = cap.read()
    if ret == False: break
    frame = imutils.resize(frame, width= 800)

    #Especificamos el area a anilizar.
    #Aqui puedes editar el area donde se necesita analizar esta en sentido de las manecillas de reloj
    area_pts = np.array([[330,240], [530,240], [530,420], [330,420]])

    # determinamos el area donde se analizara apoyandonos con una imagen auxiliar
    imgAux = np.zeros(shape=(frame.shape[:2]), dtype= np.uint8)
    imgAux = cv2.drawContours(imgAux, [area_pts],-1, (255), -1 )
    area_image = cv2.bitwise_and(frame, frame, mask = imgAux)

    # aplicamos substraccion de fondo

    fondo_mascara = video_subs.apply(area_image)
    fondo_mascara = cv2.morphologyEx(fondo_mascara, cv2.MORPH_OPEN, kernel)
    fondo_mascara = cv2.morphologyEx(fondo_mascara, cv2.MORPH_CLOSE, kernel)
    fondo_mascara = cv2.dilate(fondo_mascara, None, iterations=3)

    # encontramos los contornos presentes en fondo_mascara, para luego
    # basandonos en su area poder determinar si existe movimiento(personas)

    cnts = cv2.findContours(fondo_mascara,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]

    for cnt in cnts:
        if cv2.contourArea(cnt) > 500:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0),2)

    # si la persona cruza entre 255 y 265 en "Y", se incrementara
    # en 1 el contador de entradas al autobus
            if 255 < (y + h) < 265 :
                entrada_pcounter = entrada_pcounter + 1
                cv2.line(frame, (330,260), (530,260), (0, 255, 255), 4) # linea para entrada
    
    for cnt in cnts:
        if cv2.contourArea(cnt) > 500:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0),2)
    
    # si la persona cruza entre 375 y 385 en "Y", se incrementara
    # en 1 el contador de entradas al autobus
            if 375< (y + h) < 385 :
                salida_pcounter = salida_pcounter + 1
                cv2.line(frame, (330,380), (530,380), (0, 255, 255), 4) # linea para salida
            

    # para poder visualizar lo que estemos haciendo

    cv2.drawContours(frame, [area_pts], -1, (255, 0, 255), 2)
    cv2.line(frame, (330,260), (530,260), (0, 255, 255), 1) # linea para entrada
    cv2.line(frame, (330,380), (530,380), (0, 255, 255), 1) # linea para salida
    cv2.putText(frame, str(entrada_pcounter), (frame.shape[1]-55, 250), #texto de contador de entrada
    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

    cv2.putText(frame, str(salida_pcounter), (frame.shape[1]-55, 350), # texto de contador de salida
    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

    cv2.imshow('Frame', frame)
    #cv2.imshow('fondo_mascara', fondo_mascara)

    video = cv2.waitKey(80) & 0xFF
    if video == 27: break

#############################################################################
# conexion a base de datos

try:
    connection = mysql.connector.connect(host='localhost',
                                             database='autocar',
                                             user='root',
                                             password='')

#inicio espacio trabajar
#############################################################################
#proceso para crear tabla
    mySql_Crear_tabla = """CREATE TABLE usuarios ( 
                                 Id int(11) NOT NULL AUTO_INCREMENT, PRIMARY KEY (`Id`),
                                 entrada_pcounter float NOT NULL,
                                 salida_pcounter float NOT NULL,
                                 fecha timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
                                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4; """

    cursor = connection.cursor()
    result = cursor.execute(mySql_Crear_tabla)
    print("usuarios Table created successfully ")

except mysql.connector.Error as error:
    print("Failed to create table in MySQL: {}".format(error))

# proceso para insertar con variable en la tabla
    cursor = connection.cursor()
    mySql_insert_query = """INSERT INTO usuarios (entrada_pcounter, salida_pcounter) 
                                VALUES (%s, %s) """

    record = (entrada_pcounter, salida_pcounter)
    cursor.execute(mySql_insert_query, record)
    connection.commit()
    print("Record inserted successfully into user table")

except mysql.connector.Error as error:
    print("Failed to insert into MySQL table {}".format(error))


#############################################################################
#fin espacio para trabajar

    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)

except Error as e:
    print("Error while connecting to MySQL", e)
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL connection is closed")


#############################################################################

cap.release()
cv2.destroyAllWindows()