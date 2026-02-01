import asyncio
import websockets
import json
import ssl

async def hello_tv():
    TV_IP = "192.168.0.5"
    uri = f"wss://{TV_IP}:3001"

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with websockets.connect(uri, ping_interval=20, ping_timeout=20, ssl=ssl_context) as ws:
            print(f"Connected to {uri}! (cert ignored)")

            # The "register" handshake JSON (initial "hello" + pairing request)
            # No client-key yet (first time) → TV will prompt on screen
            # Manifest: Our "app permissions" – keep as is, it's standard from LG examples
            register_msg = {
                "type": "register",
                "id": "register_0",  # Unique ID for this message
                "payload": {
                    "forcePairing": False,  # Don't force if already paired (but we aren't)
                    "pairingType": "PROMPT",  # Show popup on TV
                    "manifest": {
                        "manifestVersion": 1,
                        "appVersion": "1.1",
                        "signed": {
                            "created": "20140509",
                            "appId": "com.lge.test",
                            "vendorId": "com.lge",
                            "localizedAppNames": {
                                "": "LG Remote App",
                                "ko-KR": "LG ????",
                                "zxx-XX": "?? R??ot? A??"
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
                                "READ_TV_CURRENT_TIME"
                            ],
                            "serial": "2f930e2d2cfe083771f68e4fe7bb07"
                        },
                        "permissions": [
                            "LAUNCH", "LAUNCH_WEBAPP", "APP_TO_APP", "CLOSE", "TEST_OPEN",
                            "TEST_PROTECTED", "CONTROL_AUDIO", "CONTROL_DISPLAY",
                            "CONTROL_INPUT_JOYSTICK", "CONTROL_INPUT_MEDIA_RECORDING",
                            "CONTROL_INPUT_MEDIA_PLAYBACK", "CONTROL_INPUT_TV",
                            "CONTROL_POWER", "READ_APP_STATUS", "READ_CURRENT_CHANNEL",
                            "READ_INPUT_DEVICE_LIST", "READ_NETWORK_STATE", "READ_RUNNING_APPS",
                            "READ_TV_CHANNEL_LIST", "WRITE_NOTIFICATION_TOAST",
                            "READ_POWER_STATE", "READ_COUNTRY_INFO"
                        ],
                        "signatures": [
                            {
                                "signatureVersion": 1,
                                "signature": "eyJhbGdvcml0aG0iOiJSU0EtU0hBMjU2Iiwia2V5SWQiOiJ0ZXN0LXNpZ25pbmctY2VydCIsInNpZ25hdHVyZVZlcnNpb24iOjF9.hrVRgjCwXVvE2OOSpDZ58hR+59aFNwYDyjQgKk3auukd7pcegmE2CzPCa0bJ0ZsRAcKkCTJrWo5iDzNhMBWRyaMOv5zWSrthlf7G128qvIlpMT0YNY+n/FaOHE73uLrS/g7swl3/qH/BGFG2Hu4RlL48eb3lLKqTt2xKHdCs6Cd4RMfJPYnzgvI4BNrFUKsjkcu+WD4OO2A27Pq1n50cMchmcaXadJhGrOqH5YmHdOCj5NSHzJYrsW0HPlpuAx/ECMeIZYDh6RMqaFM2DXzdKX9NmmyqzJ3o/0lkk/N97gfVRLW5hA29yeAwaCViZNCP8iC9aO0q9fQojoa7NQnAtw=="
                            }
                        ]
                    }
                }
            }

            # Send it!
            await ws.send(json.dumps(register_msg))
            print("Sent register handshake! Check TV screen for prompt – click 'Allow' with remote.")

            # Wait for response (TV might send multiple, but look for "registered")
            while True:  # Loop to handle responses (we'll refactor later)
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=30.0)
                    print("TV replied:", response)
                    resp_dict = json.loads(response)
                    if resp_dict.get("type") == "registered":
                        client_key = resp_dict["payload"].get("client-key")
                        if client_key:
                            print(f"Paired! Client key: {client_key}")
                            print("Save this key (e.g., in a file) for next time – add to payload['client-key'] to skip prompt.")
                            break  # Done for now
                except asyncio.TimeoutError:
                    print("No response yet – waiting... (give TV time to prompt/respond)")

    except Exception as e:
        print("Failed", e)

asyncio.run(hello_tv())