# FireProfile

A Firefox profile manager that allows you to open URLs in specific Firefox profiles based on domain rules.

## Features

- Profile Management: Create, edit, and delete Firefox profiles with custom command lines
- Domain Rules: Associate domains with specific Firefox profiles
- Profile Selector: Quick profile selection for unmatched domains
- Desktop Integration: Configure as your system's default browser

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Configure as default browser:
   - Create a desktop file:
```bash
mkdir -p ~/.local/share/applications
cp fireprofile.desktop ~/.local/share/applications/
```
   - Set as default browser in your desktop environment settings

## Usage

1. Run the configuration window:
```bash
python fireprofile.py --config
```

2. Add your Firefox profiles and domain rules

3. When clicking links from other applications:
   - If the domain matches a rule, it will open in the specified profile
   - If no rule exists, a profile selector dialog will appear

## Configuration

The configuration is stored in `~/.fireprofile.json` and includes:
- Profile definitions with command lines
- Domain rules mapping to profiles 