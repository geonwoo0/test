import cv2
from io import BytesIO
import requests
import numpy as np
from PIL import Image
from requests.auth import HTTPBasicAuth
import serial
import time
import sqlite3
import uuid
from datetime import datetime

ser = serial.Serial("/dev/ttyACM0", 9600)
VISION_API_URL = "http://192.168.10.13:8883/inference/run"

conn = sqlite3.connect('check_pi.db')
cursor = conn.cursor()


def request_image(image):
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    _, img_encoded = cv2.imencode(".jpg", image)   
    img_bytes = BytesIO(img_encoded.tobytes()) 
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}

    response = requests.post(
        url = VISION_API_URL,
        files = files
    )
    print("상태:",response.status_code)
    img_obj = response.json()["objects"]
    return img_obj

def process_image(img_obj,frame):
    image = np.array(frame)
    image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    img_cnt = {"a":0,"b":0,"c":0,"d":0,"e":0,"f":0}
    for obj in img_obj:
        cls_number = obj["class_number"]
        confidence = obj["confidence"]
        bbox = obj["bbox"]
        if cls_number == 1:
            cls_name = "a"
            img_cnt[cls_name] +=1
            color = (127,255,127)
        elif cls_number == 2:
            cls_name = "b"
            img_cnt[cls_name] +=1
            color = (255,0,0)
        elif cls_number == 3:
            cls_name = "c"
            img_cnt[cls_name] +=1
            color = (0,255,0)
        elif cls_number == 4:
            cls_name = "d"
            img_cnt[cls_name] +=1
            color = (0,0,255)
        elif cls_number == 5:
            cls_name = "e"
            img_cnt[cls_name] +=1
            color = (255,255,0)
        elif cls_number == 6:
            cls_name = "f"
            img_cnt[cls_name] +=1
            color = (30,60,90)

        a1,a2,b1,b2 = bbox
        cv2.rectangle(image, (int(a1),int(a2)), (int(b1),int(b2)), color = color, 2)

        text = f"{cls_name}: {float(confidence):.2f}"

        cv2.putText(image, text, (int(a1), int(a2) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color = color, 2)
    print("box 생성")
    k=30
    for j in img_cnt:
        text = j + ":" + str(img_cnt[j])
        k=k+30
        cv2.putText(image,text,(30,k),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    print("박스 수량")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    return image

def insert_data(datetime_value, uuid_value, is_defective, defect_reason=None,img_path):
    insert_query = '''
    INSERT INTO 제품 (datetime, uuid, is_defective, defect_reason, image_path)
    VALUES (?, ?, ?, ?, ?)
    '''
    cursor.execute(insert_query, (datetime_value, uuid_value, is_defective, defect_reason,img_path))
    conn.commit()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 프레임 폭 줄이기
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 프레임 높이 줄이기
cap.set(cv2.CAP_PROP_FPS, 15)  # 초당 프레임 수 제한

while 1:
    _, frame = cap.read()
    
    img_obj = request_image(frame)
    obj_cnt = len(img_obj)

    if obj_cnt >= 1:
        frame = process_image(img_obj,frame)
        cv2.imshow("image",frame)
        cv2.waitKey(1)
        data = ser.read()
        
        if data == b"0" and obj_cnt == 9:
            datetime_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            uuid_value = str(uuid.uuid4())
            is_defective = 0
            defect_reason = "정상"
            #이미지 경로 수정
            cv2.imwrite(f"{uuid_value}{defect_reason}.jpg",frame)
            image_path = f"{uuid_value}{defect_reason}.jpg"
            insert_data(datetime_value,uuid_value,is_defective,defect_reason,image_path)
            ser.write(b"1")

        elif data == b"0" and obj_cnt < 9:
            datetime_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            uuid_value = str(uuid.uuid4())
            is_defective = 1
            defect_reason = "불량"
            #이미지 경로 수정
            cv2.imwrite(f"{uuid_value}{defect_reason}",frame)
            image_path = f"{uuid_value}{defect_reason}"
            insert_data(datetime_value,uuid_value,is_defective,defect_reason,image_path)
            cv2.imshow("defect",frame)
            cv2.waitKey(1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                ser.write(b"1")
                pass


        else:
            pass
    else:
        cv2.imshow("image",frame)
        cv2.waitKey(1)
