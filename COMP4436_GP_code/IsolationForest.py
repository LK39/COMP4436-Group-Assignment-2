import pandas as pd
import requests
from sklearn.ensemble import IsolationForest
import time
import matplotlib.pyplot as plt

class RealTimeIsolationForest:
    def __init__(self, api_url):
        self.api_url = api_url
        self.model = IsolationForest()
        self.data = pd.DataFrame()  
        self.fetch_all_data()  
        self.previous_anomaly_count = 0 
        self.anomalies_recorded = [] 

    def fetch_all_data(self):
        response = requests.get(self.api_url)
        json_data = response.json()
        feeds = json_data.get("feeds", [])
        self.data = pd.DataFrame(feeds)
        self.preprocess_data(self.data)
        self.train_model()  

    def preprocess_data(self, df):
        
        df['field1'] = pd.to_numeric(df['field1'], errors='coerce')  # Temperature
        df['field2'] = pd.to_numeric(df['field2'], errors='coerce')  # Humidity
        df['field3'] = pd.to_numeric(df['field3'], errors='coerce')  # Sound
        df['field4'] = pd.to_numeric(df['field4'], errors='coerce')  # Light
        
        # Drop NaN values
        self.data = df[['field1', 'field2', 'field3', 'field4']].dropna()

    def train_model(self):
        if not self.data.empty:
            self.model.fit(self.data)

    def detect_anomalies(self):
        if not self.data.empty:
            predictions = self.model.predict(self.data)
            # Check for anomalies (-1 indicates anomaly)
            anomalies = self.data[predictions == -1]
            current_anomaly_count = len(anomalies)

            #MQTT must go here
            if current_anomaly_count > self.previous_anomaly_count:
                print(1)  # More anomalies detected
            else:
                print(0)  # No anomalies or less detected

            # Update the previous anomaly count
            self.previous_anomaly_count = current_anomaly_count

            # Store
            self.anomalies_recorded.append(anomalies)

    def plot_anomalies(self):
        # Combine all recorded anomalies into a single DataFrame
        all_anomalies = pd.concat(self.anomalies_recorded)
        
        plt.figure(figsize=(12, 10))

        # Subplot for Temperature
        plt.subplot(2, 2, 1)
        plt.scatter(self.data.index, self.data['field1'], color='blue', label='Normal Data', alpha=0.5)
        plt.scatter(all_anomalies.index, all_anomalies['field1'], color='red', label='Anomalies', alpha=0.8)
        plt.title('Temperature Anomalies')
        plt.xlabel('Data Point Index')
        plt.ylabel('Temperature')
        plt.legend()
        plt.grid()

        # Subplot for Humidity
        plt.subplot(2, 2, 2)
        plt.scatter(self.data.index, self.data['field2'], color='blue', label='Normal Data', alpha=0.5)
        plt.scatter(all_anomalies.index, all_anomalies['field2'], color='red', label='Anomalies', alpha=0.8)
        plt.title('Humidity Anomalies')
        plt.xlabel('Data Point Index')
        plt.ylabel('Humidity')
        plt.legend()
        plt.grid()

        # Subplot for Sound
        plt.subplot(2, 2, 3)
        plt.scatter(self.data.index, self.data['field3'], color='blue', label='Normal Data', alpha=0.5)
        plt.scatter(all_anomalies.index, all_anomalies['field3'], color='red', label='Anomalies', alpha=0.8)
        plt.title('Sound Anomalies')
        plt.xlabel('Data Point Index')
        plt.ylabel('Sound')
        plt.legend()
        plt.grid()

        # Subplot for Light
        plt.subplot(2, 2, 4)
        plt.scatter(self.data.index, self.data['field4'], color='blue', label='Normal Data', alpha=0.5)
        plt.scatter(all_anomalies.index, all_anomalies['field4'], color='red', label='Anomalies', alpha=0.8)
        plt.title('Light Anomalies')
        plt.xlabel('Data Point Index')
        plt.ylabel('Light')
        plt.legend()
        plt.grid()

        plt.tight_layout()
        plt.show()

    def run(self):
        try:
            while True:
                self.detect_anomalies()
                time.sleep(20)  
        except KeyboardInterrupt:
            print("Stopping anomaly detection.")
            self.plot_anomalies()  # Plot anomalies when stopping the detection

# Example usage 
if __name__ == "__main__":
    api_url = "https://api.thingspeak.com/channels/2920657/feeds.json?api_key=GTDM3TTFE1THM92Z"
    
    real_time_if = RealTimeIsolationForest(api_url)
    real_time_if.run()