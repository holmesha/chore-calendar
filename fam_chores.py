#!/usr/bin/env python3

import sys
import time
import requests
from PIL import Image, ImageDraw, ImageFont
import epd7in5b_V2  # E-Ink Display Driver
from datetime import datetime
import json

# Constants
API_TOKEN = "INSERT YOUR TOKEN"  # Replace with your Todoist API token
PROJECT_ID = "INSERT YOUR PROJECT ID"        # Replace with your Todoist project ID (NUMBER LISTED IN THE URL WHEN THE PROJECT IS OPEN)
LATITUDE = "XXX.XXX"  # Replace with your latitude
LONGITUDE = "-XXX.XXX"  # Replace with your longitude
TALLY_FILE = "/home/pi/fam_chores/task_tally.json"  # File to store the tally persistently

def load_tally():
    """
    Load the weekly task tally from a file.
    Reset the tally if today is Monday.
    """
    try:
        with open(TALLY_FILE, "r") as f:
            tally = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):  # Handle missing or invalid file
        tally = {"tasks_completed": 0, "counted_task_ids": [], "last_reset": None}

    # Debug: Print tally after loading
    print(f"Loaded tally: {tally}")

    # Reset if it's Monday and hasn't been reset today
    today = datetime.now().strftime("%A")
    if today == "Monday" and tally.get("last_reset") != today:
        tally = {"tasks_completed": 0, "counted_task_ids": [], "last_reset": today}
        print("Resetting tally for the new week.")

    return tally

def save_tally(tally):
    """
    Save the weekly task tally to a file.
    """
    # Debug: Print tally before saving
    print(f"Saving tally: {tally}")

    with open(TALLY_FILE, "w") as f:
        json.dump(tally, f)

