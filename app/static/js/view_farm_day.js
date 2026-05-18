// static/js/view_farm.js

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing farm view...');
    console.log('Dates data:', window.datesData); // Debug log
    
    updateStats();
    setupEventListeners();
    
    // Set default month to current month if not set
    const monthPicker = document.getElementById('monthPicker');
    if (monthPicker && !monthPicker.value) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        monthPicker.value = `${year}-${month}`;
    }
    
    // Initial render of month days
    renderMonthDays();
});

function updateStats() {
    const dates = window.datesData || [];
    const totalDays = dates.length;
    
    const totalDaysElement = document.getElementById('totalFarmDays');
    if (totalDaysElement) {
        totalDaysElement.textContent = totalDays;
    }
}

function setupEventListeners() {
    // Add event listener for month picker change
    const monthPicker = document.getElementById('monthPicker');
    if (monthPicker) {
        monthPicker.addEventListener('change', function() {
            console.log('Month changed to:', this.value);
            renderMonthDays();
        });
    }
}

async function loadFarmDayDetails(date) {
    if (!date) {
        showNoDataMessage();
        return;
    }

    showLoading();
    
    try {
        console.log('Loading farm day details for date:', date);
        const response = await fetch(`/get-farm-day-details/${date}`);
        const data = await response.json();
        
        if (data.success) {
            displayFarmDayDetails(data);
        } else {
            showError(data.error || 'Failed to load farm day details');
        }
    } catch (error) {
        console.error('Error loading farm day details:', error);
        showError('Error loading farm day details: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayFarmDayDetails(data) {
    const container = document.getElementById('dayDetailsContainer');
    container.classList.remove('d-none');
    document.getElementById('noDataMessage').classList.add('d-none');
    
    // Update day title
    document.getElementById('dayTitle').textContent = `Farm Day Details - ${data.date_info.date}`;
    
    // Display summary stats
    displayFarmSummaryStats(data.totals, data.summary);
    
    // Display day information
    displayFarmDayInfo(data.date_info, data.summary);
    
    // Display poultry data
    displayPoultryData(data.poultry_data, data.totals.poultry);
    
    // Display sales data
    displayFarmSalesData(data.totals.sales);
    
    // Display production data
    displayProductionData(data.totals.production);
    
    // Display feed data
    displayFeedData(data.totals.feed);
    
    // Display mortality data
    displayMortalityData(data.totals.mortality);
    
    // Display percentage data
    displayPercentageData(data.totals.percentage);
    
    // Display activity log
    displayFarmActivityLog(data.activity_log);
    
    // Display users involved
    displayFarmUsers(data.user_records);
}

function displayFarmSummaryStats(totals, summary) {
    const container = document.getElementById('summaryStats');
    const profitClass = totals.poultry.total_net >= 0 ? 'profit' : 'loss';
    
    container.innerHTML = `
        <div class="col-md-3">
            <div class="stat-card ${profitClass}">
                <div class="stat-value">${formatCurrency(totals.poultry.total_net)}</div>
                <div class="stat-label">Net Profit</div>
                <small>Gross: ${formatCurrency(totals.poultry.total_gross)}</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card info">
                <div class="stat-value">${formatNumber(totals.production.total_quantity)}</div>
                <div class="stat-label">Total Production</div>
                <small>${totals.production.count} products</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card neutral stats-feed">
                <div class="stat-value">${formatNumber(totals.feed.total_bags)}</div>
                <div class="stat-label">Feed Used (bags)</div>
                <small>${totals.feed.count} records</small>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card stats-mortality ${totals.mortality.total_count > 0 ? 'loss' : 'profit'}">
                <div class="stat-value">${formatNumber(totals.mortality.total_count)}</div>
                <div class="stat-label">Mortality</div>
                <small>Rate: ${totals.mortality_rate.toFixed(1)}%</small>
            </div>
        </div>
    `;
}

function displayFarmDayInfo(dateInfo, summary) {
    const container = document.getElementById('dayInfo');
    
    container.innerHTML = `
        <div class="col-md-6">
            <table class="table table-sm table-day-details opacity-75">
                <tr>
                    <th width="40%">Date:</th>
                    <td>${dateInfo.date}</td>
                </tr>
                <tr>
                    <th>Created:</th>
                    <td>${dateInfo.created_at || 'N/A'}</td>
                </tr>
                <tr>
                    <th>Created By:</th>
                    <td><span class="badge badge-record">${dateInfo.created_by || 'Unknown'}</span></td>
                </tr>
            </table>
        </div>
        <div class="col-md-6">
            <table class="table table-sm table-day-details opacity-75">
                <tr>
                    <th width="40%">Feed Efficiency:</th>
                    <td>${summary.efficiency_metrics.feed_efficiency.toFixed(2)}%</td>
                </tr>
                <tr>
                    <th>Mortality Rate:</th>
                    <td>${summary.efficiency_metrics.mortality_rate.toFixed(2)}%</td>
                </tr>
                <tr>
                    <th>Profit per Bag:</th>
                    <td>${formatCurrency(summary.efficiency_metrics.profit_per_bag)}</td>
                </tr>
            </table>
        </div>
    `;
}

function displayPoultryData(poultryData, poultryTotals) {
    const container = document.getElementById('poultryDetails');
    
    if (!poultryData || poultryData.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No poultry data recorded for this day.</div>';
        return;
    }
    
    let html = `
        <div class="alert alert-success">
            <strong>Poultry Summary:</strong> ${poultryTotals.count} houses, 
            Gross: ${formatCurrency(poultryTotals.total_gross)} | 
            Damage: ${formatCurrency(poultryTotals.total_damage)} | 
            Net: ${formatCurrency(poultryTotals.total_net)}
        </div>
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>Poultry House</th>
                    <th>Gross Profit</th>
                    <th>Damage Value</th>
                    <th>Net Production</th>
                    <th>Recorded By</th>
                    <th>Time</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    poultryData.forEach(poultry => {
        html += `
            <tr>
                <td><strong>House ${poultry.poultry_house}</strong></td>
                <td class="text-success">${formatCurrency(poultry.gross_profit)}</td>
                <td class="text-danger">${formatCurrency(poultry.damage_value)}</td>
                <td class="${poultry.net_production >= 0 ? 'text-success' : 'text-danger'}">
                    ${formatCurrency(poultry.net_production)}
                </td>
                <td><span class="badge badge-record">${poultry.updated_by || 'Unknown'}</span></td>
                <td>${formatTime(poultry.updated_at)}</td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
            <tfoot>
                <tr class="table-primary">
                    <td><strong>Totals</strong></td>
                    <td><strong>${formatCurrency(poultryTotals.total_gross)}</strong></td>
                    <td><strong>${formatCurrency(poultryTotals.total_damage)}</strong></td>
                    <td><strong>${formatCurrency(poultryTotals.total_net)}</strong></td>
                    <td colspan="2"></td>
                </tr>
            </tfoot>
        </table>
    `;
    
    container.innerHTML = html;
}

function displayFarmSalesData(salesTotals) {
    const container = document.getElementById('farmSalesDetails');
    
    let html = `
        <div class="alert alert-primary">
            <strong>Sales Summary:</strong> ${formatCurrency(salesTotals.total_amount)} total (${salesTotals.count} items)
        </div>
    `;
    
    if (salesTotals.items.length > 0) {
        // Product breakdown
        if (Object.keys(salesTotals.by_product).length > 0) {
            html += '<p><strong>Sales by Product:</strong></p><ul class="list-group mb-3">';
            Object.entries(salesTotals.by_product).forEach(([product, amount]) => {
                const percentage = (amount / salesTotals.total_amount * 100).toFixed(1);
                html += `<li class="list-group-item d-flex justify-content-between">
                    <span>${product}</span>
                    <span>${formatCurrency(amount)} (${percentage}%)</span>
                </li>`;
            });
            html += '</ul>';
        }
        
        html += `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Unit Price</th>
                            <th>Total Value</th>
                            <th>Recorded By</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        salesTotals.items.forEach(sale => {
            html += `
                <tr>
                    <td>${sale.product_type}</td>
                    <td>${formatNumber(sale.quantity)}</td>
                    <td>${formatCurrency(sale.unit_price)}</td>
                    <td>${formatCurrency(sale.total_value)}</td>
                    <td><span class="badge badge-record">${sale.updated_by}</span></td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted">No sales recorded.</p>';
    }
    
    container.innerHTML = html;
}

function displayProductionData(productionTotals) {
    const container = document.getElementById('productionDetails');
    
    let html = `
        <div class="alert alert-info">
            <strong>Production Summary:</strong> ${formatNumber(productionTotals.total_quantity)} total units (${productionTotals.count} items)
        </div>
    `;
    
    if (productionTotals.items.length > 0) {
        // Product breakdown
        if (Object.keys(productionTotals.by_product).length > 0) {
            html += '<p><strong>Production by Product:</strong></p><ul class="list-group mb-3">';
            Object.entries(productionTotals.by_product).forEach(([product, quantity]) => {
                const percentage = (quantity / productionTotals.total_quantity * 100).toFixed(1);
                html += `<li class="list-group-item d-flex justify-content-between">
                    <span>${product}</span>
                    <span>${formatNumber(quantity)} (${percentage}%)</span>
                </li>`;
            });
            html += '</ul>';
        }
        
        html += `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Product</th>
                            <th>Quantity</th>
                            <th>Recorded By</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        productionTotals.items.forEach(prod => {
            html += `
                <tr>
                    <td>${prod.product_type}</td>
                    <td>${formatNumber(prod.quantity)}</td>
                    <td><span class="badge badge-record">${prod.updated_by}</span></td>
                    <td>${formatTime(prod.updated_at)}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted">No production recorded.</p>';
    }
    
    container.innerHTML = html;
}

function displayFeedData(feedTotals) {
    const container = document.getElementById('feedDetails');
    
    let html = `
        <div class="alert alert-warning">
            <strong>Feed Summary:</strong> ${formatNumber(feedTotals.total_bags)} bags total (${feedTotals.count} records)
        </div>
    `;
    
    if (feedTotals.items.length > 0) {
        // House breakdown
        if (Object.keys(feedTotals.by_house).length > 0) {
            html += '<p><strong>Feed Usage by House:</strong></p><ul class="list-group mb-3">';
            Object.entries(feedTotals.by_house).forEach(([house, bags]) => {
                const percentage = (bags / feedTotals.total_bags * 100).toFixed(1);
                html += `<li class="list-group-item d-flex justify-content-between">
                    <span>House ${house}</span>
                    <span>${formatNumber(bags)} bags (${percentage}%)</span>
                </li>`;
            });
            html += '</ul>';
        }
        
        // Feed type breakdown
        if (Object.keys(feedTotals.by_type).length > 0) {
            html += '<p><strong>Feed Type Breakdown:</strong></p><ul class="list-group mb-3">';
            Object.entries(feedTotals.by_type).forEach(([type, bags]) => {
                html += `<li class="list-group-item d-flex justify-content-between">
                    <span>${type}</span>
                    <span>${formatNumber(bags)} bags</span>
                </li>`;
            });
            html += '</ul>';
        }
        
        html += `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>House</th>
                            <th>Feed Type</th>
                            <th>Bags Used</th>
                            <th>Recorded By</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        feedTotals.items.forEach(feed => {
            html += `
                <tr>
                    <td>House ${feed.house}</td>
                    <td>${feed.feed_type}</td>
                    <td>${formatNumber(feed.bags_used)}</td>
                    <td><span class="badge badge-record">${feed.updated_by}</span></td>
                    <td>${formatTime(feed.updated_at)}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted">No feed data recorded.</p>';
    }
    
    container.innerHTML = html;
}

function displayMortalityData(mortalityTotals) {
    const container = document.getElementById('mortalityDetails');
    
    let html = `
        <div class="alert alert-danger">
            <strong>Mortality Summary:</strong> ${formatNumber(mortalityTotals.total_count)} total deaths (${mortalityTotals.count} records)
        </div>
    `;
    
    if (mortalityTotals.items.length > 0) {
        // House breakdown
        if (Object.keys(mortalityTotals.by_house).length > 0) {
            html += '<p><strong>Mortality by House:</strong></p><ul class="list-group mb-3">';
            Object.entries(mortalityTotals.by_house).forEach(([house, count]) => {
                const percentage = (count / mortalityTotals.total_count * 100).toFixed(1);
                html += `<li class="list-group-item d-flex justify-content-between">
                    <span>House ${house}</span>
                    <span>${formatNumber(count)} (${percentage}%)</span>
                </li>`;
            });
            html += '</ul>';
        }
        
        // Reason breakdown
        if (Object.keys(mortalityTotals.by_reason).length > 0) {
            html += '<p><strong>Mortality by Reason:</strong></p><ul class="list-group mb-3">';
            Object.entries(mortalityTotals.by_reason).forEach(([reason, count]) => {
                html += `<li class="list-group-item d-flex justify-content-between">
                    <span>${reason}</span>
                    <span>${formatNumber(count)}</span>
                </li>`;
            });
            html += '</ul>';
        }
        
        html += `
            <div class="table-responsive">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>House</th>
                            <th>Reason</th>
                            <th>Count</th>
                            <th>Recorded By</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        mortalityTotals.items.forEach(mortality => {
            html += `
                <tr>
                    <td>House ${mortality.house}</td>
                    <td>${mortality.reason}</td>
                    <td class="text-danger">${formatNumber(mortality.count)}</td>
                    <td><span class="badge badge-record">${mortality.updated_by}</span></td>
                    <td>${formatTime(mortality.updated_at)}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += '<p class="text-muted">No mortality recorded.</p>';
    }
    
    container.innerHTML = html;
}

function displayPercentageData(percentageTotals) {
    const container = document.getElementById('percentageDetails');
    
    if (percentageTotals.items.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No percentage data recorded.</div>';
        return;
    }
    
    let html = `
        <div class="alert alert-secondary">
            <strong>Percentage Records:</strong> ${percentageTotals.count} records
        </div>
    `;
    
    // House breakdown
    if (Object.keys(percentageTotals.by_house).length > 0) {
        html += '<div class="row">';
        Object.entries(percentageTotals.by_house).forEach(([house, percentages]) => {
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">House ${house}</h6>
                        </div>
                        <div class="card-body">
            `;
            
            Object.entries(percentages).forEach(([type, value]) => {
                html += `
                    <div class="mb-2">
                        <strong>${type}:</strong>
                        <div class="progress">
                            <div class="progress-bar bg-info" role="progressbar" 
                                 style="width: ${value}%" aria-valuenow="${value}" 
                                 aria-valuemin="0" aria-valuemax="100">
                                ${value}%
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    html += `
        <div class="table-responsive">
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>House</th>
                        <th>Type</th>
                        <th>Value (%)</th>
                        <th>Recorded By</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    percentageTotals.items.forEach(percent => {
        html += `
            <tr>
                <td>House ${percent.house}</td>
                <td>${percent.type}</td>
                <td>
                    <div class="progress" style="height: 20px;">
                        <div class="progress-bar bg-info" role="progressbar" 
                             style="width: ${percent.value}%">${percent.value}%</div>
                    </div>
                </td>
                <td><span class="badge badge-record">${percent.updated_by}</span></td>
                <td>${formatTime(percent.updated_at)}</td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    container.innerHTML = html;
}

function displayFarmActivityLog(activityLog) {
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
                                <span class="badge bg-${getFarmActivityColor(activity.type)} me-2">${activity.type}</span>
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

function displayFarmUsers(userRecords) {
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

function getFarmActivityColor(type) {
    const colors = {
        'Day Created': 'primary',
        'Poultry Update': 'success',
        'Sales Update': 'warning',
        'Production Update': 'info',
        'Feed Update': 'secondary',
        'Mortality Update': 'danger',
        'Percentage Update': 'dark'
    };
    return colors[type] || 'secondary';
}

function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined) return '0.00';
    return parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

function formatTime(timestamp) {
    if (!timestamp) return 'N/A';

    try {
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
            <button class="btn btn-sm btn-outline-danger" onclick="loadFarmDayDetails(document.querySelector('.day-btn.active')?.getAttribute('data-date') || '')">
                <i class="fas fa-redo me-1"></i> Try Again
            </button>
        </div>
    `;
    hideLoading();
}

function loadCurrentDay() {
    const today = new Date().toISOString().split('T')[0];
    loadFarmDayDetails(today);
}

function loadPreviousDay() {
    const activeBtn = document.querySelector('.day-btn.active');
    const dates = window.datesData || [];

    if (!activeBtn) {
        if (dates.length > 0) {
            const latestDate = dates[0].date;
            const [y, m] = latestDate.split('-');
            document.getElementById('monthPicker').value = `${y}-${m}`;
            renderMonthDays();
            setTimeout(() => {
                const btn = document.querySelector(`.day-btn[data-date="${latestDate}"]`);
                if (btn) {
                    document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                }
                loadFarmDayDetails(latestDate);
            }, 50);
        }
        return;
    }

    const currentDate = activeBtn.getAttribute('data-date');
    const currentIndex = dates.findIndex(d => d.date === currentDate);

    if (currentIndex < dates.length - 1) {
        const prevDate = dates[currentIndex + 1].date;
        const [y, m] = prevDate.split('-');
        const monthPicker = document.getElementById('monthPicker');
        if (monthPicker.value !== `${y}-${m}`) {
            monthPicker.value = `${y}-${m}`;
            renderMonthDays();
        }
        setTimeout(() => {
            const btn = document.querySelector(`.day-btn[data-date="${prevDate}"]`);
            if (btn) {
                document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
            loadFarmDayDetails(prevDate);
        }, 50);
    } else {
        alert('No earlier farm days available.');
    }
}

function showComparisonModal() {
    const modal = new bootstrap.Modal(document.getElementById('comparisonModal'));
    modal.show();
}

function showDateFilterModal() {
    const modal = new bootstrap.Modal(document.getElementById('dateFilterModal'));
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
        const response = await fetch(`/compare-farm-days?date1=${date1}&date2=${date2}`);
        const data = await response.json();
        
        if (data.success) {
            displayFarmComparisonResults(data);
        } else {
            alert('Error comparing dates: ' + data.error);
        }
    } catch (error) {
        console.error('Error comparing dates:', error);
        alert('Error comparing dates: ' + error.message);
    }
}

function displayFarmComparisonResults(data) {
    const container = document.getElementById('comparisonResults');
    container.classList.remove('d-none');
    
    const comp = data.comparison;
    const arrow1 = comp.net_profit_change >= 0 ? '↑' : '↓';
    const arrow2 = comp.production_change >= 0 ? '↑' : '↓';
    const arrow3 = comp.feed_usage_change <= 0 ? '↑' : '↓'; // Less feed is better
    const arrow4 = comp.mortality_change <= 0 ? '↑' : '↓'; // Less mortality is better
    
    container.innerHTML = `
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h6 class="mb-0">Comparison Results: ${data.day1.date} vs ${data.day2.date}</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <div class="card ${comp.net_profit_change >= 0 ? 'border-success' : 'border-danger'}">
                            <div class="card-body">
                                <h6 class="card-title">Net Profit</h6>
                                <h3 class="${comp.net_profit_change >= 0 ? 'text-success' : 'text-danger'}">
                                    ${arrow1} ${Math.abs(comp.net_profit_change_percent).toFixed(1)}%
                                </h3>
                                <p class="card-text small">
                                    ${data.day1.date}: ${formatCurrency(data.day1.totals.poultry.total_net)}<br>
                                    ${data.day2.date}: ${formatCurrency(data.day2.totals.poultry.total_net)}<br>
                                    Change: ${formatCurrency(comp.net_profit_change)}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card ${comp.production_change >= 0 ? 'border-success' : 'border-danger'}">
                            <div class="card-body">
                                <h6 class="card-title">Production</h6>
                                <h3 class="${comp.production_change >= 0 ? 'text-success' : 'text-danger'}">
                                    ${arrow2} ${Math.abs(comp.production_change_percent).toFixed(1)}%
                                </h3>
                                <p class="card-text small">
                                    ${data.day1.date}: ${formatNumber(data.day1.totals.production.total_quantity)}<br>
                                    ${data.day2.date}: ${formatNumber(data.day2.totals.production.total_quantity)}<br>
                                    Change: ${formatNumber(comp.production_change)}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card ${comp.feed_usage_change <= 0 ? 'border-success' : 'border-danger'}">
                            <div class="card-body">
                                <h6 class="card-title">Feed Usage</h6>
                                <h3 class="${comp.feed_usage_change <= 0 ? 'text-success' : 'text-danger'}">
                                    ${arrow3} ${Math.abs(comp.feed_usage_change_percent).toFixed(1)}%
                                </h3>
                                <p class="card-text small">
                                    ${data.day1.date}: ${formatNumber(data.day1.totals.feed.total_bags)} bags<br>
                                    ${data.day2.date}: ${formatNumber(data.day2.totals.feed.total_bags)} bags<br>
                                    Change: ${formatNumber(comp.feed_usage_change)}
                                </p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card ${comp.mortality_change <= 0 ? 'border-success' : 'border-danger'}">
                            <div class="card-body">
                                <h6 class="card-title">Mortality</h6>
                                <h3 class="${comp.mortality_change <= 0 ? 'text-success' : 'text-danger'}">
                                    ${arrow4} ${Math.abs(comp.mortality_change_percent).toFixed(1)}%
                                </h3>
                                <p class="card-text small">
                                    ${data.day1.date}: ${formatNumber(data.day1.totals.mortality.total_count)}<br>
                                    ${data.day2.date}: ${formatNumber(data.day2.totals.mortality.total_count)}<br>
                                    Change: ${formatNumber(comp.mortality_change)}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Efficiency Changes</div>
                            <div class="card-body">
                                <p><strong>Feed Efficiency:</strong> ${comp.efficiency_change.toFixed(2)}%</p>
                                <p><strong>Mortality Rate:</strong> ${comp.mortality_rate_change.toFixed(2)}%</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">Summary</div>
                            <div class="card-body">
                                ${comp.net_profit_change >= 0 ? 
                                    '<span class="text-success">✓ Profit increased</span>' : 
                                    '<span class="text-danger">✗ Profit decreased</span>'}<br>
                                ${comp.production_change >= 0 ? 
                                    '<span class="text-success">✓ Production increased</span>' : 
                                    '<span class="text-danger">✗ Production decreased</span>'}<br>
                                ${comp.feed_usage_change <= 0 ? 
                                    '<span class="text-success">✓ Feed efficiency improved</span>' : 
                                    '<span class="text-danger">✗ Feed efficiency worsened</span>'}<br>
                                ${comp.mortality_change <= 0 ? 
                                    '<span class="text-success">✓ Mortality decreased</span>' : 
                                    '<span class="text-danger">✗ Mortality increased</span>'}
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
    
    alert('Filter functionality to be implemented');
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('dateFilterModal'));
    modal.hide();
}

function exportFarmDayReport() {
    const activeButton = document.querySelector('.day-btn.active');
    if (!activeButton) {
        alert('Please select a date first.');
        return;
    }
    
    const selectedDate = activeButton.getAttribute('data-date');
    window.open(`/export-farm-day-report/${selectedDate}`, '_blank');
}

function printFarmDayReport() {
    window.print();
}

function refreshData() {
    const activeButton = document.querySelector('.day-btn.active');
    if (activeButton) {
        const selectedDate = activeButton.getAttribute('data-date');
        loadFarmDayDetails(selectedDate);
    } else {
        // If no date selected, just refresh the month view
        renderMonthDays();
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

        btn.className = `btn btn-sm day-btn ${
            d.status === 'active' ? 'btn-success' : 'btn-outline-secondary'
        }`;

        btn.setAttribute('data-date', d.date);
        btn.innerHTML = day;
        btn.onclick = () => {
            // Update active state
            document.querySelectorAll('.day-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadFarmDayDetails(d.date);
        };

        grid.appendChild(btn);
    });
}