![Trading Bot in Action](https://gyazo.com/ff7d5607dadc1446c62b94e93d0e08b1.gif)

# Trading Bot with GUI and Mock Exchanges

This project is a simulation of a trading bot that interacts with two mock exchanges. It includes a GUI built with Tkinter, allowing you to input parameters and observe key metrics during trading. The mock exchanges simulate order book updates over WebSockets.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setting Up the Environment](#setting-up-the-environment)
- [Installing Dependencies](#installing-dependencies)
- [License](#license)

## Prerequisites

Before you begin, ensure you have the following installed on your Windows machine:

- **Python 3.8 or higher**: [Download Python](https://www.python.org/downloads/windows/)
- **Pip**: Usually comes bundled with Python.
- **Git** (optional): For cloning the repository if using Git.

## Project Structure

- **`gui.py`**: The main GUI application for the trading bot.
- **`mock_exchanges.py`**: The mock exchanges simulating order book data.
- **`requirements.txt`**: Lists the project's Python dependencies.
- **`start.bat`**: Batch script to automate starting the mock exchanges and GUI.
- **`README.md`**: This documentation file.

## Setting Up the Environment

It's recommended to use a virtual environment to manage your project's dependencies.

### Create a Virtual Environment

1. Open Command Prompt (cmd) or PowerShell.
2. Navigate to your project directory:

   ```cmd
   cd path\to\your_project
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ./start.bat
   ```

