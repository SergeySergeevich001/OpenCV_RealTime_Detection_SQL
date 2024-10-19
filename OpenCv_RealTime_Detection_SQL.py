# Определение количества людей на потоковом видео с помощью YOLO v.3
# и запись информации о количестве при наличии в БД MS SQL

import argparse
import certifi
import configparser
import cv2
import datetime
import ftplib
import hashlib
import shutil
import numpy as np
import os
from ping3 import ping, verbose_ping
import pyodbc
import requests
import time

class main_det():
    def __init__(self,ip=str(),op_nom=str(),c=0,nums= [0,0,0],flag=False,start= time.time(),TIME_TO_LOOP= 1800,ip_adres= str(requests.get('https://ip.beget.ru', verify=certifi.where()).text),del_mnog=None):
        self.ip=ip
        self.op_nom=op_nom
        self.c=c
        self.nums=nums
        self.flag=flag
        self.start=start
        self.TIME_TO_LOOP=TIME_TO_LOOP
        self.ip_adres=ip_adres
        self.del_mnog=del_mnog

    def config_reader(self):
        path = "settings.ini"
        config = configparser.ConfigParser()
        config.read(path)
        # Читаем некоторые значения из конфиг. файла.
        self.ip= config.get("Settings", "ip")
        self.op_nom = config.get("Settings", "op_nom")
        self.first_open=config.get("Settings", "first_open")
        print(self.ip)
        return self.ip, self.op_nom

    def shift(self,lst, steps): #функция проверки на рябь
        if steps < 0:
            steps = abs(steps)
            for i in range(steps):
                lst.append(lst.pop(0))
        else:
            for i in range(steps):
                lst.insert(0, lst.pop())

    def settime_in(self,b):
        if b!=self.del_mnog:
            time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(type(time))
            cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=DESKTOP-Q8AF2TD\SQLEXPRESS;DATABASE=test')
            cursor = cnxn.cursor()
            cursor.execute("INSERT INTO [test_table]([op_nom],[count_persons],[date_person])VALUES('"+ self.op_nom +"','"+ str(b) +"',CONVERT(datetime, '"+ time +"', 101))")
            cnxn.commit()
            print(time)
            self.del_mnog=b

    def detection(self): #функция распознавания обьектов
        # global ip_adres
        cap = cv2.VideoCapture(self.ip)
        time.sleep(2.0)
        ret,frame=cap.read()
        if ret==False:
            print(ip)
            stop()
        else:
            cap.release()
            #yolo_work
            ap = argparse.ArgumentParser()
            ap.add_argument("-c", "--confidence", type=float, default=0.1,
                help="minimum probability to filter weak detections")
            ap.add_argument("-t", "--threshold", type=float, default=0.5,
                help="threshold when applyong non-maxima suppression")
            args = vars(ap.parse_args())
            labelsPath = os.path.sep.join([ "coco.names"])
            LABELS = open(labelsPath).read().strip().split("\n")
            np.random.seed(42)
            COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
                dtype="uint8")
            weightsPath = os.path.sep.join(["yolov3.weights"])
            configPath = os.path.sep.join([ "yolov3.cfg"])
            net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
            image = frame
            (H, W) = image.shape[:2]
            ln = net.getLayerNames()
            ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
            blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                swapRB=True, crop=False)
            net.setInput(blob)
            start = time.time()
            layerOutputs = net.forward(ln)
            end = time.time()
            boxes = []
            confidences = []
            classIDs = []
            for output in layerOutputs:
                for detection in output:
                    scores = detection[5:]
                    classID = np.argmax(scores)
                    confidence = scores[classID]
                    if confidence > args["confidence"]:
                        if classID == 0:
                            box = detection[0:4] * np.array([W, H, W, H])
                            (centerX, centerY, width, height) = box.astype("int")
                            x = int(centerX - (width / 2))
                            y = int(centerY - (height / 2))
                            boxes.append([x, y, int(width), int(height)])
                            confidences.append(float(confidence))
                            classIDs.append(classID)
            idxs = cv2.dnn.NMSBoxes(boxes, confidences, args["confidence"],
                args["threshold"])
            # print(len(idxs))
            b=len(idxs)#взятие числа из строки
            #проверка на рябь
            self.nums.insert(len(self.nums)-1, b)
            self.nums.pop()
            self.shift(self.nums, 1)
            print(self.nums)

            if b==self.c :
                print('на фрейме', b ,'человек')
                # flag=False
                print(self.flag,'==')
            elif b>self.c:
                print('зашло', b ,'человек')
                print('на фрейме', b ,'человек')
                self.c=b
                self.flag=True
                print(self.flag,">")
            elif b<self.c:
                print('вышло', b ,'человек')
                print('на фрейме', b ,'человек')
                self.c=b
                self.flag=True

            if (self.flag==True) and (self.nums[0]==self.nums[1]==self.nums[2]): # Проверка стоит ли записывать в SQL
                print('write')
                self.settime_in(b)
                self.flag=False

    def process_video(self):
        self.config_reader()
        print(self.ip)
        while True: #бесконечный цикл для работы скрипта
            self.detection()# вызов функции распознавания
c1=main_det()
c1.process_video()
