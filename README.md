# Endless Online ColorBot

Endless Online ColorBot is a Python script designed to automate certain tasks in the 2D game Endless Online. The bot detects a specific color on the screen, moves towards it, and performs actions based on the detected color and other game parameters.

## Features

- Detects a specific color within a selected region of the screen
- Moves the character towards the detected color using keyboard simulation
- Adjusts actions based on health thresholds
- Logs actions and events to a log file
- Configurable parameters for fine-tuning

## Requirements

- Python 3.7 or higher
- OpenCV
- Numpy
- PyAutoGUI
- PyMem
- PyWin32

## Installation

1. Clone this repository:
    ```sh
    git clone https://github.com/SoulDemon/Endless-Online-Bot.git
    cd Endless-Online-Bot
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the script:
    ```sh
    python colorbot.py
    ```

2. Follow the on-screen instructions to:
    - Select the region of the screen to monitor
    - Set the center point for the bot
    - Select the target color by clicking on it

3. The bot will start detecting the color and performing actions based on the configured parameters.

## Configuration

You can adjust various parameters within the `colorbot.py` script to fine-tune the bot's behavior, such as the distance threshold for shooting and the health thresholds.

## Demonstration

### Development Issue

Below is a GIF illustrating an issue encountered during the development of the bot:

![Development Issue Pathing](https://github.com/SoulDemon/Endless-Online-Bot/blob/main/Broke.gif?raw=true)

### Bot in Action

Here are two GIFs demonstrating the bot working correctly:

1. Detecting and moving towards the target color:

![Bot Detecting and Moving]([path/to/your/working1.gif](https://github.com/SoulDemon/Endless-Online-Bot/blob/main/Fixed.gif?raw=true))

2. Performing an action based on the detected color:

![Bot Performing Action]([path/to/your/working2.gif](https://github.com/SoulDemon/Endless-Online-Bot/blob/main/Showing.gif?raw=true))

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Feel free to submit issues, fork the repository, and make pull requests. Contributions are welcome!

## Disclaimer

This bot is intended for educational and entertainment purposes only. Use it at your own risk. The author is not responsible for any consequences of using this bot.

## Acknowledgments

- [OpenCV](https://opencv.org/)
- [Numpy](https://numpy.org/)
- [PyAutoGUI](https://pyautogui.readthedocs.io/)
- [PyMem](https://github.com/srounet/Pymem)
- [PyWin32](https://github.com/mhammond/pywin32)
