document.addEventListener('DOMContentLoaded', async () => {
    // Check if the page is opened via file:// protocol
    if (window.location.protocol === 'file:') {
        console.error('CORS Error: Fetch API does not support local files (file://).');
        document.getElementById('table-body').innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center; padding: 40px; color: #f97316;">
                    <strong>由於瀏覽器安全限制 (CORS)，無法直接開啟本地檔案進行資料抓取。</strong><br><br>
                    請在終端機執行以下指令啟動本地伺服器：<br>
                    <code>python3 -m http.server</code><br><br>
                    然後在瀏覽器開啟：<a href="http://localhost:8000" style="color: #60a5fa;">http://localhost:8000</a>
                </td>
            </tr>`;
        return;
    }

    try {
        const response = await fetch('data/data.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const jsonData = await response.json();
        
        const stocks = jsonData.data;
        const metadata = jsonData.metadata;

        // Update display time
        document.getElementById('update-time').textContent = metadata.update_date;

        initPieChart(stocks);
        renderTable(stocks);
        setupShowMore(stocks.length);
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('table-body').innerHTML = '<tr><td colspan="6" style="text-align:center">無法載入資料，請確認 data.json 是否存在。</td></tr>';
    }
});

function initPieChart(stocks) {
    const chartDom = document.getElementById('industry-pie-chart');
    const myChart = echarts.init(chartDom, 'dark');
    
    // Count occurrences of each industry
    const counts = {};
    stocks.forEach(s => {
        counts[s.industry] = (counts[s.industry] || 0) + 1;
    });

    // Convert to ECharts format
    let data = Object.keys(counts).map(name => ({
        name: name,
        value: counts[name]
    }));

    // Sort and group small categories into "Other"
    data.sort((a, b) => b.value - a.value);
    
    const threshold = 2; // Categories with <= 2 stocks grouped as 'Other'
    let finalData = data.filter(item => item.value > threshold);
    let otherValue = data.filter(item => item.value <= threshold).reduce((sum, item) => sum + item.value, 0);
    
    if (otherValue > 0) {
        finalData.push({ name: '其他', value: otherValue });
    }

    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} 家 ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: { color: '#94a3b8' }
        },
        series: [
            {
                name: '產業佔比',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#1e293b',
                    borderWidth: 2
                },
                label: {
                    show: true,
                    formatter: '{b}: {d}%'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 20,
                        fontWeight: 'bold'
                    }
                },
                data: finalData
            }
        ],
        // Quality assurance colors (Reds/Oranges for buying bias)
        color: ['#ef4444', '#f97316', '#fbbf24', '#f87171', '#fb923c', '#ca8a04', '#7f1d1d', '#991b1b']
    };

    myChart.setOption(option);
    window.addEventListener('resize', myChart.resize);
}

function renderTable(stocks) {
    const tbody = document.getElementById('table-body');
    tbody.innerHTML = '';

    stocks.forEach((stock, index) => {
        const tr = document.createElement('tr');
        if (index >= 10) {
            tr.classList.add('hidden-row');
        }

        const changeClass = stock.change > 0 ? 'change-up' : (stock.change < 0 ? 'change-down' : '');
        const changePrefix = stock.change > 0 ? '+' : '';

        tr.innerHTML = `
            <td>${index + 1}</td>
            <td><span class="stock-id">${stock.id}</span> <strong>${stock.name}</strong></td>
            <td>${stock.close}</td>
            <td class="${changeClass}">${changePrefix}${stock.change} (${changePrefix}${stock.change_percent}%)</td>
            <td>${stock.volume.toLocaleString()}</td>
            <td>${stock.industry}</td>
        `;
        tbody.appendChild(tr);
    });
}

function setupShowMore(total) {
    const btn = document.getElementById('show-more-btn');
    if (total <= 10) {
        btn.style.display = 'none';
        return;
    }

    btn.addEventListener('click', () => {
        const hiddenRows = document.querySelectorAll('.hidden-row');
        hiddenRows.forEach(row => row.classList.remove('hidden-row'));
        btn.style.display = 'none';
    });
}
