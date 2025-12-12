import json
import base64
import cv2
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from ultralytics import YOLO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


try:
    model = YOLO('yolov8n.pt') 
    logger.info("✅ YOLO model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load YOLO model: {e}")
    model = None

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info("🔌 Client connected")
        
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to parking detection server',
            'timestamp': datetime.now().isoformat()
        }))
    
    async def disconnect(self, close_code):
        logger.info(f"🔌 Client disconnected: {close_code}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"📥 Received message type: {data.get('type')}")
            
            if data['type'] == 'video_frame':
               
                result = await self.process_frame(data)
                await self.send(text_data=json.dumps(result))
                
            elif data['type'] == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
                
        except Exception as e:
            logger.error(f"❌ Error in receive: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def process_frame(self, data):
        """پردازش فریم و تشخیص خودروها"""
        try:

            frame_data = data['frame']
            

            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            
            img_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return {
                    'type': 'error',
                    'message': 'Failed to decode image',
                    'count': 0
                }
            
           
            results = []
            count_car = 0
            
            if model:
                yolo_results = model(frame, conf=0.5, verbose=False)
                
               
                for result in yolo_results:
                    boxes = result.boxes
                    for box in boxes:
                        class_id = int(box.cls[0])
                        if class_id in [2, 5, 7]:  
                            count_car += 1
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            confidence = float(box.conf[0])
                            
                            results.append({
                                'class_id': class_id,
                                'confidence': confidence,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)]
                            })
                

                if data.get('annotate', False):
                    annotated_frame = yolo_results[0].plot()
                    _, buffer = cv2.imencode('.jpg', annotated_frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                else:
                    frame_base64 = None
            else:
                frame_base64 = None
            
            return {
                'type': 'detection_result',
                'count': count_car,
                'detections': results,
                'timestamp': datetime.now().isoformat(),
                'frame': frame_base64,
                'message': f'Detected {count_car} vehicles'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in process_frame: {e}")
            return {
                'type': 'error',
                'message': str(e),
                'count': 0
            }