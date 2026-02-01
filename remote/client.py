import asyncio
import websockets
import json
import ssl
import os
from .config import settings
class WebOSClient:

    def __init__(self, tv_ip, client_key_file=settings.client_key):
        self.tv_ip = tv_ip
        self.uri = f"wss://{tv_ip}:3001"
        self.client_key = client_key_file
        self.ws = None
        self.request_id = 0  # Counter for unique IDs
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def connect(self):
        self.ws = await websockets.connect(self.uri, ping_interval=20, ping_timeout=20, ssl=self.ssl_context)
        print(f"Connected to {self.uri}!")

        # Register (with key if we have it)
        register_msg = {
            "type": "register",
            "id": "register_0",
            "payload": {
                "forcePairing": False,
                "pairingType": "PROMPT",
                "manifest": {  # Same as before, trimmed for space – paste full from prev code
                    # ... (the big manifest dict here)
                }
            }
        }
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
            if resp_dict.get("type") == "registered":
                if not self.client_key:  # Save new key
                    self.client_key = resp_dict["payload"].get("client-key")
                    with open('client_key.txt', 'w') as f:
                        f.write(self.client_key)
                    print(f"🎉 Saved new key to client_key.txt: {self.client_key}")
                break
            elif resp_dict.get("type") == "error":
                print("Error:", resp_dict)
                raise Exception("Register failed")

    async def send_command(self, uri, payload=None, subscribe=False):
        self.request_id += 1
        msg_type = "subscribe" if subscribe else "request"
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
            print("ID mismatch! Ignoring.")
            return None
        if resp_dict.get("type") == "error":
            print("Error:", resp_dict)
            return None
        return resp_dict.get("payload", resp_dict)  # Return data

    async def close(self):
        if self.ws:
            await self.ws.close()