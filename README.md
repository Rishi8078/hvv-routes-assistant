# HVV Routes Home Assistant Integration

## Overview
This custom integration allows you to track public transit routes in the Hamburg area using the HVV API.

## Features
- Fetch real-time route information
- Configure start and destination stations
- Periodic route data updates

## Installation

### HACS (Recommended)
1. Add this repository to HACS.
2. Install the integration.
3. Restart Home Assistant.

### Manual Installation
1. Copy the `hvv` folder to `custom_components`.
2. Restart Home Assistant.

## Configuration
Configuration is done through the Home Assistant UI:
1. Go to **Configuration > Integrations**.
2. Click **"+"** to add a new integration.
3. Search for **"HVV"**.
4. Enter your credentials and route details.

## Requirements
- HVV API Credentials
- Internet Connection
- Python 3.8+

## Troubleshooting
- Ensure internet connectivity.
- Verify HVV API credentials.
- Check Home Assistant logs for detailed error messages.

## Contributing
Contributions are welcome! Please open issues or submit pull requests.

## License
[Your License Here]
