// static/js/view_sales.js

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
    setupEventListeners();
});

function updateStats() {
    const dates = window.datesData || [];
    const totalDays = dates.length;
    const activeDays = dates.filter(d => d.status === 'active').length;
    const closedDays = totalDays - activeDays;
    
    document.getElementById('totalDays').textContent = totalDays;
    document.getElementById('activeDays').textContent = activeDays;
    document.getElementById('closedDays').textContent = closedDays;
}

function setupEventListeners() {
    // Auto-select today's date if available
    const today = new Date().toISOString().split('T')[0];
    const dateSelect = document.getElementById('dateSelect');
    for (let option of dateSelect.options) {
        if (option.value === today) {
            dateSelect.value = today;
            loadDayDetails(today);
            break;
        }
    }
}

async function loadDayDetails(date) {
    if (!date) {
        showNoDataMessage();
        return;
    }

    showLoading();
    
    try {
        const response = await fetch(`/get-day-details/${date}`);
        const data = await response.json();
        
        if (data.success) {
            displayDayDetails(data);
        } else {
            showError(data.error || 'Failed to load day details');
        }
    } catch (error) {
        console.error('Error loading day details:', error);
        showError('Error loading day details: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayDayDetails(data) {
    const container = document.getElementById('dayDetailsContainer');
    container.classList.remove('d-none');
    document.getElementById('noDataMessage').classList.add('d-none');
    
    // Update day title
    document.getElementById('dayTitle').textContent = `Day Details - ${data.sales_data.date}`;
    
    // Display summary stats
    displaySummaryStats(data.totals, data.summary);
    
    // Display day information
    displayDayInfo(data.sales_data, data.summary);
    
    // Display opening stock
    displayOpeningStock(data.sales_data.opening_stock, data.totals.opening_stock);
    
    // Display sales
    displaySales(data.totals.cash_sales, data.totals.credit_sales);
    
    // Display expenses
    displayExpenses(data.totals.expenses);
    
    // Display banking
    displayBanking(data.totals.bank_deposit, data.totals.cash_on_hand);
    
    // Display credits
    displayCredits(data.totals.credits_to_farm, data.totals.credit_sales.credit_holders);
    
    // Display activity log
    displayActivityLog(data.activity_log);
    
    // Display users involved
    displayUsers(data.user_records);
}

function displaySummaryStats(totals, summary) {
    const container = document.getElementById('summaryStats');
    const profitClass = totals.net_profit >= 0 ? 'profit' : 'loss';
    
    container.innerHTML = `
        <div class="col-md-3">
            <div class="stat-card ${profitClass}">
                <div class="stat-value">${formatCurrency(totals.net_profit)}</div>
                <div class="stat-label">Net Profit</div>
                <small>Margin: ${summary.key_metrics.profit_margin.toFixed(1)}%</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card info">
                <div class="stat-value">${formatCurrency(totals.gross_income)}</div>
                <div class="stat-label">Total Sales</div>
                <small>${totals.cash_sales.count} cash + ${totals.credit_sales.count} credit</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card neutral stats-expenses">
                <div class="stat-value">${formatCurrency(totals.expenses.total_amount)}</div>
                <div class="stat-label">Total Expenses</div>
                <small>${totals.expenses.count} items</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card stats-deposit ${totals.deposit_variance >= 0 ? 'profit' : 'loss'}">
                <div class="stat-value">${formatCurrency(totals.deposit_variance)}</div>
                <div class="stat-label">Deposit Variance</div>
                <small>${totals.deposit_variance_percent.toFixed(1)}%</small>
            </div>
        </div>
    `;
}

function displayDayInfo(salesData, summary) {
    const container = document.getElementById('dayInfo');
    const statusBadge = salesData.status === 'active' ? 
        '<span class="badge badge-active">Active</span>' : 
        '<span class="badge badge-closed">Closed</span>';
    
    container.innerHTML = `
        <div class="col-md-6">
            <table class="table table-sm table-day-details opacity-75">
                <tr>
                    <th width="40%">Date:</th>
                    <td>${salesData.date} ${statusBadge}</td>
                </tr>
                <tr>
                    <th>Created:</th>
                    <td>${salesData.created_at || 'N/A'}</td>
                </tr>
                <tr>
                    <th>Closed:</th>
                    <td>${salesData.closed_at || 'Not closed yet'}</td>
                </tr>
                <tr>
                    <th>Opening Stock Value:</th>
                    <td>${formatCurrency(summary.financial_summary.opening_stock_value)}</td>
                </tr>
            </table>
        </div>
        <div class="col-md-6">
            <table class="table table-sm table-day-details opacity-75">
                <tr>
                    <th width="40%">Cash on Hand:</th>
                    <td>${formatCurrency(summary.financial_summary.cash_on_hand)}</td>
                </tr>
                <tr>
                    <th>Average Cash Sale:</th>
                    <td>${formatCurrency(summary.key_metrics.average_cash_sale)}</td>
                </tr>
                <tr>
                    <th>Average Expense:</th>
                    <td>${formatCurrency(summary.key_metrics.average_expense)}</td>
                </tr>
                <tr>
                    <th>Deposit Completion:</th>
                    <td>${summary.key_metrics.deposit_completion.toFixed(1)}%</td>
                </tr>
            </table>
        </div>
    `;
}

function displayOpeningStock(openingStock, totals) {
    const container = document.getElementById('openingStockDetails');
    
    if (!openingStock || (Array.isArray(openingStock) && openingStock.length === 0)) {
        container.innerHTML = '<div class="alert alert-info">No opening stock recorded for this day.</div>';
        return;
    }
    
    let html = `
        <div class="alert alert-success">
            <strong>Opening Stock Summary:</strong> ${totals.product_count} products, ${totals.section_count} sections, 
            Total Value: ${formatCurrency(totals.total_value)}
        </div>
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Section</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total Value</th>
                    <th>Recorded By</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    if (Array.isArray(openingStock)) {
        openingStock.forEach(product => {
            product.sections?.forEach(section => {
                html += `
                    <tr>
                        <td>${product.product_type}</td>
                        <td>${section.name}</td>
                        <td>${section.quantity}</td>
                        <td>${formatCurrency(section.unit_price)}</td>
                        <td>${formatCurrency(section.section_total)}</td>
                        <td><span class="badge badge-record">${section.recorded_by || 'Unknown'}</span></td>
                        <td>${formatTime(section.recorded_at)}</td>
                    </tr>
                `;
            });
        });
    }
    
    html += `
            </tbody>
            <tfoot>
                <tr class="table-primary">
                    <td colspan="4" class="text-end"><strong>Total Opening Stock Value:</strong></td>
                    <td colspan="3"><strong>${formatCurrency(totals.total_value)}</strong></td>
                </tr>
            </tfoot>
        </table>
    `;
    
    container.innerHTML = html;
}

function displaySales(cashSales, creditSales) {
    const container = document.getElementById('salesDetails');
    
    let html = '<div class="row">';
    
    // Cash Sales
    html += `
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Cash Sales</h6>
                </div>
                <div class="card-body">
                    <p><strong>Total:</strong> ${formatCurrency(cashSales.total_amount)} (${cashSales.count} transactions)</p>
    `;
    
    if (cashSales.items.length > 0) {
        html += `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Recorded By</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        cashSales.items.forEach(sale => {
            html += `
                <tr>
                    <td>${sale.name}</td>
                    <td>${formatCurrency(sale.amount)}</td>
                    <td><span class="badge badge-record">${sale.recorded_by}</span></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted">No cash sales recorded.</p>';
    }
    
    html += `
                </div>
            </div>
        </div>
    `;
    
    // Credit Sales
    html += `
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Credit Sales</h6>
                </div>
                <div class="card-body">
                    <p><strong>Total:</strong> ${formatCurrency(creditSales.total_amount)} (${creditSales.count} transactions)</p>
    `;
    
    if (creditSales.items.length > 0) {
        // Show top credit holders
        const topHolders = Object.entries(creditSales.credit_holders)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);
        
        html += '<p><strong>Top Credit Holders:</strong></p><ul class="list-group mb-3">';
        topHolders.forEach(([holder, amount]) => {
            html += `<li class="list-group-item d-flex justify-content-between">
                <span>${holder}</span>
                <span>${formatCurrency(amount)}</span>
            </li>`;
        });
        html += '</ul>';
        
        html += `
            <div class="table-responsive">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Credit Holder</th>
                            <th>Product</th>
                            <th>Amount</th>
                            <th>Recorded By</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        creditSales.items.forEach(sale => {
            html += `
                <tr>
                    <td>${sale.credit_holder}</td>
                    <td>${sale.product_type} - ${sale.section}</td>
                    <td>${formatCurrency(sale.total_amount)}</td>
                    <td><span class="badge badge-record">${sale.recorded_by}</span></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted">No credit sales recorded.</p>';
    }
    
    html += `
                </div>
            </div>
        </div>
    </div>`;
    
    container.innerHTML = html;
}

function displayExpenses(expenses) {
    const container = document.getElementById('expensesDetails');
    
    let html = `
        <div class="alert alert-danger">
            <strong>Expenses Summary:</strong> ${formatCurrency(expenses.total_amount)} total (${expenses.count} items)
        </div>
    `;
    
    // Expense categories chart
    if (Object.keys(expenses.categories).length > 0) {
        html += '<p><strong>Expense Categories:</strong></p><ul class="list-group mb-3">';
        Object.entries(expenses.categories).forEach(([category, amount]) => {
            const percentage = (amount / expenses.total_amount * 100).toFixed(1);
            html += `<li class="list-group-item d-flex justify-content-between">
                <span>${category}</span>
                <span>${formatCurrency(amount)} (${percentage}%)</span>
            </li>`;
        });
        html += '</ul>';
    }
    
    if (expenses.items.length > 0) {
        html += `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Amount</th>
                            <th>Recorded By</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        expenses.items.forEach(expense => {
            html += `
                <tr>
                    <td>${expense.description}</td>
                    <td>${formatCurrency(expense.amount)}</td>
                    <td><span class="badge badge-record">${expense.recorded_by}</span></td>
                    <td>${formatTime(expense.timestamp)}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted">No expenses recorded.</p>';
    }
    
    container.innerHTML = html;
}

function displayBanking(bankDeposit, cashOnHand) {
    const container = document.getElementById('bankingDetails');
    const variance = bankDeposit.actual - bankDeposit.expected;
    const varianceClass = variance >= 0 ? 'text-success' : 'text-danger';
    const varianceIcon = variance >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
    
    container.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Bank Deposits</h6>
                    </div>
                    <div class="card-body">
                        <table class="table">
                            <tr>
                                <th>Expected Deposit:</th>
                                <td>${formatCurrency(bankDeposit.expected || 0)}</td>
                            </tr>
                            <tr>
                                <th>Actual Deposit:</th>
                                <td>${formatCurrency(bankDeposit.actual || 0)}</td>
                            </tr>
                            <tr class="${varianceClass}">
                                <th>Variance:</th>
                                <td><i class="fas ${varianceIcon} me-1"></i> ${formatCurrency(variance)}</td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h6 class="mb-0">Cash Management</h6>
                    </div>
                    <div class="card-body">
                        <div class="text-center">
                            <h1 class="display-4">${formatCurrency(cashOnHand)}</h1>
                            <p class="text-muted">Cash on Hand</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function displayCredits(farmCredits, creditHolders) {
    const container = document.getElementById('creditsDetails');
    
    let html = '<div class="row">';
    
    // Credits to Farm
    html += `
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Credits to Farm</h6>
                </div>
                <div class="card-body">
                    <p><strong>Total:</strong> ${formatCurrency(farmCredits.total_amount)} (${farmCredits.count} creditors)</p>
    `;
    
    if (Object.keys(farmCredits.creditors).length > 0) {
        html += '<p><strong>Creditors:</strong></p><ul class="list-group">';
        Object.entries(farmCredits.creditors).forEach(([creditor, amount]) => {
            html += `<li class="list-group-item d-flex justify-content-between">
                <span>${creditor}</span>
                <span>${formatCurrency(amount)}</span>
            </li>`;
        });
        html += '</ul>';
    } else {
        html += '<p class="text-muted">No credits to farm recorded.</p>';
    }
    
    html += `
                </div>
            </div>
        </div>
    `;
    
    // Credit Sales Summary
    html += `
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">Credit Sales Summary</h6>
                </div>
                <div class="card-body">
                    <p><strong>Total Credit Outstanding:</strong> ${formatCurrency(Object.values(creditHolders).reduce((a, b) => a + b, 0))}</p>
    `;
    
    if (Object.keys(creditHolders).length > 0) {
        html += '<p><strong>Credit Holders:</strong></p><ul class="list-group">';
        Object.entries(creditHolders).forEach(([holder, amount]) => {
            html += `<li class="list-group-item d-flex justify-content-between">
                <span>${holder}</span>
                <span>${formatCurrency(amount)}</span>
            </li>`;
        });
        html += '</ul>';
    } else {
        html += '<p class="text-muted">No credit sales recorded.</p>';
    }
    
    html += `
                </div>
            </div>
        </div>
    </div>`;
    
    container.innerHTML = html;
}

function displayActivityLog(activityLog) {
    const container = document.getElementById('activityLog');
    
    if (!activityLog || activityLog.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No activity recorded for this day.</div>';
        return;
    }
    
    let html = '';
    
    activityLog.forEach(activity => {
        const time = formatTime(activity.timestamp);
        const userBadge = `<span class="badge bg-info">${activity.user}</span>`;
        
        html += `
            <div class="activity-item">
                <div class="card mb-2">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <h6 class="card-title mb-1">
                                <span class="badge bg-${getActivityColor(activity.type)} me-2">${activity.type}</span>
                                ${activity.description}
                            </h6>
                            <small class="text-muted">${time}</small>
                        </div>
                        <p class="card-text mb-1">Recorded by: ${userBadge}</p>
                        ${activity.details ? `
                            <div class="mt-2 small">
                                ${Object.entries(activity.details).map(([key, value]) => 
                                    `<span class="me-3"><strong>${key}:</strong> ${value}</span>`
                                ).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function displayUsers(userRecords) {
    const container = document.getElementById('usersDetails');
    const users = Object.values(userRecords);
    
    if (users.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No user information available.</div>';
        return;
    }
    
    let html = `
        <div class="alert alert-primary">
            <strong>${users.length} User(s) involved in recording data for this day</strong>
        </div>
        <div class="row">
    `;
    
    users.forEach(user => {
        html += `
            <div class="col-md-4 mb-3">
                <div class="card">
                    <div class="card-body text-center">
                        <div class="mb-3">
                            <i class="fas fa-user-circle fa-3x text-primary"></i>
                        </div>
                        <h5 class="card-title">${user.full_name || user.username}</h5>
                        <p class="card-text">
                            <span class="badge bg-secondary">${user.role || 'User'}</span><br>
                            <small class="text-muted">Username: ${user.username}</small>
                        </p>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

function getActivityColor(type) {
    const colors = {
        'Opening Stock': 'primary',
        'Cash Sale': 'success',
        'Credit Sale': 'warning',
        'Expense': 'danger',
        'Farm Credit': 'dark',
        'Bank Deposit': 'info',
        'Cash Management': 'secondary'
    };
    return colors[type] || 'secondary';
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '0.00';
    return parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

function formatTime(timestamp) {
    if (!timestamp) return 'N/A';

    try {
        // Handle ISO format like: 2026-02-17T20:13:21.742000
        const date = new Date(timestamp);

        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');

        return `${hours}:${minutes}`;
    } catch (error) {
        console.error('Time format error:', error);
        return 'N/A';
    }
}

function showLoading() {
    document.getElementById('loadingIndicator').classList.remove('d-none');
    document.getElementById('dayDetailsContainer').classList.add('d-none');
    document.getElementById('noDataMessage').classList.add('d-none');
}

function hideLoading() {
    document.getElementById('loadingIndicator').classList.add('d-none');
}

function showNoDataMessage() {
    document.getElementById('noDataMessage').classList.remove('d-none');
    document.getElementById('dayDetailsContainer').classList.add('d-none');
    document.getElementById('loadingIndicator').classList.add('d-none');
}

function showError(message) {
    const container = document.getElementById('dayDetailsContainer');
    container.classList.remove('d-none');
    container.innerHTML = `
        <div class="alert alert-danger">
            <h5><i class="fas fa-exclamation-triangle me-2"></i>Error</h5>
            <p>${message}</p>
            <button class="btn btn-sm btn-outline-danger" onclick="loadDayDetails(document.getElementById('dateSelect').value)">
                <i class="fas fa-redo me-1"></i> Try Again
            </button>
        </div>
    `;
    hideLoading();
}

function loadCurrentDay() {
    const today = new Date().toISOString().split('T')[0];
    const dateSelect = document.getElementById('dateSelect');
    dateSelect.value = today;
    loadDayDetails(today);
}

function loadPreviousDay() {
    const currentDate = document.getElementById('dateSelect').value;
    if (!currentDate) return;
    
    const date = new Date(currentDate);
    date.setDate(date.getDate() - 1);
    const previousDate = date.toISOString().split('T')[0];
    
    // Check if previous date exists in options
    const dateSelect = document.getElementById('dateSelect');
    for (let option of dateSelect.options) {
        if (option.value === previousDate) {
            dateSelect.value = previousDate;
            loadDayDetails(previousDate);
            return;
        }
    }
    
    alert('No data available for the previous day.');
}

function showComparisonModal() {
    const modal = new bootstrap.Modal(document.getElementById('comparisonModal'));
    modal.show();
}


async function compareSelectedDates() {
    const date1 = document.getElementById('compareDate1').value;
    const date2 = document.getElementById('compareDate2').value;
    
    if (!date1 || !date2) {
        alert('Please select both dates to compare.');
        return;
    }
    
    if (date1 === date2) {
        alert('Please select two different dates to compare.');
        return;
    }
    
    try {
        const response = await fetch(`/compare-days?date1=${date1}&date2=${date2}`);
        const data = await response.json();
        
        if (data.success) {
            displayComparisonResults(data);
        } else {
            alert('Error comparing dates: ' + data.error);
        }
    } catch (error) {
        console.error('Error comparing dates:', error);
        alert('Error comparing dates: ' + error.message);
    }
}

function displayComparisonResults(data) {
    const container = document.getElementById('comparisonResults');
    container.classList.remove('d-none');
    
    const comp = data.comparison;
    const arrow1 = comp.cash_sales_change >= 0 ? '↑' : '↓';
    const arrow2 = comp.expenses_change >= 0 ? '↑' : '↓';
    const arrow3 = comp.net_profit_change >= 0 ? '↑' : '↓';
    
    container.innerHTML = `
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h6 class="mb-0">Comparison Results: ${data.day1.date} vs ${data.day2.date}</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <div class="card ${comp.cash_sales_change >= 0 ? 'border-success' : 'border-danger'}">
                            <div class="card-body">
                                <h6 class="card-title">Cash Sales</h6>
                                <h3 class="${comp.cash_sales_change >= 0 ? 'text-success' : 'text-danger'}">
                                    ${arrow1} ${comp.cash_sales_change_percent.toFixed(1)}%
                                </h3>
                                <p class="card-text">
                                    ${data.day1.date}: ${formatCurrency(data.day1.totals.cash_sales.total_amount)}<br>
                                    ${data.day2.date}: ${formatCurrency(data.day2.totals.cash_sales.total_amount)}<br>
                                    Change: ${formatCurrency(comp.cash_sales_change)}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card ${comp.expenses_change <= 0 ? 'border-success' : 'border-danger'}">
                            <div class="card-body">
                                <h6 class="card-title">Expenses</h6>
                                <h3 class="${comp.expenses_change <= 0 ? 'text-success' : 'text-danger'}">
                                    ${arrow2} ${comp.expenses_change_percent.toFixed(1)}%
                                </h3>
                                <p class="card-text">
                                    ${data.day1.date}: ${formatCurrency(data.day1.totals.expenses.total_amount)}<br>
                                    ${data.day2.date}: ${formatCurrency(data.day2.totals.expenses.total_amount)}<br>
                                    Change: ${formatCurrency(comp.expenses_change)}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card ${comp.net_profit_change >= 0 ? 'border-success' : 'border-danger'}">
                            <div class="card-body">
                                <h6 class="card-title">Net Profit</h6>
                                <h3 class="${comp.net_profit_change >= 0 ? 'text-success' : 'text-danger'}">
                                    ${arrow3} ${comp.net_profit_change_percent.toFixed(1)}%
                                </h3>
                                <p class="card-text">
                                    ${data.day1.date}: ${formatCurrency(data.day1.totals.net_profit)}<br>
                                    ${data.day2.date}: ${formatCurrency(data.day2.totals.net_profit)}<br>
                                    Change: ${formatCurrency(comp.net_profit_change)}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function applyFilters() {
    const status = document.getElementById('filterStatus').value;
    const fromDate = document.getElementById('filterDateFrom').value;
    const toDate = document.getElementById('filterDateTo').value;
    
    // Filter logic would go here
    alert('Filter functionality to be implemented');
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('dateFilterModal'));
    modal.hide();
}

function exportDayReport() {
    const selectedDate = document.getElementById('dateSelect').value;
    if (!selectedDate) {
        alert('Please select a date first.');
        return;
    }
    
    window.open(`/export-day-report/${selectedDate}`, '_blank');
}

function printDayReport() {
    window.print();
}

function refreshData() {
    const selectedDate = document.getElementById('dateSelect').value;
    if (selectedDate) {
        loadDayDetails(selectedDate);
    }
}

function renderMonthDays() {
    const monthInput = document.getElementById('monthPicker').value;
    const grid = document.getElementById('daysGrid');
    grid.innerHTML = '';

    if (!monthInput) return;

    const [year, month] = monthInput.split('-');

    const monthDates = window.datesData.filter(d => {
        const [y, m] = d.date.split('-');
        return y === year && m === month;
    });

    if (monthDates.length === 0) {
        grid.innerHTML = `<div class="text-muted">No sales records for this month</div>`;
        return;
    }

    monthDates.forEach(d => {
        const day = d.date.split('-')[2];
        const btn = document.createElement('button');

        btn.className = `btn btn-sm ${
            d.status === 'active' ? 'btn-success' : 'btn-outline-secondary'
        }`;

        btn.innerHTML = day;
        btn.onclick = () => loadDayDetails(d.date);

        grid.appendChild(btn);
    });
}
