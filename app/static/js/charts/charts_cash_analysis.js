// charts_cash_analysis.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart
    let cashCreditChart;
    let currentPeriod = 'week'; // default period
    
    const canvas = document.getElementById('cashCreditChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const container = document.getElementById('cash-chart-container');
    
    // Add period selector above the chart
    const selectorDiv = document.createElement('div');
    selectorDiv.className = 'd-flex justify-content-end mb-2';
    selectorDiv.id = 'cash-chart-controls';
    selectorDiv.innerHTML = `
        <div class="btn-group btn-group-sm" role="group">
            <button type="button" class="btn btn-outline-primary period-btn" data-period="week">Week</button>
            <button type="button" class="btn btn-outline-primary period-btn active" data-period="month">Month</button>
            <button type="button" class="btn btn-outline-primary period-btn" data-period="year">Year</button>
        </div>
    `;
    
    // Insert selector before the chart container
    container.parentNode.insertBefore(selectorDiv, container);
    
    // Initial fetch
    fetchSalesData(currentPeriod);
    
    // Add event listeners to period buttons
    document.querySelectorAll('#cash-chart-controls .period-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            document.querySelectorAll('#cash-chart-controls .period-btn').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            
            // Get period and fetch data
            currentPeriod = this.dataset.period;
            fetchSalesData(currentPeriod);
        });
    });
    
    function fetchSalesData(period) {
        // Show loading state
        ctx.canvas.style.opacity = '0.5';
        
        fetch(`/api/sales-data?period=${period}`)
            .then(response => response.json())
            .then(data => {
                ctx.canvas.style.opacity = '1';
                if (data.success) {
                    renderChart(ctx, data.labels, data.cashData, data.creditData, period);
                } else {
                    console.error('Failed to fetch sales data');
                    showNoData(ctx, 'No sales data available');
                }
            })
            .catch(error => {
                ctx.canvas.style.opacity = '1';
                console.error('Error fetching sales data:', error);
                showNoData(ctx, 'Error loading data');
            });
    }
    
    function renderChart(ctx, labels, cashData, creditData, period) {
        // Destroy existing chart if it exists
        if (cashCreditChart) {
            cashCreditChart.destroy();
        }
        
        // Make sure canvas is visible
        ctx.canvas.style.display = 'block';
        
        // Remove any no-data message
        const parent = ctx.canvas.parentNode;
        const existingMsg = parent.querySelector('.no-data-message');
        if (existingMsg) existingMsg.remove();
        
        // Create gradient for cash sales
        const cashGradient = ctx.createLinearGradient(0, 0, 0, 300);
        cashGradient.addColorStop(0, 'rgba(145, 215, 161, 0.8)');
        cashGradient.addColorStop(1, 'rgba(62, 82, 67, 0.1)');
        
        // Create gradient for credit sales
        const creditGradient = ctx.createLinearGradient(0, 0, 0, 300);
        creditGradient.addColorStop(0, 'rgba(255, 193, 7, 0.8)');
        creditGradient.addColorStop(1, 'rgba(255, 193, 7, 0.1)');
        
        // Determine x-axis title based on period
        let xAxisTitle = 'Day';
        if (period === 'week') xAxisTitle = 'Day of Week';
        else if (period === 'month') xAxisTitle = 'Day of Month';
        else if (period === 'year') xAxisTitle = 'Month';
        
        cashCreditChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Cash Sales (K)',
                        data: cashData,
                        borderColor: '#77977e',
                        backgroundColor: cashGradient,
                        borderWidth: 2,
                        pointBackgroundColor: '#267338',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Credit Sales (K)',
                        data: creditData,
                        borderColor: '#b7aa83',
                        backgroundColor: creditGradient,
                        borderWidth: 2,
                        pointBackgroundColor: '#ffc107',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Sales Analysis (${period.charAt(0).toUpperCase() + period.slice(1)}ly View)`,
                        font: { size: 12, weight: 'bold' },
                        padding: { bottom: 10 }
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 6,
                            font: { size: 11 }
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
        if (cashCreditChart) {
            cashCreditChart.destroy();
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