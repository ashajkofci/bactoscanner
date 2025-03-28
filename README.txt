# Bactosense Data Downloader

A GUI application for downloading data files from BactoSense devices

## Overview

This application allows users to easily connect to a BactoSense device via its IP address or URL and download measurement data, including FCS files and diagnostic information. It organizes the downloaded files into a clean directory structure for easy access and analysis.

It can be used with BactoLink / Teltonika VPN by using the proxy URL in the IP address field.

## Features

- Connect to BactoSense devices using IP address or URL
- User authentication with username and password
- Option to download only FCS files or all available data files
- Downloads measurement summaries, FCS files, debug and diagnostic information
- Organizes files into a structured directory format
- Abort functionality to stop downloads in progress
- Interactive console to track download progress

## Requirements

- Windows

## Usage

1. Run the program:

2. Enter connection details:
   - IP Address or URL of your BactoSense device
   - Username (default: admin)
   - Password

3. Select download option:
   - All files: Downloads FCS files, PNG summaries, and diagnostic files (CSV, JSON). It is needed for further upload in the Cloud or Demo mode.
   - Only FCS: Downloads only the flow cytometry data files and PNG summaries

4. Click "Start Download" to begin the process
   - Progress will be displayed in the console output
   - Use the "Abort" button if you need to stop the download

## File Organization

Downloaded files are organized as follows:

```
[IP_address_with_underscores]/
│
├── auto/                      # Automatic measurements
│   ├── [date] [measurement]/  # Individual measurement directory
│   │   ├── [date]_[name]_events.fcs     # FCS file
│   │   ├── [date]_[name]_summary.png    # Summary image
│   │   └── debug/                       # If "All files" selected
│   │       ├── [date]_diagnostics.csv
│   │       ├── [date]_signal_errors.csv
│   │       ├── [date]_results.json
│   │       └── [date]_gate.json
│   │
│   └── [More measurements...]
│
└── manual/                    # Manual measurements
    └── [Same structure as auto]
```

## Troubleshooting

- If connection fails, verify the IP address/URL is correct and the device is accessible on your network
- Ensure you have the correct username and password
- Check your network connection if downloads are failing
- For permission errors when saving files, ensure you have write permissions for the directory

## License

Developed by Adrian Shajkofci (2023-2025) for bNovate Technologies SA.