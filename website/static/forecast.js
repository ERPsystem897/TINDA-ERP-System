document.addEventListener('DOMContentLoaded', function() {
    // Get the canvas elements from the HTML
    const ivoryRiceCanvas = document.getElementById('forecastIvoryRiceChart');
    const donaConchitaCanvas = document.getElementById('forecastDonaConchitaChart');

    // Data passed from Flask (forecasted values for rice)
    const ivoryRiceForecast = {{ forecast_ivory_rice_kg|tojson }};
    const donaConchitaForecast = {{ forecast_dona_conchita_kg|tojson }};
    const months = {{ future_months|tojson }};  // Months array

    // Create the chart for Ivory Rice
    new Chart(ivoryRiceCanvas, {
        type: 'line',  // Line chart for forecasting
        data: {
            labels: months,  // The months will be the labels for the x-axis
            datasets: [{
                label: 'Ivory Rice Forecast (kg)',
                data: ivoryRiceForecast,  // Forecast data for Ivory Rice
                borderColor: 'rgb(75, 192, 192)',  // Color for the line
                fill: false,  // No fill under the line
                tension: 0.1  // Smoothing the line
            }]
        },
        options: {
            responsive: true,
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
                        text: 'kg Sold'
                    }
                }
            }
        }
    });

    // Create the chart for Dona Conchita Rice
    new Chart(donaConchitaCanvas, {
        type: 'line',  // Line chart for forecasting
        data: {
            labels: months,  // The months will be the labels for the x-axis
            datasets: [{
                label: 'Dona Conchita Rice Forecast (kg)',
                data: donaConchitaForecast,  // Forecast data for Dona Conchita Rice
                borderColor: 'rgb(255, 99, 132)',  // Color for the line
                fill: false,  // No fill under the line
                tension: 0.1  // Smoothing the line
            }]
        },
        options: {
            responsive: true,
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
                        text: 'kg Sold'
                    }
                }
            }
        }
    });
});
