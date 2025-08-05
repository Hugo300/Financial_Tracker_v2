/**
 * Table Sorting Functionality
 * 
 * Provides client-side sorting for tables with data-sortable attribute.
 * Supports different data types: string, number, date, currency.
 */
(function() {
    class TableSorter {
        constructor() {
        this.init();
    }

    init() {
        const tables = document.querySelectorAll('table, table.table');
        tables.forEach(table => this.initTable(table));
    }

    initTable(table) {
        const headers = table.querySelectorAll('th[sortable]');
        headers.forEach((header, index) => {
            header.classList.add('sortable', 'resizable-header');
            header.setAttribute('aria-sort', 'none'); // IMPROVEMENT: Add initial ARIA attribute
            header.addEventListener('click', () => this.sortTable(table, index, header));
        });
    }

    sortTable(table, columnIndex, header) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const sortType = header.getAttribute('sortable');
        let isAscending = true;

        console.log('Current sort: ', header.getAttribute('aria-sort'));
        console.log(rows);

        // IMPROVEMENT: Check the current ARIA attribute to determine sort order
        const currentSort = header.getAttribute('aria-sort');
        if (currentSort === 'ascending') {
            isAscending = false;
        }
        
        // Clear all sort indicators
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
            th.setAttribute('aria-sort', 'none');
        });
        
        // Set current sort indicator and ARIA attribute
        if (isAscending) {
            header.classList.add('sort-asc');
            header.setAttribute('aria-sort', 'ascending');
        } else {
            header.classList.add('sort-desc');
            header.setAttribute('aria-sort', 'descending');
        }

        // Sort rows
        rows.sort((a, b) => {
            const aCell = a.cells[columnIndex];
            const bCell = b.cells[columnIndex];
            
            let aValue = this.getCellValue(aCell, sortType);
            let bValue = this.getCellValue(bCell, sortType);

            return this.compareValues(aValue, bValue, sortType, isAscending);
        });

        // Reorder rows in DOM
        rows.forEach(row => tbody.appendChild(row));

        this.addSortFeedback(table);
    }

    getCellValue(cell, sortType) {
        let value = cell.textContent.trim();

        switch (sortType) {
            case 'number':
            case 'currency':
                // Extract number from text (handles currency symbols, commas, etc.)
                const numberMatch = value.match(/[-+]?[\d,]+\.?\d*/);
                return numberMatch ? parseFloat(numberMatch[0].replace(/,/g, '')) : 0;

            case 'date':
                // IMPROVEMENT: More robust date parsing using Date object and a try-catch block
                try {
                    const date = new Date(value);
                    // Check for invalid dates
                    if (isNaN(date.getTime())) {
                        return new Date(0); // Return a default value for invalid dates
                    }
                    return date;
                } catch (e) {
                    return new Date(0);
                }

            case 'string':
            default:
                return value.toLowerCase();
        }
    }

    compareValues(a, b, sortType, isAscending) {
        let result = 0;

        if (sortType === 'date') {
            result = a.getTime() - b.getTime();
        } else if (sortType === 'number' || sortType === 'currency') {
            result = a - b;
        } else {
            result = a.localeCompare(b);
        }

        return isAscending ? result : -result;
    }

    addSortFeedback(table) {
        table.style.opacity = '0.8';
        setTimeout(() => {
            table.style.opacity = '1';
        }, 150);
    }
    }

    /**
     * Enhanced table functionality
     */
    class TableEnhancer {
    constructor() {
        this.init();
    }

    init() {
        this.addColumnResizing();
        this.addKeyboardNavigation();
        this.truncateText();
    }

    addColumnResizing() {
        const tables = document.querySelectorAll('.table');
        tables.forEach(table => {
            const headers = table.querySelectorAll('th');
            headers.forEach((header, index) => {
                if (index < headers.length - 1) { // Don't add to last column
                    const resizer = document.createElement('div');
                    resizer.className = 'column-resizer';
                    
                    // IMPROVEMENT: Using CSS classes instead of inline styles
                    header.classList.add('resizable-header');
                    header.appendChild(resizer);
                    
                    this.makeResizable(resizer, header);
                }
            });
        });
    }

    makeResizable(resizer, header) {
        let isResizing = false;
        let startX = 0;
        let startWidth = 0;

        const startResizing = (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = parseInt(document.defaultView.getComputedStyle(header).width, 10);
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            e.preventDefault();
        };

        const handleMouseMove = (e) => {
            if (!isResizing) return;
            const width = startWidth + e.clientX - startX;
            if (width > 50) { // Minimum width
                header.style.width = width + 'px';
            }
        };

        const handleMouseUp = () => {
            isResizing = false;
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };

        resizer.addEventListener('mousedown', startResizing);
    }

    addKeyboardNavigation() {
        const tables = document.querySelectorAll('.table');
        tables.forEach(table => {
            table.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    this.navigateTable(table, e.key === 'ArrowDown');
                }
            });
        });
    }

    navigateTable(table, down) {
        const rows = table.querySelectorAll('tbody tr');
        const currentRow = table.querySelector('tbody tr.selected');
        let newIndex = 0;

        if (currentRow) {
            const currentIndex = Array.from(rows).indexOf(currentRow);
            newIndex = down ? 
                Math.min(currentIndex + 1, rows.length - 1) : 
                Math.max(currentIndex - 1, 0);
            currentRow.classList.remove('selected');
            currentRow.removeAttribute('aria-current'); // IMPROVEMENT: Remove ARIA attribute on previous row
        }

        if (rows[newIndex]) {
            rows[newIndex].classList.add('selected');
            rows[newIndex].setAttribute('aria-current', 'true'); // IMPROVEMENT: Add ARIA attribute for current row
            rows[newIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    truncateText() {
        const cells = document.querySelectorAll('.table td');
        cells.forEach(cell => {
            if (cell.scrollWidth > cell.clientWidth) {
                cell.title = cell.textContent;
            }
        });
    }
    }

    /**
     * Table utilities
     */
    class TableUtils {
    // IMPROVEMENT: Added a locale parameter for internationalization
    static formatCurrency(value, locale = 'en-US', currency = 'USD') {
        return new Intl.NumberFormat(locale, {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(value);
    }

    // IMPROVEMENT: Added a locale parameter
    static formatNumber(value, decimals = 0, locale = 'en-US') {
        return new Intl.NumberFormat(locale, {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value);
    }

    static formatPercentage(value, decimals = 2) {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(value / 100);
    }

    static highlightRow(row, duration = 2000) {
        row.classList.add('bg-yellow-100', 'transition', 'duration-500');
        setTimeout(() => {
            row.classList.remove('bg-yellow-100');
        }, duration);
    }

    static showLoading(table) {
        const container = table.closest('.table-wrapper') || table.parentElement;
        const loading = document.createElement('div');
        loading.className = 'table-loading';
        loading.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        container.appendChild(loading);
        return loading;
    }

    static hideLoading(loading) {
        if (loading && loading.parentElement) {
            loading.parentElement.removeChild(loading);
        }
    }

    static exportToCSV(table, filename = 'table-data.csv') {
        const rows = Array.from(table.querySelectorAll('tr'));
        const csvContent = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('th, td'));
            return cells.map(cell => {
                let text = cell.textContent.trim();
                // Remove action buttons and icons
                const clone = cell.cloneNode(true);
                const buttons = clone.querySelectorAll('button, .btn, i.fas, i.far');
                buttons.forEach(btn => btn.remove());
                text = clone.textContent.trim();
                // Escape quotes and wrap in quotes if contains comma
                if (text.includes(',') || text.includes('"') || text.includes('\n')) {
                    text = '"' + text.replace(/"/g, '""') + '"';
                }
                return text;
            }).join(',');
        }).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
    }

    /**
     * Enhanced search functionality
     */
    class TableSearch {
    constructor(table, searchInput) {
        this.table = table;
        this.searchInput = searchInput;
        this.originalRows = Array.from(table.querySelectorAll('tbody tr'));
        this.init();
    }

    init() {
        this.searchInput.addEventListener('input', (e) => {
            this.search(e.target.value);
        });
    }

    search(query) {
        const searchTerm = query.toLowerCase().trim();

        this.originalRows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(searchTerm);
            row.style.display = matches ? '' : 'none';
        });

        // Update empty state
        const visibleRows = this.originalRows.filter(row => row.style.display !== 'none');
        this.updateEmptyState(visibleRows.length === 0 && searchTerm !== '');
    }

    updateEmptyState(isEmpty) {
        let emptyState = this.table.querySelector('.search-empty-state');

        if (isEmpty && !emptyState) {
            emptyState = document.createElement('tr');
            emptyState.className = 'search-empty-state';
            emptyState.innerHTML = `
                <td colspan="100%" class="table-empty">
                    <i class="fas fa-search"></i>
                    <h3>No results found</h3>
                    <p>Try adjusting your search terms</p>
                </td>
            `;
            this.table.querySelector('tbody').appendChild(emptyState);
        } else if (!isEmpty && emptyState) {
            emptyState.remove();
        }
    }

    clear() {
        this.searchInput.value = '';
        this.search('');
    }
    }

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', () => {
        new TableSorter();
        new TableEnhancer();

        // Initialize search for tables with search inputs
        const searchInputs = document.querySelectorAll('[data-table-search]');
        searchInputs.forEach(input => {
            const tableId = input.getAttribute('data-table-search');
            const table = document.getElementById(tableId);
            if (table) {
                new TableSearch(table, input);
            }
        });
    });
})()