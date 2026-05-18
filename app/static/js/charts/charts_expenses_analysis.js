// charts_expenses_analysis.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart
    let expensesChart;
    let currentPeriod = 'week'; // default period
    let chartType = 'line'; // default chart type
    
    const canvas = document.getElementById('expensesChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('expenses-chart-container');
    
    // Add controls container
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'd-flex justify-content-between align-items-center mb-2';
    controlsDiv.id = 'expenses-chart-controls';
    controlsDiv.innerHTML = `
        <div class="btn-group btn-group-sm" role="group">
            <button type="button" class="btn btn-outline-secondary chart-type-btn active" data-type="line">
                <i class="fas fa-chart-line"></i>
            </button>
            <button type="button" class="btn btn-outline-secondary chart-type-btn" data-type="bar">
                <i class="fas fa-chart-bar"></i>
            </button>
        </div>
        <div class="btn-group btn-group-sm" role="group">
            <button type="button" class="btn btn-outline-primary period-btn" data-period="week">Week</button>
            <button type="button" class="btn btn-outline-primary period-btn active" data-period="month">Month</button>
            <button type="button" class="btn btn-outline-primary period-btn" data-period="year">Year</button>
        </div>
    `;
    
    // Insert controls before the chart container
    container.parentNode.insertBefore(controlsDiv, container);
    
    // Initial fetch
    fetchExpensesData(currentPeriod);
    
    // Add event listeners to period buttons
    document.querySelectorAll('#expenses-chart-controls .period-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            document.querySelectorAll('#expenses-chart-controls .period-btn').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            
            // Get period and fetch data
            currentPeriod = this.dataset.period;
            fetchExpensesData(currentPeriod);
        });
    });
    
    // Add event listeners to chart type buttons
    document.querySelectorAll('#expenses-chart-controls .chart-type-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            document.querySelectorAll('#expenses-chart-controls .chart-type-btn').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            
            // Get chart type and update
            chartType = this.dataset.type;
            
            // Update chart type
            if (expensesChart) {
                expensesChart.config.type = chartType;
                expensesChart.update();
            }
        });
    });
    
    function fetchExpensesData(period) {
        // Show loading state
        ctx.canvas.style.opacity = '0.5';
        
        fetch(`/api/expenses-data?period=${period}`)
            .then(response => response.json())
            .then(data => {
                ctx.canvas.style.opacity = '1';
                if (data.success) {
                    renderChart(ctx, data.labels, data.expensesData, data.categories, period);
                } else {
                    console.error('Failed to fetch expenses data');
                    showNoData(ctx, 'No expenses data available');
                }
            })
            .catch(error => {
                ctx.canvas.style.opacity = '1';
                console.error('Error fetching expenses data:', error);
                showNoData(ctx, 'Error loading data');
            });
    }
    
    function renderChart(ctx, labels, expensesData, categories, period) {
        // Destroy existing chart if it exists
        if (expensesChart) {
            expensesChart.destroy();
        }
        
        // Make sure canvas is visible
        ctx.canvas.style.display = 'block';
        
        // Remove any no-data message
        const parent = ctx.canvas.parentNode;
        const existingMsg = parent.querySelector('.no-data-message');
        if (existingMsg) existingMsg.remove();
        
        // Determine x-axis title based on period
        let xAxisTitle = 'Day';
        if (period === 'week') xAxisTitle = 'Day of Week';
        else if (period === 'month') xAxisTitle = 'Day of Month';
        else if (period === 'year') xAxisTitle = 'Month';
        
        // Create datasets
        let datasets = [];
        
        if (categories && categories.length > 0 && categories[0].data && categories[0].data.length > 0) {
            // If we have category data, show them
            const colors = [
                'rgba(220, 53, 69, 0.7)',   // red
                'rgba(255, 193, 7, 0.7)',   // yellow
                'rgba(23, 162, 184, 0.7)',  // cyan
                'rgba(108, 117, 125, 0.7)', // gray
                'rgba(40, 167, 69, 0.7)',   // green
                'rgba(111, 66, 193, 0.7)'   // purple
            ];
            
            categories.forEach((category, index) => {
                const color = colors[index % colors.length];
                datasets.push({
                    label: category.name,
                    data: category.data,
                    backgroundColor: color,
                    borderColor: color.replace('0.7', '1'),
                    borderWidth: 1,
                    tension: 0.3
                });
            });
        } else {
            // Simple expenses dataset
            const gradient = ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, 'rgba(220, 53, 69, 0.8)');
            gradient.addColorStop(1, 'rgba(220, 53, 69, 0.1)');
            
            datasets = [{
                label: 'Total Expenses (K)',
                data: expensesData,
                borderColor: '#dc3545',
                backgroundColor: gradient,
                borderWidth: 2,
                pointBackgroundColor: '#dc3545',
                pointBorderColor: '#fff',
                pointBorderWidth: 1,
                pointRadius: 3,
                pointHoverRadius: 5,
                tension: 0.3,
                fill: true
            }];
        }
        
        expensesChart = new Chart(ctx, {
            type: chartType,
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Expenses Analysis (${period.charAt(0).toUpperCase() + period.slice(1)}ly View)`,
                        font: { size: 12, weight: 'bold' },
                        padding: { bottom: 10 }
                    },
                    legend: {
                        display: datasets.length > 1,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 6,
                            font: { size: 10 }
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += 'K' + context.parsed.y.toFixed(2);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            callback: function(value) {
                                return 'K' + value;
                            },
                            font: { size: 10 }
                        },
                        title: {
                            display: true,
                            text: 'Amount (K)',
                            font: { size: 10 }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            font: { size: 10 }
                        },
                        title: {
                            display: true,
                            text: xAxisTitle,
                            font: { size: 10 }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
    
    function showNoData(ctx, message) {
        if (expensesChart) {
            expensesChart.destroy();
        }
        
        // Clear canvas and show message
        const canvas = ctx.canvas;
        const parent = canvas.parentNode;
        canvas.style.display = 'none';
        
        // Remove existing message if any
        const existingMsg = parent.querySelector('.no-data-message');
        if (existingMsg) existingMsg.remove();
        
        const msgDiv = document.createElement('div');
        msgDiv.className = 'no-data-message d-flex align-items-center justify-content-center h-100';
        msgDiv.innerHTML = `<p class="text-muted mb-0">${message}</p>`;
        parent.appendChild(msgDiv);
    }
});