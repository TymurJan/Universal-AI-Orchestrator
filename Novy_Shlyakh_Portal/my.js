// my.js - Логіка Кабінету Ветерана

document.addEventListener('DOMContentLoaded', () => {

    // --- Перемикання табів ---
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const tabSpecialist = document.getElementById('tab-specialist');
    
    const formLogin = document.getElementById('login-form');
    const formRegister = document.getElementById('register-form');
    const formSpecialist = document.getElementById('specialist-form');

    function resetTabs() {
        [tabLogin, tabRegister, tabSpecialist].forEach(t => t.classList.remove('active'));
        [formLogin, formRegister, formSpecialist].forEach(f => f.classList.remove('active'));
    }

    tabLogin.addEventListener('click', () => {
        resetTabs();
        tabLogin.classList.add('active');
        formLogin.classList.add('active');
    });

    tabRegister.addEventListener('click', () => {
        resetTabs();
        tabRegister.classList.add('active');
        formRegister.classList.add('active');
    });

    tabSpecialist.addEventListener('click', () => {
        resetTabs();
        tabSpecialist.classList.add('active');
        formSpecialist.classList.add('active');
    });

    // Перехід до Back-office спеціаліста
    document.getElementById('go-to-specialist').addEventListener('click', () => {
        window.location.href = 'cabinet.html';
    });

    // --- База даних (Mock в localStorage) ---
    // Формат: { login: { name, password, questionId, answer } }
    function getDB() {
        const db = localStorage.getItem('veteran_db');
        return db ? JSON.parse(db) : {};
    }
    function saveDB(db) {
        localStorage.setItem('veteran_db', JSON.stringify(db));
    }

    // --- Дія.Підпис Імітація (Mock OAuth Gateway) ---
    const diiaBtn = document.getElementById('diia-verify-btn');
    const diiaTokenInput = document.getElementById('diia-verified-token');
    const diiaStatusText = document.getElementById('diia-status-text');

    diiaBtn.addEventListener('click', () => {
        diiaBtn.disabled = true;
        diiaBtn.style.background = '#ffc107';
        diiaBtn.style.color = '#000';
        diiaBtn.innerHTML = '⏳ Перенаправлення на портал Дія...';
        
        // Імітація OAuth2 редиректу
        setTimeout(() => {
            // В реальності тут буде window.location.href = 'https://diia.gov.ua/api/oauth2/...';
            // І після повернення URL матиме ?token=xxxxxx
            diiaTokenInput.value = 'DIIA_VERIFIED_JWT_MOCK_12345';
            
            diiaBtn.style.background = '#28a745';
            diiaBtn.style.color = '#fff';
            diiaBtn.innerHTML = '✅ Верифікацію успішно пройдено';
            
            diiaStatusText.style.color = 'var(--success)';
            diiaStatusText.textContent = 'Особу підтверджено державним реєстром. Можете завершити реєстрацію.';
        }, 3000);
    });

    // --- Реєстрація ---
    formRegister.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Отримуємо чекбокси (html5 required вже перевірив їх, але для надійності)
        const checkVerify = document.getElementById('reg-verify').checked;
        const checkNda = document.getElementById('reg-nda').checked;
        const diiaToken = diiaTokenInput.value;
        
        if (!diiaToken) {
            alert('Будь ласка, пройдіть верифікацію особи через Дію перед реєстрацією.');
            return;
        }
        
        if (!checkVerify || !checkNda) return;

        const name = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;
        const questionId = document.getElementById('reg-question').value;
        const answer = document.getElementById('reg-answer').value;

        const db = getDB();
        if (db[email]) {
            alert('Користувач з таким логіном вже існує!');
            return;
        }

        // Зберігаємо юзера (В реальності сервер перевірить JWT токен)
        db[email] = { 
            name, 
            password, 
            questionId, 
            answer: answer.toLowerCase(),
            verified_by: 'DIIA_REGISTRY',
            token: diiaToken
        };
        saveDB(db);

        alert('✅ Профіль створено! Усі дані захищені та підтверджені. Тепер ви можете увійти.');
        tabLogin.click(); // Перемикаємо на логін
        formRegister.reset();
        diiaBtn.disabled = false;
        diiaBtn.style.background = '#111';
        diiaBtn.innerHTML = '<span style="font-weight: 900; font-family: Outfit; font-size: 18px; letter-spacing: 1px;">Дія.Підпис</span> Пройти верифікацію';
        diiaStatusText.textContent = '⚠️ Очікування верифікації...';
        diiaStatusText.style.color = 'var(--danger)';
        diiaTokenInput.value = '';
    });

    // --- Вхід ---
    formLogin.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        const db = getDB();
        const user = db[email];

        if (user && user.password === password) {
            // Успішний вхід
            localStorage.setItem('current_veteran', email);
            showDashboard(user.name);
        } else {
            alert('Невірний логін або пароль.');
        }
    });

    // --- Відновлення паролю ---
    const modal = document.getElementById('recovery-modal');
    const closeBtn = document.querySelector('.close-btn');
    const forgotLink = document.getElementById('forgot-password-link');
    const recForm = document.getElementById('recovery-form');
    const recLoginInput = document.getElementById('recovery-login');
    const recQuestionBlock = document.getElementById('recovery-question-block');
    const recQuestionText = document.getElementById('recovery-question-text');
    const recAnswerInput = document.getElementById('recovery-answer');
    const recBtn = document.getElementById('recovery-btn');

    const questionsMap = {
        "1": "Дівоче прізвище матері",
        "2": "Позивний вашого першого командира",
        "3": "Назва вулиці, де ви виросли"
    };

    let recoveryState = 0; // 0 - введення логіну, 1 - відповідь на питання

    forgotLink.addEventListener('click', (e) => {
        e.preventDefault();
        modal.classList.add('active');
        recoveryState = 0;
        recLoginInput.parentElement.style.display = 'block';
        recQuestionBlock.style.display = 'none';
        recBtn.textContent = 'Далі';
        recForm.reset();
    });

    closeBtn.addEventListener('click', () => modal.classList.remove('active'));

    recForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const db = getDB();
        
        if (recoveryState === 0) {
            const login = recLoginInput.value;
            if (db[login]) {
                const qId = db[login].questionId;
                recQuestionText.textContent = questionsMap[qId];
                recLoginInput.parentElement.style.display = 'none';
                recQuestionBlock.style.display = 'block';
                recBtn.textContent = 'Перевірити';
                recoveryState = 1;
            } else {
                alert('Логін не знайдено.');
            }
        } else if (recoveryState === 1) {
            const login = recLoginInput.value;
            const answer = recAnswerInput.value.toLowerCase();
            
            if (db[login].answer === answer) {
                alert(`Ваш пароль: ${db[login].password}`);
                modal.classList.remove('active');
            } else {
                alert('Невірна відповідь на секретне питання.');
            }
        }
    });

    // --- Перемикання екранів ---
    const authScreen = document.getElementById('auth-screen');
    const dashScreen = document.getElementById('dashboard-screen');
    const displayUserName = document.getElementById('display-user-name');
    const logoutBtn = document.getElementById('logout-btn');

    // --- Керування даними (Право на забуття) ---
    const deleteBtn = document.getElementById('delete-profile-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const confirm1 = confirm('Ви впевнені, що хочете назавжди видалити свій профіль? Всі ваші дані, документи та історія консультацій будуть стерті без можливості відновлення.');
            if (confirm1) {
                const email = localStorage.getItem('current_veteran');
                const db = getDB();
                const user = db[email];
                const confirm2 = prompt('Для підтвердження введіть ваш пароль:');
                if (confirm2 === user.password) {
                    delete db[email];
                    saveDB(db);
                    localStorage.removeItem('current_veteran');
                    alert('Ваш профіль та всі пов\'язані дані успішно видалено з системи. Дякуємо, що були з нами.');
                    window.location.reload();
                } else {
                    alert('Невірний пароль. Видалення скасовано.');
                }
            }
        });
    }

    function showDashboard(name) {
        authScreen.classList.remove('active');
        dashScreen.classList.add('active');
        displayUserName.textContent = name;
    }

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('current_veteran');
        dashScreen.classList.remove('active');
        authScreen.classList.add('active');
        formLogin.reset();
    });

    // Перевірка сесії при завантаженні
    const currentUser = localStorage.getItem('current_veteran');
    if (currentUser) {
        const db = getDB();
        if (db[currentUser]) {
            showDashboard(db[currentUser].name);
        }
    }

    // --- Навігація в Дашборді ---
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    const viewSections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            // Зміна активного табу
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Зміна контенту
            const targetId = 'view-' + item.getAttribute('data-target');
            viewSections.forEach(sec => {
                if (sec.id === targetId) sec.classList.add('active');
                else sec.classList.remove('active');
            });
        });
    });

    // --- Імітація Сейфу (Upload) ---
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');

    uploadZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            const fileName = e.target.files[0].name;
            const date = new Date().toLocaleDateString();
            
            const li = document.createElement('li');
            li.className = 'file-item';
            li.innerHTML = `
                <div class="file-info">
                    <span class="file-icon">📄</span>
                    <span class="file-name">${fileName}</span>
                </div>
                <span class="file-date">${date}</span>
            `;
            fileList.appendChild(li);
            alert('Файл успішно зашифровано та збережено у Сейф.');
        }
    });

});
