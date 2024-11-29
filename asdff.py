import time
import serial
import requests
import numpy
from io import BytesIO
from pprint import pprint
from requests.auth import HTTPBasicAuth
import numpy as np

import cv2

ser = serial.Serial("/dev/ttyACM0", 9600)

# API endpoint
URL = "http://192.168.10.13:8883/inference/run"

def get_img():
    """Get Image From USB Camera

    Returns:
        numpy.array: Image numpy array
    """

    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("Camera Error")
        exit(-1)

    ret, img = cam.read()

    return img

def inference_reqeust(image: numpy.array):
    """_summary_

    Args:
        img (numpy.array): Image numpy array
        api_rul (str): API URL. Inference Endpoint
    """
    _, img_encoded = cv2.imencode(".jpg", image)   
    img_binary = img_encoded.tobytes()
    img_bytes = BytesIO(img_binary) 
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}


    """response = requests.post(
        url=URL,
        auth=HTTPBasicAuth("kdt2024_1-13", ACCESS_KEY),
        headers={"Content-Type": "image/jpeg"},
        data=image,
    )"""
    try:
        response = requests.post(
        url=URL,
        #auth=HTTPBasicAuth(TEAM, ACCESS_KEY),
        #headers={"Content-Type": "image/jpeg"},
        files = files
    )   
        if response.status_code == 200:
            pprint(response.json())
            return response.json()
            print("Image sent successfully")
        else:
            print(f"Failed to send image. Status : {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")


while 1:
    data = ser.read()
    print(data)
    img = get_img()
    cv2.imshow("img",img)
    if data == b"0":
        img = get_img()
        # crop_info = None
        result = inference_reqeust(img)
        objects = result["objects"].copy()
        img = np.array(img)
        thickness = 2 # 박스 선의 두께
        count = {"0":0, "1":0,"2":0,"3":0,"4":0,"5":0}

        for i in objects:
            box = i["bbox"]
            start_point=(int(box[0]),int(box[1]))
            end_point=(int(box[2]),int(box[3]))
            if i["class_number"] == "0":
                count[i["class_number"]] += 1
                color = (127,255,127)
            elif i["class_number"] == "1":
                color = (255,0,0)
                count[i["class_number"]] += 1
            elif i["class_number"] == "2":
                color = (0,255,0)
                count[i["class_number"]] += 1
            elif i["class_number"] == "3":
                color = (0,0,255)
                count[i["class_number"]] += 1
            elif i["class_number"] == "4":
                color = (255,255,0)
                count[i["class_number"]] += 1
            elif i["class_number"] == "5":
                color = (30,60,90)
                count[i["class_number"]] += 1
            else:
                color = (0,0,0)

            cv2.rectangle(img,start_point,end_point,color = color, thickness = thickness)
            cv2.putText(img,i["class_number"],start_point,cv2.FONT_HERSHEY_SIMPLEX, 1, color=color,thickness=1)
        text = ""
        k=30
        for j in count.keys():
            text = str(j) + " : " +str(count[j])
            k=k+30
            cv2.putText(img,text,(30,k),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.imshow("img_check",img)
        obj_count = 0
        for i in count.values():
            obj_count += i
        if obj_count == 9:
            ser.write(b"1")
        else:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                ser.write(b"1")
                pass
        
    else:
        pass

    cv2.waitKey()
    cv2.destroyAllWindows()
