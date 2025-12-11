// 배너 관리 JavaScript

let currentBannerType = 'home_top';
let currentBanners = [];

const BANNER_INFO = {
    home_top: {
        title: '홈 상단 대형 배너',
        size: '970×90px',
        maxCount: null
    },
    home_grid: {
        title: '홈 그리드 배너',
        size: '838×100px',
        maxCount: 4,
        layout: '2×2 그리드'
    },
    home_bottom: {
        title: '홈 하단 대형 배너',
        size: '728×90px',
        maxCount: null
    },
    grid_general: {
        title: '일반 대시보드 롤링 배너',
        size: '1644×150px',
        maxCount: 6,
        layout: '자동 롤링'
    },
    grid_coupang: {
        title: '쿠팡 대시보드 롤링 배너',
        size: '1644×250px',
        maxCount: 6,
        layout: '자동 롤링'
    },
    grid_profit: {
        title: '순마진계산기 롤링 배너',
        size: '1644×150px',
        maxCount: 6,
        layout: '자동 롤링'
    },
    grid_efficiency: {
        title: '손익분기ROAS 롤링 배너',
        size: '1644×150px',
        maxCount: 6,
        layout: '자동 롤링'
    },
    grid_keyword: {
        title: '키워드조합기 롤링 배너',
        size: '1644×150px',
        maxCount: 6,
        layout: '자동 롤링'
    }
};

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadBanners(currentBannerType);
    loadStats(currentBannerType);
    initForms();
});

function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            currentBannerType = tab.dataset.type;
            updateTitle();
            loadBanners(currentBannerType);
            loadStats(currentBannerType);
        });
    });
}

function updateTitle() {
    const info = BANNER_INFO[currentBannerType];
    let titleText = `${info.title} (${info.size})`;

    if (info.maxCount) {
        const currentCount = currentBanners.length;
        titleText += ` - ${currentCount}/${info.maxCount}개`;
    }

    document.getElementById('sectionTitle').textContent = titleText;

    // 사이즈 가이드 업데이트
    let guideText = `권장 크기: ${info.size}`;
    if (info.layout) {
        guideText += ` | ${info.layout}`;
    }
    if (info.maxCount) {
        guideText += ` | 최대 ${info.maxCount}개`;
    }
    document.getElementById('sizeGuide').textContent = guideText;
}

async function loadBanners(bannerType) {
    const listEl = document.getElementById('bannerList');
    listEl.innerHTML = '<div class="loading">로딩중...</div>';

    try {
        const response = await fetch(`/admin/api/banners/${bannerType}`, {
            credentials: 'same-origin'
        });
        const data = await response.json();

        if (data.success) {
            currentBanners = data.banners;
            displayBanners(data.banners);
            initSortable();
        }
    } catch (error) {
        listEl.innerHTML = '<div class="loading">배너를 불러올 수 없습니다.</div>';
    }
}

function displayBanners(banners) {
    const listEl = document.getElementById('bannerList');

    if (banners.length === 0) {
        listEl.innerHTML = '<div class="loading">등록된 배너가 없습니다.</div>';
        return;
    }

    listEl.innerHTML = banners.map(banner => `
        <div class="banner-item" data-id="${banner.id}">
            <div class="banner-previews">
                <img src="${banner.image_url}" alt="${banner.title}" class="banner-preview" title="데스크톱">
                ${banner.mobile_image_url
                    ? `<img src="${banner.mobile_image_url}" alt="${banner.title} (모바일)" class="banner-preview banner-preview-mobile" title="모바일">`
                    : '<span class="no-mobile">모바일 이미지 없음</span>'
                }
            </div>
            <div class="banner-info">
                <h4>
                    ${banner.title}
                    <span class="badge ${banner.is_active ? 'badge-active' : 'badge-inactive'}">
                        ${banner.is_active ? '활성' : '비활성'}
                    </span>
                </h4>
                <p>링크: ${banner.link_url || '-'}</p>
                <p>기간: ${banner.start_date || '-'} ~ ${banner.end_date || '-'}</p>
                <div class="banner-stats">
                    <span>노출: ${banner.impression_count || 0}회</span>
                    <span>클릭: ${banner.click_count || 0}회</span>
                    <span>CTR: ${calculateCTR(banner.click_count, banner.impression_count)}%</span>
                </div>
            </div>
            <div class="banner-actions">
                <button class="btn-primary" onclick="openEditModal(${banner.id})">수정</button>
                <button class="btn-danger" onclick="deleteBanner(${banner.id})">삭제</button>
            </div>
        </div>
    `).join('');
}

function calculateCTR(clicks, impressions) {
    if (!impressions || impressions === 0) return '0.0';
    return ((clicks / impressions) * 100).toFixed(2);
}

function initSortable() {
    const listEl = document.getElementById('bannerList');
    new Sortable(listEl, {
        animation: 150,
        handle: '.banner-item',
        onEnd: function() {
            updateBannerOrder();
        }
    });
}

