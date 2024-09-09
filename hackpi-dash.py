import time
import board
import adafruit_scd4x
import curses
import csv
from datetime import datetime
from sensirion_i2c_driver import I2cConnection, LinuxI2cTransceiver
from sensirion_i2c_sen5x import Sen5xI2cDevice

# Function to initialize CSV file and write headers
def initialize_csv():
    # Generate filename with current date and time
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"sensor_data_{timestamp}.csv"
    
    # Write headers to the CSV file
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Temperature (C)", "Humidity (%)", "CO2 (ppm)", 
                         "PM1.0 (µg/m³)", "PM2.5 (µg/m³)", "PM4.0 (µg/m³)", "PM10.0 (µg/m³)",
                         "Ambient Humidity (%)", "Ambient Temperature (C)", "VOC Index", "NOx Index"])
        
    return filename  # Return the generated filename# Function to log data to CSV file

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

# Function to map temperature values to the appropriate color
def get_color_for_temperature(value):
    if value < 0:
        return curses.color_pair(5)  # Magenta for low temperature
    elif 0 <= value <= 27:
        return curses.color_pair(1)  # Green for moderate temperature
    else:
        return curses.color_pair(3)  # Red for high temperature

# Function to draw individual graphs with specific scaling
def draw_graph(stdscr, row_offset, col_offset, data, graph_height, graph_width, scale_max, label, get_color_func):
    y_labels = [0, scale_max // 4, scale_max // 2, 3 * scale_max // 4, scale_max] # 5 labels
    num_labels = len(y_labels)
    
    # Calculate step size as an integer to avoid uneven spacing
    step_size = graph_height // (num_labels - 1)
    
    for i, label_value in enumerate(y_labels):
        # Calculate label position using integer division for even spacing
        label_pos = i * step_size
        
        # Ensure the label position is valid within the graph's height
        if graph_height - label_pos + row_offset < max_height:
            stdscr.addstr(graph_height - label_pos + row_offset, col_offset, f"{label_value:>4} |")
            
    # Truncate data if it exceeds graph_width
    if len(data) > graph_width:
        data = data[-graph_width:]
        
    # Scale the data to fit within the graph height
    scaled_data = [int((value / scale_max) * graph_height) for value in data]
    
    for i, (height, value) in enumerate(zip(scaled_data, data)):
        color = get_color_func(value)
        
        # Draw the bars of the graph
        for j in range(graph_height):
            if j < height and graph_height - j + row_offset < max_height:
                stdscr.addstr(graph_height - j + row_offset, i + col_offset + 6, "#", color)
                
    # Add the graph label
    stdscr.addstr(row_offset + 1, col_offset + 15, label, curses.A_BOLD)
    
    

# Function to display the data across 6 grid panels
def display_data(stdscr, co2_data, temperature_data, humidity_data, particle_data, voc_data, nox_data, co2, values):
    stdscr.clear()

    # Get the screen dimensions
    global max_height, max_width
    max_height, max_width = stdscr.getmaxyx()

    # Ensure there's enough space for the graphs
    if max_height < 30 or max_width < 80:
        stdscr.addstr(0, 0, "Terminal window is too small for the display! Resize and try again.")
        stdscr.refresh()
        return
    
    stdscr.addstr(1, 25, "Hackberry Pi Environmental Monitor V1.0", curses.A_BOLD)
    stdscr.addstr(3, 0, f"{values}")  # Display other sensor data (8 lines long)
    stdscr.addstr(11, 0, f"CO2 Level (ppm):             {co2}")
    # Calculate the starting row for the graphs to avoid overlap
    start_row = 15  # Start drawing the graphs after 10 lines (8 lines of data + 2 lines spacing)

    # Set row spacing between each graph
    row_spacing = 4  # Add 2 lines of spacing between each row of graphs

    # Calculate the height and width for each of the six graphs
    graph_height = min(6, (max_height - start_row) // 3)  # Height for each graph
    graph_width = (max_width // 2) - 10  # Adjusted for 2 columns with space between

    # Draw the 6 graphs in a 2-column and 3-row layout
    draw_graph(stdscr, start_row, 0, co2_data, graph_height, graph_width, 2000, f"CO2 ({co2} ppm)", get_color)
    draw_graph(stdscr, start_row, max_width // 2, temperature_data, graph_height, graph_width, 50, f"Temperature ({values.ambient_temperature.degrees_celsius}°C)", get_color_for_temperature)
    
    draw_graph(stdscr, start_row + graph_height + row_spacing, 0, humidity_data, graph_height, graph_width, 100, f"Humidity ({values.ambient_humidity.percent_rh}%)", get_color)
    draw_graph(stdscr, start_row + graph_height + row_spacing, max_width // 2, particle_data, graph_height, graph_width, 100, f"Particles ({values.mass_concentration_10p0.physical} µg/m³)", get_color)
    
    draw_graph(stdscr, start_row + 2 * (graph_height + row_spacing), 0, voc_data, graph_height, graph_width, 500, f"VOC Index ({values.voc_index.scaled})", get_color)
    draw_graph(stdscr, start_row + 2 * (graph_height + row_spacing), max_width // 2, nox_data, graph_height, graph_width, 500, f"NOx Index ({values.nox_index.scaled})", get_color)

    stdscr.refresh()

def main(stdscr):
    # Initialize limited colors
    init_colors()

    # Initialize the sensor
    i2c = board.I2C()  # uses the board.SCL and board.SDA 
    scd4x = adafruit_scd4x.SCD4X(i2c)
    scd4x.start_periodic_measurement()

    co2_data = []
    temperature_data = []
    humidity_data = []
    particle_data = []
    voc_data = []
    nox_data = []
    csv_filename = initialize_csv()  # Use the new dynamic filename
    

    while True:
        with LinuxI2cTransceiver('/dev/i2c-1') as i2c_transceiver:
            device = Sen5xI2cDevice(I2cConnection(i2c_transceiver))
            # Start measurement
            device.start_measurement()
            # Read measured values
            values = device.read_measured_values()
            temperature_data.append(values.ambient_temperature.degrees_celsius)
            humidity_data.append(values.ambient_humidity.percent_rh)
            particle_data.append(values.mass_concentration_10p0.physical)
            voc_data.append(values.voc_index.scaled)
            nox_data.append(values.nox_index.scaled)

        if scd4x.data_ready:
            temperature = scd4x.temperature
            humidity = scd4x.relative_humidity
            co2 = scd4x.CO2
            co2_data.append(co2)

            # Log the data to CSV
            log_data_to_csv(csv_filename, temperature, humidity, co2, values)

            # Call the display function with all graphs
            display_data(stdscr, co2_data, temperature_data, humidity_data, particle_data, voc_data, nox_data, co2, values)

        time.sleep(60)

# Start the curses application
curses.wrapper(main)
