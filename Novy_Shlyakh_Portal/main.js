document.addEventListener('DOMContentLoaded', () => {
    const specTabs = document.querySelectorAll('.tab-btn');
    const specialistGrid = document.getElementById('specialistGrid');
    const btnJoin = document.getElementById('btn-join-specialist');

    // База даних спеціалістів (тепер завантажується асинхронно з JSON)
    let specialists = [];

    async function loadSpecialists() {
        try {
            const response = await fetch('backend/data/specialists.json');
            if (!response.ok) throw new Error('Помилка завантаження');
            specialists = await response.json();
            
            // Рендеримо тільки верифікованих для публічного списку
            renderSpecialists();
            initNetworkMap();
        } catch (error) {
            console.warn("Локальний запуск (без сервера), використовуємо fallback дані", error);
            specialists = [
                { id: "f1", category: "legal", name: "Олександр Іваненко (Fallback)", role: "Юрист (Земельні питання)", phone: "+380671112233", address: "м. Черкаси, вул. Смілянська, 10", status: "verified", coordinates: [49.4444, 32.0597], rating: "4.9", bio: "Експерт з виплат." },
                { id: "f2", category: "psychology", name: "Марія Ковальчук (Fallback)", role: "Психолог (ПТСР)", phone: "+380634445566", address: "м. Черкаси, б-р Шевченка, 205", status: "verified", coordinates: [49.4411, 32.0622], rating: "5.0", bio: "Кризова допомога." }
            ];
            renderSpecialists();
            initNetworkMap();
        }
    }

    // --- ЛОГІКА МЕРЕЖЕВОЇ МАПИ ---
    function initNetworkMap() {
        const mapContainer = document.getElementById('networkMap');
        if (!mapContainer) return;

        const map = L.map('networkMap').setView([49.4444, 32.0597], 13);
        
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        specialists.filter(s => s.status === 'verified').forEach(spec => {
            const marker = L.marker(spec.coordinates).addTo(map);
            marker.bindPopup(`
                <div style="color: #333; font-family: 'Inter', sans-serif;">
                    <b style="color: var(--primary-green);">${spec.name}</b><br>
                    <small>${spec.role || spec.category}</small><br>
                    <p style="margin: 5px 0; font-size: 12px;">📍 ${spec.address}</p>
                    <a href="tel:${spec.phone}" class="btn-primary" style="display:block; text-align:center; padding: 5px; font-size: 11px; margin-top: 5px;">Зателефонувати</a>
                </div>
            `);
        });
    }

    // --- ТЕЛЕГРАМ MINI APP ДЕТЕКЦІЯ ---
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.expand();
        tg.ready();
        
        const desktopPlatforms = ['tdesktop', 'macos', 'weba', 'webk', 'web'];
        if (desktopPlatforms.includes(tg.platform)) {
            document.body.classList.add('is-desktop-tg');
        } else {
            document.body.classList.add('is-tg-app');
        }
        
        // Змінюємо колір хедера під тему Telegram
        tg.setHeaderColor('#1A1C1A');
    }

    const isUserLoggedIn = localStorage.getItem('current_veteran');

    function renderSpecialists(filter = 'all') {
        if (!specialistGrid) return;
        specialistGrid.innerHTML = '';
        
        let filtered = filter === 'all' 
            ? specialists 
            : specialists.filter(s => s.category === filter);

        // --- НОВА ЛОГІКА ТОР-СПЕЦІАЛІСТІВ ---
        if (!isUserLoggedIn) {
            // Сортуємо за рейтингом (Top)
            filtered.sort((a, b) => parseFloat(b.rating) - parseFloat(a.rating));
            // Показуємо лише топ-3 для неавторизованих
            filtered = filtered.slice(0, 3);
            
            // Додаємо інфо-плашку
            if (specialists.length > 3) {
                const info = document.createElement('div');
                info.style.gridColumn = "1 / -1";
                info.style.textAlign = "center";
                info.style.padding = "20px";
                info.style.color = "var(--primary-green)";
                info.innerHTML = `💡 Це список ТОП-фахівців. Відкрийте <a href="https://t.me/Veteran_Novy_Shlyakh_Bot" style="color:white; text-decoration:underline;">Telegram-бота</a>, щоб побачити повний перелік (${specialists.length}+)`;
                specialistGrid.appendChild(info);
            }
        }

        filtered.forEach(spec => {
            const card = document.createElement('div');
            card.className = 'spec-card';
            card.innerHTML = `
                <div class="spec-img" style="background-color: var(--deep-teal)">
                    <div class="spec-rating">⭐ ${spec.rating || '5.0'}</div>
                </div>
                <div class="spec-info">
                    <span class="spec-tag">${spec.role || spec.category}</span>
                    <h4>${spec.name}</h4>
                    <p class="spec-power">${spec.bio || spec.power || ''}</p>
                    <div class="spec-stats" style="flex-direction: column; gap: 5px;">
                        <span>📍 ${spec.address || 'Черкаси'}</span>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <a href="tel:${spec.phone}" class="btn-card" style="text-align:center; display: flex; align-items: center; justify-content: center; text-decoration: none;">
                            📞 Зателефонувати
                        </a>
                        <button class="btn-card" onclick="handleBooking('${spec.name}')" style="flex: 1;">
                            Записатися через Бот
                        </button>
                    </div>
                </div>
            `;
            specialistGrid.appendChild(card);
        });
    }

    // Глобальна функція обробки запису
    window.handleBooking = (specName) => {
        window.location.href = 'https://t.me/Veteran_Novy_Shlyakh_Bot';
    };

    // Обробка кліків по табам
    specTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            specTabs.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderSpecialists(btn.dataset.category);
        });
    });

    // Обробка кнопки приєднання
    if (btnJoin) {
        btnJoin.addEventListener('click', () => {
            alert('Дякуємо за ваш інтерес! Форма реєстрації для спеціалістів буде відкрита найближчим часом. Будь ласка, залиште заявку в нашому Telegram-боті.');
            window.location.href = "https://t.me/Veteran_Novy_Shlyakh_Bot";
        });
    }

    // Плавний скрол
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // --- Education Hub Logic ---
    const eduTabs = document.querySelectorAll('#eduTabs .tab-btn');
    const trainingGrid = document.getElementById('trainingGrid');
    let education = [];

    async function loadEducation() {
        try {
            const response = await fetch('backend/data/education.json');
            if (!response.ok) throw new Error('Error loading education');
            education = await response.json();
            renderEducation();
        } catch (error) {
            console.warn("Education fallback used");
            education = [
                { id: 1, category: "vouchers", institution: "Держслужба зайнятості", title: "Ваучер на навчання", desc: "Безоплатне навчання за 70+ професіями.", price: "Безкоштовно", link: "#", deadline: "Постійно" }
            ];
            renderEducation();
        }
    }

    function renderEducation(filter = 'all') {
        if (!trainingGrid) return;
        trainingGrid.innerHTML = '';
        const filtered = filter === 'all' ? education : education.filter(e => e.category === filter);

        filtered.forEach(item => {
            const card = document.createElement('div');
            card.className = 'edu-card';
            card.innerHTML = `
                <div class="edu-content">
                    <span class="edu-badge">${item.category}</span>
                    <p class="edu-inst">${item.institution}</p>
                    <h4>${item.title}</h4>
                    <p class="edu-desc">${item.desc}</p>
                </div>
                <div class="edu-footer">
                    <span class="edu-price">${item.price}</span>
                    <a href="${item.link}" target="_blank" class="btn-primary" style="font-size: 12px; padding: 8px 15px;">Детальніше</a>
                </div>
            `;
            trainingGrid.appendChild(card);
        });
    }

    eduTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            eduTabs.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderEducation(btn.dataset.edu);
        });
    });

    // Перший рендер (завантаження даних)
    loadSpecialists();
    loadEducation();
});

