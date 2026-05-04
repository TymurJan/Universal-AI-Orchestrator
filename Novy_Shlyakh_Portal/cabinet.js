document.addEventListener('DOMContentLoaded', () => {
    // Екрани
    const screenLogin = document.getElementById('screen-login');
    const screenNda = document.getElementById('screen-nda');
    const screenDashboard = document.getElementById('screen-dashboard');

    // Кнопки
    const btnLogin = document.getElementById('btnLogin');
    const tokenInput = document.getElementById('tokenInput');
    const loginError = document.getElementById('loginError');

    const btnSignDiia = document.getElementById('btnSignDiia');
    const btnSignKep = document.getElementById('btnSignKep');
    const signatureStatus = document.getElementById('signatureStatus');

    // Дашборд елементи
    const statusCheckbox = document.getElementById('statusCheckbox');
    const statusText = document.getElementById('statusText');
    const requestsTableBody = document.getElementById('requestsTableBody');

    // Фейкові дані заявок
    const mockRequests = [
        { id: "REQ-001", type: "Юридична", desc: "Допомога в отриманні УБД", date: "Сьогодні, 10:45" },
        { id: "REQ-002", type: "Психологічна", desc: "ПТСР, сімейний конфлікт", date: "Сьогодні, 09:15" },
        { id: "REQ-003", type: "Кар'єра", desc: "Грант на власний бізнес", date: "Вчора, 18:30" },
    ];

    // Логіка Логіну
    btnLogin.addEventListener('click', () => {
        const token = tokenInput.value.trim();
        if (token.length > 3) {
            // Успішно. Переходимо до NDA
            screenLogin.classList.remove('active');
            screenNda.classList.add('active');
        } else {
            loginError.style.display = 'block';
        }
    });

    // Логіка Підпису NDA (Імітація)
    function simulateSignature() {
        btnSignDiia.style.display = 'none';
        btnSignKep.style.display = 'none';
        signatureStatus.style.display = 'block';

        setTimeout(() => {
            signatureStatus.textContent = "КЕП успішно верифіковано. Завантаження даних...";
            
            setTimeout(() => {
                screenNda.classList.remove('active');
                screenDashboard.classList.add('active');
                renderRequests();
            }, 1000);
        }, 1500);
    }

    btnSignDiia.addEventListener('click', simulateSignature);
    btnSignKep.addEventListener('click', simulateSignature);

    // Логіка Дашборду
    statusCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
            statusText.textContent = "Статус: Готовий до роботи";
            statusText.style.color = "var(--primary-green)";
        } else {
            statusText.textContent = "Статус: Не приймаю заявки";
            statusText.style.color = "#888";
        }
    });

    function renderRequests() {
        requestsTableBody.innerHTML = '';
        mockRequests.forEach(req => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${req.id}</td>
                <td><span style="background: rgba(255,255,255,0.1); padding: 4px 8px; border-radius: 4px;">${req.type}</span></td>
                <td>${req.desc}</td>
                <td>${req.date}</td>
                <td><button class="btn-take" onclick="alert('Запит ${req.id} взято в роботу!')">Взяти в роботу</button></td>
            `;
            requestsTableBody.appendChild(tr);
        });
    }
});
