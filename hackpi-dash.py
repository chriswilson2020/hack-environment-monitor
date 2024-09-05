import time
import board
import adafruit_scd4x
import curses
import csv
from datetime import datetime
from sensirion_i2c_driver import I2cConnection, LinuxI2cTransceiver
from sensirion_i2c_sen5x import Sen5xI2cDevice

# Function to initialize CSV file and write headers
def initialize_csv(filename="sensor_data.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Temperature (C)", "Humidity (%)", "CO2 (ppm)", 
                         "PM1.0 (µg/m³)", "PM2.5 (µg/m³)", "PM4.0 (µg/m³)", "PM10.0 (µg/m³)",
                         "Ambient Humidity (%)", "Ambient Temperature (C)", "VOC Index", "NOx Index"])

# Function to log data to CSV file
def log_data_to_csv(filename, temperature, humidity, co2, values):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp, 
            round(temperature, 2), 
            round(humidity, 2), 
            co2, 
            values.mass_concentration_1p0.physical, 
            values.mass_concentration_2p5.physical, 
            values.mass_concentration_4p0.physical, 
            values.mass_concentration_10p0.physical,
            values.ambient_humidity.percent_rh, 
            values.ambient_temperature.degrees_celsius, 
            values.voc_index.scaled, 
            values.nox_index.scaled
        ])

# Function to map CO2 values to the 8 available colors
def init_colors():
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green for low CO2
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Yellow for moderate CO2
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)  # Red for high CO2
    curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # Magenta for very high CO2
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Cyan for mid-range CO2

# Function to get color based on CO2 level
def get_color(value):
    if value <= 550:
        return curses.color_pair(5)  # Cyan
    elif 550 < value <= 1000:
        return curses.color_pair(1)  # Green
    elif 1000 < value <= 1500:
        return curses.color_pair(2)  # Yellow
    elif 1500 < value <= 2000:
        return curses.color_pair(3)  # Red
    else:
        return curses.color_pair(4)  # Magenta

# Function to display the data
def display_data(stdscr, temperature, humidity, co2_data, co2, values):
    stdscr.clear()

    # Display the CO2 graph label
    stdscr.addstr(0, 0, f"CO2 Level (ppm): {co2}")

    max_height, max_width = stdscr.getmaxyx()
    
    graph_height = 15  # Smaller height for the graph
    graph_width = max_width - 8  # Adjusted to leave space for y-axis

    if len(co2_data) > graph_width:
        co2_data = co2_data[-graph_width:]

    max_co2 = 2000
    scaled_data = [int((value / max_co2) * graph_height) for value in co2_data]

    # Draw Y-axis with labels
    y_labels = [0, 500, 1000, 1500, 2000]
    for i, label in enumerate(y_labels):
        label_pos = int((i / (len(y_labels) - 1)) * graph_height)
        stdscr.addstr(graph_height - label_pos + 5, 0, f"{label:>4} |")  # Offset by 5 to move below the label
    
    # Draw the graph with limited colors
    for i, (height, value) in enumerate(zip(scaled_data, co2_data)):
        color = get_color(value)
        for j in range(graph_height):
            if j < height:
                stdscr.addstr(graph_height - j + 5, i + 6, "#", color)  # Offset by 5 to move below the label
    stdscr.addstr(1, 0, f"{values}")

    stdscr.refresh()

def main(stdscr):
    # Initialize limited colors
    init_colors()

    # Initialize the sensor
    i2c = board.I2C()  # uses the board.SCL and board.SDA 
    scd4x = adafruit_scd4x.SCD4X(i2c)
    scd4x.start_periodic_measurement()
    
    co2_data = []
    csv_filename = "sensor_data.csv"
    initialize_csv(csv_filename)
    
    while True:
        with LinuxI2cTransceiver('/dev/i2c-1') as i2c_transceiver:
            device = Sen5xI2cDevice(I2cConnection(i2c_transceiver))
            # Start measurement
            device.start_measurement()
            # Read measured values
            values = device.read_measured_values()
            
        if scd4x.data_ready:
            temperature = scd4x.temperature
            humidity = scd4x.relative_humidity
            co2 = scd4x.CO2
            co2_data.append(co2)
            
            # Log the data to CSV
            log_data_to_csv(csv_filename, temperature, humidity, co2, values)
            
            # Call the display function
            display_data(stdscr, temperature, humidity, co2_data, co2, values)

        time.sleep(60)

# Start the curses application
curses.wrapper(main)
