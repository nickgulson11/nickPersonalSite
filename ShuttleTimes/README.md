# Northwestern Bus Times

A real-time bus tracking website for Northwestern University's Intercampus Shuttle service. This website displays live arrival and departure times for both Inbound and Outbound routes.

## 🚌 Live Website

**[View Live Bus Times](https://your-username.github.io/northwestern-bus-times/)**

The website automatically updates every 5 minutes with the latest bus information.

## 📱 Features

- **Real-time Updates**: Live bus arrival/departure times
- **Two Routes**:
  - **Outbound** (Chicago → Evanston): Next buses arriving at Ward
  - **Inbound** (Evanston → Chicago): Next buses departing from Tech
- **Auto-refresh**: Updates every 5 minutes via GitHub Actions
- **Mobile Friendly**: Responsive design works on all devices
- **Clean UI**: Beautiful gradient design with Northwestern colors

## 🛠 Technical Details

### Architecture
- **Frontend**: Static HTML/CSS hosted on GitHub Pages
- **Backend**: Python script that fetches live data from Northwestern's TripShot API
- **Automation**: GitHub Actions runs every 5 minutes to update the site
- **No Client-side JavaScript API calls**: Avoids CORS issues by processing data server-side

### Files Structure
```
├── index.html                     # Main website (GitHub Pages serves this)
├── bus_api_client.py              # Core bus data fetching logic
├── update_website.py              # Updates index.html with fresh data
├── .github/workflows/
│   └── update-bus-times.yml       # GitHub Actions workflow
└── requirements.txt               # Python dependencies
```

### How It Works
1. **GitHub Actions** runs `update_website.py` every 5 minutes
2. **Python script** calls Northwestern's TripShot API for both routes
3. **Data processing** filters for specific stops and formats the response
4. **HTML update** replaces placeholder content in `index.html`
5. **Auto-commit** pushes the updated HTML back to the repository
6. **GitHub Pages** automatically serves the updated website

## 🚀 Setup Instructions

### For GitHub Pages Deployment

1. **Fork this repository**
2. **Enable GitHub Pages**:
   - Go to Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` → `/ (root)`
3. **Enable GitHub Actions**:
   - Go to Settings → Actions → General
   - Allow all actions and reusable workflows
4. **Update the repository URL**:
   - Edit `index.html` line 197 to point to your repository
5. **Trigger first update**:
   - Go to Actions → "Update Bus Times" → "Run workflow"

### For Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/northwestern-bus-times.git
   cd northwestern-bus-times
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Test the bus data fetching**:
   ```bash
   python3 bus_api_client.py outbound
   python3 bus_api_client.py inbound
   ```

4. **Update the website locally**:
   ```bash
   python3 update_website.py
   ```

5. **Open `index.html`** in your browser to view the result

## 📊 API Details

The system uses Northwestern University's TripShot API endpoints:

- **Outbound Route**: `23174203-507c-48fe-811a-5d13fcf7be65`
- **Inbound Route**: `EBEE9228-C993-4279-B7CE-8FCA0A46CA65`

Each API call:
- Automatically uses the current date
- Filters for specific bus stops
- Returns the next 2 upcoming buses
- Includes arrival times, delay status, and minutes until arrival

## 🎨 Customization

### Changing Update Frequency
Edit `.github/workflows/update-bus-times.yml`:
```yaml
schedule:
  - cron: '*/10 * * * *'  # Every 10 minutes instead of 5
```

### Styling
Modify the CSS in `index.html` to match your preferred colors and layout.

### Adding Routes
Extend `bus_api_client.py` with additional route configurations and update the HTML template accordingly.

## 📋 Requirements

- **Python 3.7+**
- **Dependencies**: `requests`, `beautifulsoup4`, `lxml`
- **GitHub Repository** with Pages and Actions enabled

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Disclaimer

This is an unofficial tool created for convenience. Bus times are provided by Northwestern University's official systems. Always verify important travel times with official sources.

---

*Last updated: Auto-generated via GitHub Actions*