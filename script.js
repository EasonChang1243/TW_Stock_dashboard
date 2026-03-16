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

        updateDashboard(jsonData);
    } catch (error) {
        console.error('Error loading data:', error);
        const tbody = document.getElementById('table-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">\u7121\u6cd5\u8f09\u5165\u8cc7\u6599\uff0c\u8acb\u78ba\u8a8d data.json \u662f\u5426\u5b58\u5728\u3002</td></tr>';
        }
    }
});

function updateDashboard(data) {
    if (!data) return;
    const stocks = data.rankings[currentInvestorType] ? data.rankings[currentInvestorType][currentInterval] : null;
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

    // Update table header
    const volumeHeader = document.querySelector('th:nth-child(5)');
    if (volumeHeader) volumeHeader.textContent = `${currentInterval}\u65e5\u7d2f\u7a4d\u8cb7\u8d85 (\u5bc5)`;

    // Module 3: US Markets
    renderUSMarkets(data.us_markets);

    // Module 2: Industry Pie & Consecutive
    initPieChart('industry-pie-chart', stocks);
    initPieChart('consecutive-industry-pie-chart', data.consecutive_buys[currentInvestorType], stocks);
    renderConsecutiveBuys(data.consecutive_buys[currentInvestorType], stocks);
    setupTableShowMore('consecutive-body', 'consecutive-show-more-btn', data.consecutive_buys[currentInvestorType].length, '.consecutive-section .card');

    // Module 1: Main Table
    renderTable(stocks);
    setupTableShowMore('table-body', 'show-more-btn', stocks.length, '.table-section .card');
}

function renderUSMarkets(markets) {
    const grid = document.getElementById('us-market-grid');
    if (!grid || !markets) return;
    grid.innerHTML = '';

    markets.forEach(m => {
        const isUp = m.change_percent >= 0;
        const colorClass = isUp ? 'text-up' : 'text-down';
        const bgClass = isUp ? 'bg-up' : 'bg-down';
        const sign = isUp ? '+' : '';

        const card = document.createElement('div');
        card.className = 'market-card';
        card.innerHTML = `
            <div class="market-info">
                <div class="market-name">${m.name}</div>
                <div class="market-id">${m.id}</div>
            </div>
            <div class="market-sparkline-container">
                <canvas id="sparkline-${m.id.replace('^', '').replace('.', '-')}" width="120" height="40"></canvas>
            </div>
            <div class="market-value ${colorClass}">${m.close.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
            <div class="market-change-container">
                <div class="market-change ${bgClass}">${sign}${(m.change_percent || 0).toFixed(2)}%</div>
            </div>
        `;
        grid.appendChild(card);
        
        // Draw Sparkline
        setTimeout(() => {
            const canvas = document.getElementById(`sparkline-${m.id.replace('^', '').replace('.', '-')}`);
            if (canvas && m.history && m.history.length > 0) {
                drawSparkline(canvas, m.history, isUp ? '#22c55e' : '#ef4444');
            }
        }, 0);
    });
}

function drawSparkline(canvas, data, color) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    if (data.length < 2) return;
    
    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;
    
    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    
    const xStep = width / (data.length - 1);
    
    data.forEach((val, i) => {
        const x = i * xStep;
        const y = height - ((val - min) / range) * height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    
    ctx.stroke();
    
    // Add subtle gradient fill
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, color + '33'); // 20% opacity
    gradient.addColorStop(1, color + '00'); // 0% opacity
    ctx.fillStyle = gradient;
    ctx.fill();
}

