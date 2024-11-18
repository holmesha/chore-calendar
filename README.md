
# Family Chores Display

A Python-based project that uses an e-ink display and the Todoist API to track family chores. This project fetches tasks categorized by family members, highlights completed tasks, tracks weekly progress, and provides weather updates—all displayed on an e-ink screen.

---

## Features

- **Todoist Integration**:
  - Fetches tasks by section (e.g., "Mom," "Dad," "Kid 1").
  - Displays tasks due today or earlier (no future tasks).
  - Includes tasks with no due date.
  - Tracks completed tasks weekly with automatic reset on Monday.

- **Weather Information**:
  - Displays current weather using OpenWeatherMap or NWS API.

- **E-Ink Display**:
  - Uses a Waveshare e-ink screen (7.5" B/W/R) for a clean and power-efficient interface.
  - Includes a sleek layout with sections, task lists, and weekly progress.

- **Automatic Updates**:
  - Refreshes the display every 15 minutes.

---

## Setup Instructions

### Prerequisites

- Raspberry Pi (tested on Pi Zero 2W or higher).
- Waveshare 7.5" e-ink display (B/W/R model).
- Python 3.9 or later installed.
- API keys for:
  - **Todoist API** ([Generate here](https://todoist.com/app/settings/integrations)).
  - **Weather API**:
    - OpenWeatherMap ([Sign up here](https://openweathermap.org/api)) or
    - NWS API ([Documentation](https://www.weather.gov/documentation/services-web-api)) - I used this one because, free.

---

### Installation

1. **Clone or Download the Repository**:
   - Clone the repo or manually download the files to your Raspberry Pi.

2. **Install Dependencies**:
   - Install the required Python libraries:
     ```bash
     pip install -r requirements.txt
     ```

3. **Update Configuration**:
   - Open the `fam_chores.py` file.
   - Replace the placeholders (`API_TOKEN`, `LATITUDE`, `LONGITUDE`, etc.) with your API keys and location details.

4. **Test the Display**:
   - Run the script to verify it works:
     ```bash
     python3 fam_chores.py
     ```

---

## Usage

### Automatic Startup

To run the script automatically on startup, follow these steps:

1. Open the crontab editor:
   ```bash
   crontab -e
2. Add the following line to run the script at boot:
   ```bash
   @reboot /usr/bin/python3 /home/pi/chore-calendar/fam_chores.py
3. Save and exit
   ```bash
   sudo reboot
