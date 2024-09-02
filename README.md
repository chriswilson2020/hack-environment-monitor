# hack-environment-monitor
Hackberry-Pi Python Script for SD4X CO2 Temp and Humidity sensor

## Requirements
`pip3 install adafruit-circuitpython-scd4x`

### Installation

Ensure that you make a link between I2C-11 and I2C-1 for the pi to be able to communicate over the StemmaQT port.
`sudo ln -s /dev/i2c-11 /dev/i2c-1`

*Note: this will need to be done each time you reboot the device unless you make it permanent see below.

Clone the repository:
`git clone https://github.com/chriswilson2020/hack-environment-monitor.git`

Make sure that the sensor is plugged into the StemmaQT port on the right hand side of the HackberryPi ensuring that you insert the plug carefully so as not to bend the delicate pins. 

`cd hack-environment-monitor`
`python3 hackpi-dash.py`

You should see output similar to this on your screen:

<img src="https://github.com/user-attachments/assets/7cad9ce5-5ee3-43cd-a6ab-06cffe5b4862" alt="HackPi-Enviro" width="400">



### How to make the symlink permanent
For this we will use a udev rule because it is the most native and flexible method for handling device nodes in Linux.
Udev rules are specifically designed for managing device files, making this approach clean and reliable.
It automatically triggers when the device appears, without needing a full reboot or additional services.

1. Create a new udev rule file in /etc/udev/rules.d/: `sudo nano /etc/udev/rules.d/99-i2c-symlink.rules`

2. Add the following line to the file: `KERNEL=="i2c-11", SYMLINK+="i2c-1"`

3. Save and close the file.

To apply the new rule without rebooting, you can reload the udev rules with:

`sudo udevadm control --reload-rules`

`sudo udevadm trigger`


