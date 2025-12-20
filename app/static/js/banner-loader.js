// 배너 동적 로딩 JavaScript

// 롤링 배너 설정
const ROLLING_CONFIG = {
    interval: 5000,           // 5초마다 전환
    transitionDuration: 500,  // 0.5초 페이드
    maxBanners: 6,            // 최대 6개
    pauseOnHover: true,       // 호버 시 정지
    showIndicators: true      // 인디케이터 표시
};

// 롤링 배너 상태 관리
const rollingBannerStates = {};

// 모바일 체크 (768px 이하)
function isMobile() {
    return window.innerWidth <= 768;
}

async function loadBanners(bannerType, containerId) {
    try {
        const response = await fetch(`/api/banners/${bannerType}`, {
            credentials: 'same-origin'
        });
        const data = await response.json();

        if (data.success && data.banners.length > 0) {
            displayBanners(data.banners, containerId, bannerType);
            trackImpressions(data.banners);
        } else {
            // 배너가 없으면 컨테이너 숨기기
            const container = document.getElementById(containerId);
            if (container) {
                container.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Banner load error:', error);
    }
}

function displayBanners(banners, containerId, bannerType) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // 배너 타입별 렌더링
    if (bannerType === 'home_grid') {
        // 홈페이지 2x2 그리드 (4개만 사용)
        displayGridBanners(banners.slice(0, 4), container);
    } else if (bannerType === 'grid_general' || bannerType === 'grid_coupang' ||
               bannerType === 'grid_profit' || bannerType === 'grid_efficiency' ||
               bannerType === 'grid_keyword') {
        // 일반/쿠팡/순마진/손익분기/키워드 대시보드 대형 롤링 배너 (최대 6개)
        displayRollingBanner(banners.slice(0, ROLLING_CONFIG.maxBanners), container, containerId);
    } else if (bannerType === 'home_top' || bannerType === 'home_bottom') {
        // 홈페이지 대형 배너 (1개)
        displayLargeBanner(banners[0], container);
    }
}

/**
 * 그리드 배너 표시 (홈페이지 2x2)
 * 모바일에서 mobile_image_url이 없는 배너는 숨김
 */
function displayGridBanners(banners, container) {
    // 모바일에서는 mobile_image_url이 있는 배너만 표시
    const filteredBanners = isMobile()
        ? banners.filter(banner => banner.mobile_image_url)
        : banners;

    if (filteredBanners.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.innerHTML = filteredBanners
        .map(banner => createGridBanner(banner))
        .join('');
    container.style.removeProperty('display');
}

/**
 * 대형 배너 표시 (홈페이지 상단/하단)
 * 모바일에서 mobile_image_url이 없으면 숨김
 */
function displayLargeBanner(banner, container) {
    if (!banner) return;

    // 모바일인데 모바일 이미지가 없으면 배너 숨김
    if (isMobile() && !banner.mobile_image_url) {
        container.style.display = 'none';
        return;
    }

    // 모바일이면 모바일 이미지, 아니면 데스크톱 이미지 사용
    const imageUrl = isMobile() && banner.mobile_image_url
        ? banner.mobile_image_url
        : banner.image_url;

    container.innerHTML = `
        <a href="${banner.link_url || '#'}"
           target="_blank"
           rel="noopener noreferrer"
           onclick="trackClick(${banner.id})"
           class="banner-link">
            <img src="${imageUrl}"
                 alt="${banner.title}"
                 class="banner-image"
                 loading="lazy">
        </a>
    `;
    container.style.display = 'block';
}

/**
 * 그리드 배너 HTML 생성
 * 모바일이면 mobile_image_url 사용 (이미 필터링됨)
 */
function createGridBanner(banner) {
    // 모바일이면 모바일 이미지 사용
    const imageUrl = isMobile() && banner.mobile_image_url
        ? banner.mobile_image_url
        : banner.image_url;

    return `
        <a href="${banner.link_url || '#'}"
           target="_blank"
           rel="noopener noreferrer"
           onclick="trackClick(${banner.id})"
           class="grid-banner-item">
            <img src="${imageUrl}"
                 alt="${banner.title}"
                 loading="lazy">
        </a>
    `;
}

function trackImpressions(banners) {
    banners.forEach(banner => {
        fetch(`/api/banners/${banner.id}/impression`, {
            method: 'POST',
            credentials: 'same-origin'
        }).catch(() => {});
    });
}

function trackClick(bannerId) {
    fetch(`/api/banners/${bannerId}/click`, {
        method: 'POST',
        credentials: 'same-origin'
    }).catch(() => {});
}

/**
 * 롤링 배너 표시 (일반/쿠팡 대시보드)
 * 모바일에서 mobile_image_url이 없는 배너는 숨김
 */
function displayRollingBanner(banners, container, containerId) {
    if (!banners || banners.length === 0) {
        container.style.display = 'none';
        return;
    }

    // 모바일에서는 mobile_image_url이 있는 배너만 표시
    const filteredBanners = isMobile()
        ? banners.filter(banner => banner.mobile_image_url)
        : banners;

    if (filteredBanners.length === 0) {
        container.style.display = 'none';
        return;
    }

    // 1개만 있으면 롤링 없이 표시
    if (filteredBanners.length === 1) {
        const banner = filteredBanners[0];
        const imageUrl = isMobile() && banner.mobile_image_url
            ? banner.mobile_image_url
            : banner.image_url;

        container.innerHTML = `
            <div class="rolling-banner-container">
                <div class="rolling-banner-wrapper">
                    <div class="rolling-banner-item active">
                        <a href="${banner.link_url || '#'}"
                           target="_blank"
                           rel="noopener noreferrer"
                           onclick="trackClick(${banner.id})">
                            <img src="${imageUrl}"
                                 alt="${banner.title}"
                                 loading="lazy">
                        </a>
                    </div>
                </div>
            </div>
        `;
        container.style.removeProperty('display');
        return;
    }

    // 롤링 배너 HTML 생성 (모바일이면 모바일 이미지 사용)
    const bannersHTML = filteredBanners
        .map((banner, index) => {
            const imageUrl = isMobile() && banner.mobile_image_url
                ? banner.mobile_image_url
                : banner.image_url;

            return `
                <div class="rolling-banner-item ${index === 0 ? 'active' : ''}" data-index="${index}">
                    <a href="${banner.link_url || '#'}"
                       target="_blank"
                       rel="noopener noreferrer"
                       onclick="trackClick(${banner.id})">
                        <img src="${imageUrl}"
                             alt="${banner.title}"
                             loading="${index === 0 ? 'eager' : 'lazy'}">
                    </a>
                </div>
            `;
        })
        .join('');

    // 인디케이터 HTML 생성
    const indicatorsHTML = ROLLING_CONFIG.showIndicators
        ? `
            <div class="rolling-indicators">
                ${filteredBanners
                    .map((_, index) => `
                        <div class="rolling-indicator ${index === 0 ? 'active' : ''}"
                             data-index="${index}"
                             onclick="jumpToSlide('${containerId}', ${index})"></div>
                    `)
                    .join('')}
            </div>
          `
        : '';

    container.innerHTML = `
        <div class="rolling-banner-container" id="${containerId}-container">
            <div class="rolling-banner-wrapper">
                ${bannersHTML}
            </div>
            ${indicatorsHTML}
        </div>
    `;
    container.style.removeProperty('display');

    // 롤링 시작
    initRollingBanner(containerId, filteredBanners.length);
}

/**
 * 롤링 배너 초기화 및 시작
 */
function initRollingBanner(containerId, totalBanners) {
    const bannerContainer = document.getElementById(`${containerId}-container`);
    if (!bannerContainer) return;

    // 상태 초기화
    rollingBannerStates[containerId] = {
        currentIndex: 0,
        totalBanners: totalBanners,
        isPaused: false,
        intervalId: null
    };

    // 자동 롤링 시작
    startRolling(containerId);

    // 호버 시 정지
    if (ROLLING_CONFIG.pauseOnHover) {
        bannerContainer.addEventListener('mouseenter', () => {
            pauseRolling(containerId);
        });

        bannerContainer.addEventListener('mouseleave', () => {
            resumeRolling(containerId);
        });
    }
}

/**
 * 롤링 시작
 */
function startRolling(containerId) {
    const state = rollingBannerStates[containerId];
    if (!state) return;

    // 기존 인터벌 제거
    if (state.intervalId) {
        clearInterval(state.intervalId);
    }

    // 새 인터벌 설정
    state.intervalId = setInterval(() => {
        if (!state.isPaused) {
            nextSlide(containerId);
        }
    }, ROLLING_CONFIG.interval);
}

/**
 * 다음 슬라이드로 이동
 */
function nextSlide(containerId) {
    const state = rollingBannerStates[containerId];
    if (!state) return;

    const nextIndex = (state.currentIndex + 1) % state.totalBanners;
    goToSlide(containerId, nextIndex);
}

/**
 * 특정 슬라이드로 이동
 */
function goToSlide(containerId, index) {
    const state = rollingBannerStates[containerId];
    if (!state || index === state.currentIndex) return;

    const container = document.getElementById(`${containerId}-container`);
    if (!container) return;

    const items = container.querySelectorAll('.rolling-banner-item');
    const indicators = container.querySelectorAll('.rolling-indicator');

    // 현재 활성 슬라이드 비활성화
    items[state.currentIndex].classList.remove('active');
    if (indicators.length > 0) {
        indicators[state.currentIndex].classList.remove('active');
    }

    // 새 슬라이드 활성화
    items[index].classList.add('active');
    if (indicators.length > 0) {
        indicators[index].classList.add('active');
    }

    // 상태 업데이트
    state.currentIndex = index;
}

/**
 * 슬라이드 점프 (인디케이터 클릭)
 */
function jumpToSlide(containerId, index) {
    goToSlide(containerId, index);

    // 롤링 리셋 (클릭 후 다시 카운트)
    const state = rollingBannerStates[containerId];
    if (state && !state.isPaused) {
        startRolling(containerId);
    }
}

/**
 * 롤링 일시 정지
 */
function pauseRolling(containerId) {
    const state = rollingBannerStates[containerId];
    if (!state) return;

    state.isPaused = true;
}

/**
 * 롤링 재개
 */
function resumeRolling(containerId) {
    const state = rollingBannerStates[containerId];
    if (!state) return;

    state.isPaused = false;
}

// 페이지 로드 시 자동 실행 - home_dashboard.html용
if (document.getElementById('homeTopBanner')) {
    loadBanners('home_top', 'homeTopBanner');
}
if (document.getElementById('homeGridBanners')) {
    loadBanners('home_grid', 'homeGridBanners');
}
if (document.getElementById('homeBottomBanner')) {
    loadBanners('home_bottom', 'homeBottomBanner');
}

// ad_dashboard_v2.html용
if (document.getElementById('generalGridBanners')) {
    loadBanners('grid_general', 'generalGridBanners');
}

// ad_dashboard_coupang.html용
if (document.getElementById('coupangGridBanners')) {
    loadBanners('grid_coupang', 'coupangGridBanners');
}

// profit_simulator.html (순마진계산기)용
if (document.getElementById('profitBanners')) {
    loadBanners('grid_profit', 'profitBanners');
}

// ad_efficiency.html (손익분기ROAS)용
if (document.getElementById('efficiencyBanners')) {
    loadBanners('grid_efficiency', 'efficiencyBanners');
}

// keyword_combiner.html (키워드조합기)용
if (document.getElementById('keywordBanners')) {
    loadBanners('grid_keyword', 'keywordBanners');
}

// 화면 리사이즈 시 배너 다시 로드 (debounce 적용)
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // 홈 대시보드 배너 다시 로드
        if (document.getElementById('homeTopBanner')) {
            loadBanners('home_top', 'homeTopBanner');
        }
        if (document.getElementById('homeGridBanners')) {
            loadBanners('home_grid', 'homeGridBanners');
        }
        if (document.getElementById('homeBottomBanner')) {
            loadBanners('home_bottom', 'homeBottomBanner');
        }
    }, 250);
});

// 페이지 언로드 시 인터벌 정리
window.addEventListener('beforeunload', () => {
    Object.values(rollingBannerStates).forEach(state => {
        if (state.intervalId) {
            clearInterval(state.intervalId);
        }
    });
});
