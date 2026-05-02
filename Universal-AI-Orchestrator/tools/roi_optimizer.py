"""
Universal AI Orchestrator — ROI & Token Optimizer
Smart Resource Routing Module (Фінансовий Оптимізатор)

Цей модуль розраховує вартість запитів для різних LLM моделей 
та автоматично пропонує найефективнішу модель для задачі (Smart Routing),
забезпечуючи економію до 40-60%.

Використання:
  python roi_optimizer.py estimate --input_words 1000 --output_words 500 --quality "standard"
  python roi_optimizer.py estimate --input_words 50000 --output_words 1000 --quality "high"
"""

import argparse
import sys

# Вартість за 1М токенів (у USD)
MODELS_PRICING = {
    "high": [
        {"model": "GPT-4o", "input": 5.0, "output": 15.0},
        {"model": "Claude 3.5 Sonnet", "input": 3.0, "output": 15.0},
    ],
    "standard": [
        {"model": "GPT-4o-mini", "input": 0.15, "output": 0.60},
        {"model": "Claude 3 Haiku", "input": 0.25, "output": 1.25},
    ],
    "fast": [
        {"model": "Llama 3 8B (Local)", "input": 0.0, "output": 0.0}, # Local/Free
    ]
}

def estimate_cost(input_tokens: int, output_tokens: int, model_data: dict) -> float:
    cost_in = (input_tokens / 1_000_000) * model_data["input"]
    cost_out = (output_tokens / 1_000_000) * model_data["output"]
    return cost_in + cost_out

def get_best_model(quality, input_words, output_words):
    """
    Програмний інтерфейс для отримання рекомендації моделі.
    """
    multiplier = 1.6 
    input_tokens = int(input_words * multiplier)
    output_tokens = int(output_words * multiplier)
    
    results = []
    for tier, models in MODELS_PRICING.items():
        for m in models:
            cost = estimate_cost(input_tokens, output_tokens, m)
            results.append({"model": m["model"], "tier": tier, "cost": cost})

    # Сортуємо від найдорожчої (baseline) до найдешевшої
    results = sorted(results, key=lambda x: x["cost"], reverse=True)
    baseline_cost = results[0]["cost"]

    recommended = None
    for r in results:
        if r["tier"] == quality:
            recommended = r
            break
    
    # Якщо за якістю не знайдено, беремо найдешевшу доступну
    if not recommended:
        recommended = results[-1]

    savings_pct = 0
    if baseline_cost > 0:
        savings_pct = 100 - (recommended["cost"] / baseline_cost * 100)

    return {
        "model": recommended["model"],
        "cost": recommended["cost"],
        "savings_pct": savings_pct,
        "tokens": {"input": input_tokens, "output": output_tokens}
    }

def cmd_estimate(args):
    data = get_best_model(args.quality, args.input_words, args.output_words)
    
    print(f"\n📊 ROI OPTIMIZER (Smart Routing)")
    print("=" * 50)
    print(f"Вхідні дані: ~{args.input_words} слів ({data['tokens']['input']} токенів)")
    print(f"Очікувана відповідь: ~{args.output_words} слів ({data['tokens']['output']} токенів)")
    print(f"Вимога до якості: {args.quality.upper()}\n")

    print(f"✅ РІШЕННЯ ОРКЕСТРАТОРА:")
    print(f"   Задачу рекомендовано спрямувати на [{data['model']}].")
    print(f"   Прогнозована вартість: ${data['cost']:.6f}")
    if data['savings_pct'] > 0:
        print(f"   Економія бюджету: {data['savings_pct']:.1f}%", end="\n\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Universal AI Orchestrator: Smart Routing & ROI Optimizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Команди")

    est_p = subparsers.add_parser("estimate", help="Оцінити вартість та вибрати модель")
    est_p.add_argument("--input_words", type=int, required=True, help="Кількість слів на вході")
    est_p.add_argument("--output_words", type=int, required=True, help="Очікувана кількість слів на виході")
    est_p.add_argument("--quality", choices=["high", "standard", "fast"], default="standard", 
                       help="Вимоги до глибини аналізу (high - складний аналіз, standard - драфти, fast - банальна обробка)")

    args = parser.parse_args()

    if args.command == "estimate":
        cmd_estimate(args)
    else:
        parser.print_help()
