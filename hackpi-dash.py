import time
import board
import adafruit_scd4x
import curses

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
        return curses.color_pair(5)  # Green
    elif 550 < value <= 1000:
        return curses.color_pair(1)  # Cyan
    elif 1000 < value <= 1500:
        return curses.color_pair(2)  # Yellow
    elif 1500 < value <= 2000:
        return curses.color_pair(3)  # Red
    else:
        return curses.color_pair(4)  # Magenta

# Function to display the data
def display_data(stdscr, temperature, humidity, co2_data, co2):
    stdscr.clear()

    # Display temperature and humidity
    stdscr.addstr(0, 0, f"Temperature: {temperature:.1f} *C")
    stdscr.addstr(1, 0, f"Humidity: {humidity:.1f} %")

    # Display the CO2 graph label
    stdscr.addstr(3, 0, f"CO2 Level (ppm): {co2}")

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

    stdscr.refresh()

def main(stdscr):
    # Initialize limited colors
    init_colors()

    # Initialize the sensor
    i2c = board.I2C()  # uses the board.SCL and board.SDA 
    scd4x = adafruit_scd4x.SCD4X(i2c)
    scd4x.start_periodic_measurement()
    
    co2_data = []
    
    while True:
        if scd4x.data_ready:
            temperature = scd4x.temperature
            humidity = scd4x.relative_humidity
            co2 = scd4x.CO2
            co2_data.append(co2)
            
            # Call the display function
            display_data(stdscr, temperature, humidity, co2_data, co2)
        
        time.sleep(20)

# Start the curses application
curses.wrapper(main)
