import json

# Load the full data
with open('backtest_results.json', 'r') as f:
    full_data = json.load(f)

# HTML Template
html_content = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USD & QLD 10년 적립식 백테스트 리포트</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@100;400;700&display=swap');
        body { font-family: 'Pretendard', sans-serif; background-color: #020617; color: #f8fafc; overflow: hidden; }
        .slide { 
            position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; 
            padding: 4rem; display: flex; flex-direction: column; justify-content: center; align-items: center;
            opacity: 0; transform: scale(0.95); transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
        }
        .slide.active { 
            opacity: 1; transform: scale(1); pointer-events: auto; z-index: 10;
        }
        .glass { background: rgba(30, 41, 59, 0.4); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .gradient-text { background: linear-gradient(90deg, #38bdf8, #818cf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .btn-nav { width: 3rem; height: 3rem; border-radius: 50%; background: rgba(255,255,255,0.05); display: flex; justify-content: center; align-items: center; transition: all 0.3s; }
        .btn-nav:hover { background: rgba(255,255,255,0.2); transform: scale(1.1); }
        .chart-box { width: 100%; max-width: 900px; height: 400px; }
        .table-container { max-height: 50vh; overflow-y: auto; width: 100%; max-width: 1000px; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
    </style>
</head>
<body>

    <div class="fixed bottom-8 right-8 z-50 flex gap-4">
        <button onclick="prevSlide()" class="btn-nav"><i class="fas fa-chevron-left"></i></button>
        <div id="slide-num" class="flex items-center text-sm font-mono text-slate-500 px-2">1 / 7</div>
        <button onclick="nextSlide()" class="btn-nav"><i class="fas fa-chevron-right"></i></button>
    </div>

    <div id="presentation">
        <section class="slide active">
            <h1 class="text-7xl font-bold mb-6 gradient-text">Quant Report</h1>
            <p class="text-3xl text-slate-400 mb-12">USD & QLD 10년 장기 적립식 백테스트</p>
            <div class="glass p-10 rounded-3xl text-center max-w-3xl">
                <div class="grid grid-cols-2 gap-8 mb-8">
                    <div>
                        <p class="text-slate-500 mb-1 uppercase tracking-widest text-xs">Monthly Buy</p>
                        <p class="text-2xl font-bold">800,000 KRW</p>
                    </div>
                    <div>
                        <p class="text-slate-500 mb-1 uppercase tracking-widest text-xs">Strategy</p>
                        <p class="text-2xl font-bold text-blue-400">2x Leverage DCA</p>
                    </div>
                </div>
                <p class="text-slate-500 italic">"레버리지와 시간이 결합할 때 발생하는 복리의 마법"</p>
            </div>
            <div class="mt-16 animate-bounce text-slate-600 text-sm">Use Arrow Keys to Navigate</div>
        </section>

        <section class="slide">
            <h2 class="text-4xl font-bold mb-12">투자 기간별 성과 지표 요약</h2>
            <div id="summary-grid" class="grid grid-cols-3 gap-6 max-w-6xl w-full"></div>
        </section>

        <section class="slide">
            <h2 class="text-4xl font-bold mb-8 text-center">기간이 길어질수록 압도적인 수익률</h2>
            <div class="chart-box glass p-8 rounded-3xl">
                <canvas id="trendChart"></canvas>
            </div>
        </section>

        <section class="slide">
            <h2 class="text-4xl font-bold mb-8">손실을 회피하고 수익을 고정하는 시간</h2>
            <div class="chart-box glass p-8 rounded-3xl">
                <canvas id="winRateChart"></canvas>
            </div>
            <div class="mt-8 glass p-6 rounded-2xl max-w-2xl text-center">
                <p class="text-lg">4년 이상 투자 시 <span class="text-blue-400 font-bold">원금 보존 확률 100%</span></p>
            </div>
        </section>

        <section class="slide">
            <h2 class="text-4xl font-bold mb-8">연도별 자산별 변동성 데이터</h2>
            <div class="table-container glass rounded-3xl">
                <table class="w-full text-left text-sm">
                    <thead class="bg-white/5 text-slate-400 sticky top-0">
                        <tr>
                            <th class="px-8 py-4">연도</th>
                            <th class="px-8 py-4 text-green-400">USD (2x Semi)</th>
                            <th class="px-8 py-4 text-blue-400">QLD (2x QQQ)</th>
                            <th class="px-8 py-4 text-slate-300">달러 환율</th>
                        </tr>
                    </thead>
                    <tbody id="matrix-body"></tbody>
                </table>
            </div>
        </section>

        <section class="slide">
            <div class="flex justify-between items-end w-full max-w-5xl mb-8">
                <h2 class="text-4xl font-bold">상세 투자 시나리오 익스플로러</h2>
                <select id="period-sel" class="bg-slate-800 border border-slate-700 rounded-lg px-6 py-2">
                    <option value="2Y">2년</option>
                    <option value="3Y">3년</option>
                    <option value="5Y" selected>5년</option>
                    <option value="10Y">10년</option>
                </select>
            </div>
            <div class="table-container glass rounded-3xl">
                <table class="w-full text-left text-sm">
                    <thead class="bg-white/5 text-slate-400 sticky top-0">
                        <tr>
                            <th class="px-8 py-4">시작 일자</th>
                            <th class="px-8 py-4">종료 일자</th>
                            <th class="px-8 py-4">수익률</th>
                            <th class="px-8 py-4">최종 평가액 (KRW)</th>
                        </tr>
                    </thead>
                    <tbody id="scenario-body"></tbody>
                </table>
            </div>
        </section>

        <section class="slide">
            <h2 class="text-5xl font-bold mb-16 gradient-text">결론 및 제언</h2>
            <div class="grid grid-cols-2 gap-12 max-w-5xl">
                <div class="glass p-10 rounded-3xl">
                    <h3 class="text-2xl font-bold mb-6 text-blue-400">전략적 우위</h3>
                    <ul class="space-y-4 text-slate-300">
                        <li><i class="fas fa-check mr-2 text-green-500"></i> 장기 투자 시 레버리지 비용보다 지수 상승폭이 압도적임</li>
                        <li><i class="fas fa-check mr-2 text-green-500"></i> 하락장에서도 환율이 일정 부분 완충 작용을 함</li>
                        <li><i class="fas fa-check mr-2 text-green-500"></i> 적립식 투자가 고점 매수 리스크를 효과적으로 분산</li>
                    </ul>
                </div>
                <div class="glass p-10 rounded-3xl">
                    <h3 class="text-2xl font-bold mb-6 text-red-400">주의 사항</h3>
                    <ul class="space-y-4 text-slate-300">
                        <li><i class="fas fa-exclamation-triangle mr-2 text-yellow-500"></i> 2년 내외 단기 투자 시 최대 40% 손실 가능</li>
                        <li><i class="fas fa-exclamation-triangle mr-2 text-yellow-500"></i> 횡보장에서의 음의 복리 발생 가능</li>
                        <li><i class="fas fa-exclamation-triangle mr-2 text-yellow-500"></i> 정신적인 고통을 견딜 수 있는 여유 자금 필수</li>
                    </ul>
                </div>
            </div>
        </section>
    </div>

    <script>
        const backtestData = REPLACE_DATA;

        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');

        function showSlide(index) {
            slides.forEach(s => s.classList.remove('active'));
            slides[index].classList.add('active');
            currentSlide = index;
            document.getElementById('slide-num').innerText = `${index + 1} / ${slides.length}`;
        }

        function nextSlide() { if (currentSlide < slides.length - 1) showSlide(currentSlide + 1); }
        function prevSlide() { if (currentSlide > 0) showSlide(currentSlide - 1); }

        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
        });

        function init() {
            renderSummary();
            renderCharts();
            renderMatrix();
            renderScenarios('5Y');
            document.getElementById('period-sel').onchange = (e) => renderScenarios(e.target.value);
        }

        function renderSummary() {
            const grid = document.getElementById('summary-grid');
            const keys = ["2Y", "3Y", "4Y", "5Y", "8Y", "10Y"];
            keys.forEach(k => {
                const data = backtestData.summary[k];
                const card = document.createElement('div');
                card.className = 'glass p-6 rounded-2xl flex flex-col justify-between';
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-4">
                        <span class="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full text-xs font-bold">${k}</span>
                        <span class="text-xs text-slate-500 font-mono">Win Rate ${data.win_rate.toFixed(0)}%</span>
                    </div>
                    <div class="text-3xl font-bold mb-1">${data.avg.toFixed(1)}%</div>
                    <div class="text-xs text-slate-400">Avg Return</div>
                    <div class="mt-4 pt-4 border-t border-white/5 space-y-1">
                        <div class="flex justify-between text-xs text-green-400"><span>Max</span> <span>+${data.max.toFixed(0)}%</span></div>
                        <div class="flex justify-between text-xs text-red-400"><span>Min</span> <span>${data.min.toFixed(0)}%</span></div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function renderCharts() {
            const keys = Object.keys(backtestData.summary);
            const avgs = keys.map(k => backtestData.summary[k].avg);
            const wins = keys.map(k => backtestData.summary[k].win_rate);

            new Chart(document.getElementById('trendChart'), {
                type: 'line',
                data: {
                    labels: keys,
                    datasets: [{ label: '평균 수익률 (%)', data: avgs, borderColor: '#38bdf8', fill: true, backgroundColor: '#38bdf822', tension: 0.4 }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } }, scales: { y: { ticks: { color: '#94a3b8' }, grid: { color: '#ffffff08' } }, x: { ticks: { color: '#94a3b8' }, grid: { display: false } } } }
            });

            new Chart(document.getElementById('winRateChart'), {
                type: 'bar',
                data: {
                    labels: keys,
                    datasets: [{ label: '원금 방어 확률 (%)', data: wins, backgroundColor: '#6366f1', borderRadius: 8 }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { max: 100, ticks: { color: '#94a3b8' }, grid: { color: '#ffffff08' } }, x: { ticks: { color: '#94a3b8' }, grid: { display: false } } } }
            });
        }

        function renderMatrix() {
            const body = document.getElementById('matrix-body');
            [...backtestData.yearly_performance].reverse().forEach(r => {
                const tr = document.createElement('tr');
                tr.className = 'border-b border-white/5 hover:bg-white/5 transition';
                tr.innerHTML = `
                    <td class="px-8 py-4 font-bold">${r.year}</td>
                    <td class="px-8 py-4 ${r.USD > 0 ? 'text-green-400' : 'text-red-400'}">${r.USD > 0 ? '+' : ''}${r.USD.toFixed(1)}%</td>
                    <td class="px-8 py-4 ${r.QLD > 0 ? 'text-blue-400' : 'text-red-400'}">${r.QLD > 0 ? '+' : ''}${r.QLD.toFixed(1)}%</td>
                    <td class="px-8 py-4 text-slate-500">${r.KRW > 0 ? '+' : ''}${r.KRW.toFixed(1)}%</td>
                `;
                body.appendChild(tr);
            });
        }

        function renderScenarios(period) {
            const body = document.getElementById('scenario-body');
            body.innerHTML = '';
            backtestData.details[period].forEach(item => {
                const tr = document.createElement('tr');
                tr.className = 'border-b border-white/5';
                tr.innerHTML = `
                    <td class="px-8 py-4 text-slate-500 font-mono">${item.start}</td>
                    <td class="px-8 py-4 text-slate-500 font-mono">${item.end}</td>
                    <td class="px-8 py-4 font-bold ${item.return_pct > 0 ? 'text-blue-400' : 'text-red-400'}">${item.return_pct.toFixed(1)}%</td>
                    <td class="px-8 py-4 text-slate-300 font-mono">${item.final_value.toLocaleString()} 원</td>
                `;
                body.appendChild(tr);
            });
        }

        init();
    </script>
</body>
</html>"""

# Inject data
final_html = html_content.replace('REPLACE_DATA', json.dumps(full_data))

with open('report.html', 'w') as f:
    f.write(final_html)

print("Report fixed and data inlined.")