async function updateBannerOrder() {
    const items = document.querySelectorAll('.banner-item');
    const orderList = Array.from(items).map(item => parseInt(item.dataset.id));

    try {
        await fetch('/admin/api/banners/reorder', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin',
            body: JSON.stringify({
                banner_type: currentBannerType,
                order_list: orderList
            })
        });
    } catch (error) {
        alert('순서 변경 실패');
    }
}

async function loadStats(bannerType) {
    try {
        const response = await fetch(`/admin/api/banners/stats?banner_type=${bannerType}`, {
            credentials: 'same-origin'
        });
        const data = await response.json();

        if (data.success) {
            displayStats(data.stats);
        }
    } catch (error) {
        console.error('Stats error:', error);
    }
}

function displayStats(stats) {
    const statsEl = document.getElementById('statsGrid');
    statsEl.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">총 배너</div>
            <div class="stat-value">${stats.total_banners || 0}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">총 노출</div>
            <div class="stat-value">${(stats.total_impressions || 0).toLocaleString()}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">총 클릭</div>
            <div class="stat-value">${(stats.total_clicks || 0).toLocaleString()}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">평균 CTR</div>
            <div class="stat-value">${stats.avg_ctr || 0}%</div>
        </div>
    `;
}

function initForms() {
    document.getElementById('uploadForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(e.target);
        formData.append('banner_type', currentBannerType);

        try {
            const response = await fetch('/admin/api/banners', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            });

            const result = await response.json();

            if (result.success) {
                alert('배너가 업로드되었습니다.');
                closeUploadModal();
                loadBanners(currentBannerType);
                loadStats(currentBannerType);
                e.target.reset();
            } else {
                alert('업로드 실패: ' + result.message);
            }
        } catch (error) {
            alert('서버 오류');
        }
    });

    document.getElementById('editForm').addEventListener('submit', async (e) => {
        e.preventDefault();

        const bannerId = document.getElementById('editBannerId').value;
        const formData = new FormData();

        const imageFile = document.getElementById('editImageFile').files[0];
        if (imageFile) {
            formData.append('image', imageFile);
        }

        // 모바일 이미지 추가
        const mobileImageFile = document.getElementById('editMobileImageFile').files[0];
        if (mobileImageFile) {
            formData.append('mobile_image', mobileImageFile);
        }

        formData.append('title', document.getElementById('editTitle').value);
        formData.append('link_url', document.getElementById('editLinkUrl').value);
        formData.append('position_order', document.getElementById('editPositionOrder').value);
        formData.append('is_active', document.getElementById('editIsActive').value);
        formData.append('start_date', document.getElementById('editStartDate').value);
        formData.append('end_date', document.getElementById('editEndDate').value);

        try {
            const response = await fetch(`/admin/api/banners/${bannerId}`, {
                method: 'PUT',
                body: formData,
                credentials: 'same-origin'
            });

            const result = await response.json();

            if (result.success) {
                alert('배너가 수정되었습니다.');
                closeEditModal();
                loadBanners(currentBannerType);
            } else {
                alert('수정 실패: ' + result.message);
            }
        } catch (error) {
            alert('서버 오류');
        }
    });
}

function openUploadModal() {
    const info = BANNER_INFO[currentBannerType];

    // 최대 개수 체크
    if (info.maxCount && currentBanners.length >= info.maxCount) {
        alert(`⚠️ ${info.title}는 최대 ${info.maxCount}개까지 등록 가능합니다.\n먼저 기존 배너를 삭제해주세요.`);
        return;
    }

    document.getElementById('uploadModal').style.display = 'block';
}

function closeUploadModal() {
    document.getElementById('uploadModal').style.display = 'none';
}

function openEditModal(bannerId) {
    const banner = currentBanners.find(b => b.id === bannerId);
    if (!banner) return;

    document.getElementById('editBannerId').value = banner.id;
    document.getElementById('editTitle').value = banner.title;
    document.getElementById('editLinkUrl').value = banner.link_url || '';
    document.getElementById('editPositionOrder').value = banner.position_order;
    document.getElementById('editIsActive').value = banner.is_active ? 'true' : 'false';
    document.getElementById('editStartDate').value = banner.start_date || '';
    document.getElementById('editEndDate').value = banner.end_date || '';

    document.getElementById('editModal').style.display = 'block';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

async function deleteBanner(bannerId) {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    try {
        const response = await fetch(`/admin/api/banners/${bannerId}`, {
            method: 'DELETE',
            credentials: 'same-origin'
        });

        const result = await response.json();

        if (result.success) {
            alert('배너가 삭제되었습니다.');
            loadBanners(currentBannerType);
            loadStats(currentBannerType);
        } else {
            alert('삭제 실패: ' + result.message);
        }
    } catch (error) {
        alert('서버 오류');
    }
}

window.onclick = function(event) {
    const uploadModal = document.getElementById('uploadModal');
    const editModal = document.getElementById('editModal');

    if (event.target === uploadModal) {
        closeUploadModal();
    }
    if (event.target === editModal) {
        closeEditModal();
    }
}
