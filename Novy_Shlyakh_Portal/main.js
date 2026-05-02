document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContent = document.querySelector('.tab-content');

    // База даних спеціалістів для прототипу
    const specialists = {
        legal: [
            { name: "Олександр Ковальчук", tag: "Провідний юрист", power: "Вирішення складних земельних питань та виплат.", rating: "4.9", cases: "42", reviews: "15" },
            { name: "Марина Петренко", tag: "Адвокат з прав ветеранів", power: "Оскарження рішень ВЛК та супровід у судах.", rating: "4.7", cases: "28", reviews: "9" }
        ],
        psych: [
            { name: "Іван Дроздов", tag: "Кризовий психолог", power: "Робота з гострими станами ПТСР та безсонням.", rating: "5.0", cases: "115", reviews: "45" },
            { name: "Олена Світла", tag: "Сімейний терапевт", power: "Реінтеграція в сім'ю та робота з дітьми ветеранів.", rating: "4.8", cases: "64", reviews: "22" }
        ],
        physio: [
            { name: "Віктор Сила", tag: "Фізіо-реабілітолог", power: "Відновлення моторики після важких поранень.", rating: "4.9", cases: "89", reviews: "31" },
            { name: "Артем Кінезіо", tag: "Мануальний терапевт", power: "Корекція постави та зняття хронічного болю.", rating: "4.6", cases: "52", reviews: "14" }
        ],
        career: [
            { name: "Сергій Вектор", tag: "Кар'єрний консультант", power: "Профорієнтація та підготовка до співбесід.", rating: "4.9", cases: "73", reviews: "18" },
            { name: "Ганна Грант", tag: "Бізнес-ментор", power: "Допомога у відкритті власної справи та отриманні грантів.", rating: "4.7", cases: "14", reviews: "5" }
        ],
        social: [
            { name: "Наталія Опіка", tag: "Соціальний кейс-менеджер", power: "Повний супровід у отриманні державних пільг.", rating: "5.0", cases: "156", reviews: "60" }
        ]
    };

    function renderSpecialists(category) {
        const grid = document.querySelector('.specialist-grid');
        grid.innerHTML = ''; // Очистка

        specialists[category].forEach(spec => {
            const card = document.createElement('div');
            card.className = 'spec-card';
            card.innerHTML = `
                <div class="spec-img placeholder-img">
                    <div class="spec-rating">⭐ ${spec.rating}</div>
                </div>
                <div class="spec-info">
                    <h4>${spec.name}</h4>
                    <p class="spec-tag">${spec.tag}</p>
                    <p class="spec-power"><strong>Суперсила:</strong> ${spec.power}</p>
                    <div class="spec-stats">
                        <span>📂 ${spec.cases} успішних кейсів</span>
                        <span>💬 ${spec.reviews} відгуків</span>
                    </div>
                    <button class="btn-card">Записатися</button>
                </div>
            `;
            grid.appendChild(card);
        });
    }

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all buttons
            tabButtons.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            btn.classList.add('active');
            
            const category = btn.getAttribute('data-tab');
            renderSpecialists(category);
        });
    });

    // Додамо плавний скрол для посилань
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});
