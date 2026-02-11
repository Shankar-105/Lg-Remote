import asyncio
import websockets
import json
import ssl
import os
from dotenv import set_key, find_dotenv
from config import settings

class WebOSClient:

    def __init__(self, tv_ip, client_key=settings.client_key):
        self.tv_ip = tv_ip
        self.uri = f"wss://{tv_ip}:3001"
        self.client_key = client_key
        self.ws = None
        self.input_ws = None
        self.request_id = 0
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def save_client_key(self, new_key: str):
        dotenv_path = find_dotenv(usecwd=True)
        if not dotenv_path:
            dotenv_path = os.path.join(os.getcwd(), ".env")
            open(dotenv_path, 'a').close()

        success, key, old = set_key(
            dotenv_path=dotenv_path,
            key_to_set="CLIENT_KEY",
            value_to_set=new_key,
            quote_mode="always",
            export=False
        )
        if success:
            print(f"Updated CLIENT_KEY in .env → {new_key}")
            self.client_key = new_key
            settings.client_key = new_key
        else:
            print("Failed to update .env – check permissions or path")

    async def connect(self, force_repair=False):
        self.ws = await websockets.connect(self.uri, ping_interval=600, ping_timeout=600, ssl=self.ssl_context)
        print(f"Connected to {self.uri}!")

        register_payload = {
            "forcePairing": force_repair or not self.client_key,
            "pairingType": "PROMPT",
            "manifest": {
                "appVersion": "1.1",
                "manifestVersion": 1,
                "permissions": [  
                    "LAUNCH",
                    "LAUNCH_WEBAPP",
                    "APP_TO_APP",
                    "CLOSE",
                    "TEST_OPEN",
                    "TEST_PROTECTED",
                    "CONTROL_AUDIO",
                    "CONTROL_DISPLAY",
                    "CONTROL_INPUT_JOYSTICK",
                    "CONTROL_INPUT_MEDIA_RECORDING",
                    "CONTROL_INPUT_MEDIA_PLAYBACK",
                    "CONTROL_INPUT_TV",
                    "CONTROL_POWER",
                    "CONTROL_TV_SCREEN",
                    "READ_APP_STATUS",
                    "READ_CURRENT_CHANNEL",
                    "READ_INPUT_DEVICE_LIST",
                    "READ_NETWORK_STATE",
                    "READ_RUNNING_APPS",
                    "READ_TV_CHANNEL_LIST",
                    "WRITE_NOTIFICATION_TOAST",
                    "READ_POWER_STATE",
                    "READ_COUNTRY_INFO",
                    "CONTROL_INPUT_TEXT",
                    "CONTROL_MOUSE_AND_KEYBOARD",  
                    "READ_INSTALLED_APPS",
                    "READ_SETTINGS",
                    "READ_STORAGE_DEVICE_LIST",
                ],
                "signatures": [
                    {
                        "signature": (
                            "eyJhbGdvcml0aG0iOiJSU0EtU0hBMjU2Iiwia2V5SWQiOiJ0ZXN0LXNpZ25p"
                            "bmctY2VydCIsInNpZ25hdHVyZVZlcnNpb24iOjF9.hrVRgjCwXVvE2OOSpDZ"
                            "58hR+59aFNwYDyjQgKk3auukd7pcegmE2CzPCa0bJ0ZsRAcKkCTJrWo5iDz"
                            "NhMBWRyaMOv5zWSrthlf7G128qvIlpMT0YNY+n/FaOHE73uLrS/g7swl3/q"
                            "H/BGFG2Hu4RlL48eb3lLKqTt2xKHdCs6Cd4RMfJPYnzgvI4BNrFUKsjkcu+W"
                            "D4OO2A27Pq1n50cMchmcaXadJhGrOqH5YmHdOCj5NSHzJYrsW0HPlpuAx/ECM"
                            "eIZYDh6RMqaFM2DXzdKX9NmmyqzJ3o/0lkk/N97gfVRLW5hA29yeAwaCViZN"
                            "CP8iC9aO0q9fQojoa7NQnAtw=="
                        ),
                        "signatureVersion": 1,
                    }
                ],
                "signed": {
                    "appId": "com.lge.test",
                    "created": "20140509",
                    "localizedAppNames": {
                        "": "LG Remote App",
                        "ko-KR": "리모컨 앱",
                        "zxx-XX": "ЛГ Rэмotэ AПП",
                    },
                    "localizedVendorNames": {"": "LG Electronics"},
                    "permissions": [
                        "TEST_SECURE",
                        "CONTROL_INPUT_TEXT",
                        "CONTROL_MOUSE_AND_KEYBOARD",
                        "READ_INSTALLED_APPS",
                        "READ_LGE_SDX",
                        "READ_NOTIFICATIONS",
                        "SEARCH",
                        "WRITE_SETTINGS",
                        "WRITE_NOTIFICATION_ALERT",
                        "CONTROL_POWER",
                        "READ_CURRENT_CHANNEL",
                        "READ_RUNNING_APPS",
                        "READ_UPDATE_INFO",
                        "UPDATE_FROM_REMOTE_APP",
                        "READ_LGE_TV_INPUT_EVENTS",
                        "READ_TV_CURRENT_TIME",
                    ],
                    "serial": "2f930e2d2cfe083771f68e4fe7bb07",
                    "vendorId": "com.lge",
                },
            },
        }

        if self.client_key and not force_repair:
            register_payload["client-key"] = self.client_key
            print("Using saved client-key")
        else:
            print("Forcing pairing prompt - ACCEPT ON TV WITH REMOTE!")

        register_msg = {
            "type": "register",
            "id": "register_0",
            "payload": register_payload
        }

        await self.ws.send(json.dumps(register_msg))
        print("Sent register!")

        while True:
            resp = await self.ws.recv()
            resp_dict = json.loads(resp)
            print("TV:", resp)
            if resp_dict.get("type") == "registered":
                client_key = resp_dict["payload"].get("client-key")
                if client_key and self.client_key != client_key:
                    self.save_client_key(client_key)
                print("Registered successfully!")
                break
            elif resp_dict.get("type") == "error":
                print("Error:", resp_dict)
                if "permissions" in str(resp_dict).lower():
                    raise PermissionError("Permissions error - clear TV pairings (Settings > Devices > External Devices > Remove all), reboot TV, then run with force_repair=True")
                raise Exception("Register failed")

    async def send_command(self, uri, payload=None):
        self.request_id += 1
        msg = {
            "type": "request",
            "id": f"cmd_{self.request_id}",
            "uri": uri,
            "payload": payload or {}
        }
        await self.ws.send(json.dumps(msg))
        print(f"Sent request to {uri}")

        resp = await self.ws.recv()
        resp_dict = json.loads(resp)
        print(f"Response: {resp_dict}")

        if resp_dict.get("id") != msg["id"]:
            print("ID mismatch!")
            return None
        if resp_dict.get("type") == "error":
            print("TV Error:", resp_dict)
            if "permissions" in str(resp_dict).lower():
                raise PermissionError(f"Insufficient permissions for {uri}")
            return None
        print(f"Payload: {resp_dict.get('payload', resp_dict)}")
        return resp_dict.get("payload", resp_dict)

    # AUDIO RELATED ENDPOINTS
    async def get_mute(self):
        return await self.send_command("ssap://audio/getMute")

    async def set_mute(self, mute: bool = True):
        return await self.send_command("ssap://audio/setMute", {"mute": mute})

    async def get_volume(self):
        return await self.send_command("ssap://audio/getVolume")

    async def set_volume(self, volume: int = 20):  # 0-100 typically
        if not 0 <= volume <= 100:
            raise ValueError("Volume must be 0-100")
        return await self.send_command("ssap://audio/setVolume", {"volume": volume})

    async def volume_up(self):
        return await self.send_command("ssap://audio/volumeUp")

    async def volume_down(self):
        return await self.send_command("ssap://audio/volumeDown")

    async def get_audio_status(self):
        return await self.send_command("ssap://audio/getStatus")
    
    # OPEN APPS
    async def list_apps(self):
        return await self.send_command("ssap://com.webos.applicationManager/listApps")

    async def list_launch_points(self):
        return await self.send_command("ssap://com.webos.applicationManager/listLaunchPoints")

    async def get_foreground_app(self):
        return await self.send_command("ssap://com.webos.applicationManager/getForegroundAppInfo")

    async def launch_app(self, app_id: str, params: dict = None):
        payload = {"id": app_id}
        if params:
            payload["params"] = params
        return await self.send_command("ssap://system.launcher/launch", payload)

    # Convenience shortcuts
    async def launch_netflix(self):     return await self.launch_app("netflix")
    async def launch_youtube(self):     return await self.launch_app("youtube.leanback.v4")
    async def launch_prime_video(self): return await self.launch_app("amazon")
    async def launch_jio_hotstar(self): return await self.launch_app("jiohotstar")
    # TV / CHANNELS
    # use this to get channelId
    async def get_channel_list(self):             
        return await self.send_command("ssap://tv/getChannelList")     
    async def get_current_channel(self):            
        return await self.send_command("ssap://tv/getCurrentChannel")
    async def open_channel(self, channel_id: str): 
        return await self.send_command("ssap://tv/openChannel", {"channelId": channel_id})
    async def channel_up(self):                   
        return await self.send_command("ssap://tv/channelUp")
    async def channel_down(self):                  
        return await self.send_command("ssap://tv/channelDown")
    async def get_external_inputs(self):           
        return await self.send_command("ssap://tv/getExternalInputList")
    async def switch_input(self, input_id: str):   
        return await self.send_command("ssap://tv/switchInput", {"inputId": input_id})  # "HDMI1", "AV1" etc.
    
    # MEDIA CONTROL
    async def media_play(self):                  
        return await self.send_command("ssap://media.controls/play")
    async def media_pause(self):                  
        return await self.send_command("ssap://media.controls/pause")
    async def media_stop(self):                  
        return await self.send_command("ssap://media.controls/stop")
    async def media_rewind(self):               
        return await self.send_command("ssap://media.controls/rewind")
    async def media_fast_forward(self):         
        return await self.send_command("ssap://media.controls/fastForward")
    
    # SYSTEM / POWER
    async def power_off(self):                    
        return await self.send_command("ssap://system/turnOff")
    async def get_system_info(self):     
        return await self.send_command("ssap://system/getSystemInfo")
    async def get_power_state(self):      
        return await self.send_command("ssap://com.webos.service.tvpower/power/getPowerState")
    async def turn_off_screen(self):      
        return await self.send_command("ssap://com.webos.service.tvpower/power/turnOffScreen")
    async def turn_on_screen(self):       
        return await self.send_command("ssap://com.webos.service.tvpower/power/turnOnScreen")
    
    async def connect_input(self):
        """Get and connect to the pointer/input websocket."""
        if self.input_ws:
            print("Input socket already connected!")
            return

        response = await self.send_command("ssap://com.webos.service.networkinput/getPointerInputSocket")
        if not response or "socketPath" not in response:
            raise Exception("Failed to get input socket path")
        
        sock_path = response["socketPath"]
        print(f"Got input socket: {sock_path}")

        self.input_ws = await websockets.connect(sock_path, ping_interval=600, ping_timeout=600, ssl=self.ssl_context)
        print(f"Connected to input socket {sock_path}!")

    async def disconnect_input(self):
        """Close the input websocket."""
        if self.input_ws:
            await self.input_ws.close()
            self.input_ws = None
            print("Input socket closed.")

    async def _send_input_button(self, button_name: str):
        """Internal helper to send a button over input ws."""
        if not self.input_ws:
            await self.connect_input()  # Auto-connect if needed
        
        payload = f"type:button\nname:{button_name}\n\n"
        await self.input_ws.send(payload)
        print(f"Sent button: {button_name}")

    # NAVIGATION / CURSOR CONTROL (for apps like YouTube)
    async def cursor_up(self):
        await self._send_input_button("UP")
    
    async def cursor_down(self):
        await self._send_input_button("DOWN")
    
    async def cursor_left(self):
        await self._send_input_button("LEFT")
    
    async def cursor_right(self):
        await self._send_input_button("RIGHT")
    
    async def cursor_click(self):
        await self._send_input_button("ENTER")
    
    async def cursor_back(self):
        await self._send_input_button("BACK")
    
    async def go_home(self):
        await self._send_input_button("HOME")
    
    # close the socket Gracefully
    async def close(self):
        await self.disconnect_input()
        if self.ws:
            print("Bye byee Socket Closing")
            await self.ws.close()