# 📺 WebOS LG TV Remote Control Console Simulator

## 🚀 Overview

The **WebOS LG TV Remote Control Console Simulator** is an interactive command-line tool that allows you to control your LG WebOS television over a local network. Instead of using a physical remote, you can control various aspects of your TV—such as launching applications, adjusting volume, navigating menus, and controlling playback—directly from your computer.

This tool leverages the **WebSocket protocol** and provides a user-friendly menu-driven interface, making it easy to interact with your television without needing deep technical knowledge of WebOS APIs.

## 🛠️ How to Use the Console Simulator

Follow these steps to set up and start controlling your TV:

### 1. Initial Setup (Crucial)
Before running the script, you must prepare your environment:
*   **Rename the configuration file**: Locate `.env.sample` in the root directory and rename it to **`.env`**.
*   This file is essential for storing your unique **Client Key**, which allows the TV to trust your computer for future connections.

### 2. First-Time Connection & Pairing
*   **Start the Application**: Navigate to the project directory and run `python main.py`.
*   **Approval Prompt**: Since it's your first time, a prompt will appear on your **TV screen** asking for permission.
*   **Click "Yes"**: Use your physical remote to select **"Yes"** or **"Allow"** on the TV.
*   **Automatic Saving**: Once approved, the TV generates a Client Key. Our script automatically captures this key and saves it into your `.env` file. You won't need to pair again!

### 3. Using the Simulator
Once connected, you can navigate the menu-driven system:
*   **Select a Category**: Choose from Audio, Applications, Channels/Inputs, Media, or System (1-5).
*   **Execute Commands**: Pick a specific operation by entering its number.
*   **Interactive Inputs**: For actions like "Set Volume," simply follow the text prompts to enter a value.
*   **Navigation**: Use the improved **Navigation controls** (Up, Down, Left, Right, OK, Back) to browse through apps like YouTube or Netflix.

## 🏗️ Device Discovery and Connection Architecture

### 🔍 How the TV is Discovered
The discovery process utilizes the **Universal Plug and Play (UPnP)** protocol. When the script starts, it broadcasts a multicast request to `239.255.255.250` on port `1900`. 

Your LG TV listens for these requests and responds with its **IP address** and identifying metadata. This "zero-config" approach means you don't need to manually find or type in your TV's IP address—the tool handles it all automatically over your Wi-Fi network.

### 🔌 Connection and Dual-Socket Operations
The script establishes a secure WebSocket connection (WSS) on port `3001`. This primary channel handles most tasks like app launching and volume control.

However, for **Input Operations** (cursor movement, button presses), the TV requires a specialized connection. The simulator automatically manages a **dedicated input socket** for these real-time actions, ensuring that navigation is snappy and responsive. The transition between these sockets is handled seamlessly behind the scenes.

---

## 🙏 Thank You

I would like to extend my heartfelt gratitude to everyone who has taken the time to explore and use this WebOS LG TV Remote Control Console Simulator. Creating this tool has been a rewarding journey, and I hope it brings convenience to your viewing experience. 🌟

This project demonstrates the power of open protocols and how they can be leveraged to build intuitive bridges between your devices. Thank you for your interest and support! 🚀

**M Bhavani Shankar**