// Глобальні функції (поза DOMContentLoaded для виклику з HTML)
function openCharityModal() {
    // В реальному проекті тут буде виклик модалки з IBAN/WayForPay
    alert('Дякуємо! Система благодійних внесків проєкту Ашрам зараз інтегрується. \nВи можете зв’язатися з нами в Telegram для прямої підтримки: @Talan_UA_Admin');
}



// --- AI Search Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('aiSearchInput');
    const searchBtn = document.getElementById('aiSearchBtn');
    const responseArea = document.getElementById('aiSearchResponse');

    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') performSearch();
        });
    }

    function performSearch() {
        const text = searchInput.value.trim();
        if (!text) return;

        responseArea.style.display = 'block';
        responseArea.innerHTML = `<div style="color: var(--primary-green); text-align: center;">Аналізую базу знань...</div>`;

        // Simulate AI response
        setTimeout(() => {
            responseArea.innerHTML = `
                <div style="border-left: 3px solid var(--primary-green); padding-left: 15px; margin-bottom: 15px;">
                    <p style="color: #ccc; font-style: italic; margin-bottom: 10px;">Ваш запит: "${text}"</p>
                    <p style="color: white; line-height: 1.6;">Наразі мій серверний RAG-модуль знаходиться в стадії розгортання, тому я не маю доступу до законодавчої бази. <br><br> Будь ласка, скористайтеся <a href="https://t.me/Veteran_Novy_Shlyakh_Bot" style="color: var(--primary-green); font-weight: bold; text-decoration: none;">нашим Telegram-ботом</a> для отримання допомоги просто зараз.</p>
                </div>
            `;
        }, 1500);
    }
});
