import gradio as gr
from gradio_webrtc import WebRTC
import cv2
from io import BytesIO
import requests
import numpy as np
from PIL import Image
from requests.auth import HTTPBasicAuth
import serial

ser = serial.Serial("/dev/ttyACM0", 9600)
#VISION_API_URL = "https://suite-endpoint-api-apne2.superb-ai.com/endpoints/80451a40-16a1-4506-9084-783c033421f3/inference"
VISION_API_URL = "http://192.168.10.13:8883/inference/run"
#TEAM = "kdt2024_1-13"
#ACCESS_KEY = "k2lhkX9AGq4vbsvXUnObOaPqW0Bz2cJ299zsCUlO"

def process_image(image):
    count = {0:0, 1:0,2:0,3:0,4:0,5:0}
    # 이미지를 OpenCV 형식으로 변환
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # 이미지를 API에 전송할 수 있는 형식으로 변환
    _, img_encoded = cv2.imencode(".jpg", image)   
    img_binary = img_encoded.tobytes()
    img_bytes = BytesIO(img_binary) 
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}

    # API 호출 및 결과 받기 - 실습1
    response = requests.post(
        url=VISION_API_URL,
        #auth=HTTPBasicAuth(TEAM, ACCESS_KEY),
        #headers={"Content-Type": "image/jpeg"},
        files = files
    )   
    result = response.json()
    # API 결과를 바탕으로 박스 그리기 - 실습2
    print(response.status_code)
    print(response.json())
    objects = result["objects"].copy()
    print(objects)
    for i in objects:
        box = i["bbox"]
        start_point=(int(box[0]),int(box[1]))
        end_point=(int(box[2]),int(box[3]))
        if i["class_number"] == 0:
            count[i["class_number"]] += 1
            color = (127,255,127)
        elif i["class_number"] == 1:
            color = (255,0,0)
            count[i["class_number"]] += 1
        elif i["class_number"] == 2:
            color = (0,255,0)
            count[i["class_number"]] += 1
        elif i["class_number"] == 3:
            color = (0,0,255)
            count[i["class_number"]] += 1
        elif i["class_number"] == 4:
            color = (255,255,0)
            count[i["class_number"]] += 1
        elif i["class_number"] == 5:
            color = (30,60,90)
            count[i["class_number"]] += 1
        else:
            color = (0,0,0)
        print(box,start_point,end_point)
        cv2.rectangle(image,start_point,end_point,color = color, thickness = 1)
        print("asdf")
        cv2.putText(image,str(i["class_number"]),start_point,cv2.FONT_HERSHEY_SIMPLEX, 1, color=color,thickness=1)
    print("asdf")
    
    text = ""
    k=30
    for j in count.keys():
        text = str(j) + " : " +str(count[j])
        k=k+30
        cv2.putText(image,text,(30,k),cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    # BGR 이미지를 RGB로 변환
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print("asdf")
    return image, count#Image.fromarray(image)

def generation():    
    cap = cv2.VideoCapture(0)
    #ret, img = cap.read()
    #cap1 = process_image(img)
    #iterating = True
    while 1:
        data = ser.read()
        _, frame = cap.read()
        frame, count = process_image(frame)
        if data == b"0":
            obj_count = 0
            for i in count.values():
                obj_count += i
            if obj_count == 9:
                ser.write(b"1")
            else:
                cv2.waitKey(0)
                ser.write(b"1")
        yield frame
        

with gr.Blocks() as demo:
    output_video = WebRTC(label="Video Stream", mode="receive", modality="video")
    button = gr.Button("Start", variant="primary")
    output_video.stream(
        fn=generation, inputs=None, outputs=[output_video],
        trigger=button.click
    )

if __name__ == "__main__":
    demo.launch()