import pytest
from playwright.sync_api import Page, expect
import re


class TestPortfolioPage:
    """Test suite for the Portfolio page of the Financial Tracker app."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup method that runs before each test."""
        # Navigate to the portfolio page before each test
        page.goto("/stocks")  # Adjust URL as needed for your app, e.g., "/stocks" or "/portfolio"
        page.wait_for_load_state("domcontentloaded")

    def test_portfolio_summary_cards(self, page: Page):
        """Test that all portfolio summary cards are displayed."""
        summary_cards = page.locator(".summary-cards .summary-card")
        expect(summary_cards).to_have_count(4)
        
        # Test Portfolio Value card
        portfolio_value_card = summary_cards.nth(0)
        expect(portfolio_value_card.locator("h3")).to_contain_text("Portfolio Value")
        expect(portfolio_value_card.locator("i.fas.fa-chart-line")).to_be_visible()
        expect(portfolio_value_card.locator(".summary-detail")).to_contain_text("Current market value")
        
        # Test Total Cost Basis card
        cost_basis_card = summary_cards.nth(1)
        expect(cost_basis_card.locator("h3")).to_contain_text("Total Cost Basis")
        expect(cost_basis_card.locator("i.fas.fa-coins")).to_be_visible()
        expect(cost_basis_card.locator(".summary-detail")).to_contain_text("Amount invested")
        
        # Test Total P&L card
        pnl_card = summary_cards.nth(2)
        expect(pnl_card.locator("h3")).to_contain_text("Total P&L")
        expect(pnl_card.locator("i.fas.fa-balance-scale")).to_be_visible()
        
        # Test Holdings card
        holdings_card = summary_cards.nth(3)
        expect(holdings_card.locator("h3")).to_contain_text("Holdings")
        expect(holdings_card.locator("i.fas.fa-briefcase")).to_be_visible()
        expect(holdings_card.locator(".summary-detail")).to_contain_text("Different stocks")
    
    def test_holdings_table_structure(self, page: Page):
        """Test the structure of the holdings table."""
        # Check if holdings exist
        holdings_table = page.locator("#portfolio-table")
        
        if holdings_table.is_visible():
            # Test table headers
            headers = holdings_table.locator("thead th")
            expected_headers = ["Symbol", "Company", "Shares", "Avg Cost", "Current Price", 
                              "Market Value", "Gain/Loss", "%", "Actions"]
            
            for i, expected_header in enumerate(expected_headers):
                expect(headers.nth(i)).to_contain_text(expected_header)
            
            # Test sortable headers have the sortable class
            sortable_headers = holdings_table.locator("thead th.sortable")
            expect(sortable_headers).to_have_count(8)  # All headers except Actions
    
    def test_holdings_table_data_when_populated(self, page: Page):
        """Test holdings table data when portfolio has holdings."""
        holdings_table = page.locator("#portfolio-table")
        
        if holdings_table.is_visible():
            # Check that table body exists and has rows
            table_rows = holdings_table.locator("tbody tr")
            
            if table_rows.count() > 0:
                # Test first row structure
                first_row = table_rows.first
                
                # Test symbol cell with link
                symbol_cell = first_row.locator(".symbol-cell a")
                expect(symbol_cell).to_be_visible()
                expect(symbol_cell).to_have_class(re.compile("stock-symbol"))
                
                # Test company cell
                expect(first_row.locator(".company-cell")).to_be_visible()
                
                # Test shares cell
                expect(first_row.locator(".shares-cell")).to_be_visible()
                
                # Test number cells
                number_cells = first_row.locator(".number-cell")
                expect(number_cells).to_have_count(5)
                
                # Test action buttons
                action_buttons = first_row.locator(".actions-cell .action-buttons")
                expect(action_buttons).to_be_visible()
                
                view_btn = action_buttons.locator('a[title="View Details"]')
                expect(view_btn).to_be_visible()
                
                trade_btn = action_buttons.locator('a[title="Buy/Sell"]')
                expect(trade_btn).to_be_visible()
    
    def test_empty_holdings_state(self, page: Page):
        """Test the empty state when no holdings exist."""
        empty_state = page.locator(".empty-state")
        
        if empty_state.is_visible():
            expect(empty_state.locator("h3")).to_contain_text("No holdings found")
            expect(empty_state.locator("p")).to_contain_text("Start building your portfolio")
            
            # Test empty state action buttons
            add_stock_btn = empty_state.get_by_role('link', name='Add Your First Stock')
            expect(add_stock_btn).to_be_visible()
            
            record_transaction_btn = empty_state.get_by_role('link', name='Record Transaction')
            expect(record_transaction_btn).to_be_visible()
            expect(record_transaction_btn).to_contain_text("Record Transaction")
    
    def test_recent_transactions_header(self, page: Page):
        """Test the recent transactions section."""
        transactions_section = page.locator(".card-group").nth(1)  # Second card-group
        
        # Test section header
        header = transactions_section.locator(".card-header h3")
        expect(header).to_contain_text("Recent Stock Transactions")
        
        # Test "View All" link
        view_all_link = transactions_section.get_by_role('link', name='View All')
        expect(view_all_link).to_be_visible()
    
    def test_recent_transactions_table_structure(self, page: Page):
        """Test recent transactions table structure."""
        transactions_section = page.locator(".card-group").nth(1)
        transactions_table = transactions_section.locator("table")
        
        if transactions_table.is_visible():
            # Test table headers
            headers = transactions_table.locator("thead th")
            expected_headers = ["Date", "Symbol", "Type", "Shares", "Price", "Total", "Fees"]
            
            for i, expected_header in enumerate(expected_headers):
                expect(headers.nth(i)).to_contain_text(expected_header)
    
    def test_recent_transactions_data_when_populated(self, page: Page):
        """Test recent transactions data when transactions exist."""
        transactions_section = page.locator(".card-group").nth(1)
        transactions_table = transactions_section.locator("table")
        
        if transactions_table.is_visible():
            table_rows = transactions_table.locator("tbody tr")
            
            if table_rows.count() > 0:
                first_row = table_rows.first
                
                # Test date cell
                expect(first_row.locator(".date-cell")).to_be_visible()
                
                # Test symbol cell with link
                symbol_link = first_row.locator(".symbol-cell a")
                expect(symbol_link).to_be_visible()
                
                # Test transaction type badge
                type_badge = first_row.locator(".transaction-type")
                expect(type_badge).to_be_visible()
                # Should have one of the transaction type classes
                expect(type_badge).to_have_class(re.compile("transaction-type-(buy|sell|dividend)"))
                
                # Test numeric cells
                expect(first_row.locator(".shares-cell")).to_be_visible()
                number_cells = first_row.locator(".number-cell")
                expect(number_cells).to_have_count(3)  # Price, Total, Fees
    
    def test_empty_transactions_state(self, page: Page):
        """Test empty state for recent transactions."""
        transactions_section = page.locator(".card-group").nth(1)
        empty_state = transactions_section.locator(".empty-state-small")
        
        if empty_state.is_visible():
            expect(empty_state.locator("p")).to_contain_text("No recent transactions found")
            
            record_btn = empty_state.locator('a[href*="create_stock_transaction"]')
            expect(record_btn).to_be_visible()
            expect(record_btn).to_contain_text("Record First Transaction")
    
    def test_update_prices_functionality(self, page: Page):
        """Test the update prices button functionality."""
        update_btn = page.locator("#refresh-prices-btn")
        
        # Mock the API response
        page.route("/update_all_prices", lambda route: route.fulfill(
            json={"success": True}
        ))
        
        # Click the update button
        with page.expect_response("/update_all_prices") as response_info:
            update_btn.click()
        
        response = response_info.value
        assert response.status == 200
        
        # Check that button shows loading state briefly
        expect(update_btn.locator("i")).to_have_class(re.compile("fa-spin"))
    
    def test_navigation_links(self, page: Page):
        """Test that navigation links work correctly."""
        # Test stock symbol links (if holdings exist)
        stock_links = page.locator(".stock-symbol")
        if stock_links.count() > 0:
            first_stock_link = stock_links.first
            href = first_stock_link.get_attribute("href")
            assert "view" in href
            assert "stock_id=" in href
        
        # Test action button links
        view_buttons = page.locator('a[title="View Details"]')
        if view_buttons.count() > 0:
            first_view_btn = view_buttons.first
            href = first_view_btn.get_attribute("href")
            assert "view" in href
            assert "stock_id=" in href
        
        trade_buttons = page.locator('a[title="Buy/Sell"]')
        if trade_buttons.count() > 0:
            first_trade_btn = trade_buttons.first
            href = first_trade_btn.get_attribute("href")
            assert "transactions/new" in href
            assert "stock_id=" in href
    
    def test_responsive_design_mobile(self, page: Page):
        """Test responsive design on mobile viewport."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        
        # Check that summary cards stack properly on mobile
        summary_cards = page.locator(".summary-cards")
        expect(summary_cards).to_be_visible()
        
        # Check that page header is responsive
        page_header = page.locator(".page-header")
        expect(page_header).to_be_visible()
        
        # Check that tables are horizontally scrollable
        table_responsive = page.locator(".table-responsive")
        if table_responsive.count() > 0:
            expect(table_responsive.first).to_be_visible()
    
    def test_positive_negative_indicators(self, page: Page):
        """Test that positive/negative gain/loss indicators work correctly."""
        # Check for positive/negative classes in P&L summary
        pnl_card = page.locator(".summary-cards .summary-card").nth(2)
        pnl_value = pnl_card.locator(".summary-value")
        
        if pnl_value.is_visible():
            # Should have either positive or negative class
            classes = pnl_value.get_attribute("class")
            assert "positive" in classes or "negative" in classes

        pnl_percent = pnl_card.locator(".summary-detail")
        
        if pnl_percent.is_visible():
            # Should have either positive or negative class
            classes = pnl_percent.get_attribute("class")
            assert "positive" in classes or "negative" in classes
        
        # Check for gain/loss indicators in holdings table
        gain_loss_cells = page.locator("td.percentage-cell")
        
        for cell in gain_loss_cells.all():
            classes = cell.get_attribute("class")
            # Should have arrow icons for positive/negative values
            if "positive" in classes:
                expect(cell.locator("i.fa-arrow-up")).to_be_visible()
            elif "negative" in classes:
                expect(cell.locator("i.fa-arrow-down")).to_be_visible()

# Test configuration
@pytest.mark.slow
class TestPortfolioPageIntegration:
    """Integration tests that require specific data states."""
    
    def test_full_portfolio_workflow(self, page: Page):
        """Test complete portfolio workflow with data."""
        # This test would require setting up test data
        # and testing the complete user flow
        page.goto("/stocks")
        
        # Add assertions based on your test data setup
        # This is a placeholder for more complex integration tests
        expect(page.locator(".page-header")).to_be_visible()


# Utility functions for test setup
def create_test_portfolio_data():
    """Helper function to create test portfolio data."""
    # This would interact with your test database
    # to create sample stocks, transactions, etc.
    pass


def cleanup_test_data():
    """Helper function to clean up test data after tests."""
    # This would clean up any test data created
    pass