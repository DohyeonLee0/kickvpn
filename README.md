<p align="center">
  <img src="https://raw.githubusercontent.com/DohyeonLee0/kickvpn/main/assets/banner.png" alt="KickVPN Banner" width="100%">
</p>
# KickVPN

> 🧠 This VPN project was co-developed with **ChatGPT**, used as an assistant for system design, backend logic, networking, and full-stack coding.

KickVPN is a fully functional VPN MVP (Minimum Viable Product) designed for real-world usage. It includes user authentication, proxy-based traffic routing, traffic metering, a GUI client, and a reward system.

---

## 🚀 Features

- ✅ User Authentication (JWT-based)
- ✅ Traffic Proxy Server (HTTP CONNECT support)
- ✅ Traffic Limiting per User
- ✅ Premium/Free Server System
- ✅ Reward Code System (+MB rewards)
- ✅ VPN GUI Client App (Python + CustomTkinter)
- ✅ Traffic Log Storage & Viewer
- ✅ System Proxy Configuration for IP tunneling
- ✅ Deployable on VPS for real IP changing

---

## 📂 Project Structure

```
kickvpn/
├── vpn_gui_client.py
├── relay_proxy_server.py
├── traffic_log_api.py
├── vpn_users.db
├── README.md
└── requirements.txt
```

---

## 🧪 How to Run (Local Test)

```bash
pip install fastapi uvicorn python-jose[cryptography] passlib[bcrypt] pydantic requests customtkinter
python3 traffic_log_api.py
python3 relay_proxy_server.py
python3 vpn_gui_client.py
```

Then set system proxy (macOS example):

```bash
sudo networksetup -setwebproxy Wi-Fi 127.0.0.1 9001
sudo networksetup -setsecurewebproxy Wi-Fi 127.0.0.1 9001
```

Go to [https://whatismyipaddress.com](https://whatismyipaddress.com) to check IP.

---

## 📌 Notes

- This project was developed in collaboration with GPT as an AI development partner.
- All networking code, GUI logic, and backend systems were built using AI-assisted guidance.
- Designed for educational and prototyping use, not production-ready yet.

---
