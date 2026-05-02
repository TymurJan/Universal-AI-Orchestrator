import re

html_path = 'd:/ГО Талан UA/Talan UA Antigravity manager/Universal-AI-Orchestrator/landing/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Define the refined SVG (Exact copy of Brain & Profile, delicate lines, emerald tint, no text)
drawing_svg = """
<div class="hero-graphic">
    <svg viewBox="0 0 500 300" style="width: 100%; height: 100%;" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <filter id="gentleGlowHero">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
        </defs>

        <!-- Brain Component (Left) -->
        <g transform="translate(40, 40) scale(1.1)" filter="url(#gentleGlowHero)">
            <!-- Main Outline -->
            <path d="M100,50 C140,50 170,80 170,120 C170,160 140,190 100,190 C60,190 30,160 30,120 C30,80 60,50 100,50 Z" 
                  fill="none" stroke="rgba(193, 248, 232, 0.4)" stroke-width="0.8" />
            
            <!-- Technical Paths (High detail) -->
            <g stroke="rgba(193, 248, 232, 0.5)" stroke-width="0.6" fill="none">
                <path d="M100,60 Q120,65 130,80 Q140,100 130,130 Q110,150 90,145 Q70,140 65,110" />
                <path d="M135,90 Q150,110 145,140 Q130,165 110,170" />
                <path d="M65,95 Q50,115 55,145 Q70,170 95,175" />
                <path d="M100,50 L100,190" stroke-opacity="0.2" stroke-dasharray="2 2" />
                
                <!-- Inner complex folds -->
                <path d="M80,90 Q100,100 120,90" />
                <path d="M85,140 Q100,130 115,140" />
                
                <!-- Synapse Pulse -->
                <path d="M20,120 L35,120 L40,110 L45,130 L50,120 L150,120 L155,105 L160,135 L165,120 L180,120" stroke="var(--step-peak)" stroke-width="1.2" filter="url(#gentleGlowHero)" />
            </g>
        </g>

        <!-- Profile Component (Right) -->
        <g transform="translate(300, 30) scale(0.9)" filter="url(#gentleGlowHero)">
            <!-- Face Outline (Delicate) -->
            <path d="M80,20 C110,20 140,50 140,100 C140,120 135,145 130,160 L125,230 L90,230 C80,230 70,210 65,190 C60,170 60,140 55,120 C50,100 45,90 45,80 C45,45 60,20 80,20 Z" 
                  fill="none" stroke="rgba(193, 248, 232, 0.5)" stroke-width="0.8" />
            
            <!-- Neural Cluster -->
            <g opacity="0.8">
                <circle cx="95" cy="70" r="2" fill="#fff" />
                <circle cx="85" cy="60" r="1" fill="#fff" opacity="0.6" />
                <circle cx="105" cy="80" r="1.5" fill="var(--step-peak)" />
                <circle cx="100" cy="55" r="0.8" fill="#fff" />
                <circle cx="80" cy="85" r="1" fill="#fff" />
                <path d="M85,60 L95,70 L105,80 M100,55 L95,70 L80,85" stroke="rgba(193, 248, 232, 0.3)" stroke-width="0.3" />
            </g>
        </g>
    </svg>
</div>
"""

# 2. Update Hero Section to 2-column layout
hero_old = re.compile(r'<section class="hero">.*?</section>', re.DOTALL)
hero_new = r"""    <section class="hero">
        <div class="container" style="max-width: 1200px;">
            <div class="hero-content">
                <div class="hero-text">
                    <h1 data-i18n="hero.h1">Впровадьте <span class="text-gradient-hero">Штучний Інтелект</span> у свій бізнес за 1 день.</h1>
                    <p style="font-size: 1.15rem; color: var(--text-secondary); margin-bottom: 2rem;" data-i18n="hero.p">
                        Автоматизуйте рутину, збережіть час та збільшіть прибуток.
                        <strong class="glass-step-1" style="font-weight: 500;">Розумний Експерт для вашої компанії</strong>, 
                        який бере на себе всю нудну роботу. Без програмування.
                    </p>
                    <div style="display: flex; gap: 1rem;">
                        <a href="#features" class="btn btn-step-1" data-i18n="nav.features">Подивитись Фічі</a>
                        <a href="#mission" class="btn btn-glass" data-i18n="nav.mission">Проєкт Ашрам</a>
                    </div>
                </div>
                """ + drawing_svg + """
            </div>
        </div>
    </section>"""

content = hero_old.sub(hero_new, content)

# 3. Remove SVG from Mission Section
mission_graphic_pattern = re.compile(r'<div>\s*<!-- Місце під реальне фото Ашраму -->\s*<div style="width: 100%; height: 400px;.*?</div>\s*</div>', re.DOTALL)
# We replace it with just an empty div or a space for actual photo later.
content = mission_graphic_pattern.sub('<div><!-- Місце для реального фото Проєкту Ашрам --></div>', content)

# 4. Refine Shield Icon (thinner lines, emerald, keep frame)
shield_old = r'<div class="feature-icon" style="color: var\(--step-3\);">.*?<h4>Абсолютна Безпека \(Human-in-the-loop\)'
shield_new = """<div class="feature-icon" style="color: #c1f8e8;">
    <svg viewBox="0 0 100 100" fill="none" stroke="currentColor" stroke-width="0.8" stroke-linecap="round" stroke-linejoin="round">
        <!-- Shield Outline (Delicate) -->
        <path d="M 50 15 L 15 25 V 50 C 15 75 50 90 50 90 C 50 90 85 75 85 50 V 25 L 50 15 Z" />
        
        <!-- Organic Circuit traces -->
        <path d="M 50 25 L 65 35 L 65 50 L 75 55" />
        <circle cx="75" cy="55" r="1.5" fill="currentColor" stroke="none"/>
        
        <path d="M 50 40 L 60 40 L 60 25 L 75 25" />
        <circle cx="75" cy="25" r="1.5" fill="currentColor" stroke="none"/>

        <path d="M 50 60 L 70 60 L 70 75 L 80 75" />
        <circle cx="80" cy="75" r="1.5" fill="currentColor" stroke="none"/>

        <path d="M 50 80 L 60 85" />
        <circle cx="62" cy="86" r="1" fill="currentColor" stroke="none"/>
        
        <!-- Tech particles (dust) -->
        <circle cx="25" cy="30" r="0.5" fill="currentColor" />
        <circle cx="35" cy="20" r="0.5" fill="currentColor" />
        <circle cx="10" cy="45" r="0.6" fill="currentColor" />
        <circle cx="20" cy="70" r="0.4" fill="currentColor" />
        <circle cx="40" cy="85" r="0.5" fill="currentColor" />
    </svg>
</div>
                <h4>Абсолютна Безпека (Human-in-the-loop)"""

content = re.sub(shield_old, shield_new, content, flags=re.DOTALL)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Hero layout updated, drawing moved, shield refined.")
