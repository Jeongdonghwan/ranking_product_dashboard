// 전역 변수
let currentSnapshotId = null;
let currentMetrics = null;
let trendChart = null;
let manualDataBuffer = [];

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initUpload();
    loadSnapshots();

    // 현재 월 자동 설정
    const today = new Date();
    const yearMonth = today.toISOString().slice(0, 7);
    document.getElementById('goalMonth').value = yearMonth;
});

// 탭 전환
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 모든 탭 비활성화
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(tc => tc.classList.add('hidden'));

            // 클릭한 탭 활성화
            this.classList.add('active');
            const tabName = this.dataset.tab;
            document.getElementById(`tab-${tabName}`).classList.remove('hidden');

            // 저장된 분석 탭이면 목록 새로고침
            if (tabName === 'saved') {
                loadSnapshots();
            }
        });
    });
}

// 파일 업로드 초기화
function initUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // 클릭 시 파일 선택
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // 파일 선택 시
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // 드래그 앤 드롭
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragging');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragging');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragging');

        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
}

// 파일 업로드 처리
async function uploadFile(file) {
    // 진행 표시
    document.getElementById('uploadProgress').classList.remove('hidden');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('snapshot_name', `분석 ${new Date().toLocaleDateString()}`);

    try {
        const response = await fetch('/api/ad-analysis/upload', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });

        const result = await response.json();

        if (result.success) {
            // 분석 결과 저장
            currentSnapshotId = result.snapshot_id;
            currentMetrics = result.metrics;

            // 분석 탭으로 전환
            document.querySelector('[data-tab="analysis"]').click();

            // 탭 전환 완료 후 차트 렌더링 (타이밍 이슈 방지)
            setTimeout(() => {
                displayMetrics(result.metrics);
                displayChart(result.metrics.daily_trend);
                displayCampaigns(result.metrics.campaigns);
                displayInsights(result.insights);
            }, 150);

            alert('✅ 분석 완료!');
        } else {
            alert('❌ 업로드 실패: ' + result.error);
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('❌ 업로드 중 오류가 발생했습니다. 상단의 제휴문의를 통해 문의해주세요');
    } finally {
        document.getElementById('uploadProgress').classList.add('hidden');
    }
}

// 메트릭스 표시
function displayMetrics(metrics) {
    const grid = document.getElementById('metricsGrid');

    const metricCards = [
        { label: 'ROAS', value: metrics.avg_roas.toFixed(2), class: 'green' },
        { label: 'CTR', value: metrics.avg_ctr.toFixed(2) + '%', class: 'blue' },
        { label: 'CPA', value: metrics.avg_cpa.toLocaleString() + '원', class: 'orange' },
        { label: '전환율', value: metrics.cvr.toFixed(2) + '%', class: '' },
        { label: '총 지출', value: (metrics.total_spend / 10000).toFixed(0) + '만원', class: '' },
        { label: '총 매출', value: (metrics.total_revenue / 10000).toFixed(0) + '만원', class: 'green' }
    ];

    grid.innerHTML = metricCards.map(card => `
        <div class="metric-card ${card.class}">
            <div class="metric-label">${card.label}</div>
            <div class="metric-value">${card.value}</div>
        </div>
    `).join('');
}

