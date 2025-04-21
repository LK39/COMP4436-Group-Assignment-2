from LSTM import LSTMModel
import torch
import numpy as np
import pandas as pd
import requests
from sklearn.preprocessing import MinMaxScaler
from datetime import timedelta

class AI_Prediction:
    def __init__(self,input_size,hidden_size,num_layers,output_size,device,model_path):
        self.sequence_length = 60

        self.device = device

        self.model = LSTMModel(input_size, hidden_size, num_layers, output_size, self.device)

        self.model.load_state_dict(torch.load(model_path))

        self.model.to(self.device)

        self.features = ['Temperature', 'Humidity', 'Light']

    

    # Function to forecast future values
    def _forecast_future(self, current_sequence, steps=60):
        self.model.eval()
        
        future_predictions = []
        
        with torch.no_grad():
            for _ in range(steps):
                # Convert to tensor
                seq_tensor = torch.tensor(current_sequence, dtype=torch.float32).unsqueeze(0).to(self.device)
                
                # Predict next step
                model_output = self.model(seq_tensor)
                next_step = model_output.cpu().numpy()[0]
                
                # Append to results
                future_predictions.append(next_step)
                
                # Update sequence by removing first step and adding the predicted step
                current_sequence = np.append(current_sequence[1:], [next_step], axis=0)
        
        return np.array(future_predictions)
    
    def _get_thingspeak_data(self, channel_id, read_api_key, results=120):
        url = f'https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_api_key}&results={results}'
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            feeds = data['feeds']

            # Create DataFrame from feeds
            df = pd.DataFrame(feeds)
            
            # Select only fields 1, 2, and 4 and convert to float
            selected_fields = ['field1', 'field2', 'field4']
            for field in selected_fields:
                df[field] = pd.to_numeric(df[field], errors='coerce')
            
            # Create new timestamps: 120 minutes ending now (current time)
            current_time = pd.Timestamp.now().floor('min')  # Round to nearest minute
            start_time = current_time - pd.Timedelta(minutes=119)  # 119 minutes ago
            
            # Create the time range with 120 points
            new_time_index = pd.date_range(start=start_time, end=current_time, freq='1min')
            
            # Create a new DataFrame with our custom time index
            new_df = pd.DataFrame(index=range(120), columns=selected_fields)
            
            # Distribute the values from the original data across our 120 timestamps
            # We're essentially mapping the most recent data points to the most recent timestamps
            rows_in_original = min(len(df), 120)
            for field in selected_fields:
                # Get the last rows_in_original values
                values = df[field].values[-rows_in_original:]
                # Pad with NaN if we have fewer than 120 values
                if rows_in_original < 120:
                    padding = [np.nan] * (120 - rows_in_original)
                    values = np.concatenate([padding, values])
                # Assign to new DataFrame
                new_df[field] = values
            
            # Fill any missing values through interpolation
            new_df = new_df.interpolate(method='linear')
            
            # Assign the new time index
            new_df.index = new_time_index
            
            # Rename columns to meaningful names
            new_df.rename(columns={
                'field1': 'Temperature',
                'field2': 'Humidity',
                'field4': 'Light'
            }, inplace=True)
            
            new_df['Light'] = new_df['Light'].div(10)

            return new_df
        else:
            print(f"Failed to retrieve data. Status Code: {response.status_code}, Response: {response.text}")
            return None

    def run(self, channel_id, read_api_key, on,threshold):
        if on == True:
            # Get the data from ThingSpeak
            df = self._get_thingspeak_data(channel_id, read_api_key)
            
            dataset = df[self.features].values

            # Normalize the data
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(dataset)

            # Get the last sequence from our data
            last_sequence = scaled_data[-self.sequence_length:]

            current_sequence = last_sequence.copy()

            # Predict future values
            future_scaled = self._forecast_future(current_sequence)

            # Inverse transform to get actual values
            future_actual = scaler.inverse_transform(future_scaled)

            # Create a DataFrame with the predictions
            last_date = df.index[-1]

            # Create a date range for the next 60 minutes
            forecast_dates = pd.date_range(start=last_date + timedelta(minutes=1), periods=60, freq='1min')

            # Create a DataFrame for the forecasted values
            forecasts = pd.DataFrame(future_actual, index=forecast_dates, columns=self.features)


            return forecasts
            
        else:
            return None    