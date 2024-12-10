import gradio as gr
from gradio_webrtc import WebRTC
import cv2
from io import BytesIO
import requests
import numpy as np
from PIL import Image
from requests.auth import HTTPBasicAuth
import serial
import time

ser = serial.Serial("/dev/ttyACM0", 9600)
VISION_API_URL = "http://192.168.10.13:8883/inference/run"


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
    img_cnt = {}
    for obj in img_obj:
        cls_number = obj["class_number"]
        confidence = obj["confidence"]
        bbox = obj["bbox"]
        if i["class_number"] == 1:
            cls_name = "a"
            img_cnt[cls_name] +=1
            color = (127,255,127)
        elif i["class_number"] == 2:
            cls_name = "b"
            img_cnt[cls_name] +=1
            color = (255,0,0)
        elif i["class_number"] == 3:
            cls_name = "c"
            img_cnt[cls_name] +=1
            color = (0,255,0)
        elif i["class_number"] == 4:
            cls_name = "d"
            img_cnt[cls_name] +=1
            color = (0,0,255)
        elif i["class_number"] == 5:
            cls_name = "e"
            img_cnt[cls_name] +=1
            color = (255,255,0)
        elif i["class_number"] == 6:
            cls_name = "f"
            img_cnt[cls_name] +=1
            color = (30,60,90)

        a1,a2,b1,b2 = bbox
        cv2.rectangle(image, (int(a1),int(a2)), (int(b1),int(b2)), color = color, 2)

        text = f"{cls_name} : {obj[confidence]}"
        cv2.putText(image, text, (int(a1), int(a2) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color = color, 2)
    print("box 생성")

    for j in img_cnt:
        text = j + ":" + str(img_cnt[j])
        k=k+30
        cv2.putText(image,text,(30,k),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    print("박스 수량")

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    return image



def generation():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 프레임 폭 줄이기
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 프레임 높이 줄이기
    cap.set(cv2.CAP_PROP_FPS, 15)  # 초당 프레임 수 제한

    while 1:
!       _, frame = cap.read()
        data = ser.read()
        img_obj = request_image(frame)
        obj_cnt = len(img_obj)

        if obj_cnt >= 1:
            frame = process_image(img_obj,frame)
            yield frame

            if data == b"0" and obj_cnt == 9:
                ser.write(b"1")
            else:
                pass
        else:
            yield frame


with gr.Blocks() as demo:
    output_video = gr.Video(label="Video Stream")
    button = gr.Button("Start", variant="primary")
    output_video.stream(
        fn=generation, inputs=None, outputs=[output_video],
        trigger=button.click
    )

if __name__ == "__main__":
    demo.launch()