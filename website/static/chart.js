// Ensure Chart.js is properly imported (only if you're using TypeScript and modules)
import { Chart } from 'chart.js';

const months_2024 = ["January", "February", "March", "April"];
const sheets_sold_2024 = [100, 150, 130, 180];
const sales_2024 = [350000, 500000, 460000, 630000];

// Debug: Check if data is being passed correctly
    console.log("Months 2024:", {{ months_2024 | tojson }});
    console.log("Sheets Sold 2024:", {{ sheets_sold_2024 | tojson }});
    console.log("Revenue 2024:", {{ sales_2024 | tojson }});

// Sheets Sold Chart (2024)
const salesChart = new Chart(document.getElementById('salesChart'), {
    type: 'line',
    data: {
        labels: months_2024,
        datasets: [{
            label: 'Sheets Sold (2024)',
            data: sheets_sold_2024,
            borderColor: 'rgb(75, 192, 192)',
            fill: false,
            tension: 0.1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Month'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Sheets Sold'
                }
            }
        }
    }
});

// Revenue Chart (2024)
const revenueChart = new Chart(document.getElementById('revenueChart'), {
    type: 'line',
    data: {
        labels: months_2024,
        datasets: [{
            label: 'Revenue (₱, 2024)',
            data: sales_2024,
            borderColor: 'rgb(153, 102, 255)',
            fill: false,
            tension: 0.1
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Month'
                }
            },
            y: {
                title: {
                    display: true,
                    text: 'Revenue (₱)'
                }
            }
        }
    }
});


