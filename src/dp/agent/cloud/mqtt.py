"""
MQTT Cloud Client for device control and status monitoring.
"""
import json
import time
import os
import uuid
import hmac
import base64
import asyncio
import threading
import logging
from hashlib import sha1
from typing import Dict, Any, Optional, Callable, List, Awaitable, Union
from paho.mqtt import client as mqtt
import redis
import dotenv

# Set up logging
logger = logging.getLogger("cloud")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Load environment variables
dotenv.load_dotenv()

# Redis channel prefix for device status updates
REDIS_STATUS_CHANNEL_PREFIX = "device_status:"

class MQTTCloud:
    """MQTT Cloud Client for device control and status monitoring.
    
    This class provides methods to send device control messages and receive device status updates.
    It can be used by the MCP server to interact with devices.
    """
    
    def __init__(self, 
                 instance_id: Optional[str] = None,
                 endpoint: Optional[str] = None,
                 device_id: Optional[str] = None,
                 group_id: Optional[str] = None,
                 port: Optional[str] = None,
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 device_control_topic: Optional[str] = None,
                 device_status_topic: Optional[str] = None,
                 redis_config: Optional[Dict[str, str]] = None):
        """Initialize the MQTT Cloud Client.
        
        Args:
            instance_id: MQTT实例ID，如果为None则从环境变量获取
            endpoint: MQTT服务端点，如果为None则从环境变量获取
            device_id: 设备ID，如果为None则从环境变量获取
            group_id: 组ID，如果为None则从环境变量获取
            port: 端口，如果为None则从环境变量获取
            access_key: 访问密钥，如果为None则从环境变量获取
            secret_key: 密钥，如果为None则从环境变量获取
            device_control_topic: 设备控制主题，如果为None则从环境变量获取
            device_status_topic: 设备状态主题，如果为None则从环境变量获取
            redis_config: Redis配置，如果为None则从环境变量获取
        """
        # Load configuration from environment variables if not provided
        self.instance_id = instance_id or os.getenv("MQTT_INSTANCE_ID")
        self.endpoint = endpoint or os.getenv("MQTT_ENDPOINT")
        self.device_id = device_id or os.getenv("MQTT_DEVICE_ID")
        self.group_id = group_id or os.getenv("MQTT_GROUP_ID")
        self.port = port or os.getenv("MQTT_PORT")
        self.access_key = access_key or os.getenv("MQTT_AK")
        self.secret_key = secret_key or os.getenv("MQTT_SK")
        
        # Topics
        self.device_control_topic = device_control_topic or os.getenv("MQTT_DEVICE_CONTROL_TOPIC", "device_control")
        self.device_status_topic = device_status_topic or os.getenv("MQTT_DEVICE_STATUS_TOPIC", "device_status")
        
        # Redis configuration
        self.redis_config = redis_config or {
            "host": os.getenv("REDIS_HOST"),
            "port": os.getenv("REDIS_PORT", "6379"),
            "db": os.getenv("REDIS_DB", "0"),
            "password": os.getenv("REDIS_PASSWORD")
        }
        
        # Create client ID from group ID and device ID
        self.client_id = f"{self.group_id}@@@{self.device_id}_cloud"
        
        # Initialize clients
        self.mqtt_client = None
        self.redis_client = None
        self.redis_pubsub = None
        self.pubsub_thread = None
        
        # Initialize state
        self.pending_requests = {}
        self.status_updates = []
        self.callbacks = {}
        self.long_running_tasks = {}
        self.redis_available = False
        
        # Initialize async callback handling
        self.async_callback_queue = []
        self.async_callback_lock = threading.Lock()
        self.async_callback_thread = None
        self.async_callback_thread_running = False
        
    def _start_async_callback_thread(self):
        """Start a dedicated thread for processing async callbacks."""
        if self.async_callback_thread is not None and self.async_callback_thread.is_alive():
            return
        
        self.async_callback_thread_running = True
        
        def async_callback_worker():
            """Worker function for the async callback thread."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            logger.info("Started async callback worker thread with dedicated event loop")
            
            try:
                while self.async_callback_thread_running:
                    with self.async_callback_lock:
                        if not self.async_callback_queue:
                            pass
                        else:
                            callback, payload, channel = self.async_callback_queue.pop(0)
                            try:
                                logger.info(f"Processing async callback{callback} for channel {channel} in dedicated thread")
                                task = loop.create_task(callback(payload))
                                self.long_running_tasks[channel] = task
                            except Exception as e:
                                logger.error(f"Error processing async callback for channel {channel}: {str(e)}")
                    time.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in async callback worker thread: {str(e)}")
            finally:
                loop.close()
                logger.info("Async callback worker thread stopped")
        
        self.async_callback_thread = threading.Thread(target=async_callback_worker)
        self.async_callback_thread.daemon = True
        self.async_callback_thread.start()
        
    def setup_redis(self) -> bool:
        """Set up the Redis client for pubsub.
        
        Returns:
            bool: True if Redis connection was successful, False otherwise
        """
        if not all(key in self.redis_config and self.redis_config[key] for key in ["host", "port", "password"]):
            logger.error("Missing required Redis configuration")
            return False
            
        try:
            redis_host = self.redis_config["host"].strip()
            redis_port = int(self.redis_config["port"].strip())
            redis_db = int(self.redis_config.get("db", "0").strip())
            
            logger.info(f"Connecting to Redis at {redis_host}:{redis_port}")
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                password=self.redis_config["password"],
                decode_responses=True,
                socket_connect_timeout=5.0,
                socket_timeout=5.0
            )
            
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            
            self.redis_pubsub = self.redis_client.pubsub()
            self.redis_available = True
            
            return True
        except Exception as e:
            logger.error(f"Error connecting to Redis: {str(e)}")
            return False
            
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the MQTT broker."""
        logger.info(f"Connected to MQTT broker with result code {rc}")
        client.subscribe(self.device_status_topic)
        logger.info(f"Subscribed to {self.device_status_topic}")
        
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received from the MQTT broker."""
        try:
            logger.info(f"Received status update on topic {msg.topic}: {msg.payload.decode()}")
            
            payload = json.loads(msg.payload.decode())
            request_id = payload.get("request_id")
            
            if request_id:
                if request_id in self.pending_requests:
                    self.pending_requests[request_id]["response"] = payload
                    self.pending_requests[request_id]["completed"] = True
                    
                redis_channel = f"{REDIS_STATUS_CHANNEL_PREFIX}{request_id}"
                if self.redis_available and self.redis_client:
                    try:
                        self.redis_client.publish(redis_channel, json.dumps(payload))
                        logger.info(f"Published status update to Redis channel {redis_channel}")
                    except Exception as e:
                        logger.error(f"Error publishing to Redis: {str(e)}")
                        
                if request_id in self.callbacks:
                    callback = self.callbacks[request_id]
                    if asyncio.iscoroutinefunction(callback):
                        with self.async_callback_lock:
                            self.async_callback_queue.append((callback, payload, redis_channel))
                    else:
                        try:
                            callback(payload)
                        except Exception as e:
                            logger.error(f"Error executing callback for request {request_id}: {str(e)}")
                            
            self.status_updates.append(payload)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the MQTT broker."""
        logger.info(f"Disconnected from MQTT broker with result code {rc}")
        
    def setup_mqtt_client(self):
        """Set up the MQTT client."""
        self.mqtt_client = mqtt.Client(
            client_id=self.client_id,
            protocol=mqtt.MQTTv311,
            clean_session=True
        )
        
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        
        try:
            self.mqtt_client.connect(self.endpoint, int(self.port), 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {str(e)}")
            
    def start(self):
        """Start the MQTT client and initialize connections."""
        self.setup_redis()
        self.setup_mqtt_client()
        self._start_async_callback_thread()
        
    def stop(self):
        """Stop the MQTT client and clean up resources."""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            
        if self.async_callback_thread:
            self.async_callback_thread_running = False
            self.async_callback_thread.join()
            
        if self.redis_pubsub:
            self.redis_pubsub.close()
            
        if self.redis_client:
            self.redis_client.close()
            
    def send_device_control(self, 
                          device_name: str, 
                          device_action: str, 
                          device_params: Optional[Dict[str, Any]] = None) -> str:
        """Send a device control message.
        
        Args:
            device_name: 设备名称
            device_action: 设备动作
            device_params: 设备参数
            
        Returns:
            str: 请求ID
        """
        request_id = str(uuid.uuid4())
        message = {
            "request_id": request_id,
            "device_name": device_name,
            "action": device_action,
            "params": device_params or {}
        }
        
        try:
            self.mqtt_client.publish(self.device_control_topic, json.dumps(message))
            self.pending_requests[request_id] = {
                "request": message,
                "response": None,
                "completed": False,
                "timestamp": time.time()
            }
            return request_id
        except Exception as e:
            logger.error(f"Error sending device control message: {str(e)}")
            return None
            
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get the status of a request.
        
        Args:
            request_id: 请求ID
            
        Returns:
            Dict[str, Any]: 请求状态
        """
        return self.pending_requests.get(request_id, {})
        
    def get_device_status(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent device status updates.
        
        Args:
            limit: 返回的状态更新数量
            
        Returns:
            List[Dict[str, Any]]: 状态更新列表
        """
        return self.status_updates[-limit:]
        
    def wait_for_status_update(self, request_id: str, timeout: float = 30.0) -> Dict[str, Any]:
        """Wait for a status update for a specific request.
        
        Args:
            request_id: 请求ID
            timeout: 超时时间（秒）
            
        Returns:
            Dict[str, Any]: 状态更新
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if request_id in self.pending_requests:
                request = self.pending_requests[request_id]
                if request["completed"]:
                    return request["response"]
            time.sleep(0.1)
        return {"error": "timeout"}
        
    def set_callback(self, 
                    request_id: str, 
                    callback: Union[Callable[[Dict[str, Any]], None], 
                                  Awaitable[None]]):
        """Set a callback for a specific request.
        
        Args:
            request_id: 请求ID
            callback: 回调函数
        """
        self.callbacks[request_id] = callback
        
    async def cleanup_old_requests(self):
        """Clean up old pending requests."""
        current_time = time.time()
        to_remove = []
        
        for request_id, request in self.pending_requests.items():
            if current_time - request["timestamp"] > 3600:  # 1 hour
                to_remove.append(request_id)
                
        for request_id in to_remove:
            del self.pending_requests[request_id]
            if request_id in self.callbacks:
                del self.callbacks[request_id]
            if request_id in self.long_running_tasks:
                del self.long_running_tasks[request_id]

_mqtt_cloud_instance = None

def get_mqtt_cloud_instance() -> MQTTCloud:
    """Get the global MQTT Cloud instance.
    
    Returns:
        MQTTCloud: 全局MQTT Cloud实例
    """
    global _mqtt_cloud_instance
    if _mqtt_cloud_instance is None:
        _mqtt_cloud_instance = MQTTCloud()
    return _mqtt_cloud_instance 