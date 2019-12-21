# Socket-based Instant Messaging System (Python)

### Features
* Low latency (with multi-threading and multi-processing)
* RSA and AES encryption for messaging
* Multi-client instant voice chat
* Support for adding friends and offline messaging

### Dependence
* Software Dependence
  *MySQL
* Python Package Dependence
  *Python Driver for MySQL (Connector/Python), PyQt5, rsa, cryptography, pyaudio.

### Preparation
1. Create two datebase in MySQL `login_data` and `message_data` as the following image shows.
![MySQL Database](https://github.com/youweiliang/Instant-Messaging/blob/master/MySQL_Database.png)

2. Configure the username and password of MySQL in `IM_server.py`, and configure  the server IP and port in `IM_server.py` and `Client.py`.

3. (Optional) Configure `VOICEPORT` for voise transmission in `recv_voice.py` and `send_voice.py`.

4. (Optional) Configure `RECV_PORT` and `SEND_PORT` for file transmission in `file_transfer.py`.

### Example Usage
1. Start server in local machine: `python IM_server,py`.
2. Start clients in user PC: `python IM_client.py`.
3. Have fun!