// 차트 표시
function displayChart(dailyData) {
    // 데이터 검증
    if (!dailyData) {
        console.error('❌ Chart Error: dailyData is null or undefined');
        alert('차트 데이터가 없습니다. 데이터를 먼저 업로드하세요.');
        return;
    }

    if (!Array.isArray(dailyData)) {
        console.error('❌ Chart Error: dailyData is not an array', dailyData);
        alert('차트 데이터 형식이 올바르지 않습니다.');
        return;
    }

    if (dailyData.length === 0) {
        console.warn('⚠️ Chart Warning: dailyData is empty');
        alert('차트에 표시할 데이터가 없습니다.');
        return;
    }

    console.log('📊 Rendering chart with', dailyData.length, 'data points:', dailyData);

    const ctx = document.getElementById('trendChart').getContext('2d');

    // 기존 차트 제거
    if (trendChart) {
        trendChart.destroy();
    }

    const dates = dailyData.map(d => d.date);
    const roasData = dailyData.map(d => d.roas);
    const ctrData = dailyData.map(d => d.ctr);
    const spendData = dailyData.map(d => d.spend / 10000); // 만원 단위

    // ROAS 데이터 범위 로깅 (디버깅용)
    const roasMin = Math.min(...roasData);
    const roasMax = Math.max(...roasData);
    console.log(`📊 Chart Data - ROAS range: ${roasMin.toFixed(2)} ~ ${roasMax.toFixed(2)}`);
    console.log(`📊 Chart Data - Spend range: ${Math.min(...spendData).toFixed(0)} ~ ${Math.max(...spendData).toFixed(0)}만원`);

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'ROAS',
                    data: roasData,
                    borderColor: 'rgb(46, 204, 113)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4
                },
                {
                    label: 'CTR (%)',
                    data: ctrData,
                    borderColor: 'rgb(52, 152, 219)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4
                },
                {
                    label: '지출 (만원)',
                    data: spendData,
                    type: 'bar',
                    backgroundColor: 'rgba(155, 89, 182, 0.3)',
                    borderColor: 'rgb(155, 89, 182)',
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                title: {
                    display: true,
                    text: '일별 성과 트렌드',
                    font: { size: 16 }
                },
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: 'ROAS',
                        color: 'rgb(46, 204, 113)',
                        font: { size: 14, weight: 'bold' }
                    },
                    min: 0,
                    suggestedMax: roasMax > 0 ? Math.ceil(roasMax * 1.2) : 5,
                    ticks: {
                        stepSize: 0.5,
                        color: 'rgb(46, 204, 113)',
                        font: { weight: 'bold' }
                    },
                    grid: {
                        color: 'rgba(46, 204, 113, 0.1)'
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'CTR (%)',
                        color: 'rgb(52, 152, 219)',
                        font: { size: 14, weight: 'bold' }
                    },
                    ticks: {
                        color: 'rgb(52, 152, 219)',
                        font: { weight: 'bold' }
                    },
                    grid: { drawOnChartArea: false }
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: '지출 (만원)',
                        color: 'rgb(155, 89, 182)',
                        font: { size: 14, weight: 'bold' }
                    },
                    ticks: {
                        color: 'rgb(155, 89, 182)',
                        font: { weight: 'bold' }
                    },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// 캠페인 테이블 표시
function displayCampaigns(campaigns) {
    const tbody = document.getElementById('campaignTableBody');

    tbody.innerHTML = campaigns.map(c => {
        let statusClass = 'status-excellent';
        let statusText = '우수';

        if (c.status === 'good') {
            statusClass = 'status-good';
            statusText = '보통';
        } else if (c.status === 'poor') {
            statusClass = 'status-poor';
            statusText = '개선필요';
        }

        return `
            <tr>
                <td>${c.rank}</td>
                <td>${c.campaign_name}</td>
                <td><strong>${c.roas.toFixed(2)}</strong></td>
                <td>${c.ctr.toFixed(2)}%</td>
                <td>${c.cpa.toLocaleString()}원</td>
                <td>${(c.spend / 10000).toFixed(0)}만원</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
            </tr>
        `;
    }).join('');
}

// AI 인사이트 표시
function displayInsights(insights) {
    document.getElementById('aiInsights').textContent = insights;
}

// 분석 저장
function saveCurrentAnalysis() {
    if (!currentSnapshotId) {
        alert('저장할 분석이 없습니다.');
        return;
    }

    document.getElementById('saveModal').style.display = 'block';
}

function closeSaveModal() {
    document.getElementById('saveModal').style.display = 'none';
}

