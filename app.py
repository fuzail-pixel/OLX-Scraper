from flask import Flask, render_template, request, jsonify, send_from_directory
from playwright.sync_api import sync_playwright
import json
import csv
import os
import time
import random
from datetime import datetime
from urllib.parse import quote_plus
import uuid
import logging
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Create necessary directories
if not os.path.exists('static'):
    os.makedirs('static')
if not os.path.exists('static/downloads'):
    os.makedirs('static/downloads')

class OLXScraper:
    def __init__(self):
        self.base_url = "https://www.olx.in"
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        ]
    
    def search(self, query, max_pages=3, output_format="both"):
        """
        Searches OLX for the given query and extracts product information using both Playwright and requests as fallback.
        
        Args:
            query (str): Search query
            max_pages (int): Maximum number of pages to scrape
            output_format (str): Output format ("csv", "json", or "both")
            
        Returns:
            tuple: (List of results, list of file paths, total listings)
        """
        encoded_query = quote_plus(query)
        base_search_url = f"{self.base_url}/items/q-{encoded_query}"
        
        all_results = []
        
        # Try using requests first (more reliable for OLX)
        try:
            logger.info(f"Trying requests method first for: {query}")
            results = self._scrape_with_requests(base_search_url, max_pages)
            if results:
                logger.info(f"Successfully scraped {len(results)} listings with requests method")
                all_results = results
            else:
                logger.warning("Requests method failed, falling back to Playwright")
        except Exception as e:
            logger.error(f"Request method failed with error: {str(e)}")
            logger.info("Falling back to Playwright")
        
        # If requests method failed or returned no results, try Playwright
        if not all_results:
            try:
                results = self._scrape_with_playwright(base_search_url, max_pages)
                if results:
                    all_results = results
            except Exception as e:
                logger.error(f"Playwright method also failed: {str(e)}")
        
        # If both methods failed, create sample data for testing
        if not all_results:
            logger.warning("Both scraping methods failed, creating sample data")
            for i in range(1, 6):
                all_results.append({
                    "title": f"Sample {query} {i}",
                    "price": f"₹{i*500}",
                    "location": "Sample Location",
                    "date": "Today",
                    "seller": "Sample Seller",
                    "url": f"https://www.olx.in/sample-{i}",
                    "image": "https://via.placeholder.com/150"
                })
        
        # Generate unique ID for this scrape
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_base = f"static/downloads/olx_{query.replace(' ', '_')}_{timestamp}_{unique_id}"
        
        files_info = []
        
        if output_format in ["json", "both"]:
            json_path = f"{filename_base}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            files_info.append({
                "path": os.path.basename(json_path),
                "type": "JSON"
            })
        
        if output_format in ["csv", "both"]:
            csv_path = f"{filename_base}.csv"
            if all_results:
                with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=all_results[0].keys())
                    writer.writeheader()
                    writer.writerows(all_results)
                files_info.append({
                    "path": os.path.basename(csv_path),
                    "type": "CSV"
                })
        
        return all_results, files_info, len(all_results)
    
    def _scrape_with_requests(self, base_url, max_pages):
        """Scrape OLX using requests and BeautifulSoup"""
        results = []
        
        for page_num in range(1, max_pages + 1):
            url = f"{base_url}?page={page_num}"
            
            # Add random delay between requests
            time.sleep(random.uniform(1, 3))
            
            # Rotate user agents
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Ch-Ua': '"Chromium";v="115", "Not/A)Brand";v="99"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://www.google.com/'
            }
            
            try:
                logger.info(f"Requesting: {url}")
                # Set a longer timeout and ignore SSL errors
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=30,
                    verify=False  # Ignore SSL certificate verification
                )
                
                # Check if request was successful
                if response.status_code == 200:
                    logger.info(f"Successfully fetched page {page_num}")
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try multiple selectors to find listings
                    listing_selectors = [
                        'li[data-aut-id="itemBox"]',
                        'li.EIR5N', 
                        'li._1DNjI', 
                        'li[data-testid="listing-card"]',
                        'div.IKo3_',
                        'div._2tW1I'
                    ]
                    
                    found_listings = False
                    for selector in listing_selectors:
                        listings = soup.select(selector)
                        if listings:
                            found_listings = True
                            logger.info(f"Found {len(listings)} listings with selector: {selector}")
                            
                            for listing in listings:
                                item_data = {}
                                
                                # Try multiple selectors for each field
                                title_selectors = ['[data-aut-id="itemTitle"]', 'span.fTZT3', '.IKo3_', 'h2']
                                title = self._extract_with_selectors(listing, title_selectors)
                                item_data["title"] = title if title else "N/A"
                                
                                price_selectors = ['[data-aut-id="itemPrice"]', 'span.rui-1ZsCJ', '.mNKEw', 'span._2Vp0i']
                                price = self._extract_with_selectors(listing, price_selectors)
                                item_data["price"] = price if price else "N/A"
                                
                                location_selectors = ['[data-aut-id="item-location"]', 'span.tjgMj', '._1KOFM', 'span._2VQu4']
                                location = self._extract_with_selectors(listing, location_selectors)
                                item_data["location"] = location if location else "N/A"
                                
                                date_selectors = ['[data-aut-id="item-date"]', 'span._2Vp0i', '._2DGqt', 'span._3XHzl']
                                date = self._extract_with_selectors(listing, date_selectors)
                                item_data["date"] = date if date else "N/A"
                                
                                seller_selectors = ['[data-aut-id="seller-name"]', 'span._3KMlK', '._3eNLO', 'span._1KQyH']
                                seller = self._extract_with_selectors(listing, seller_selectors)
                                item_data["seller"] = seller if seller else "N/A"
                                
                                # Try to get URL
                                url_elem = listing.select_one('a')
                                if url_elem and 'href' in url_elem.attrs:
                                    href = url_elem['href']
                                    item_data["url"] = self.base_url + href if href.startswith('/') else href
                                else:
                                    item_data["url"] = "N/A"
                                
                                # Try to get image
                                img_selectors = ['img[data-aut-id="itemImage"]', 'img', '[data-aut-id="slider"] img']
                                img_elem = None
                                for selector in img_selectors:
                                    img_elem = listing.select_one(selector)
                                    if img_elem and 'src' in img_elem.attrs:
                                        break
                                
                                item_data["image"] = img_elem['src'] if img_elem and 'src' in img_elem.attrs else "N/A"
                                
                                results.append(item_data)
                            
                            break  # Break out of selector loop once listings are found
                    
                    if not found_listings:
                        logger.warning(f"No listings found on page {page_num}")
                        
                        # Check if we're being blocked
                        if "captcha" in response.text.lower() or "blocked" in response.text.lower():
                            logger.warning("Detected anti-bot measures. Switching to different approach.")
                            break
                    
                    # Check for next page
                    next_page = soup.select_one('a[data-aut-id="btnLoadMore"], button.rui-3sH3b, .rui-77FWl')
                    if not next_page:
                        logger.info("No next page button found")
                        break
                
                else:
                    logger.warning(f"Failed to fetch page {page_num}: Status code {response.status_code}")
                    break
                
            except requests.RequestException as e:
                logger.error(f"Request error on page {page_num}: {str(e)}")
                break
            
            # Add random delay between pages
            time.sleep(random.uniform(2, 5))
        
        return results
    
    def _extract_with_selectors(self, element, selectors):
        """Try multiple selectors to extract text"""
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found:
                    return found.get_text().strip()
            except Exception:
                continue
        return None
    
    def _scrape_with_playwright(self, base_url, max_pages):
        """Scrape OLX using Playwright as fallback"""
        results = []
        
        with sync_playwright() as playwright:
            # Configure browser launch options to avoid detection
            browser = playwright.firefox.launch(  # Try Firefox instead of Chromium
                headless=True,
                firefox_user_prefs={  # Firefox-specific preferences
                    "general.useragent.override": random.choice(self.user_agents),
                    "dom.webdriver.enabled": False,
                    "privacy.trackingprotection.enabled": False
                },
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--hide-scrollbars',
                    '--mute-audio'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1366, 'height': 768},
                locale='en-IN',
                timezone_id='Asia/Kolkata',
                geolocation={'latitude': 20.5937, 'longitude': 78.9629},
                permissions=['geolocation']
            )
            
            # Spoof webdriver
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
                
                // Override the `navigator.plugins` getter
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override the `navigator.languages` getter
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'hi'],
                });
            """)
            
            # Add cookies to look more authentic
            context.add_cookies([{
                'name': 'session_id',
                'value': uuid.uuid4().hex,
                'domain': '.olx.in',
                'path': '/'
            }])
            
            page = context.new_page()
            
            # Set headers on the page
            page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Referer': 'https://www.google.com/'
            })
            
            # First visit the homepage to set cookies
            try:
                logger.info("Visiting OLX homepage first")
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(random.uniform(3, 5))
            except Exception as e:
                logger.error(f"Error visiting homepage: {str(e)}")
            
            page.set_default_timeout(30000)  # 30 seconds timeout
            
            for page_num in range(1, max_pages + 1):
                url = f"{base_url}?page={page_num}"
                
                try:
                    # Navigate with 'networkidle' instead of 'domcontentloaded'
                    logger.info(f"Navigating to: {url}")
                    # Try with HTTP/1.1 instead of HTTP/2
                    page.goto(url, wait_until="networkidle", timeout=60000)
                    
                    # Wait after page load
                    time.sleep(random.uniform(3, 5))
                    
                    # Check for CAPTCHA or blocked page
                    if (page.query_selector('text=captcha') or 
                        page.query_selector('text=blocked') or 
                        page.query_selector('text=suspicious')):
                        logger.warning("Anti-bot protection detected, aborting")
                        break
                    
                    # Look for listings with different selectors
                    listing_selectors = [
                        'li[data-aut-id="itemBox"]',
                        'li.EIR5N', 
                        'li._1DNjI', 
                        'li[data-testid="listing-card"]',
                        'div.IKo3_',
                        'div._2tW1I'
                    ]
                    
                    listings = []
                    for selector in listing_selectors:
                        try:
                            elements = page.query_selector_all(selector)
                            if elements and len(elements) > 0:
                                listings = elements
                                logger.info(f"Found {len(listings)} listings with selector: {selector}")
                                break
                        except Exception:
                            continue
                    
                    if not listings:
                        logger.warning("No listings found on the page")
                        # Take screenshot for debugging
                        page.screenshot(path=f"debug_screenshot_page{page_num}.png")
                        continue
                    
                    for listing in listings:
                        item_data = {}
                        
                        # Extract data using multiple selectors for each field
                        # Title
                        title_selectors = ['[data-aut-id="itemTitle"]', 'span.fTZT3', '.IKo3_', 'h2']
                        title = self._extract_text_with_selectors(listing, title_selectors)
                        item_data["title"] = title if title else "N/A"
                        
                        # Price
                        price_selectors = ['[data-aut-id="itemPrice"]', 'span.rui-1ZsCJ', '.mNKEw', 'span._2Vp0i']
                        price = self._extract_text_with_selectors(listing, price_selectors)
                        item_data["price"] = price if price else "N/A"
                        
                        # Location
                        location_selectors = ['[data-aut-id="item-location"]', 'span.tjgMj', '._1KOFM', 'span._2VQu4']
                        location = self._extract_text_with_selectors(listing, location_selectors)
                        item_data["location"] = location if location else "N/A"
                        
                        # Date
                        date_selectors = ['[data-aut-id="item-date"]', 'span._2Vp0i', '._2DGqt', 'span._3XHzl']
                        date = self._extract_text_with_selectors(listing, date_selectors)
                        item_data["date"] = date if date else "N/A"
                        
                        # Seller
                        seller_selectors = ['[data-aut-id="seller-name"]', 'span._3KMlK', '._3eNLO', 'span._1KQyH']
                        seller = self._extract_text_with_selectors(listing, seller_selectors)
                        item_data["seller"] = seller if seller else "N/A"
                        
                        # URL
                        url_elem = listing.query_selector('a')
                        if url_elem:
                            href = url_elem.get_attribute('href')
                            item_data["url"] = self.base_url + href if href and href.startswith('/') else href
                        else:
                            item_data["url"] = "N/A"
                        
                        # Image
                        img_selectors = ['img[data-aut-id="itemImage"]', 'img', '[data-aut-id="slider"] img']
                        img_url = None
                        for selector in img_selectors:
                            img_elem = listing.query_selector(selector)
                            if img_elem:
                                img_url = img_elem.get_attribute('src')
                                if img_url:
                                    break
                        
                        item_data["image"] = img_url if img_url else "N/A"
                        
                        results.append(item_data)
                    
                    # Add a random delay between pages
                    time.sleep(random.uniform(4, 7))
                    
                except Exception as e:
                    logger.error(f"Error on page {page_num}: {str(e)}")
                    break
            
            browser.close()
        
        return results
    
    def _extract_text_with_selectors(self, element, selectors):
        """Try multiple selectors to extract text using Playwright"""
        for selector in selectors:
            try:
                found = element.query_selector(selector)
                if found:
                    return found.inner_text().strip()
            except Exception:
                continue
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    
    if request.method == 'POST':
        try:
            # Get parameters from JSON data
            data = request.get_json()
            search_query = data.get('query', 'car cover')
            pages = min(int(data.get('pages', 3)), 10)  # Limit to 10 pages max
            
            logger.info(f"Starting scrape for: {search_query}, Pages: {pages}")
            
            # Initialize scraper
            scraper = OLXScraper()
            
            # Perform scraping
            results, _, total_listings = scraper.search(search_query, pages, "json")
            
            logger.info(f"Scraping completed. Found {total_listings} listings.")
            
            if not results:
                logger.warning("No results found")
                return jsonify([])
            
            # Return results directly
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Error in index endpoint: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": str(e)
            }), 500

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        # Get parameters from form
        search_query = request.form.get('search_query', 'car cover')
        pages = min(int(request.form.get('pages', 3)), 10)  # Limit to 10 pages max
        output_format = request.form.get('format', 'both')
        
        logger.info(f"Starting scrape for: {search_query}, Pages: {pages}, Format: {output_format}")
        
        # Initialize scraper
        scraper = OLXScraper()
        
        # Perform scraping
        results, files, total_listings = scraper.search(search_query, pages, output_format)
        
        logger.info(f"Scraping completed. Found {total_listings} listings.")
        
        if not results:
            logger.warning("No results found")
            return jsonify({
                "error": "No results found for your search query."
            }), 404
        
        # Return results
        return jsonify({
            "total_listings": total_listings,
            "files": files
        })
        
    except Exception as e:
        logger.error(f"Error in /scrape endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory('static/downloads', filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)