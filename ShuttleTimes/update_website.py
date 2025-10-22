#!/usr/bin/env python3
"""
Northwestern Bus Website Updater for GitHub Pages
Updates the index.html file with current bus times by replacing placeholder content
"""

import subprocess
import sys
import os
from datetime import datetime
import re

def run_bus_script(direction):
    """Execute the bus script and return the output"""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bus_script_path = os.path.join(script_dir, 'bus_api_client.py')

        # Run the bus script with the specified direction
        result = subprocess.run(
            [sys.executable, bus_script_path, direction],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=script_dir
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error loading {direction} buses"

    except subprocess.TimeoutExpired:
        return f"Error: {direction} request timed out"
    except Exception as e:
        return f"Error loading {direction} buses"

def format_bus_output_for_html(output):
    """Convert bus script output to HTML format"""
    if not output or output.startswith("Error"):
        return f'<div class="error">{output or "No data available"}</div>'

    # Split into lines and process
    lines = output.strip().split('\n')
    html_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Header line (Next X buses...)
        if line.startswith("Next "):
            html_lines.append(f'<div class="bus-header">{line}</div>')
        # Individual bus times (  1. 8:15 PM (20 min) - OnTime)
        elif line.strip().startswith(("1.", "2.")):
            # Parse the line: "  1. 8:15 PM (20 min) - OnTime"
            parts = line.strip().split(" - ")
            if len(parts) == 2:
                time_part = parts[0]  # "1. 8:15 PM (20 min)"
                status = parts[1]     # "OnTime"

                # Extract time and minutes
                if "(" in time_part and ")" in time_part:
                    before_paren = time_part.split("(")[0].strip()  # "1. 8:15 PM "
                    in_paren = time_part.split("(")[1].split(")")[0]  # "20 min"

                    # Extract just the time
                    time_only = before_paren.split(". ", 1)[1] if ". " in before_paren else before_paren

                    html_lines.append(f'''
                    <div class="bus-time-item">
                        <span class="time">{time_only}</span>
                        <span class="minutes">{in_paren}</span>
                        <span class="status">{status}</span>
                    </div>
                    ''')
                else:
                    html_lines.append(f'<div style="padding: 5px 0;">{line}</div>')
            else:
                html_lines.append(f'<div style="padding: 5px 0;">{line}</div>')

    if not html_lines:
        return '<div class="error">No upcoming buses found</div>'

    return '\n'.join(html_lines)

def update_html_file():
    """Update the index.html file with current bus data"""

    # File paths
    html_file = 'index.html'

    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found")
        return False

    print("Fetching current bus times...")

    # Get current bus times
    outbound_output = run_bus_script('outbound')
    inbound_output = run_bus_script('inbound')

    print(f"Outbound: {outbound_output[:50]}...")
    print(f"Inbound: {inbound_output[:50]}...")

    # Format for HTML
    outbound_html = format_bus_output_for_html(outbound_output)
    inbound_html = format_bus_output_for_html(inbound_output)

    # Get current timestamp
    current_time = datetime.utcnow().strftime('%I:%M:%S %p UTC on %B %d, %Y')

    # Read current HTML
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading {html_file}: {e}")
        return False

    # Replace outbound data
    outbound_pattern = r'<!-- OUTBOUND_DATA_PLACEHOLDER -->.*?<!-- END_OUTBOUND_DATA_PLACEHOLDER -->'
    outbound_replacement = f'<!-- OUTBOUND_DATA_PLACEHOLDER -->\n{outbound_html}\n                    <!-- END_OUTBOUND_DATA_PLACEHOLDER -->'
    html_content = re.sub(outbound_pattern, outbound_replacement, html_content, flags=re.DOTALL)

    # Replace inbound data
    inbound_pattern = r'<!-- INBOUND_DATA_PLACEHOLDER -->.*?<!-- END_INBOUND_DATA_PLACEHOLDER -->'
    inbound_replacement = f'<!-- INBOUND_DATA_PLACEHOLDER -->\n{inbound_html}\n                    <!-- END_INBOUND_DATA_PLACEHOLDER -->'
    html_content = re.sub(inbound_pattern, inbound_replacement, html_content, flags=re.DOTALL)

    # Replace timestamp
    timestamp_pattern = r'<!-- TIMESTAMP_PLACEHOLDER -->.*?<!-- END_TIMESTAMP_PLACEHOLDER -->'
    timestamp_replacement = f'<!-- TIMESTAMP_PLACEHOLDER -->{current_time}<!-- END_TIMESTAMP_PLACEHOLDER -->'
    html_content = re.sub(timestamp_pattern, timestamp_replacement, html_content, flags=re.DOTALL)

    # Write updated HTML
    try:
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Successfully updated {html_file}")
        return True
    except Exception as e:
        print(f"Error writing {html_file}: {e}")
        return False

def main():
    """Main function"""
    print("Northwestern Bus Times - Website Updater")
    print("=" * 50)

    success = update_html_file()

    if success:
        print("🚌 Bus times updated successfully!")
        return 0
    else:
        print("❌ Failed to update bus times")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)