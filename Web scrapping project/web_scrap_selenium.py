from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import csv
import os
import re

class DarazSeleniumScraper:
    """
    A scraper for extracting product information from Daraz search results using Selenium
    """
    
    def __init__(self, headless=True):
        """
        Initialize the scraper with browser settings
        
        Args:
            headless (bool): Whether to run browser in headless mode
        """
        self.base_url = "https://www.daraz.com.bd"
        self.search_url = f"{self.base_url}/catalog/?q="
        self.products = []
        
        # Set up Chrome options
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("--disable-popup-blocking")
        
        # Set up user agent
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Initialize the driver
        self.driver = None
    
    def start_browser(self):
        """Start the browser session"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.maximize_window()
            print("Browser started successfully.")
        except Exception as e:
            print(f"Error starting browser: {e}")
            raise
    
    def close_browser(self):
        """Close the browser session"""
        if self.driver:
            self.driver.quit()
            print("Browser closed successfully.")
    
    def search_product(self, query, max_pages=5):
        """
        Search for products with the given query and scrape results
        
        Args:
            query (str): Product search term
            max_pages (int): Maximum number of pages to scrape
        
        Returns:
            list: List of dictionaries containing product information
        """
        if not self.driver:
            self.start_browser()
        
        # Clear previous products if any
        self.products = []
        
        # Start the search
        search_url = f"{self.search_url}{query}"
        print(f"Navigating to: {search_url}")
        self.driver.get(search_url)
        
        # Wait for the page to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.box--ujueT"))
            )
        except TimeoutException:
            print("Timeout waiting for page to load. Check if Daraz has changed their layout.")
            return self.products
        
        # Handle cookie consent if present
        self._handle_cookie_consent()
        
        # Process pages
        current_page = 1
        
        while current_page <= max_pages:
            print(f"Scraping page {current_page}...")
            
            # Scroll down to load all products
            self._scroll_page()
            
            # Wait for products to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.box--ujueT"))
                )
                
                # Extract product information
                product_items = self.driver.find_elements(By.CSS_SELECTOR, "div.box--ujueT")
                
                # If no products found, break the loop
                if not product_items:
                    print(f"No products found on page {current_page} or reached the end of results.")
                    break
                
                # Process each product
                for item in product_items:
                    product_info = self._extract_product_info(item)
                    if product_info:
                        self.products.append(product_info)
                
                # Check if there's a next page
                if current_page < max_pages:
                    if not self._go_to_next_page(current_page + 1):
                        print(f"No more pages available after page {current_page}.")
                        break
                    
                # Move to the next page
                current_page += 1
                
                # Add a delay to avoid detection
                time.sleep(2)
                
            except TimeoutException:
                print(f"Timeout waiting for products on page {current_page}.")
                break
            except Exception as e:
                print(f"Error on page {current_page}: {e}")
                break
        
        return self.products
    
    def _handle_cookie_consent(self):
        """Handle cookie consent dialog if present"""
        try:
            cookie_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.cookie-btn"))
            )
            cookie_button.click()
            print("Cookie consent handled.")
        except TimeoutException:
            # No cookie consent dialog, continue
            pass
    
    def _scroll_page(self):
        """Scroll the page to load all products"""
        # Scroll in chunks to simulate human-like behavior
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Scroll down
            for i in range(0, last_height, 300):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.1)
            
            # Wait for page to load
            time.sleep(2)
            
            # Calculate new scroll height and compare with last scroll height
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def _go_to_next_page(self, next_page_number):
        """
        Navigate to the next page of results
        
        Args:
            next_page_number (int): The next page number
        
        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            # Look for the next page button
            next_button = self.driver.find_element(By.XPATH, f"//li[@title='Page {next_page_number}']")
            next_button.click()
            
            # Wait for the next page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.box--ujueT"))
            )
            return True
        except (TimeoutException, NoSuchElementException):
            try:
                # Fallback method: try to find next button by aria-label
                next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next Page']")
                next_button.click()
                
                # Wait for the next page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.box--ujueT"))
                )
                return True
            except (TimeoutException, NoSuchElementException):
                return False
    
    def _extract_product_info(self, item):
        """
        Extract relevant information from a product item
        
        Args:
            item (WebElement): Selenium WebElement of the product item
        
        Returns:
            dict: Dictionary containing product information
        """
        try:
            # Extract product name
            try:
                name_elem = item.find_element(By.CSS_SELECTOR, "div.title--wFj93")
                name = name_elem.text.strip()
            except NoSuchElementException:
                name = "N/A"
            
            # Extract product URL
            try:
                url_elem = item.find_element(By.TAG_NAME, "a")
                url = url_elem.get_attribute("href")
            except NoSuchElementException:
                url = "N/A"
            
            # Extract price
            try:
                price_elem = item.find_element(By.CSS_SELECTOR, "div.price--NVB62")
                price = price_elem.text.strip()
            except NoSuchElementException:
                price = "N/A"
            
            # Extract sold count
            try:
                sold_elem = item.find_element(By.CSS_SELECTOR, "div.sold--yGzjT")
                sold = sold_elem.text.strip()
            except NoSuchElementException:
                sold = "0 sold"
            
            # Extract rating
            try:
                rating_elem = item.find_element(By.CSS_SELECTOR, "div.rating--ZI3Ol")
                rating = rating_elem.text.strip()
            except NoSuchElementException:
                rating = "No ratings"
            
            # Extract review count
            try:
                review_elem = item.find_element(By.CSS_SELECTOR, "div.rating__review--ygkUy")
                reviews = review_elem.text.strip()
            except NoSuchElementException:
                reviews = "0 reviews"
            
            # Extract discount information if available
            try:
                discount_elem = item.find_element(By.CSS_SELECTOR, "div.discount--HADrE")
                discount = discount_elem.text.strip()
            except NoSuchElementException:
                discount = "No discount"
            
            # Clean up the data and parse numeric values
            clean_price = re.sub(r'[^\d.]', '', price) if price != "N/A" else "0"
            
            # Extract sold count numbers
            sold_count = 0
            if sold != "0 sold":
                sold_match = re.search(r'(\d+)', sold)
                if sold_match:
                    sold_count = int(sold_match.group(1))
            
            # Extract review numbers
            review_count = 0
            if reviews != "0 reviews":
                review_match = re.search(r'(\d+)', reviews)
                if review_match:
                    review_count = int(review_match.group(1))
            
            return {
                'name': name,
                'url': url,
                'price': price,
                'price_numeric': clean_price,
                'sold': sold,
                'sold_count': sold_count,
                'rating': rating,
                'reviews': reviews,
                'review_count': review_count,
                'discount': discount
            }
        except Exception as e:
            print(f"Error extracting product info: {e}")
            return None
    
    def save_to_csv(self, filename="daraz_products.csv"):
        """
        Save the scraped products to a CSV file
        
        Args:
            filename (str): Name of the CSV file
        """
        if not self.products:
            print("No products to save.")
            return
        
        try:
            df = pd.DataFrame(self.products)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"Successfully saved {len(self.products)} products to {filename}")
            
            # Get absolute path for user reference
            abs_path = os.path.abspath(filename)
            print(f"File saved at: {abs_path}")
            
        except Exception as e:
            print(f"Error saving to CSV with pandas: {e}")
            
            # Fallback to using csv module
            try:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=self.products[0].keys())
                    writer.writeheader()
                    writer.writerows(self.products)
                print(f"Successfully saved {len(self.products)} products using csv module")
                
                # Get absolute path for user reference
                abs_path = os.path.abspath(filename)
                print(f"File saved at: {abs_path}")
                
            except Exception as e2:
                print(f"Failed to save using csv module too: {e2}")
    
    def get_product_stats(self):
        """
        Get basic statistics about the scraped products
        
        Returns:
            dict: Dictionary containing statistics
        """
        if not self.products:
            return {"error": "No products available"}
        
        try:
            df = pd.DataFrame(self.products)
            
            # Convert price to numeric
            df['price_numeric'] = pd.to_numeric(df['price_numeric'], errors='coerce')
            
            stats = {
                "total_products": len(df),
                "avg_price": df['price_numeric'].mean(),
                "min_price": df['price_numeric'].min(),
                "max_price": df['price_numeric'].max(),
                "total_sold": df['sold_count'].sum(),
                "total_reviews": df['review_count'].sum(),
                "avg_reviews_per_product": df['review_count'].mean()
            }
            
            return stats
        except Exception as e:
            print(f"Error calculating stats: {e}")
            return {"error": str(e)}

