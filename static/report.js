window.addEventListener('load', () => {
    if (!window.Chart) return;
    const read = (id) => {
        const node = document.getElementById(id);
        return node ? JSON.parse(node.textContent) : null;
    };
    const draw = (id, config) => {
        const canvas = document.getElementById(id);
        if (!canvas) return;
        const current = Chart.getChart(canvas);
        if (current) current.destroy();
        new Chart(canvas, config);
    };

    draw('areaChart', {
        type: 'doughnut',
        data: {
            labels: ['Mainframe', 'Distribuido'],
            datasets: [{data: read('chart-data'), backgroundColor: ['#165c78', '#51c5bb'], borderWidth: 0, hoverOffset: 6}],
        },
        options: {plugins: {legend: {position: 'bottom'}}, cutout: '74%'},
    });

    const charts = read('chart-reports');
    if (!charts) return;

    draw('passChart', {
        type: 'bar',
        data: {
            labels: charts.pass.labels,
            datasets: [{label: '% de aprobación', data: charts.pass.values, backgroundColor: '#4a7de3', borderRadius: 4}],
        },
        options: {
            indexAxis: 'y',
            scales: {x: {min: 0, max: 100, ticks: {callback: (v) => v + '%'}}},
            plugins: {legend: {display: false}},
        },
    });

    draw('trendChart', {
        data: {
            labels: charts.trend.labels,
            datasets: [
                {type: 'bar', label: 'Intentos', data: charts.trend.attempts, backgroundColor: '#9db4e8', yAxisID: 'y', order: 2},
                {type: 'line', label: 'Promedio (%)', data: charts.trend.average, borderColor: '#168f98', backgroundColor: '#168f98', tension: 0.25, yAxisID: 'y1', order: 1},
            ],
        },
        options: {
            scales: {
                y: {beginAtZero: true, ticks: {precision: 0}, title: {display: true, text: 'Intentos'}},
                y1: {position: 'right', min: 0, max: 100, grid: {drawOnChartArea: false}, title: {display: true, text: 'Promedio %'}},
            },
            plugins: {legend: {position: 'bottom'}},
        },
    });
});
