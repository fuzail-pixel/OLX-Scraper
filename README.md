# OLX Scraper

A full stack web application for scraping OLX.in listings using Flask, Playwright, and BeautifulSoup.

## 📖 Overview

This project allows users to extract product listings from OLX.in through a convenient web interface. Simply enter your search query, and the app will retrieve all relevant listings, displaying them directly in the browser with options to download in JSON or CSV format.

## ✨ Features

* Search for any product listings on OLX.in
* Dual scraping approach:
  * Fast fallback using `requests + BeautifulSoup`
  * Headless browser scraping using `Playwright` for dynamic content
* Export results in JSON, CSV, or both formats
* Responsive Bootstrap UI for mobile and desktop use
* Auto-generated downloads stored in organized folders
* Comprehensive logging for debugging

## 🛠️ Technologies Used

* **Backend:** Flask, Python
* **Scraping:** Playwright, BeautifulSoup, Requests
* **Frontend:** HTML, Bootstrap 5
* **Deployment:** Gunicorn-ready

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

* Python 3.9+
* Google Chrome or Chromium browser (for Playwright)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/fuzail-pixel/OLX-Scraper.git
   cd olx-scraper
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows, use: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright Browsers**

   ```bash
   playwright install
   ```

### Running the Application

Start the Flask server:

```bash
python app.py
```

By default, the server runs on `http://localhost:5000`.

### Usage

* Open `http://localhost:5000` in your browser
* Enter your search query in the provided field
* Click "Search" to start scraping
* View results directly in the browser
* Download results in your preferred format (JSON/CSV)

## 📁 Project Structure

```
OLX SCRAPER/
├── static/
│   └── downloads/           # Auto-saved JSON & CSV results
├── templates/
│   └── index.html           # Main frontend template
├── venv/                    # Virtual environment (excluded from Git)
├── app.py                   # Flask backend application
├── requirements.txt         # Python dependencies
├── scraper.log              # Runtime logs
```

## 📝 Notes

* For dynamic content scraping, ensure Chromium is properly installed for Playwright
* Logs are written to `scraper.log` to assist with debugging
* Supports up to 10 pages per query
* Handles rate-limiting with automatic retry mechanism
* The app is designed to be respectful of OLX's website by adding proper delays

## 🤝 Contributing

Contributions are welcome! Feel free to fork this repo, create a new branch, and submit a pull request.

## 📃 License

This project is licensed under the GPL-3.0 License.

## 📧 Contact

Feel free to reach out on [LinkedIn](https://linkedin.com/in/fuzail-rehman-31a755241/) or [GitHub](https://github.com/fuzail-pixel) if you have any questions or feedback.

---

Thanks for using the OLX Scraper! 😊