def main():
    print("="*50)
    print("Daraz Product Scraper with Selenium")
    print("="*50)
    
    # Ask if browser should be visible or headless
    headless_option = input("Run in headless mode (browser not visible)? (y/n, default: y): ").lower()
    headless_mode = True if headless_option != 'n' else False
    
    # Create the scraper
    scraper = DarazSeleniumScraper(headless=headless_mode)
    
    try:
        # Get search query from user
        search_query = input("Enter the product to search for on Daraz: ")
        
        # Ask for the number of pages to scrape
        try:
            max_pages = int(input("Enter the maximum number of pages to scrape (default is 5): ") or 5)
        except ValueError:
            print("Invalid input. Using default value of 5 pages.")
            max_pages = 5
        
        # Search for products
        print(f"\nSearching for '{search_query}' on Daraz...")
        products = scraper.search_product(search_query, max_pages)
        
        # Print the results
        print(f"\nFound {len(products)} products.")
        
        # Show stats
        stats = scraper.get_product_stats()
        if "error" not in stats:
            print("\nProduct Statistics:")
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    if key.startswith(("avg_", "min_", "max_")):
                        print(f"  {key.replace('_', ' ').title()}: {value:.2f}")
                    else:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
            
        # Ask if the user wants to save the results
        save_option = input("\nDo you want to save the results to a CSV file? (y/n): ").lower()
        
        if save_option == 'y':
            filename = input("Enter the filename (default is daraz_products.csv): ") or "daraz_products.csv"
            scraper.save_to_csv(filename)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser when done
        scraper.close_browser()

if __name__ == "__main__":
    main()