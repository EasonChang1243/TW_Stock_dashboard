let allRankings = {};
let currentInterval = "5";
let currentInvestorType = "foreign";

document.addEventListener('DOMContentLoaded', async () => {
    // Check if the page is opened via file:// protocol
    if (window.location.protocol === 'file:') {
        console.error('CORS Error: Fetch API does not support local files (file://).');
        const tbody = document.getElementById('table-body');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align:center; padding: 40px; color: #f97316;">
                        <strong>\u7531\u65bc\u700f\u89bd\u5668\u5b89\u5168\u9650\u5236 (CORS)\uff0c\u7121\u6cd5\u76f4\u63a5\u958b\u555f\u672c\u5730\u6a94\u6848\u9032\u884c\u8cc7\u6599\u6293\u53d6\u3002</strong><br><br>
                        \u8acb\u5728\u7d42\u7aef\u6a5f\u57f7\u884c\u4ee5\u4e0b\u6307\u4ee4\u5554\u52d5\u672c\u5730\u4f3a\u670d\u5668\uff1a<br>
                        <code>python3 -m http.server</code><br><br>
                        \u7136\u5f8c\u5728\u700f\u89bd\u5668\u958b\u555f\uff1a<a href="http://localhost:8000" style="color: #60a5fa;">http://localhost:8000</a>
                    </td>
                </tr>`;
        }
        return;
    }

    try {
        const response = await fetch('data/data.json');
        if (!response.ok) throw new Error('Network response was not ok');
        const jsonData = await response.json();
        
        allRankings = jsonData.rankings;
        const metadata = jsonData.metadata;

        // Update display time
        const updateTimeEl = document.getElementById('update-time');
        if (updateTimeEl) updateTimeEl.textContent = metadata.update_date;

        // Investor Selector
        const investorSelector = document.getElementById('investor-selector');
        if (investorSelector) {
            investorSelector.addEventListener('change', (e) => {
                currentInvestorType = e.target.value;
                updateDashboard();
            });
        }

        // Day Selector
        const daySelector = document.getElementById('day-selector');
        if (daySelector) {
            daySelector.addEventListener('change', (e) => {
                currentInterval = e.target.value;
                updateDashboard();
            });
        }

        updateDashboard();
    } catch (error) {
        console.error('Error loading data:', error);
        const tbody = document.getElementById('table-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">\u7121\u6cd5\u8f09\u5165\u8cc7\u6599\uff0c\u8acb\u78ba\u8a8d data.json \u662f\u5426\u5b58\u5728\u3002</td></tr>';
        }
    }
});

function updateDashboard() {
    const stocks = allRankings[currentInvestorType] ? allRankings[currentInvestorType][currentInterval] : null;
    if (!stocks) return;

    const investorName = currentInvestorType === "foreign" ? "\u5916\u8cc7" : "\u6295\u4fe1";

    // Update subtitles
    const subtitleDays = document.getElementById('subtitle-days');
    if (subtitleDays) {
        const headerP = document.querySelector('.header-content p');
        if (headerP) {
            headerP.innerHTML = `\u8ffd\u8e64${investorName} <span id="subtitle-days">${currentInterval}</span> \u65e5\u7d2f\u7a4d\u8cb7\u8d85\u6392\u884c (\u5b98\u65b9\u6578\u64da\u7248)`;
        }
    }
    
    const tableTitle = document.querySelector('.card-title');
    if (tableTitle) tableTitle.textContent = `${investorName}\u8fd1 ${currentInterval} \u65e5\u7d2f\u7a4d\u8cb7\u8d85\u6392\u884c\u699c (Top 50)`;

    // Update table header if needed
    const volumeHeader = document.querySelector('th:nth-child(5)');
    if (volumeHeader) volumeHeader.textContent = `${currentInterval}\u65e5\u7d2f\u7a4d\u8cb7\u8d85 (\u5bc5)`;

    initPieChart(stocks);
    renderTable(stocks);
    setupShowMore(stocks.length);
}

function initPieChart(stocks) {
    const chartDom = document.getElementById('industry-pie-chart');
    if (!chartDom || typeof echarts === 'undefined') return;

    // Clear previous instance
    echarts.dispose(chartDom);
    const myChart = echarts.init(chartDom, 'dark');
    
    const counts = {};
    stocks.forEach(s => {
        counts[s.industry] = (counts[s.industry] || 0) + 1;
    });

    let data = Object.keys(counts).map(name => ({
        name: name,
        value: counts[name]
    }));

    data.sort((a, b) => b.value - a.value);
    
    const threshold = 2; 
    let finalData = data.filter(item => item.value > threshold);
    let otherValue = data.filter(item => item.value <= threshold).reduce((sum, item) => sum + item.value, 0);
    
    if (otherValue > 0) {
        finalData.push({ name: '\u5176\u4ed6', value: otherValue });
    }

    const option = {
        backgroundColor: 'transparent',
        tooltip: {
            trigger: 'item',
            formatter: '{b}: {c} \u5bb6 ({d}%)'
        },
        legend: {
            orient: 'vertical',
            left: 'left',
            textStyle: { color: '#94a3b8' }
        },
        series: [
            {
                name: '\u7522\u696d\u4f54\u6bd4',
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: true,
                itemStyle: {
                    borderRadius: 10,
                    borderColor: '#111827',
                    borderWidth: 2
                },
                label: {
                    show: true,
                    formatter: '{b}: {d}%'
                },
                emphasis: {
                    label: {
                        show: true,
                        fontSize: 18,
                        fontWeight: 'bold'
                    }
                },
                data: finalData
            }
        ],
        color: ['#ef4444', '#f97316', '#fbbf24', '#f87171', '#fb923c', '#eab308', '#991b1b', '#7c2d12']
    };

    myChart.setOption(option);
    window.addEventListener('resize', () => myChart.resize());
}

function renderTable(stocks) {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;
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

    const btn = document.getElementById('show-more-btn');
    if (btn) {
        btn.style.display = stocks.length > 10 ? 'block' : 'none';
        btn.textContent = `\u986f\u793a\u66f4\u591a (\u9918 ${stocks.length - 10} \u6a94)`;
    }
}

function setupShowMore(total) {
    const btn = document.getElementById('show-more-btn');
    if (!btn) return;

    // Remove old listeners to avoid multiple binds
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    let isExpanded = false;

    newBtn.addEventListener('click', () => {
        const hiddenRows = document.querySelectorAll('#table-body tr');
        isExpanded = !isExpanded;

        hiddenRows.forEach((row, index) => {
            if (index >= 10) {
                if (isExpanded) {
                    row.classList.remove('hidden-row');
                } else {
                    row.classList.add('hidden-row');
                }
            }
        });

        if (isExpanded) {
            newBtn.textContent = `\u6536\u5408\u5167\u5bb9`;
        } else {
            newBtn.textContent = `\u986f\u793a\u66f4\u591a (\u9918 ${total - 10} \u6a94)`;
            // Optional: scroll back to table start
            document.querySelector('.table-wrapper').scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
}
