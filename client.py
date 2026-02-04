import websockets,json,ssl,os
from dotenv import set_key, find_dotenv
from config import settings
from register_payload import register_msg

class WebOSClient:

    def __init__(self,tv_ip,client_key_file=settings.client_key):
        self.tv_ip = tv_ip                # tv ip address
        #  the WebOs LG TV is listening on wss on 3001 port
        # so we will be sending a websocket request to the TV
        self.uri = f"wss://{tv_ip}:3001"   # url to connect
        self.client_key = client_key_file  # load client key from '.env'
        self.ws = None                     # currently we aren't connected so None
        self.request_id = 0                # Counter for unique ID's
        # rewriting SSL, in simple words we are telling the TV 
        # you can trust me and return the client-token and permit me to control you
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    # used to save the client-key to the .env dynamically
    def save_client_key(self,new_key: str):
        """Update or add CLIENT_KEY to .env using python-dotenv"""
        dotenv_path = find_dotenv(usecwd=True)  # Finds .env in current dir or parents
        if not dotenv_path:
            dotenv_path = os.path.join(os.getcwd(), ".env")
            # Create empty .env if missing
            open(dotenv_path, 'a').close()

        # set_key returns (success, key, old_value)
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
            settings.client_key = new_key  # if you want settings obj updated
        else:
            print("Failed to update .env – check permissions or path")
            
    # connection method used intially to connect to the TV
    async def connect(self):
        self.ws = await websockets.connect(self.uri, ping_interval=20, ping_timeout=20, ssl=self.ssl_context)
        print(f"Connected to {self.uri}!")

        # Register (with key if we have it)
        
        if self.client_key:
            register_msg["payload"]["client-key"] = self.client_key
            print("Using saved client-key – no prompt!")

        await self.ws.send(json.dumps(register_msg))
        print("Sent register!")

        # Handle responses until registered
        while True:
            resp = await self.ws.recv()
            resp_dict = json.loads(resp)
            print("TV:", resp)
            # if TV permits you this case is hit
            if resp_dict.get("type") == "registered":
                client_key=resp_dict["payload"].get("client-key")
                if client_key and self.client_key != client_key:  # Save new key
                    new_key=client_key
                    self.save_client_key(new_key=new_key)
                break
            # check the register_msg ,TV ip, port and the returned error message
            elif resp_dict.get("type") == "error":
                print("Error:", resp_dict)
                raise Exception("Register failed")
    # used to send commands to TV
    async def send_command(self,uri,payload=None):
        self.request_id += 1
        msg_type = "request"
        msg = {
            "type": msg_type,
            "id": f"cmd_{self.request_id}",
            "uri": uri,
            "payload": payload or {}
        }
        await self.ws.send(json.dumps(msg))
        print(f"Sent {msg_type} to {uri}")

        # Wait for response
        resp = await self.ws.recv()
        resp_dict = json.loads(resp)

        if resp_dict.get("id") != msg["id"]:
            print("ID mismatch!")
            return None
        
        if resp_dict.get("type") == "error":
            print("That's an Error:",resp_dict)
            return None
        
        print(f"PayLoad of the Above Response From TV {resp_dict.get("payload",resp_dict)}")
        return resp_dict.get("payload",resp_dict)  # Return data
    
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
    
    # close the socket Gracefully
    async def close(self):
        if self.ws:
            print("Bye byee Socket Closing")
            await self.ws.close()