def fetch_todoist_sections(api_token, project_id):
    url = f"https://api.todoist.com/rest/v2/sections?project_id={project_id}"
    headers = {"Authorization": f"Bearer {api_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sections = response.json()
        return {section['id']: section['name'] for section in sections}
    else:
        print(f"Error fetching sections: {response.status_code}")
        return {}

def fetch_completed_tasks(api_token, project_id):
    """
    Fetch completed tasks for the specified project.
    """
    url = "https://api.todoist.com/sync/v9/completed/get_all"
    headers = {"Authorization": f"Bearer {api_token}"}
    params = {"project_id": project_id}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("items", [])
    else:
        print(f"Error fetching completed tasks: {response.status_code}")
        return []

def fetch_tasks_by_section(api_token, project_id):
    sections = fetch_todoist_sections(api_token, project_id)

    url = f"https://api.todoist.com/rest/v2/tasks?project_id={project_id}"
    headers = {"Authorization": f"Bearer {api_token}"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        tasks = response.json()

        # Fetch completed tasks
        completed_tasks = fetch_completed_tasks(api_token, project_id)
        completed_task_ids = {task["task_id"] for task in completed_tasks}

        # Load the tally to check previously counted tasks
        tally = load_tally()
        counted_task_ids = set(tally.get("counted_task_ids", []))

        # Identify new completions
        new_completions = completed_task_ids - counted_task_ids
        tally["tasks_completed"] += len(new_completions)
        tally["counted_task_ids"] = list(counted_task_ids.union(completed_task_ids))
        tally["last_reset"] = datetime.now().strftime("%A")
        
        # Save updated tally
        save_tally(tally)

        # Debug: Verify the tally file after saving
        print(f"Tally after processing: {tally}")

        # Group tasks by section
        tasks_by_section = {section: {"incomplete": [], "completed_count": 0} for section in sections.values()}
        for task in tasks:
            section_id = task.get("section_id")
            section_name = sections.get(section_id, "Uncategorized")
            if task["id"] in completed_task_ids:
                tasks_by_section[section_name]["completed_count"] += 1
            else:
                tasks_by_section[section_name]["incomplete"].append(task["content"])

        return tasks_by_section
    else:
        print(f"Error fetching tasks: {response.status_code}")
        return {}

def fetch_weather_nws(lat, lon):
    """
    Fetch weather forecast using the NWS API.
    """
    try:
        # Fetch weather station data
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_response = requests.get(points_url)
        points_data = points_response.json()
        
        # Extract forecast URL
        forecast_url = points_data['properties']['forecast']
        
        # Fetch forecast data
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()
        
        # Extract today's forecast
        today_forecast = forecast_data['properties']['periods'][0]
        temperature = today_forecast['temperature']
        temperature_unit = today_forecast['temperatureUnit']
        short_forecast = today_forecast['shortForecast']
        
        return f"{short_forecast}, {temperature}°{temperature_unit}"
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return "Weather data unavailable"

def draw_todoist_tasks(epd, tasks_by_section, weather_info):
    """
    Draw Todoist tasks in horizontal (landscape) mode, with a styled layout.
    """
    # Load weekly tally
    tally = load_tally()

    # Swap dimensions for horizontal layout
    landscape_width, landscape_height = epd.width, epd.height

    # Create canvases
    black_image = Image.new('1', (landscape_width, landscape_height), 255)
    red_image = Image.new('1', (landscape_width, landscape_height), 255)
    draw_black = ImageDraw.Draw(black_image)
    draw_red = ImageDraw.Draw(red_image)

    # Add title in bold red text
    title_text = "Family Chores"
    title_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSansBold.ttf', 48)
    title_size = draw_red.textsize(title_text, font=title_font)

    title_x = (landscape_width - title_size[0]) // 2  # Center the title
    title_y = 10
    draw_red.text((title_x, title_y), title_text, font=title_font, fill=0)

    # Add date in non-bold red text
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    date_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 36)
    date_size = draw_red.textsize(current_date, font=date_font)

    date_x = (landscape_width - date_size[0]) // 2  # Center the date
    date_y = title_y + title_size[1] + 10
    draw_red.text((date_x, date_y), current_date, font=date_font, fill=0)

    # Display weekly tally below the date
    tally_text = f"Weekly Completed Tasks: {tally['tasks_completed']}"
    tally_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 28)
    tally_size = draw_black.textsize(tally_text, font=tally_font)

    tally_x = (landscape_width - tally_size[0]) // 2
    tally_y = date_y + date_size[1] + 20
    draw_black.text((tally_x, tally_y), tally_text, font=tally_font, fill=0)

    # Adjust y_offset for sections
    y_offset = tally_y + tally_size[1] + 20

    # Fonts for tasks and completed counts
    task_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 24)
    italic_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf', 24)  # Italic font

    # Divide screen into thirds for sections
    section_width = landscape_width // 3

    for idx, (section, tasks) in enumerate(tasks_by_section.items()):
        if idx >= 3:  # Limit to 3 sections
            break

        x_offset = idx * section_width + 10  # Section starting x position

        # Draw section header
        draw_red.text((x_offset, y_offset), section, font=date_font, fill=0)
        header_size = draw_black.textsize(section, font=date_font)

        # Add red underline below the section header
        draw_red.line(
            (x_offset, y_offset + header_size[1] + 2, x_offset + section_width - 10, y_offset + header_size[1] + 2),
            fill=0,
            width=2
        )

        # Draw completed count below the header in italics
        completed_text = f"Completed - {tasks['completed_count']}"
        draw_black.text((x_offset, y_offset + header_size[1] + 10), completed_text, font=italic_font, fill=0)

        # Draw tasks
        y_current = y_offset + header_size[1] + 40  # Adjust to account for "Completed" text
        for task in tasks["incomplete"][:5]:  # Limit to 5 tasks per section
            task_lines = wrap_text(task, task_font, section_width - 40, draw_black)
            # Calculate task height for multi-line tasks
            task_height = len(task_lines) * (task_font.getsize("Test")[1] + 5)

            # Draw single red box for the task
            box_size = 12
            draw_red.rectangle((x_offset, y_current, x_offset + box_size, y_current + box_size), outline=0, width=2)
            # Draw each line of the task text
            for line in task_lines:
                draw_black.text((x_offset + box_size + 5, y_current), line, font=task_font, fill=0)
                y_current += task_font.getsize(line)[1] + 5  # Add line spacing
            # Add padding after the task
            y_current += 5

    # Add red line above the weather section
    line_y = landscape_height - 70
    draw_red.line((10, line_y, landscape_width - 10, line_y), fill=0, width=2)

    # Add weather info at the bottom
    weather_font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf', 30)
    weather_x = (landscape_width - draw_black.textsize(weather_info, font=weather_font)[0]) // 2
    weather_y = line_y + 10  # Position below the line
    draw_black.text((weather_x, weather_y), weather_info, font=weather_font, fill=0)

    # Rotate the canvas for horizontal display (270 degrees)
    black_image = black_image.rotate(270, expand=True)
    red_image = red_image.rotate(270, expand=True)

    # Update the e-ink display
    epd.display(epd.getbuffer(black_image), epd.getbuffer(red_image))
    print("Display updated successfully.")

def wrap_text(text, font, max_width, draw):
    """
    Wrap text to fit within a specified width.
    """
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if draw.textsize(test_line, font=font)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def main():
    try:
        print("Initializing e-ink display...")
        epd = epd7in5b_V2.EPD()
        epd.init()
        epd.Clear()
        print("Display initialized and cleared.")

        print(f"Fetching tasks from project: {PROJECT_ID}")
        tasks_by_section = fetch_tasks_by_section(API_TOKEN, PROJECT_ID)
        if not tasks_by_section:
            print("No tasks found in the project.")
            return

        print("Fetching weather information...")
        weather_info = fetch_weather_nws(LATITUDE, LONGITUDE)

        print("Drawing tasks and weather on the display...")
        draw_todoist_tasks(epd, tasks_by_section, weather_info)

        print("Tasks and weather displayed successfully.")

    except IOError as e:
        print(f"IOError: {e}")
    except KeyboardInterrupt:
        print("Program interrupted. Exiting...")
        epd7in5b_V2.epdconfig.module_exit()
        sys.exit()

if __name__ == "__main__":
    try:
        while True:  # Refresh every 15 minutes
            main()
            print("Sleeping for 15 minutes...")
            time.sleep(900)  # 15 minutes in seconds
    except KeyboardInterrupt:
        print("Program interrupted. Exiting...")
        sys.exit()


