import tkinter as tk
from tkinter import ttk, messagebox, font
import matplotlib.pyplot as plt
import threading
import requests
import json
import time
from datetime import datetime, timedelta
import sv_ttk  # For modern theme (pip install sv-ttk)
import os

class PremiumSmartHomeUI:
    def __init__(self, root, api_url="http://localhost:5000"):
        self.root = root
        self.root.title("Smart Home Intelligence Center")
        self.root.geometry("1000x800")
        self.api_url = api_url
        self.is_closing = False  # Add this line
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)  # Add this 
        
        # Apply Sun Valley theme (modern premium look)
        sv_ttk.set_theme("dark")
        
        # System state
        self.system_on = False
        self.thresholds = {
            "Temperature": 25.0,  # °C
            "Humidity": 60.0,     # %
            "Light": 500.0        # Lux
        }
        self.forecast_minutes = 30  # Default prediction time
        self.forecast_interval = 3  # Default update interval in minutes
        
        # Initialize connection status
        self.connected = False
        
        self.setup_fonts()

        self.create_widgets()

          # Load saved settings
        self.load_settings()

        self.update_thread = None
        self.running = False
        
        # Initial connection check
        self.check_connection()

    def on_closing(self):
        """Handle window closing properly"""
        self.is_closing = True
        self.running = False  # Stop monitoring thread
        
        # Wait briefly for threads to terminate
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=0.5)
        
        # Destroy the window
        self.root.destroy()

    def save_settings(self):
        """Save current settings to a file"""
        settings = {
            "thresholds": self.thresholds,
            "forecast_minutes": self.forecast_minutes,
            "forecast_interval": self.forecast_interval  # Add this line
        }
        
        try:
            with open('smart_home_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            self.add_log_entry("Settings saved")
        except Exception as e:
            self.add_log_entry(f"Error saving settings: {str(e)}")
        
    def load_settings(self):
        """Load settings from a file"""
        try:
            if os.path.exists('./smart_home_settings.json'):
                with open('./smart_home_settings.json', 'r') as f:
                    settings = json.load(f)
                    
                # Update thresholds
                if "thresholds" in settings:
                    self.thresholds = settings["thresholds"]
                    
                # Update forecast minutes
                if "forecast_minutes" in settings:
                    self.forecast_minutes = settings["forecast_minutes"]
                    
                # Update forecast interval
                if "forecast_interval" in settings:
                    self.forecast_interval = settings["forecast_interval"]

                # Update UI elements
                self.temp_var.set(self.thresholds["Temperature"])
                self.humidity_var.set(self.thresholds["Humidity"])
                self.light_var.set(self.thresholds["Light"])
                self.time_var.set(self.forecast_minutes)
                self.interval_var.set(self.forecast_interval)  # Add this line
                
                # Update labels
                self.update_threshold_label("temp")
                self.update_threshold_label("humidity")
                self.update_threshold_label("light")
                    
                self.add_log_entry("Settings loaded from file")
                return True
        except Exception as e:
            self.add_log_entry(f"Error loading settings: {str(e)}")
        
        return False

    def restore_default_settings(self):
        """Reset to default settings"""
        # Define default values
        self.thresholds = {
            "Temperature": 25.0,
            "Humidity": 60.0,
            "Light": 500.0
        }
        self.forecast_minutes = 30
        self.forecast_interval = 3  # Default interval
        
        # Update UI elements
        self.temp_var.set(self.thresholds["Temperature"])
        self.humidity_var.set(self.thresholds["Humidity"])
        self.light_var.set(self.thresholds["Light"])
        self.time_var.set(self.forecast_minutes)
        self.interval_var.set(self.forecast_interval)  # Add this line
        
        # Update labels
        self.update_threshold_label("temp")
        self.update_threshold_label("humidity")
        self.update_threshold_label("light")
        
        # Log and notify
        self.add_log_entry("Settings restored to defaults")
        messagebox.showinfo("Settings Reset", "Settings have been restored to defaults")

        # Save the default settings to file
        self.apply_settings()
    
    def setup_fonts(self):
        """Setup custom fonts for a premium look"""
        self.header_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.subheader_font = font.Font(family="Segoe UI", size=12, weight="bold")
        self.text_font = font.Font(family="Segoe UI", size=10)
        self.mono_font = font.Font(family="Consolas", size=10)
    
    def create_widgets(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Configure main container
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # Top bar with logo and connection status
        top_bar = ttk.Frame(main_container)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        top_bar.columnconfigure(1, weight=1)
        
        # Logo/Title
        ttk.Label(
            top_bar, 
            text="SMART HOME INTELLIGENCE", 
            font=self.header_font
        ).grid(row=0, column=0, sticky="w")
        
        # Connection status
        self.connection_frame = ttk.Frame(top_bar)
        self.connection_frame.grid(row=0, column=2, sticky="e")
        
        self.connection_indicator = ttk.Label(
            self.connection_frame, 
            text="●", 
            foreground="red",
            font=font.Font(size=16)
        )
        self.connection_indicator.grid(row=0, column=0, padx=(0, 5))
        
        self.connection_label = ttk.Label(
            self.connection_frame, 
            text="DISCONNECTED",
            font=self.text_font
        )
        self.connection_label.grid(row=0, column=1)
        
        # Two-column layout for controls and visualization
        content_frame = ttk.Frame(main_container)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Left panel for controls
        left_panel = ttk.Frame(content_frame, padding="10")
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left_panel.columnconfigure(0, weight=1)
        
        # System Control Panel
        control_frame = ttk.LabelFrame(
            left_panel, 
            text="System Control", 
            padding="15",
            borderwidth=2,
            relief="groove"
        )
        control_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        
        # Power button with custom styling
        power_frame = ttk.Frame(control_frame)
        power_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        self.power_status = tk.StringVar(value="OFF")
        self.power_button = ttk.Button(
            power_frame,
            text="POWER",
            command=self.toggle_system,
            width=15
        )
        self.power_button.grid(row=0, column=0, sticky="w")
        
        self.status_indicator = ttk.Label(
            power_frame, 
            textvariable=self.power_status,
            foreground="red",
            font=self.subheader_font
        )
        self.status_indicator.grid(row=0, column=1, sticky="w", padx=(10, 0))
        
        # Divider
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, sticky="ew", pady=10)
        
        # Forecast time selection
        time_frame = ttk.Frame(control_frame)
        time_frame.grid(row=2, column=0, sticky="ew", pady=5)
        
        ttk.Label(
            time_frame, 
            text="Forecast Duration:",
            font=self.text_font
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        time_values = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
        self.time_var = tk.IntVar(value=self.forecast_minutes)
        time_dropdown = ttk.Combobox(
            time_frame, 
            values=time_values,
            textvariable=self.time_var,
            width=5,
            state="readonly"
        )
        time_dropdown.grid(row=0, column=1, sticky="w")
        
        ttk.Label(
            time_frame, 
            text="minutes",
            font=self.text_font
        ).grid(row=0, column=2, sticky="w", padx=(5, 0))

        # After the existing forecast duration controls
        # Add separator to visually group the controls
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, sticky="ew", pady=10)

        # Forecast interval selection
        interval_frame = ttk.Frame(control_frame)
        interval_frame.grid(row=4, column=0, sticky="ew", pady=5)

        ttk.Label(
            interval_frame, 
            text="Forecast Interval:",
            font=self.text_font
        ).grid(row=0, column=0, sticky="w", padx=(0, 10))

        interval_values = [1, 3, 5, 10, 20, 30, 40, 50, 60]
        self.interval_var = tk.IntVar(value=self.forecast_interval)
        interval_dropdown = ttk.Combobox(
            interval_frame, 
            values=interval_values,
            textvariable=self.interval_var,
            width=5,
            state="readonly"
        )
        interval_dropdown.grid(row=0, column=1, sticky="w")

        ttk.Label(
            interval_frame, 
            text="minutes",
            font=self.text_font
        ).grid(row=0, column=2, sticky="w", padx=(5, 0))
        
        # Thresholds Panel
        threshold_frame = ttk.LabelFrame(
            left_panel, 
            text="Environmental Thresholds", 
            padding="15",
            borderwidth=2,
            relief="groove"
        )
        threshold_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        threshold_frame.columnconfigure(0, weight=1)
        
        # Temperature threshold with premium slider and display
        temp_frame = ttk.Frame(threshold_frame)
        temp_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        temp_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            temp_frame, 
            text="Temperature Threshold:",
            font=self.text_font
        ).grid(row=0, column=0, sticky="w")
        
        temp_control_frame = ttk.Frame(temp_frame)
        temp_control_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        temp_control_frame.columnconfigure(0, weight=1)
        
        self.temp_var = tk.DoubleVar(value=self.thresholds["Temperature"])
        
        temp_scale = ttk.Scale(
            temp_control_frame,
            from_=15.0,
            to=35.0,
            variable=self.temp_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=lambda val: self.update_threshold_label("temp")
        )
        temp_scale.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.temp_label = ttk.Label(
            temp_control_frame, 
            text=f"{self.temp_var.get():.1f} °C",
            width=8,
            font=self.mono_font,
            background="#222222",
            foreground="#00FF00",
            borderwidth=1,
            relief="sunken",
            anchor=tk.CENTER
        )
        self.temp_label.grid(row=0, column=1)
        
        # Humidity threshold with premium slider and display
        humidity_frame = ttk.Frame(threshold_frame)
        humidity_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        humidity_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            humidity_frame, 
            text="Humidity Threshold:",
            font=self.text_font
        ).grid(row=0, column=0, sticky="w")
        
        humidity_control_frame = ttk.Frame(humidity_frame)
        humidity_control_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        humidity_control_frame.columnconfigure(0, weight=1)
        
        self.humidity_var = tk.DoubleVar(value=self.thresholds["Humidity"])
        
        humidity_scale = ttk.Scale(
            humidity_control_frame,
            from_=30.0,
            to=90.0,
            variable=self.humidity_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=lambda val: self.update_threshold_label("humidity")
        )
        humidity_scale.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.humidity_label = ttk.Label(
            humidity_control_frame, 
            text=f"{self.humidity_var.get():.1f} %",
            width=8,
            font=self.mono_font,
            background="#222222",
            foreground="#00FF00",
            borderwidth=1,
            relief="sunken",
            anchor=tk.CENTER
        )
        self.humidity_label.grid(row=0, column=1)
        
        # Light threshold with premium slider and display
        light_frame = ttk.Frame(threshold_frame)
        light_frame.grid(row=2, column=0, sticky="ew")
        light_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            light_frame, 
            text="Light Threshold:",
            font=self.text_font
        ).grid(row=0, column=0, sticky="w")
        
        light_control_frame = ttk.Frame(light_frame)
        light_control_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        light_control_frame.columnconfigure(0, weight=1)
        
        self.light_var = tk.DoubleVar(value=self.thresholds["Light"])
        
        light_scale = ttk.Scale(
            light_control_frame,
            from_=0.0,
            to=1000.0,
            variable=self.light_var,
            orient=tk.HORIZONTAL,
            length=150,
            command=lambda val: self.update_threshold_label("light")
        )
        light_scale.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.light_label = ttk.Label(
            light_control_frame, 
            text=f"{self.light_var.get():.1f} Lux",
            width=8,
            font=self.mono_font,
            background="#222222",
            foreground="#00FF00",
            borderwidth=1,
            relief="sunken",
            anchor=tk.CENTER
        )
        self.light_label.grid(row=0, column=1)
        
        # Button frame for apply and restore buttons
        button_frame = ttk.Frame(left_panel)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Apply button
        self.apply_button = ttk.Button(
            button_frame, 
            text="Apply Settings",
            style="Accent.TButton",
            command=self.apply_settings
        )
        self.apply_button.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Restore defaults button
        self.restore_button = ttk.Button(
            button_frame,
            text="Restore Defaults",
            command=self.restore_default_settings
        )
        self.restore_button.grid(row=0, column=1, sticky="ew", padx=(5, 0))
                
        # Status panel
        status_frame = ttk.LabelFrame(
            left_panel,
            text="System Status",
            padding="15",
            borderwidth=2,
            relief="groove"
        )
        status_frame.grid(row=3, column=0, sticky="nsew")
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(2, weight=1)
        
        # Make the status frame expandable
        left_panel.rowconfigure(3, weight=1)
        
        # Last updated
        update_frame = ttk.Frame(status_frame)
        update_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        update_frame.columnconfigure(1, weight=1)
        
        ttk.Label(
            update_frame,
            text="Last Updated:",
            font=self.text_font
        ).grid(row=0, column=0, sticky="w")
        
        self.last_update_label = ttk.Label(
            update_frame,
            text="--",
            font=self.mono_font
        )
        self.last_update_label.grid(row=0, column=1, sticky="e")

        ttk.Label(
            update_frame,
            text="Next Forecast:",
            font=self.text_font
        ).grid(row=1, column=0, sticky="w")

        self.next_forecast_label = ttk.Label(
            update_frame,
            text="--",
            font=self.mono_font
        )
        self.next_forecast_label.grid(row=1, column=1, sticky="e")

        
        # Event log (scrollable)
        ttk.Label(
            status_frame, 
            text="Event Log:",
            font=self.text_font
        ).grid(row=1, column=0, sticky="w", pady=(0, 5))
        
        log_frame = ttk.Frame(status_frame)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(
            log_frame,
            height=8,
            width=30,
            font=self.mono_font,
            background="#222222",
            foreground="#CCCCCC",
            wrap=tk.WORD
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        self.log_text.config(state=tk.DISABLED)
        
        # Right panel with results
        right_panel = ttk.Frame(content_frame)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)  # Make results frame expandable
        
        # Results frame - Main prediction display
        self.results_frame = ttk.LabelFrame(
            right_panel, 
            text="Prediction Results", 
            padding="15",
            borderwidth=2,
            relief="groove"
        )
        self.results_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.results_frame.columnconfigure(0, weight=1)
        
        # Current time and forecast information
        time_info_frame = ttk.Frame(self.results_frame)
        time_info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        time_info_frame.columnconfigure(1, weight=1)

        # Current time
        current_time_frame = ttk.Frame(time_info_frame)
        current_time_frame.grid(row=0, column=0, sticky="ew", pady=5, columnspan=2)
        current_time_frame.columnconfigure(1, weight=1)
        
        ttk.Label(
            current_time_frame, 
            text="Current Time:",
            font=self.subheader_font
        ).grid(row=0, column=0, sticky="w")
        
        self.current_time_display = ttk.Label(
            current_time_frame,
            text="--",
            font=self.mono_font
        )
        self.current_time_display.grid(row=0, column=1, sticky="e")

        # Forecast time
        forecast_time_frame = ttk.Frame(time_info_frame)
        forecast_time_frame.grid(row=1, column=0, sticky="ew", pady=5, columnspan=2)
        forecast_time_frame.columnconfigure(1, weight=1)
        
        ttk.Label(
            forecast_time_frame, 
            text="Forecast Time:",
            font=self.subheader_font
        ).grid(row=0, column=0, sticky="w")
        
        self.forecast_time_display = ttk.Label(
            forecast_time_frame,
            text="--",
            font=self.mono_font
        )
        self.forecast_time_display.grid(row=0, column=1, sticky="e")

        # Minutes ahead
        forecast_minutes_frame = ttk.Frame(time_info_frame)
        forecast_minutes_frame.grid(row=2, column=0, sticky="ew", pady=5, columnspan=2)
        forecast_minutes_frame.columnconfigure(1, weight=1)
        
        ttk.Label(
            forecast_minutes_frame, 
            text="Prediction Timeframe:",
            font=self.subheader_font
        ).grid(row=0, column=0, sticky="w")
        
        self.forecast_minutes_display = ttk.Label(
            forecast_minutes_frame,
            text="--",
            font=self.mono_font
        )
        self.forecast_minutes_display.grid(row=0, column=1, sticky="e")

        # Separator
        ttk.Separator(self.results_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, sticky="ew", pady=15)

        # Prediction values - use a larger, more prominent display
        prediction_values_frame = ttk.Frame(self.results_frame)
        prediction_values_frame.grid(row=2, column=0, sticky="nsew", pady=10)
        prediction_values_frame.columnconfigure(0, weight=1)
        
        # Title for prediction section
        ttk.Label(
            prediction_values_frame,
            text="PREDICTED ENVIRONMENTAL VALUES",
            font=self.header_font,
            anchor=tk.CENTER
        ).grid(row=2, column=0, sticky="ew", pady=10)

        # Temperature prediction - Fix spacing
        temp_prediction_frame = ttk.Frame(prediction_values_frame)
        temp_prediction_frame.grid(row=3, column=0, sticky="ew", pady=15)
        # Set proper column weight distribution
        temp_prediction_frame.columnconfigure(0, weight=0)  # Icon - fixed width
        temp_prediction_frame.columnconfigure(1, weight=0)  # Label - fixed width
        temp_prediction_frame.columnconfigure(2, weight=1)  # Spacer - takes all extra space
        temp_prediction_frame.columnconfigure(3, weight=0)  # Unit - fixed width
        temp_prediction_frame.columnconfigure(4, weight=0)  # Value - fixed width
        
        # Use grid for better alignment
        temp_icon_label = ttk.Label(
            temp_prediction_frame,
            text="🌡",  # Temperature icon   
            font=font.Font(size=24)
        )
        temp_icon_label.grid(row=3, column=0, padx=(5, 10))

        ttk.Label(
            temp_prediction_frame,
            text="Temperature",
            font=self.subheader_font,
        ).grid(row=3, column=1, sticky="w")

        # Spacer frame to absorb extra space
        ttk.Frame(temp_prediction_frame).grid(row=3, column=2, sticky="ew")

        ttk.Label(
            temp_prediction_frame,
            text="°C",
            font=self.subheader_font
        ).grid(row=3, column=3, padx=(0, 5), sticky="e")  # Move to column 3

        self.temp_prediction = ttk.Label(
            temp_prediction_frame,
            text="--",
            font=font.Font(family="Consolas", size=24, weight="bold"),
            background="#222222",
            foreground="#FF5555",  # Red for temperature
            width=8,
            borderwidth=2,
            relief="sunken",
            anchor=tk.CENTER
        )
        self.temp_prediction.grid(row=3, column=4, padx=(0, 10), sticky="e")

        # Humidity prediction
        humidity_prediction_frame = ttk.Frame(prediction_values_frame)
        humidity_prediction_frame.grid(row=4, column=0, sticky="ew", pady=15)
        # For humidity prediction frame
        humidity_prediction_frame.columnconfigure(0, weight=0)  # Icon
        humidity_prediction_frame.columnconfigure(1, weight=0)  # Label
        humidity_prediction_frame.columnconfigure(2, weight=1)  # Spacer
        humidity_prediction_frame.columnconfigure(3, weight=0)  # Unit
        humidity_prediction_frame.columnconfigure(4, weight=0)  # Value


        humidity_icon_label = ttk.Label(
            humidity_prediction_frame,
            text="💧",  # Humidity icon
            font=font.Font(size=24)
        )
        humidity_icon_label.grid(row=4, column=0, padx=(5, 10))

        ttk.Label(
            humidity_prediction_frame,
            text="Humidity",
            font=self.subheader_font
        ).grid(row=4, column=1, sticky="w")

        ttk.Frame(humidity_prediction_frame).grid(row=4, column=2, sticky="ew")

        ttk.Label(
            humidity_prediction_frame,
            text="%",
            font=self.subheader_font
        ).grid(row=4, column=3, padx=(0, 5), sticky="e")

        self.humidity_prediction = ttk.Label(
            humidity_prediction_frame,
            text="--",
            font=font.Font(family="Consolas", size=24, weight="bold"),
            background="#222222",
            foreground="#55FFFF",  # Cyan for humidity
            width=8,
            borderwidth=2,
            relief="sunken",
            anchor=tk.CENTER
        )
        self.humidity_prediction.grid(row=4, column=4, padx=(0, 10), sticky="e")

        # Light prediction
        light_prediction_frame = ttk.Frame(prediction_values_frame)
        light_prediction_frame.grid(row=5, column=0, sticky="ew", pady=15)
        # For light prediction frame 
        light_prediction_frame.columnconfigure(0, weight=0)  # Icon
        light_prediction_frame.columnconfigure(1, weight=0)  # Label
        light_prediction_frame.columnconfigure(2, weight=1)  # Spacer
        light_prediction_frame.columnconfigure(3, weight=0)  # Unit
        light_prediction_frame.columnconfigure(4, weight=0)  # Value
                
        light_icon_label = ttk.Label(
            light_prediction_frame,
            text="💡",  # Light icon
            font=font.Font(size=24)
        )
        light_icon_label.grid(row=5, column=0, padx=(5, 10))

        ttk.Label(
            light_prediction_frame,
            text="Light",
            font=self.subheader_font
        ).grid(row=5, column=1, sticky="w")

        # Add a spacer frame
        ttk.Frame(light_prediction_frame).grid(row=5, column=2, sticky="ew")

        ttk.Label(
            light_prediction_frame,
            text="Lux",
            font=self.subheader_font
        ).grid(row=5, column=3, padx=(0, 5), sticky="e")

        self.light_prediction = ttk.Label(
            light_prediction_frame,
            text="--",
            font=font.Font(family="Consolas", size=24, weight="bold"),
            background="#222222",
            foreground="#FFFF55",  # Yellow for Light
            width=8,
            borderwidth=2,
            relief="sunken",
            anchor=tk.CENTER
        )
        self.light_prediction.grid(row=5, column=4, padx=(0, 10), sticky="e")

        # Device status section
        device_status_frame = ttk.LabelFrame(
            right_panel,
            text="Smart Device Status",
            padding="15",
            borderwidth=2,
            relief="groove"
        )
        device_status_frame.grid(row=1, column=0, sticky="ew", pady=(15, 0), padx=0)
        device_status_frame.columnconfigure(0, weight=1)

        # AC status row
        self.ac_frame = ttk.Frame(device_status_frame)
        self.ac_frame.grid(row=0, column=0, sticky="ew", pady=5)

        # Configure columns properly
        self.ac_frame.columnconfigure(0, weight=0)  # Icon - fixed width
        self.ac_frame.columnconfigure(1, weight=0)  # Label - fixed width
        self.ac_frame.columnconfigure(2, weight=1)  # Spacer - flexible
        self.ac_frame.columnconfigure(3, weight=0)  # Status - fixed width

        # Icon
        self.ac_icon = ttk.Label(
            self.ac_frame,
            text="❄",
            font=font.Font(size=18)
        )
        self.ac_icon.grid(row=0, column=0, padx=(5, 10))

        # Label
        ttk.Label(
            self.ac_frame,
            text="Air Conditioner:",
            font=self.text_font
        ).grid(row=0, column=1, sticky="w")

        # Spacer
        ttk.Frame(self.ac_frame).grid(row=0, column=2, sticky="ew")

        # Status
        self.ac_status = ttk.Label(
            self.ac_frame,
            text="OFF",
            foreground="gray",
            font=self.subheader_font
        )
        self.ac_status.grid(row=0, column=3, padx=10, sticky="e")

        # Lights status row
        self.lights_frame = ttk.Frame(device_status_frame)
        self.lights_frame.grid(row=1, column=0, sticky="ew", pady=5)
        # Fix this line:
        self.lights_frame.columnconfigure(0, weight=0)  # Icon - fixed width
        self.lights_frame.columnconfigure(1, weight=0)  # Label - fixed width
        self.lights_frame.columnconfigure(2, weight=1)  # Spacer - flexible
        self.lights_frame.columnconfigure(3, weight=0)  # Status - fixed width

        # Add a spacer frame to the lights row
        ttk.Frame(self.lights_frame).grid(row=0, column=2, sticky="ew")

        self.lights_icon = ttk.Label(
            self.lights_frame,
            text="💡",
            font=font.Font(size=18)
        )
        self.lights_icon.grid(row=0, column=0, padx=(5, 10))

        ttk.Label(
            self.lights_frame,
            text="Lights:",
            font=self.text_font
        ).grid(row=0, column=1, sticky="w")

        self.lights_status = ttk.Label(
            self.lights_frame,
            text="OFF",
            foreground="gray",
            font=self.subheader_font
        )
        self.lights_status.grid(row=0, column=3, padx=10, sticky="e")

        # Humidity status row
        self.humidity_frame = ttk.Frame(device_status_frame)
        self.humidity_frame = ttk.Frame(device_status_frame)
        self.humidity_frame.grid(row=2, column=0, sticky="ew", pady=5)
        # Fix this line:
        self.humidity_frame.columnconfigure(0, weight=0)  # Icon - fixed width
        self.humidity_frame.columnconfigure(1, weight=0)  # Label - fixed width
        self.humidity_frame.columnconfigure(2, weight=1)  # Spacer - flexible
        self.humidity_frame.columnconfigure(3, weight=0)  # Status - fixed width

        # Add a spacer frame to the humidity row
        ttk.Frame(self.humidity_frame).grid(row=0, column=2, sticky="ew")
                
        self.humidity_icon = ttk.Label(
            self.humidity_frame,
            text="💧",
            font=font.Font(size=18)
        )
        self.humidity_icon.grid(row=0, column=0, padx=(5, 10))

        ttk.Label(
            self.humidity_frame,
            text="Humidity:",
            font=self.text_font
        ).grid(row=0, column=1, sticky="w")

        self.humidity_status = ttk.Label(
            self.humidity_frame,
            text="OFF",
            foreground="gray",
            font=self.subheader_font
        )
        self.humidity_status.grid(row=0, column=3, padx=10, sticky="e")

        # Alert status section
        alert_frame = ttk.LabelFrame(
            right_panel,
            text="Threshold Alert Status",
            padding="10",
            borderwidth=2,
            relief="groove"
        )
        alert_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0), padx=0)
        alert_frame.columnconfigure(0, weight=1)
        
        self.alert_label = ttk.Label(
            alert_frame,
            text="All values within threshold limits",
            font=self.text_font,
            foreground="green"
        )
        self.alert_label.grid(row=0, column=0, pady=5)
    
    def setup_empty_plots(self):
        """Create empty plots with good styling"""
        self.fig.clear()
        
        # Create subplots for each sensor with tight spacing
        ax1 = self.fig.add_subplot(311)
        ax2 = self.fig.add_subplot(312)
        ax3 = self.fig.add_subplot(313)
        
        for ax, title, color in [
            (ax1, 'Temperature Forecast', '#FF5555'),
            (ax2, 'Humidity Forecast', '#55FFFF'),
            (ax3, 'Light Intensity Forecast', '#FFFF55')
        ]:
            ax.set_title(title, color='white', fontsize=12)
            ax.set_facecolor('#1E1E1E')
            ax.grid(True, linestyle='--', alpha=0.3)
            # Add placeholder text
            ax.text(0.5, 0.5, "No Data Available", 
                   horizontalalignment='center',
                   color='gray',
                   fontsize=12,
                   transform=ax.transAxes)
                
        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()
    
    def update_threshold_label(self, sensor_type):
        """Update the display labels when sliders are moved"""
        if sensor_type == "temp":
            self.temp_label.config(text=f"{self.temp_var.get():.1f} °C")
        elif sensor_type == "humidity":
            self.humidity_label.config(text=f"{self.humidity_var.get():.1f} %")
        elif sensor_type == "light":
            self.light_label.config(text=f"{self.light_var.get():.1f} Lux")
    
    def toggle_system(self):
        """Toggle system on/off"""
        self.system_on = not self.system_on
        
        if self.system_on:
            # Existing code for turning ON remains unchanged
            self.power_status.set("ON")
            self.status_indicator.config(foreground="green")
            self.power_button.config(style="Accent.TButton")
            self.add_log_entry("System activated")
            
            # Debug logging
            print("Sending system ON request to server...")
            
            try:
                response = requests.post(
                    f"{self.api_url}/system_status", 
                    json={"system_on": True},
                    timeout=5
                )
                print(f"System ON response: {response.status_code}, {response.text}")
                if response.status_code == 200:
                    self.start_monitoring()
                else:
                    # Error handling code remains unchanged
                    messagebox.showerror("Error", f"Failed to turn on system: {response.text}")
                    self.system_on = False
                    self.power_status.set("OFF")
                    self.status_indicator.config(foreground="red")
                    self.power_button.config(style="TButton")
            except Exception as e:
                # Exception handling code remains unchanged
                print(f"System ON request failed: {str(e)}")
                messagebox.showerror("Connection Error", f"Could not connect to server: {str(e)}")
                self.system_on = False
                self.power_status.set("OFF")
                self.status_indicator.config(foreground="red")
                self.power_button.config(style="TButton")
        else:
            # Code for turning system OFF - with enhancements
            self.power_status.set("OFF")
            self.status_indicator.config(foreground="red")
            self.power_button.config(style="TButton")
            
            # Update device status UI immediately to show all devices OFF
            self.ac_status.config(text="OFF", foreground="gray")
            self.lights_status.config(text="OFF", foreground="gray")
            self.humidity_status.config(text="OFF", foreground="gray")
            
            self.add_log_entry("System deactivated - All appliances turned off")
            self.stop_monitoring()
            
            # Notify the server to turn off all appliances
            try:
                response = requests.post(
                    f"{self.api_url}/system_status", 
                    json={"system_on": False, "turn_off_all_appliances": True},
                    timeout=5
                )
                if response.status_code == 200:
                    self.add_log_entry("All appliances turned off successfully")
                else:
                    self.add_log_entry(f"Failed to turn off all appliances: {response.text}")
            except Exception as e:
                self.add_log_entry(f"Failed to turn off appliances: {str(e)}")
    
    def apply_settings(self):
        """Apply the current settings to the remote system"""
        # Update local thresholds
        self.thresholds["Temperature"] = self.temp_var.get()
        self.thresholds["Humidity"] = self.humidity_var.get()
        self.thresholds["Light"] = self.light_var.get()
        self.forecast_minutes = self.time_var.get()
        self.forecast_interval = self.interval_var.get()  # Add this line
        
        # Save settings to file
        self.save_settings()

        # Send to remote system
        self.send_settings()
        
        # Log the action
        self.add_log_entry(f"Settings updated: T={self.thresholds['Temperature']:.1f}°C, "
                        f"H={self.thresholds['Humidity']:.1f}%, "
                        f"L={self.thresholds['Light']:.1f}Lux, "
                        f"Time={self.forecast_minutes}min, "
                        f"Interval={self.forecast_interval}min")  # Update this line
        
    def start_monitoring(self):
        """Start the monitoring thread"""
        self.running = True
        self.update_thread = threading.Thread(target=self.monitoring_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        
        # Send system status to server
        self.send_system_status()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def monitoring_loop(self):
        """Background thread for periodic updates"""
        while self.running:
            self.update_predictions()
            # Convert minutes to seconds for sleep
            sleep_time = self.forecast_interval * 60
            
            # To avoid long sleep periods that would delay shutdown,
            # we can break it into smaller chunks
            chunk_size = 10  # Check every 10 seconds if we should exit
            for _ in range(sleep_time // chunk_size):
                if not self.running:
                    return  # Exit early if monitoring was stopped
                time.sleep(chunk_size)
            
        # Sleep the remainder
        remaining_time = sleep_time % chunk_size
        if remaining_time > 0 and self.running:
            time.sleep(remaining_time)
    def check_connection(self):
        """Check connection to the remote server"""
        threading.Thread(target=self._check_connection_worker).daemon = True
        threading.Thread(target=self._check_connection_worker).start()

    def _check_connection_worker(self):
        try:
            # Attempt to contact the server
            response = requests.get(f"{self.api_url}/status", timeout=2)
            
            if response.status_code == 200:
                if not self.is_closing:
                    self.root.after(0, lambda: self._update_connection_status(True))
            else:
                if not self.is_closing:
                    self.root.after(0, lambda: self._update_connection_status(False, "ERROR"))
        except Exception as e:
            if not self.is_closing:
                self.root.after(0, lambda: self._update_connection_status(False))
        finally:
            if not self.is_closing:
                self.root.after(15000, self.check_connection)

    def _update_connection_status(self, connected, status_text=None):
            """Update connection status UI elements"""
            self.connected = connected
            if connected:
                self.connection_indicator.config(foreground="green")
                self.connection_label.config(text="CONNECTED")
            else:
                self.connection_indicator.config(foreground="red")
                self.connection_label.config(text=status_text or "DISCONNECTED")
    
    def send_settings(self):
        """Send settings to the remote server"""
        threading.Thread(target=self._send_settings_worker).daemon = True
        threading.Thread(target=self._send_settings_worker).start()
    
    def _send_settings_worker(self):
        if self.is_closing:
            return  # Don't do anything if app is closing
    
        if not self.connected:
            self.root.after(0, lambda: messagebox.showerror("Connection Error", "Cannot update settings: Server unreachable"))
            return
            
        try:
            settings = {
                "thresholds": self.thresholds,
                "forecast_minutes": self.forecast_minutes,
                "forecast_interval": self.forecast_interval  # Add this line
            }
            
            response = requests.post(
                f"{self.api_url}/settings", 
                json=settings,
                timeout=5
            )
            if response.status_code == 200:
                if not self.is_closing:
                    self.root.after(0, lambda: self.add_log_entry("Settings applied successfully"))
            else:
                if not self.is_closing:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Server Error", 
                        f"Failed to update settings: {response.text}"
                    ))
        except Exception as e:
            if not self.is_closing:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", 
                    f"Failed to send settings: {str(e)}"
                ))

    def send_system_status(self):
        """Send system on/off status to server"""
        if not self.check_connection():
            return False
            
        try:
            status = {
                "system_on": self.system_on
            }
            
            response = requests.post(
                f"{self.api_url}/system_status", 
                json=status,
                timeout=5
            )
            
            if response.status_code == 200:
                return True
            else:
                # Don't show error message here to avoid popup spam
                self.add_log_entry(f"Failed to update system status: {response.text}")
                return False
        except Exception as e:
            self.add_log_entry(f"Failed to send system status: {str(e)}")
            return False
    
    def update_predictions(self):
        """Request updated predictions from the server"""
        threading.Thread(target=self._update_predictions_worker).daemon = True
        threading.Thread(target=self._update_predictions_worker).start()
    
    def _update_predictions_worker(self):
        if self.is_closing or not self.connected:
            return
            
        try:
            response = requests.get(
                f"{self.api_url}/forecast",
                params={
                    "minutes": self.forecast_minutes
                },
                timeout=10
            )
            
            if response.status_code == 200:
                if not self.is_closing:
                    forecast_data = response.json()
                    self.root.after(0, lambda: self.process_forecast_data(forecast_data))
                    self.root.after(0, lambda: self.update_last_update_time())
            else:
                if not self.is_closing:
                    self.root.after(0, lambda: self.add_log_entry(f"Failed to get forecast: {response.text}"))
        except Exception as e:
            if not self.is_closing:
                self.root.after(0, lambda: self.add_log_entry(f"Forecast error: {str(e)}"))
        
    def process_forecast_data(self, forecast_data):
        """Process and display the forecast data received from server"""
        try:
            # Parse the forecast data
            timestamps = forecast_data["timestamps"]
            temperature = forecast_data["temperature"]
            humidity = forecast_data["humidity"]
            light = forecast_data["light"]
            
            # Get device status if available
            device_status = forecast_data.get("device_status", {})
            status_messages = forecast_data.get("status_messages", [])
            
            # We only care about the final prediction point
            final_index = -1  # Last element in the arrays
            
            # Get the final prediction values
            final_temp = temperature[final_index]
            final_humidity = humidity[final_index]
            final_light = light[final_index]
            
            # Convert timestamp to datetime if it's a string
            if isinstance(timestamps[final_index], str):
                final_timestamp = datetime.fromisoformat(timestamps[final_index])
            else:
                final_timestamp = timestamps[final_index]
                
            # Update the time displays
            current_time = datetime.now()
            self.current_time_display.config(text=current_time.strftime("%Y-%m-%d %H:%M:%S"))
            self.forecast_time_display.config(text=final_timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            self.forecast_minutes_display.config(text=f"{self.forecast_minutes} minutes")
            
            # Update prediction values with nice formatting
            self.temp_prediction.config(text=f"{final_temp:.1f}")
            self.humidity_prediction.config(text=f"{final_humidity:.1f}")
            self.light_prediction.config(text=f"{final_light:.1f}")
            
            # Update device status
            self._update_device_status(device_status)
            
            # Log status messages
            for msg in status_messages:
                self.add_log_entry(msg)
            
            # Check threshold status and update alert
            alerts = []
            if final_temp > self.thresholds['Temperature']:
                alerts.append(f"Temperature ({final_temp:.1f}°C) exceeds threshold")
            if final_humidity > self.thresholds['Humidity']:
                alerts.append(f"Humidity ({final_humidity:.1f}%) exceeds threshold")
            if final_light > self.thresholds['Light']:
                alerts.append(f"Light ({final_light:.1f} Lux) exceeds threshold")
            
            if alerts:
                alert_text = "\n".join(alerts)
                self.alert_label.config(text=alert_text, foreground="red")
                self.add_log_entry(f"Alert: {', '.join(alerts)}", is_alert=True)
            else:
                self.alert_label.config(text="All values within threshold limits", foreground="green")
            
            self.add_log_entry("Forecast updated successfully")
        except Exception as e:
            self.add_log_entry(f"Error processing forecast: {str(e)}")

    def _update_device_status(self, device_status):
        """Update device status displays based on server data"""
        # Air conditioner status
        ac_status = device_status.get("air_conditioner", "OFF")
        if ac_status == "ON":
            self.ac_status.config(text="ON", foreground="#00FF00")  # Green for ON
        else:
            self.ac_status.config(text="OFF", foreground="gray")
            
        # Lights status
        lights_status = device_status.get("lights", "OFF")
        if lights_status == "ON":
            self.lights_status.config(text="ON", foreground="#FFFF00")  # Yellow for ON
        else:
            self.lights_status.config(text="OFF", foreground="gray")
            
        # Moisture absorber status
        moisture_status = device_status.get("moisture_absorber", "OFF")
        if moisture_status == "ON":
            self.humidity_status.config(text="ON", foreground="#00FFFF")  # Cyan for ON
        else:
            self.humidity_status.config(text="OFF", foreground="gray")
    
    def update_visualization(self, timestamps, temperature, humidity, light):
        """Update visualization with new data"""
        # Clear previous plots
        self.fig.clear()
        
        # Convert timestamps to datetime objects (if they're not already)
        if isinstance(timestamps[0], str):
            timestamps = [datetime.fromisoformat(ts) for ts in timestamps]
        
        # Create subplots for each sensor with premium styling
        ax1 = self.fig.add_subplot(311)
        ax2 = self.fig.add_subplot(312)
        ax3 = self.fig.add_subplot(313)
        
        # Plot temperature with gradient fill and threshold line
        ax1.plot(timestamps, temperature, 'r-', linewidth=2)
        ax1.fill_between(timestamps, temperature, min(temperature), color='red', alpha=0.2)
        ax1.axhline(y=self.thresholds['Temperature'], color='white', linestyle='--', alpha=0.7)
        ax1.set_title('Temperature Forecast', color='white', fontsize=12)
        ax1.set_ylabel('°C', color='white')
        ax1.set_facecolor('#1E1E1E')
        ax1.grid(True, linestyle='--', alpha=0.3)
        
        # Plot humidity with gradient fill and threshold line
        ax2.plot(timestamps, humidity, 'c-', linewidth=2)
        ax2.fill_between(timestamps, humidity, min(humidity), color='cyan', alpha=0.2)
        ax2.axhline(y=self.thresholds['Humidity'], color='white', linestyle='--', alpha=0.7)
        ax2.set_title('Humidity Forecast', color='white', fontsize=12)
        ax2.set_ylabel('%', color='white')
        ax2.set_facecolor('#1E1E1E')
        ax2.grid(True, linestyle='--', alpha=0.3)
        
        # Plot light with gradient fill and threshold line
        ax3.plot(timestamps, light, 'y-', linewidth=2)
        ax3.fill_between(timestamps, light, min(light), color='yellow', alpha=0.2)
        ax3.axhline(y=self.thresholds['Light'], color='white', linestyle='--', alpha=0.7)
        ax3.set_title('Light Intensity Forecast', color='white', fontsize=12)
        ax3.set_ylabel('Lux', color='white')
        ax3.set_facecolor('#1E1E1E')
        ax3.grid(True, linestyle='--', alpha=0.3)
        
        # Improve x-axis formatting
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        self.fig.tight_layout(pad=2.0)
        self.canvas.draw()
    
    def check_thresholds(self, temperature, humidity, light):
        """Check if any forecasted values exceed the thresholds"""
        # Check if any forecasted values exceed thresholds
        temp_exceeded = max(temperature) > self.thresholds['Temperature']
        humidity_exceeded = max(humidity) > self.thresholds['Humidity']
        light_exceeded = max(light) > self.thresholds['Light']
        
        # Format alerts
        alerts = []
        if temp_exceeded:
            alerts.append(f"Temperature will reach {max(temperature):.1f}°C")
        if humidity_exceeded:
            alerts.append(f"Humidity will reach {max(humidity):.1f}%")
        if light_exceeded:
            alerts.append(f"Light will reach {max(light):.1f} Lux")
        
        if alerts:
            alert_message = "ALERT: " + ", ".join(alerts)
            self.add_log_entry(alert_message, is_alert=True)
            
            # Show alert dialog
            messagebox.showwarning("Environmental Alert", 
                                  f"The following thresholds will be exceeded:\n" +
                                  "\n".join(f"• {alert}" for alert in alerts))
    
    def update_last_update_time(self):
        """Update the last update time display"""
        current_time = datetime.now()
        current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        self.last_update_label.config(text=current_time_str)
        
        # Calculate and display next forecast time
        if self.system_on:
            next_forecast = current_time + timedelta(minutes=self.forecast_interval)
            next_forecast_str = next_forecast.strftime("%H:%M:%S")
            self.next_forecast_label.config(text=next_forecast_str)
        else:
            self.next_forecast_label.config(text="--")
    
    def add_log_entry(self, message, is_alert=False):
        """Add an entry to the log display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.log_text.config(state=tk.NORMAL)
        
        # Ensure we don't exceed a reasonable number of log entries
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 100:  # Keep only the last 100 entries
            self.log_text.delete("1.0", "end-100l")
            
        # Add timestamp and message with appropriate color
        self.log_text.insert(tk.END, f"[{current_time}] ", "timestamp")
        
        if is_alert:
            self.log_text.insert(tk.END, f"{message}\n", "alert")
        else:
            self.log_text.insert(tk.END, f"{message}\n", "normal")
            
        # Add tags for styling
        self.log_text.tag_config("timestamp", foreground="#AAAAAA")
        self.log_text.tag_config("normal", foreground="#FFFFFF")
        self.log_text.tag_config("alert", foreground="#FF5555")
        
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)  # Scroll to bottom

#To run the UI
if __name__ == "__main__":
    # Note: Install required packages with:
    # pip install sv-ttk requests matplotlib
    
    root = tk.Tk()
    app = PremiumSmartHomeUI(root, api_url="http://localhost:5000")
    root.mainloop()