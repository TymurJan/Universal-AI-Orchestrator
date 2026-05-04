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
            renderSpecialists();
        } catch (error) {
            console.warn("Локальний запуск (без сервера), використовуємо fallback дані", error);
            specialists = [
                { id: 1, category: "legal", name: "Олександр Ковальчук (Fallback)", tag: "Провідний юрист", power: "Вирішення складних земельних питань та виплат.", rating: "4.9", cases: "42", reviews: "15" },
                { id: 2, category: "legal", name: "Марина Петренко (Fallback)", tag: "Адвокат з прав ветеранів", power: "Оскарження рішень ВЛК та супровід у судах.", rating: "4.7", cases: "28", reviews: "9" },
                { id: 3, category: "psychology", name: "Іван Дроздов (Fallback)", tag: "Кризовий психолог", power: "Робота з гострими станами ПТСР та бойовою травмою.", rating: "5.0", cases: "115", reviews: "45" }
            ];
            renderSpecialists();
        }
    }

    function renderSpecialists(filter = 'all') {
        specialistGrid.innerHTML = '';
        
        const filtered = filter === 'all' 
            ? specialists 
            : specialists.filter(s => s.category === filter);

        filtered.forEach(spec => {
            const card = document.createElement('div');
            card.className = 'spec-card';
            card.innerHTML = `
                <div class="spec-img" style="background-color: var(--deep-teal)">
                    <div class="spec-rating">⭐ ${spec.rating}</div>
                </div>
                <div class="spec-info">
                    <span class="spec-tag">${spec.tag}</span>
                    <h4>${spec.name}</h4>
                    <p class="spec-power">${spec.power}</p>
                    <div class="spec-stats">
                        <span>📂 ${spec.cases} кейсів</span>
                        <span>💬 ${spec.reviews} відгуків</span>
                    </div>
                    <button class="btn-card">Записатися</button>
                </div>
            `;
            specialistGrid.appendChild(card);
        });
    }

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
            window.location.href = "https://t.me/your_bot";
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

    // Перший рендер (завантаження даних)
    loadSpecialists();
});

// Глобальні функції (поза DOMContentLoaded для виклику з HTML)
function openCharityModal() {
    // В реальному проекті тут буде виклик модалки з IBAN/WayForPay
    alert('Дякуємо! Система благодійних внесків проєкту Ашрам зараз інтегрується. \nВи можете зв’язатися з нами в Telegram для прямої підтримки: @Talan_UA_Admin');
}

function openSpecialistCabinet() {
    window.location.href = 'cabinet.html';
}

// Обробка кнопки "Кабінет спеціаліста" в навігації
document.addEventListener('click', (e) => {
    if (e.target.closest('.btn-cabinet')) {
        e.preventDefault();
        openSpecialistCabinet();
    }
});

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
                    <p style="color: white; line-height: 1.6;">Наразі мій серверний RAG-модуль знаходиться в стадії розгортання, тому я не маю доступу до законодавчої бази. <br><br> Будь ласка, скористайтеся <a href="https://t.me/Novy_Shlyakh_Bot" style="color: var(--primary-green); font-weight: bold; text-decoration: none;">нашим Telegram-ботом</a> для отримання допомоги просто зараз.</p>
                </div>
            `;
        }, 1500);
    }
});