async function confirmSave() {
    const name = document.getElementById('saveName').value;
    const tags = document.getElementById('saveTags').value;
    const memo = document.getElementById('saveMemo').value;

    if (!name) {
        alert('분석 이름을 입력하세요.');
        return;
    }

    try {
        const response = await fetch(`/api/ad-analysis/snapshots/${currentSnapshotId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                is_saved: true,
                snapshot_name: name,
                tags: tags,
                memo: memo
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ 저장 완료!');
            closeSaveModal();
            loadSnapshots();
        }
    } catch (error) {
        console.error('Save error:', error);
        alert('❌ 저장 실패');
    }
}

// 저장된 분석 목록 로드
async function loadSnapshots() {
    try {
        const response = await fetch('/api/ad-analysis/snapshots?saved_only=true', {
            credentials: 'same-origin'
        });

        const result = await response.json();
        const snapshots = result.snapshots;

        // 목록 표시
        const listContainer = document.getElementById('snapshotList');

        if (snapshots.length === 0) {
            listContainer.innerHTML = '<p style="text-align:center; color:#7f8c8d;">저장된 분석이 없습니다.</p>';
        } else {
            listContainer.innerHTML = snapshots.map(s => `
                <div class="snapshot-item">
                    <div class="snapshot-info">
                        <h4>${s.snapshot_name}</h4>
                        <p>${s.period_start} ~ ${s.period_end} | ROAS ${s.metrics_summary?.avg_roas || 'N/A'} | 지출 ${((s.metrics_summary?.total_spend || 0) / 10000).toFixed(0)}만원</p>
                        ${s.tags ? `<p style="color:#3498db;">🏷️ ${s.tags}</p>` : ''}
                    </div>
                    <div class="snapshot-actions">
                        <button class="btn btn-primary" onclick="loadSnapshot(${s.id})">열기</button>
                        <button class="btn btn-danger" onclick="deleteSnapshot(${s.id})">삭제</button>
                    </div>
                </div>
            `).join('');
        }

        // 비교 셀렉트박스 업데이트
        updateCompareSelects(snapshots);

    } catch (error) {
        console.error('Load snapshots error:', error);
    }
}

// 스냅샷 불러오기
async function loadSnapshot(snapshotId) {
    try {
        const response = await fetch(`/api/ad-analysis/snapshots/${snapshotId}`, {
            credentials: 'same-origin'
        });

        const data = await response.json();

        currentSnapshotId = snapshotId;
        currentMetrics = data.metrics;

        // 분석 탭으로 전환
        document.querySelector('[data-tab="analysis"]').click();

        // 탭 전환 완료 후 차트 렌더링 (타이밍 이슈 방지)
        setTimeout(() => {
            displayMetrics(data.metrics);
            displayChart(data.metrics.daily_trend);
            displayCampaigns(data.metrics.campaigns);
            displayInsights(data.insights);
        }, 150);

    } catch (error) {
        console.error('Load snapshot error:', error);
        alert('불러오기 실패');
    }
}

// 스냅샷 삭제
async function deleteSnapshot(snapshotId) {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    try {
        const response = await fetch(`/api/ad-analysis/snapshots/${snapshotId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ 삭제 완료');
            loadSnapshots();
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('❌ 삭제 실패');
    }
}

// 비교 셀렉트 업데이트
function updateCompareSelects(snapshots) {
    const selectA = document.getElementById('compareSnapshotA');
    const selectB = document.getElementById('compareSnapshotB');

    const options = snapshots.map(s =>
        `<option value="${s.id}">${s.snapshot_name} (${s.period_start} ~ ${s.period_end})</option>`
    ).join('');

    selectA.innerHTML = '<option value="">선택하세요</option>' + options;
    selectB.innerHTML = '<option value="">선택하세요</option>' + options;
}

// 비교 분석
async function compareAnalysis() {
    const snapshotA = document.getElementById('compareSnapshotA').value;
    const snapshotB = document.getElementById('compareSnapshotB').value;

    if (!snapshotA || !snapshotB) {
        alert('두 분석을 모두 선택하세요.');
        return;
    }

    try {
        const response = await fetch(`/api/ad-analysis/compare?snapshot_a=${snapshotA}&snapshot_b=${snapshotB}`, {
            credentials: 'same-origin'
        });

        const result = await response.json();

        // 결과 표시
        document.getElementById('comparisonResult').classList.remove('hidden');
        document.getElementById('comparisonSummary').textContent = result.summary;

        const tbody = document.getElementById('comparisonTableBody');
        const comparison = result.comparison;

        const labels = {
            'avg_roas': 'ROAS',
            'avg_ctr': 'CTR',
            'avg_cpa': 'CPA',
            'cvr': '전환율',
            'avg_cpc': 'CPC'
        };

        tbody.innerHTML = Object.entries(comparison).map(([key, data]) => {
            const trendClass = data.trend === 'up' ? 'trend-up' : (data.trend === 'down' ? 'trend-down' : '');
            const arrow = data.trend === 'up' ? '▲' : (data.trend === 'down' ? '▼' : '=');

            return `
                <tr>
                    <td>${labels[key]}</td>
                    <td>${data.a}</td>
                    <td>${data.b}</td>
                    <td class="${trendClass}">${arrow} ${Math.abs(data.change)}%</td>
                </tr>
            `;
        }).join('');

    } catch (error) {
        console.error('Compare error:', error);
        alert('❌ 비교 실패');
    }
}

// 목표 저장
async function saveGoal() {
    const yearMonth = document.getElementById('goalMonth').value;
    const budget = document.getElementById('goalBudget').value;
    const targetRoas = document.getElementById('goalRoas').value;

    if (!yearMonth || !budget || !targetRoas) {
        alert('모든 필드를 입력하세요.');
        return;
    }

    try {
        const response = await fetch('/api/ad-analysis/goals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                year_month: yearMonth,
                budget: parseFloat(budget),
                target_roas: parseFloat(targetRoas)
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ 목표 저장 완료!');
            loadBudgetPacing();
        }
    } catch (error) {
        console.error('Save goal error:', error);
        alert('❌ 저장 실패');
    }
}

// 예산 소진 현황 로드
async function loadBudgetPacing() {
    const yearMonth = document.getElementById('goalMonth').value;

    try {
        const response = await fetch(`/api/ad-analysis/budget-pacing?year_month=${yearMonth}`, {
            credentials: 'same-origin'
        });

        const data = await response.json();

        if (data.error) {
            document.getElementById('budgetPacing').innerHTML = `<p>${data.error}</p>`;
            return;
        }

        const statusColor = data.status === 'FAST' ? '#e74c3c' : (data.status === 'SLOW' ? '#f39c12' : '#2ecc71');

        document.getElementById('budgetPacing').innerHTML = `
            <div style="padding: 20px; background: #f8f9fa; border-radius: 8px;">
                <h3>월 예산: ${(data.budget / 10000).toLocaleString()}만원</h3>
                <p>사용액: ${(data.spent / 10000).toLocaleString()}만원 (${data.spent_rate}%)</p>

                <div style="background: #ecf0f1; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0;">
                    <div style="width: ${data.spent_rate}%; height: 100%; background: ${statusColor}; transition: width 0.5s;"></div>
                </div>

                <p>진행률: ${data.progress_rate}% (${data.days_passed}/${data.days_total}일)</p>
                <p style="color: ${statusColor}; font-weight: 600; font-size: 18px; margin-top: 10px;">
                    ${data.status === 'FAST' ? '⚠️ 빠름' : (data.status === 'SLOW' ? '⏰ 느림' : '✅ 정상')}
                </p>
                <p>${data.suggestion}</p>
            </div>
        `;

    } catch (error) {
        console.error('Load pacing error:', error);
    }
}

// 템플릿 다운로드
function downloadTemplate(type) {
    window.location.href = `/api/ad-analysis/template/${type}`;
}

// PDF 내보내기
function exportPDF() {
    if (!currentSnapshotId) {
        alert('내보낼 분석이 없습니다.');
        return;
    }

    window.open(`/api/ad-analysis/export/pdf/${currentSnapshotId}`, '_blank');
}

// Excel 내보내기
function exportExcel() {
    if (!currentSnapshotId) {
        alert('내보낼 분석이 없습니다.');
        return;
    }

    window.open(`/api/ad-analysis/export/excel/${currentSnapshotId}`, '_blank');
}

// 수기 입력 모달
function openManualInputModal() {
    manualDataBuffer = [];
    document.getElementById('manualInputModal').style.display = 'block';
    document.getElementById('manualDate').valueAsDate = new Date();
    updateManualDataCount();
}

function closeManualInputModal() {
    document.getElementById('manualInputModal').style.display = 'none';
}

function addManualData() {
    const data = {
        date: document.getElementById('manualDate').value,
        campaign_name: document.getElementById('manualCampaign').value,
        spend: parseFloat(document.getElementById('manualSpend').value),
        clicks: parseInt(document.getElementById('manualClicks').value),
        conversions: parseInt(document.getElementById('manualConversions').value),
        revenue: parseFloat(document.getElementById('manualRevenue').value)
    };

    // 유효성 검사
    if (!data.date || !data.campaign_name || !data.spend || !data.clicks || !data.conversions || !data.revenue) {
        alert('모든 필드를 입력하세요.');
        return;
    }

    manualDataBuffer.push(data);
    updateManualDataCount();

    // 폼 초기화 (날짜와 캠페인명 제외)
    document.getElementById('manualSpend').value = '';
    document.getElementById('manualClicks').value = '';
    document.getElementById('manualConversions').value = '';
    document.getElementById('manualRevenue').value = '';

    alert('✅ 데이터 추가됨');
}

function updateManualDataCount() {
    document.getElementById('manualDataCount').textContent = manualDataBuffer.length;
}

async function submitManualData() {
    if (manualDataBuffer.length === 0) {
        alert('입력된 데이터가 없습니다.');
        return;
    }

    try {
        const response = await fetch('/api/ad-analysis/manual-input', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                snapshot_name: `수기입력 ${new Date().toLocaleDateString()}`,
                data: manualDataBuffer
            })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ 데이터 저장 완료!');
            closeManualInputModal();

            // 자동으로 분석 로드
            loadSnapshot(result.snapshot_id);
        }
    } catch (error) {
        console.error('Submit error:', error);
        alert('❌ 저장 실패');
    }
}
