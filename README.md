# COMP4436-Group-Assignment-2

![Screenshot 2025-04-23 234643](https://github.com/user-attachments/assets/745965d7-39c0-42ec-91f8-0cf9424c1dac)

# Smart Home System: A Comprehensive IoT Implementation

## $${\color{red}IMPORTANT}$$

Our **web interface** could be accessed via this link: http://158.132.154.210:5000/ Our server is kept on for now and you can access it via the $${\color{red}PolyU}$$ $${\color{red}WiFi}$$ $${\color{red}Networks}$$.
Note that to turn on the system, you just need to click power and see $${\color{green}green}$$ words $${\color{green}"ON"}$$.

![image](https://github.com/user-attachments/assets/27254c8f-5577-42ba-9c95-7a40affa78c7)

We also have a **Grafana Interface** for Admin Monitoring Dashboard and AI Predictions. 

![image](https://github.com/user-attachments/assets/47ff5aeb-0198-4b57-b498-d4f34474c1e7)


## Introduction

Our project implements a sophisticated Smart Home System that integrates various sensors, data processing technologies, and notification systems to create an intelligent home environment. The system architecture combines hardware components, communication protocols, and advanced analytics to monitor and automate home functions.

## Key Components

### Hardware Infrastructure
- **Sensors**: DHT11 (temperature/humidity), LDR (light), sound sensors, and cameras for environmental monitoring
- **Processing Units**: Raspberry Pi as the central controller, ESP32 for edge computing, and M5StickCPlus2 for device simulation
- **Communication**: Local server managing data flow between components

### Data Management
- **MQTT Protocol**: Facilitates lightweight communication between IoT devices
- **InfluxDB**: Time-series database storing sensor readings for analysis
- **Grafana Dashboard**: Visualization platform for real-time monitoring

### Intelligent Processing
- **Time Series Analysis**: ARIMA and LSTM models for trend prediction
- **Anomaly Detection**: Isolation Trees to identify unusual patterns
- **Object Detection**: Computer vision for camera feeds
- **Node-red**: For visual programming and workflow automation

### User Interface
- **Centralized Web Interface**: Single access point for system control
- **ThingSpeak Integration**: Cloud platform for IoT analytics
- **WhatsApp Notifications**: Real-time alerts for important events

## Technical Innovations

Our implementation distinguishes itself through the seamless integration of edge computing with cloud analytics, creating a hybrid system that balances local processing with powerful backend analysis. The architecture supports both real-time monitoring and long-term trend analysis, providing immediate responses to environmental changes while building intelligence through data accumulation.
