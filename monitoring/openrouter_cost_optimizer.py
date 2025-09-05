#!/usr/bin/env python3
"""OpenRouter Cost Optimizer - Zero-cost AI operations"""

def main():
    print("OpenRouter Cost Optimizer")
    print("=" * 40)
    
    free_models = [
        "openai/gpt-oss-20b:free",
        "qwen/qwen3-coder:free", 
        "meta-llama/llama-3.3-70b-instruct:free"
    ]
    
    print("FREE AI MODELS AVAILABLE:")
    for i, model in enumerate(free_models, 1):
        print(f"  {i}. {model}")
    
    monthly_tokens = 50000
    savings = monthly_tokens * 0.002 / 1000
    print(f"\nCOST OPTIMIZATION FOR {monthly_tokens:,} TOKENS:")
    print(f"  Using Free Models: $0.00")
    print(f"  Typical Paid Cost: ${savings:.2f}")
    print(f"  SAVINGS: 100% (${savings:.2f})")

if __name__ == "__main__":
    main()
