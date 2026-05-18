<script src="path/to/chartjs/dist/chart.umd.min.js"></script>
<script>
    const myChart = new Chart(ctx, {...});
</script>
const labels = Utils.months({count: 7});
const data = {
  labels: labels,
  datasets: [{
    label: 'My First Dataset',
    data: [65, 59, 80, 81, 56, 55, 40],
    fill: false,
    borderColor: 'rgb(75, 192, 192)',
    tension: 0.1
  }]
};