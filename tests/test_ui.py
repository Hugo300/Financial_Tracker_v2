"""
UI tests for the Financial Tracker application using Selenium.

This module tests critical user flows through the web interface.
"""

import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException


@pytest.fixture(scope="module")
def driver():
    """Create a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for CI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
    except Exception as e:
        pytest.skip(f"Chrome WebDriver not available: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()


@pytest.fixture(scope="module")
def live_server(app):
    """Start a live server for testing."""
    import threading
    import socket
    from werkzeug.serving import make_server
    
    # Find a free port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    
    server = make_server('localhost', port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    yield f"http://localhost:{port}"
    
    server.shutdown()


class TestDashboardUI:
    """Test dashboard user interface."""
    
    def test_dashboard_loads(self, driver, live_server):
        """Test that the dashboard loads and displays key elements."""
        driver.get(live_server)
        
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        
        try:
            # Check that the dashboard title is present
            dashboard_title = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            assert "Dashboard" in dashboard_title.text
            
            # Check for navigation menu
            nav = driver.find_element(By.CLASS_NAME, "navbar")
            assert nav is not None
            
            # Check for summary cards
            summary_cards = driver.find_elements(By.CLASS_NAME, "summary-card")
            assert len(summary_cards) >= 3  # Should have at least Net Worth, Assets, Portfolio cards
            
            # Check for main content area
            main_content = driver.find_element(By.CLASS_NAME, "main-content")
            assert main_content is not None
            
        except TimeoutException:
            pytest.fail("Dashboard did not load within timeout period")
    
    def test_navigation_menu(self, driver, live_server):
        """Test that navigation menu works correctly."""
        driver.get(live_server)
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # Test Accounts link
            accounts_link = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Accounts"))
            )
            accounts_link.click()
            
            # Wait for accounts page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            assert "accounts" in driver.current_url.lower()
            
            # Test Transactions link
            transactions_link = driver.find_element(By.LINK_TEXT, "Transactions")
            transactions_link.click()
            
            # Wait for transactions page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            assert "transactions" in driver.current_url.lower()
            
            # Test Stocks link
            stocks_link = driver.find_element(By.LINK_TEXT, "Stocks")
            stocks_link.click()
            
            # Wait for stocks page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            assert "stocks" in driver.current_url.lower()
            
            # Return to dashboard
            dashboard_link = driver.find_element(By.LINK_TEXT, "Dashboard")
            dashboard_link.click()
            
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            current_url = driver.current_url.rstrip('/')
            assert current_url == live_server
            
        except TimeoutException:
            pytest.fail("Navigation menu did not work within timeout period")
    
    def test_theme_toggle(self, driver, live_server):
        """Test theme toggle functionality."""
        driver.get(live_server)
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # Find theme toggle button
            theme_toggle = wait.until(
                EC.element_to_be_clickable((By.ID, "theme-toggle"))
            )
            
            # Get initial theme class
            html_element = driver.find_element(By.TAG_NAME, "html")
            initial_class = html_element.get_attribute("class")
            
            # Click theme toggle
            theme_toggle.click()
            
            # Wait a moment for theme to change
            time.sleep(0.5)
            
            # Check that theme class changed
            new_class = html_element.get_attribute("class")
            assert initial_class != new_class
            
            # Should toggle between theme-light and theme-dark
            assert ("theme-light" in initial_class and "theme-dark" in new_class) or \
                   ("theme-dark" in initial_class and "theme-light" in new_class)
            
        except TimeoutException:
            pytest.fail("Theme toggle did not work within timeout period")


class TestAccountManagement:
    """Test account management user interface."""
    
    def test_create_account_flow(self, driver, live_server):
        """Test the complete account creation flow."""
        driver.get(f"{live_server}/accounts/")
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # Click "Add Account" button
            add_account_btn = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Add Account"))
            )
            add_account_btn.click()
            
            # Wait for form to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))
            
            # Fill out the form
            name_field = driver.find_element(By.NAME, "name")
            name_field.send_keys("UI Test Account")
            
            account_type_select = Select(driver.find_element(By.NAME, "account_type"))
            account_type_select.select_by_value("checking")
            
            balance_field = driver.find_element(By.NAME, "balance")
            balance_field.clear()
            balance_field.send_keys("1500.00")
            
            description_field = driver.find_element(By.NAME, "description")
            description_field.send_keys("Account created via UI test")
            
            institution_field = driver.find_element(By.NAME, "institution")
            institution_field.send_keys("UI Test Bank")
            
            # Submit the form
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_btn.click()
            
            # Wait for redirect and check success
            wait.until(lambda d: "accounts" in d.current_url)
            
            # Look for success message or the created account
            page_source = driver.page_source.lower()
            assert "ui test account" in page_source or "success" in page_source
            
        except TimeoutException:
            pytest.fail("Account creation flow did not complete within timeout period")
        except Exception as e:
            # Take a screenshot for debugging
            driver.save_screenshot("account_creation_error.png")
            pytest.fail(f"Account creation flow failed: {e}")
    
    def test_account_list_display(self, driver, live_server):
        """Test that the account list displays correctly."""
        driver.get(f"{live_server}/accounts/")
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            
            # Check for accounts section
            page_source = driver.page_source.lower()
            assert "accounts" in page_source
            
            # Check for summary cards
            summary_cards = driver.find_elements(By.CLASS_NAME, "summary-card")
            assert len(summary_cards) >= 1  # Should have at least one summary card
            
            # Check for add account button
            add_account_elements = driver.find_elements(By.LINK_TEXT, "Add Account")
            assert len(add_account_elements) >= 1
            
        except TimeoutException:
            pytest.fail("Account list page did not load within timeout period")


class TestTransactionManagement:
    """Test transaction management user interface."""
    
    def test_transaction_list_loads(self, driver, live_server):
        """Test that the transaction list loads correctly."""
        driver.get(f"{live_server}/transactions/")
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            
            # Check page title
            page_title = driver.find_element(By.TAG_NAME, "h1")
            assert "transaction" in page_title.text.lower()
            
            # Check for filter form or transaction list
            page_source = driver.page_source.lower()
            assert "transaction" in page_source
            
        except TimeoutException:
            pytest.fail("Transaction list page did not load within timeout period")
    
    def test_transaction_filters(self, driver, live_server):
        """Test transaction filtering functionality."""
        driver.get(f"{live_server}/transactions/")
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            
            # Look for filter form
            filter_elements = driver.find_elements(By.CSS_SELECTOR, "form, .filter-form")
            if filter_elements:
                # If filters exist, test that they can be interacted with
                selects = driver.find_elements(By.TAG_NAME, "select")
                inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[type='text']")
                
                # Should have some filter controls
                assert len(selects) + len(inputs) > 0
            
        except TimeoutException:
            pytest.fail("Transaction filters did not load within timeout period")


# Helper function to check if Chrome WebDriver is available
def is_chrome_available():
    """Check if Chrome WebDriver is available."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.quit()
        return True
    except Exception:
        return False


# Skip all UI tests if Chrome is not available
pytestmark = pytest.mark.skipif(
    not is_chrome_available(),
    reason="Chrome WebDriver not available"
)
