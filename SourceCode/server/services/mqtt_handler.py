import paho.mqtt.client as mqtt
import json
from config import settings
from datetime import datetime

class MQTTHandler:
    def __init__(self, on_slot_update=None):
        self.client = mqtt.Client()
        self.on_slot_update = on_slot_update
        self.camera_frame_callback = None  # Callback cho camera frames
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Credentials (chỉ set nếu username không rỗng)
        if settings.MQTT_USERNAME and settings.MQTT_USERNAME.strip():
            self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            print(f"[MQTT] Using authentication with username: {settings.MQTT_USERNAME}")
        else:
            print(f"[MQTT] No authentication")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT] SUCCESS Connected to MQTT broker: {settings.MQTT_BROKER}")
            # Subscribe vào topic slots
            client.subscribe(settings.MQTT_TOPIC_SLOTS)
            print(f"[MQTT] Subscribed to topic: {settings.MQTT_TOPIC_SLOTS}")
        else:
            print(f"[MQTT] Failed to connect to MQTT broker, code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            
            print(f"[MQTT] Topic: {topic}")
            print(f"[MQTT] Message: {payload}")
            
            # Parse JSON
            try:
                data = json.loads(payload)
                
                # Gọi callback để cập nhật database
                if self.on_slot_update:
                    self.on_slot_update(data)
            
            except json.JSONDecodeError:
                print(f"[MQTT] Invalid JSON: {payload}")
        
        except Exception as e:
            print(f"[MQTT] Error processing message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        
        # Callback khi mất kết nối
        if rc != 0:
            print(f"[MQTT] ERROR Unexpected disconnection. Reconnecting...")
    
    def connect(self):
        
        # Kết nối đến MQTT broker
        try:
            self.client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"[MQTT] Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        
        # Ngắt kết nối
        self.client.loop_stop()
        self.client.disconnect()
        print("✓ Disconnected from MQTT broker")
    
    def publish(self, topic, message):
        
        # Publish message
        try:
            # Check if client is connected
            if not self.client.is_connected():
                print(f"[MQTT] ERROR Client not connected")
                return False
            
            result = self.client.publish(topic, json.dumps(message), qos=1)
            
            # Wait for publish to complete (timeout 2 seconds)
            result.wait_for_publish(2.0)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS and result.is_published():
                print(f"[MQTT] Published to {topic}: {message}")
                return True
            else:
                print(f"[MQTT] Publish failed - rc: {result.rc}, published: {result.is_published()}")
                return False
        except Exception as e:
            print(f"[MQTT] Error publishing: {e}")
        return False

# Global MQTT client instance
mqtt_client = MQTTHandler()