function renderConsecutiveBuys(streaks) {
    const tbody = document.getElementById('consecutive-body');
    const title = document.getElementById('consecutive-title');
    if (!tbody || !streaks) return;

    const investorName = currentInvestorType === "foreign" ? "\u5916\u8cc7" : "\u6295\u4fe1";
    if (title) title.textContent = `${investorName}\u9023\u7e8c\u8cb7\u8d85\u6392\u884c\u699c`;

    tbody.innerHTML = '';
    streaks.forEach((item, index) => {
        const tr = document.createElement('tr');
        if (index >= 10) tr.classList.add('hidden-row');
        
        const isUp = item.change >= 0;
        const colorClass = isUp ? 'text-up' : 'text-down';
        const sign = isUp ? '+' : '';

        tr.innerHTML = `
            <td>${index + 1}</td>
            <td class="stock-name-cell">
                <span class="stock-name">${item.name}</span>
            </td>
            <td>${item.close > 0 ? item.close.toFixed(2) : '--'}</td>
            <td class="${colorClass}">${item.change !== 0 ? sign + item.change.toFixed(2) : '0'}</td>
            <td class="${colorClass}">${item.change_percent !== 0 ? sign + item.change_percent.toFixed(2) + '%' : '0%'}</td>
            <td class="text-up">${item.volume.toLocaleString()}</td>
            <td class="text-up">${item.amount.toLocaleString()}</td>
            <td><span class="streak-badge">${item.days} \u5929</span></td>
        `;
        tbody.innerHTML += tr.outerHTML;
    });

    setupShowMore('consecutive-show-more-btn', 'consecutive-body', streaks.length);
}


function initPieChart(chartId, stocks, metadataSource = null) {
    const chartDom = document.getElementById(chartId);
    if (!chartDom || typeof echarts === 'undefined') return;

    // Clear previous instance
    const existing = echarts.getInstanceByDom(chartDom);
    if (existing) existing.dispose();

    const myChart = echarts.init(chartDom, 'dark');
    
    const counts = {};
    if (stocks && stocks.length > 0) {
        stocks.forEach(s => {
            let industry = s.industry;
            if (!industry && metadataSource) {
                const meta = metadataSource.find(m => m.id === s.id);
                industry = meta ? meta.industry : "\u5176\u4ed6";
            }
            if (!industry) industry = "\u5176\u4ed6";
            
            counts[industry] = (counts[industry] || 0) + 1;
        });
    }

    let data = Object.keys(counts).map(name => ({
        name: name,
        value: counts[name]
    }));

    data.sort((a, b) => b.value - a.value);
    
    // Adjust threshold based on item count
    const threshold = stocks.length > 20 ? 2 : 0; 
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
            textStyle: { color: '#94a3b8' },
            type: 'scroll',
            show: stocks.length > 5
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
                    show: false
                },
                data: finalData
            }
        ],
        color: ['#ef4444', '#f97316', '#fbbf24', '#f87171', '#fb923c', '#eab308', '#991b1b', '#7c2d12']
    };

    myChart.setOption(option);
}

function renderTable(stocks) {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    stocks.forEach((stock, index) => {
        const tr = document.createElement('tr');
        if (index >= 10) {
            tr.classList.add('hidden-row');
            tr.style.display = 'none';
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

function setupTableShowMore(tbodyId, showMoreBtnId, total, scrollTargetSelector) {
    const btn = document.getElementById(showMoreBtnId);
    if (!btn) return;

    // Use total for consistency
    btn.style.display = total > 10 ? 'block' : 'none';
    btn.textContent = `\u986f\u793a\u66f4\u591a (\u9918 ${total - 10} \u6a94)`;

    // Remove old listeners
    const newBtn = btn.cloneNode(true);
    btn.parentNode.replaceChild(newBtn, btn);

    let isExpanded = false;
    newBtn.addEventListener('click', () => {
        const tbody = document.getElementById(tbodyId);
        const hiddenRows = tbody.querySelectorAll('tr.hidden-row');
        isExpanded = !isExpanded;

        hiddenRows.forEach((row) => {
            row.style.display = isExpanded ? 'table-row' : 'none';
        });

        if (isExpanded) {
            newBtn.textContent = `\u6536\u5408\u5167\u5bb9`;
        } else {
            newBtn.textContent = `\u986f\u793a\u66f4\u591a (\u9918 ${total - 10} \u6a94)`;
            document.querySelector(scrollTargetSelector).scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
}
