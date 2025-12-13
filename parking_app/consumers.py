import json
import base64
import cv2
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor
from channels.generic.websocket import AsyncWebsocketConsumer
from ultralytics import YOLO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Thread pool برای عملیات سنگین
executor = ThreadPoolExecutor(max_workers=4)

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
            
            if data['type'] == 'video_frame':
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    executor, 
                    self._process_frame_sync, 
                    data
                )
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
    
    def _process_frame_sync(self, data):
        """تابع sync برای پردازش فریم"""
        try:
            frame_data = data['frame']
            
            # حذف prefix اگر وجود دارد
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
            
            # دریافت ابعاد اصلی تصویر
            original_height, original_width = frame.shape[:2]
            
            vehicles = []
            count_car = 0
            
            if model:
                # اجرای مدل YOLO
                yolo_results = model(frame, conf=0.3, verbose=False)
                
                for result in yolo_results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            class_id = int(box.cls[0])
                            # 2: car, 5: bus, 7: truck, 3: motorcycle
                            if class_id in [2, 5, 7, 3]:  # وسایل نقلیه
                                count_car += 1
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                confidence = float(box.conf[0])
                                
                                # محاسبه width و height
                                width = x2 - x1
                                height = y2 - y1
                                
                                # نام کلاس
                                class_name = model.names[class_id]
                                
                                vehicles.append({
                                    'x': x1,
                                    'y': y1,
                                    'width': width,
                                    'height': height,
                                    'confidence': confidence,
                                    'class': class_name,
                                    'class_id': class_id
                                })
                
                # اگر درخواست آنوتیشن دارد
                if data.get('annotate', False) and len(yolo_results) > 0:
                    # ایجاد تصویر با مستطیل‌های رسم شده
                    annotated_frame = frame.copy()
                    
                    # رسم مستطیل‌ها روی تصویر
                    for vehicle in vehicles:
                        x1, y1 = int(vehicle['x']), int(vehicle['y'])
                        x2 = int(x1 + vehicle['width'])
                        y2 = int(y1 + vehicle['height'])
                        
                        # انتخاب رنگ براساس کلاس
                        if vehicle['class_id'] == 2:  # car
                            color = (0, 255, 0)  # سبز
                        elif vehicle['class_id'] == 5:  # bus
                            color = (255, 0, 0)  # آبی
                        elif vehicle['class_id'] == 7:  # truck
                            color = (0, 0, 255)  # قرمز
                        else:  # motorcycle
                            color = (255, 255, 0)  # زرد
                        
                        # رسم مستطیل
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        
                        # نوشتن برچسب
                        label = f"{vehicle['class']} {vehicle['confidence']:.2f}"
                        cv2.putText(annotated_frame, label, (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    # کدگذاری تصویر به base64
                    _, buffer = cv2.imencode('.jpg', annotated_frame, 
                                            [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                else:
                    frame_base64 = None
            else:
                frame_base64 = None
            
            return {
                'type': 'detection_result',
                'count': count_car,
                'vehicles': vehicles,  # لیست خودروهای تشخیص داده شده
                'original_width': original_width,  # عرض تصویر اصلی
                'original_height': original_height,  # ارتفاع تصویر اصلی
                'timestamp': datetime.now().isoformat(),
                'frame': frame_base64,  # تصویر آنوتیت شده (اختیاری)
                'message': f'Detected {count_car} vehicles'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in _process_frame_sync: {e}")
            return {
                'type': 'error',
                'message': str(e),
                'count': 0
            }