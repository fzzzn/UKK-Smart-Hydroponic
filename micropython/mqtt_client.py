from umqtt.simple import MQTTClient
import ujson
import time
import ubinascii

class MQTTClientWrapper:
    def __init__(self, config, callback):
        self.config = config
        self.callback = callback
        self.client = None
        self.last_reconnect_attempt = 0
        self.reconnect_interval = 5000

    def connect(self):
        client_id = 'Fauzan-Hydroponic-' + ubinascii.hexlify(self.config['server'].encode())[:8].decode()

        try:
            self.client = MQTTClient(
                client_id,
                self.config['server'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                keepalive=60
            )
            self.client.set_callback(self._on_message)
            self.client.connect()
            self._subscribe_topics()
            print("MQTT connected")
            return True
        except Exception as e:
            print("MQTT connect error:", e)
            return False

    def _subscribe_topics(self):
        topics = self.config['topics']
        self.client.subscribe(topics['mode'])
        self.client.subscribe(topics['relay'])

    def _on_message(self, topic, msg):
        topic_str = topic.decode('utf-8')
        message = msg.decode('utf-8').lower()
        self.callback(topic_str, message)

    def is_connected(self):
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    def reconnect(self):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_reconnect_attempt) < self.reconnect_interval:
            return False

        self.last_reconnect_attempt = current_time
        print("Attempting MQTT reconnect...")

        try:
            self.client.disconnect()
        except:
            pass

        return self.connect()

    def check_msg(self):
        if self.is_connected():
            try:
                self.client.check_msg()
            except Exception as e:
                print("MQTT check_msg error:", e)

    def publish_status(self, data):
        if not self.is_connected():
            return False

        try:
            payload = ujson.dumps(data)
            self.client.publish(self.config['topics']['status'], payload)
            return True
        except Exception as e:
            print("MQTT publish error:", e)
            return False
