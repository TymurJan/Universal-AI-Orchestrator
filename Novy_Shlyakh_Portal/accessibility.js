/* accessibility.js */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Створюємо HTML структуру панелі
    const panelHTML = `
        <button class="accessibility-toggle" id="accessOpen" title="Налаштування доступності">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            <span class="access-text-btn">Доступність</span>
        </button>

        <div class="accessibility-panel" id="accessPanel">
            <button class="close-access" id="accessClose">&times;</button>
            <h3>Налаштування доступності</h3>

            <div class="access-group">
                <label>Розмір шрифту</label>
                <div class="access-btns">
                    <button class="a-btn" data-type="font" data-val="font-small">A-</button>
                    <button class="a-btn active" data-type="font" data-val="font-normal">A</button>
                    <button class="a-btn" data-type="font" data-val="font-large">A+</button>
                    <button class="a-btn" data-type="font" data-val="font-xlarge">A++</button>
                </div>
            </div>

            <div class="access-group">
                <label>Колірна схема</label>
                <div class="access-btns">
                    <button class="a-btn active" data-type="theme" data-val="theme-normal">Звичайна</button>
                    <button class="a-btn" data-type="theme" data-val="theme-contrast">Контрастна</button>
                    <button class="a-btn" data-type="theme" data-val="theme-monochrome">Чорно-біла</button>
                </div>
            </div>

            <div class="access-group">
                <label>Шрифт</label>
                <div class="access-btns">
                    <button class="a-btn active" data-type="family" data-val="font-sans">Без засічок</button>
                    <button class="a-btn" data-type="family" data-val="font-serif">З засічками</button>
                </div>
            </div>

            <div class="access-group">
                <label>Інтервал</label>
                <div class="access-btns">
                    <button class="a-btn active" data-type="spacing" data-val="spacing-normal">Звичайний</button>
                    <button class="a-btn" data-type="spacing" data-val="spacing-large">Великий</button>
                </div>
            </div>

            <div class="access-group">
                <label>Зображення</label>
                <div class="access-btns">
                    <button class="a-btn active" data-type="img" data-val="show-images">Показувати</button>
                    <button class="a-btn" data-type="img" data-val="hide-images">Приховати</button>
                </div>
            </div>

            <button class="btn-primary" id="resetAccess" style="width: 100%; margin-top: 20px;">Скинути налаштування</button>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', panelHTML);

    const toggle = document.getElementById('accessOpen');
    const panel = document.getElementById('accessPanel');
    const close = document.getElementById('accessClose');
    const reset = document.getElementById('resetAccess');
    const btns = document.querySelectorAll('.a-btn');

    // Відкриття/Закриття
    toggle.addEventListener('click', () => panel.classList.add('active'));
    close.addEventListener('click', () => panel.classList.remove('active'));

    // Логіка кнопок
    btns.forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            const val = btn.dataset.val;

            // Видаляємо старі класи цього типу
            const groupBtns = document.querySelectorAll(`.a-btn[data-type="${type}"]`);
            groupBtns.forEach(b => {
                b.classList.remove('active');
                document.body.classList.remove(b.dataset.val);
            });

            // Додаємо новий
            btn.classList.add('active');
            if (val.indexOf('normal') === -1 && val.indexOf('show-images') === -1) {
                document.body.classList.add(val);
            }

            // Зберігаємо в LocalStorage
            saveSettings();
        });
    });

    reset.addEventListener('click', () => {
        btns.forEach(b => {
            b.classList.remove('active');
            document.body.classList.remove(b.dataset.val);
            if (b.dataset.val.includes('normal') || b.dataset.val.includes('show-images')) {
                b.classList.add('active');
            }
        });
        localStorage.removeItem('access_settings');
    });

    function saveSettings() {
        const activeVals = Array.from(document.querySelectorAll('.a-btn.active')).map(b => b.dataset.val);
        localStorage.setItem('access_settings', JSON.stringify(activeVals));
    }

    function loadSettings() {
        const saved = JSON.parse(localStorage.getItem('access_settings'));
        if (saved) {
            saved.forEach(val => {
                const btn = document.querySelector(`.a-btn[data-val="${val}"]`);
                if (btn) btn.click();
            });
        }
    }

    loadSettings();
});
