

// Global variable for product types from server
const productTypes = {{ product_types|tojson|safe }};

// Update sections based on product type selection
document.getElementById('productType')?.addEventListener('change', function() {
    const productType = this.value;
    updateSections(productType, 'sectionsContainer', 'openingStockTotal');
});

document.getElementById('closingProductType')?.addEventListener('change', function() {
    const productType = this.value;
    updateSections(productType, 'closingSectionsContainer', 'closingStockTotal', true);
});

// Update credit sections
document.getElementById('creditProductType')?.addEventListener('change', function() {
    const productType = this.value;
    const sectionSelect = document.getElementById('creditSection');
    if (sectionSelect) {
        sectionSelect.innerHTML = '<option value="">Select Section</option>';
        
        if (productType && productTypes[productType]) {
            productTypes[productType].sections.forEach((section, index) => {
                const option = document.createElement('option');
                option.value = section;
                option.textContent = section;
                sectionSelect.appendChild(option);
            });
        }
    }
});

// Function to handle revenue form submission
function handleRevenueSubmit() {
    const revenueName = document.getElementById('revenue_name').value;
    const amount = document.getElementById('revenue_amount').value;
    const description = document.getElementById('revenue_description').value;
    
    if (!revenueName || !amount) {
        alert('Please fill in required fields');
        return;
    }
    
    const revenueData = {
        revenue_name: revenueName,
        amount: parseFloat(amount),
        description: description
    };
    
    fetch('/api/save_revenue', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(revenueData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear the form
            document.getElementById('revenue_name').value = '';
            document.getElementById('revenue_amount').value = '';
            document.getElementById('revenue_description').value = '';
            
            // Show success message
            showNotification('Revenue saved successfully!', 'success');
            
            // IMPORTANT: Refresh the revenue data display
            refreshRevenueDisplay();
            
            // Also refresh overall totals
            loadTodayData();
        } else {
            showNotification('Failed to save revenue', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error saving revenue', 'error');
    });
}

// Function to refresh revenue display
function refreshRevenueDisplay() {
    const today = new Date().toISOString().split('T')[0];
    
    fetch(`/api/get_today_data`)
    .then(response => response.json())
    .then(data => {
        if (data.revenue && data.revenue.length > 0) {
            updateRevenueTable(data.revenue);
            updateRevenueTotal(data.revenue);
        } else {
            clearRevenueDisplay();
        }
    })
    .catch(error => {
        console.error('Error loading revenue data:', error);
    });
}

// Function to update revenue table
function updateRevenueTable(revenueItems) {
    const tbody = document.getElementById('revenueTableBody');
    if (!tbody) return;
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    // Add new rows
    revenueItems.forEach((item, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${item.revenue_name}</td>
            <td>${item.description || ''}</td>
            <td class="text-right">KES ${parseFloat(item.amount).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
            <td>${new Date(item.recorded_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
            <td>${item.recorded_by || ''}</td>
        `;
        tbody.appendChild(row);
    });
}

// Function to update revenue total display
function updateRevenueTotal(revenueItems) {
    const totalElement = document.getElementById('revenueTotalAmount');
    if (!totalElement) return;
    
    const total = revenueItems.reduce((sum, item) => sum + parseFloat(item.amount), 0);
    totalElement.textContent = `KES ${total.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Function to clear revenue display
function clearRevenueDisplay() {
    const tbody = document.getElementById('revenueTableBody');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No revenue recorded yet</td></tr>';
    }
    
    const totalElement = document.getElementById('revenueTotalAmount');
    if (totalElement) {
        totalElement.textContent = 'KES 0.00';
    }
}

// Calculate credit total
const creditQuantityInput = document.getElementById('creditQuantity');
const creditUnitPriceInput = document.getElementById('creditUnitPrice');

if (creditQuantityInput && creditUnitPriceInput) {
    creditQuantityInput.addEventListener('input', calculateCreditTotal);
    creditUnitPriceInput.addEventListener('input', calculateCreditTotal);
}

function calculateCreditTotal() {
    const quantity = parseFloat(document.getElementById('creditQuantity')?.value) || 0;
    const unitPrice = parseFloat(document.getElementById('creditUnitPrice')?.value) || 0;
    const total = quantity * unitPrice;
    const creditTotalElement = document.getElementById('creditTotal');
    if (creditTotalElement) {
        creditTotalElement.textContent = total.toFixed(2);
    }
}

function updateSections(productType, containerId, totalElementId, isClosing = false) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    if (productType && productTypes[productType]) {
        const product = productTypes[productType];
        
        product.sections.forEach((section, index) => {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'row mb-3';
            sectionDiv.innerHTML = `
                <div class="col-md-4">
                    <label class="form-label">${section}</label>
                    <input type="number" class="form-control ${isClosing ? 'closing' : 'opening'}-quantity" 
                           data-section="${section}" step="0.01" placeholder="Quantity" 
                           oninput="calculateSectionTotal(this, '${totalElementId}', ${isClosing})">
                </div>
                <div class="col-md-4">
                    <label class="form-label">Unit</label>
                    <input type="text" class="form-control" value="${product.units[index]}" readonly>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Unit Price (K)</label>
                    <input type="number" class="form-control ${isClosing ? 'closing' : 'opening'}-price" 
                           data-section="${section}" step="0.01" placeholder="Price" 
                           oninput="calculateSectionTotal(this, '${totalElementId}', ${isClosing})">
                </div>
            `;
            container.appendChild(sectionDiv);
        });
    }
}

function calculateSectionTotal(input, totalElementId, isClosing = false) {
    const section = input.dataset.section;
    const prefix = isClosing ? 'closing' : 'opening';
    const row = input.closest('.row');
    const quantityInput = row.querySelector(`.${prefix}-quantity`);
    const priceInput = row.querySelector(`.${prefix}-price`);
    
    const quantity = parseFloat(quantityInput?.value) || 0;
    const price = parseFloat(priceInput?.value) || 0;
    
    // Update total
    recalculateTotal(totalElementId, isClosing);
}

function recalculateTotal(totalElementId, isClosing = false) {
    const prefix = isClosing ? 'closing' : 'opening';
    const quantityInputs = document.querySelectorAll(`.${prefix}-quantity`);
    let total = 0;
    
    quantityInputs.forEach((input) => {
        const row = input.closest('.row');
        const priceInput = row.querySelector(`.${prefix}-price`);
        const quantity = parseFloat(input.value) || 0;
        const price = parseFloat(priceInput?.value) || 0;
        total += quantity * price;
    });
    
    const totalElement = document.getElementById(totalElementId);
    if (totalElement) {
        totalElement.textContent = total.toFixed(2);
    }
}

// Form submissions
const forms = [
    { id: 'openingStockForm', handler: saveOpeningStock },
    { id: 'revenueForm', handler: saveRevenue },
    { id: 'creditSalesForm', handler: saveCreditSale },
    { id: 'expensesForm', handler: saveExpense },
    { id: 'bankDepositForm', handler: saveBankDeposit },
    { id: 'closingStockForm', handler: saveClosingStock },
    { id: 'creditOwedForm', handler: saveCreditOwed }
];

forms.forEach(formConfig => {
    const form = document.getElementById(formConfig.id);
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            formConfig.handler();
        });
    }
});

// API Call functions
async function saveOpeningStock() {
    const productType = document.getElementById('productType')?.value;
    const sections = [];
    
    document.querySelectorAll('.opening-quantity').forEach((input) => {
        const row = input.closest('.row');
        const priceInput = row.querySelector('.opening-price');
        const unitInput = row.querySelector('input[type="text"]');
        
        sections.push({
            name: input.dataset.section,
            quantity: input.value || 0,
            unit_price: priceInput?.value || 0,
            unit: unitInput?.value || ''
        });
    });
    
    const data = {
        product_type: productType,
        sections: sections
    };
    
    try {
        const response = await fetch('/api/save_opening_stock', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            alert('Opening stock saved successfully!');
            loadTodayData();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving opening stock');
    }
}

async function saveRevenue() {
    const data = {
        revenue_name: document.getElementById('revenueName')?.value,
        amount: document.getElementById('revenueAmount')?.value,
        description: document.getElementById('revenueDescription')?.value
    };
    
    try {
        const response = await fetch('/api/save_revenue', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            alert('Revenue saved successfully!');
            const form = document.getElementById('revenueForm');
            if (form) form.reset();
            loadTodayData();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving revenue');
    }
}

async function saveCreditSale() {
    const data = {
        credit_holder: document.getElementById('creditHolder')?.value,
        product_type: document.getElementById('creditProductType')?.value,
        section: document.getElementById('creditSection')?.value,
        quantity: document.getElementById('creditQuantity')?.value,
        unit_price: document.getElementById('creditUnitPrice')?.value,
        due_date: document.getElementById('creditDueDate')?.value
    };
    
    try {
        const response = await fetch('/api/save_credit_sale', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            alert('Credit sale saved successfully!');
            const form = document.getElementById('creditSalesForm');
            if (form) form.reset();
            document.getElementById('creditTotal').textContent = '0.00';
            loadTodayData();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving credit sale');
    }
}

async function saveExpense() {
    const data = {
        description: document.getElementById('expenseDescription')?.value,
        amount: document.getElementById('expenseAmount')?.value,
        category: document.getElementById('expenseCategory')?.value
    };
    
    try {
        const response = await fetch('/api/save_expense', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            alert('Expense saved successfully!');
            const form = document.getElementById('expensesForm');
            if (form) form.reset();
            loadTodayData();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving expense');
    }
}

async function saveBankDeposit() {
    const data = {
        expected_deposit: document.getElementById('expectedDeposit')?.value,
        actual_deposit: document.getElementById('actualDeposit')?.value,
        cash_on_hand: document.getElementById('cashOnHand')?.value
    };
    
    try {
        const response = await fetch('/api/save_bank_deposit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            alert('Bank details saved successfully!');
            loadTodayData();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving bank details');
    }
}

async function saveClosingStock() {
    const productType = document.getElementById('closingProductType')?.value;
    const sections = [];
    
    document.querySelectorAll('.closing-quantity').forEach((input) => {
        const row = input.closest('.row');
        const priceInput = row.querySelector('.closing-price');
        const unitInput = row.querySelector('input[type="text"]');
        
        sections.push({
            name: input.dataset.section,
            quantity: input.value || 0,
            unit_price: priceInput?.value || 0,
            unit: unitInput?.value || ''
        });
    });
    
    const data = {
        product_type: productType,
        sections: sections
    };
    
    try {
        const response = await fetch('/api/save_closing_stock', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            alert('Closing stock saved successfully!');
            loadTodayData();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving closing stock');
    }
}

async function saveCreditOwed() {
    const data = {
        debtor_name: document.getElementById('debtorName')?.value,
        farm_name: document.getElementById('farmName')?.value,
        amount: document.getElementById('creditOwedAmount')?.value,
        description: document.getElementById('creditOwedDescription')?.value,
        due_date: document.getElementById('creditOwedDueDate')?.value
    };
    
    try {
        const response = await fetch('/api/save_credit_owed', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            alert('Credit owed saved successfully!');
            const form = document.getElementById('creditOwedForm');
            if (form) form.reset();
            loadTodayData();
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving credit owed');
    }
}

// Load today's data
async function loadTodayData() {
    try {
        const response = await fetch('/api/get_today_data');
        const data = await response.json();
        
        if (data.totals) {
            updateElementText('summaryRevenue', data.totals.revenue.toFixed(2));
            updateElementText('summaryCreditSales', data.totals.credit_sales.toFixed(2));
            updateElementText('summaryExpenses', data.totals.expenses.toFixed(2));
            updateElementText('summaryCreditOwed', data.totals.credit_owed.toFixed(2));
            updateElementText('totalRevenue', data.totals.revenue.toFixed(2));
        }
        
        // Update revenue list
        const revenueList = document.getElementById('revenueList');
        if (revenueList) {
            revenueList.innerHTML = '';
            if (data.revenue && data.revenue.length > 0) {
                data.revenue.forEach(item => {
                    const div = document.createElement('div');
                    div.className = 'list-group-item';
                    div.innerHTML = `
                        <div class="d-flex justify-content-between">
                            <span>${item.revenue_name}</span>
                            <span>K${item.amount?.toFixed(2) || '0.00'}</span>
                        </div>
                        ${item.description ? `<small class="text-muted">${item.description}</small>` : ''}
                    `;
                    revenueList.appendChild(div);
                });
            }
        }
    } catch (error) {
        console.error('Error loading today data:', error);
    }
}

function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

// Load data on page load
window.addEventListener('DOMContentLoaded', function() {
    {% if active_day %}
    loadTodayData();
    {% endif %}
});