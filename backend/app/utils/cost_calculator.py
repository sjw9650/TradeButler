"""OpenAI API 비용 계산 유틸리티"""
from typing import Dict, Tuple

# OpenAI GPT 모델별 1000 토큰당 비용 (USD)
MODEL_COSTS = {
    "gpt-3.5-turbo": {
        "input": 0.0015,   # $0.0015 per 1K input tokens
        "output": 0.002    # $0.002 per 1K output tokens
    },
    "gpt-4": {
        "input": 0.03,     # $0.03 per 1K input tokens
        "output": 0.06     # $0.06 per 1K output tokens
    },
    "gpt-4-turbo": {
        "input": 0.01,     # $0.01 per 1K input tokens
        "output": 0.03     # $0.03 per 1K output tokens
    }
}

def calculate_openai_cost(
    model_name: str, 
    tokens_in: int, 
    tokens_out: int
) -> Tuple[float, Dict[str, float]]:
    """
    OpenAI API 호출 비용 계산
    
    Args:
        model_name: 사용된 모델명
        tokens_in: 입력 토큰 수
        tokens_out: 출력 토큰 수
        
    Returns:
        Tuple[float, Dict[str, float]]: 총 비용과 상세 비용 내역
        
    Examples:
        >>> cost, breakdown = calculate_openai_cost("gpt-3.5-turbo", 1000, 500)
        >>> print(f"총 비용: ${cost:.4f}")
        >>> print(f"상세 내역: {breakdown}")
    """
    if model_name not in MODEL_COSTS:
        # 알 수 없는 모델은 gpt-3.5-turbo 기준으로 계산
        model_name = "gpt-3.5-turbo"
    
    model_cost = MODEL_COSTS[model_name]
    
    # 1000 토큰 단위로 비용 계산
    input_cost = (tokens_in / 1000) * model_cost["input"]
    output_cost = (tokens_out / 1000) * model_cost["output"]
    total_cost = input_cost + output_cost
    
    breakdown = {
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "input_cost": round(input_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(total_cost, 6),
        "model": model_name
    }
    
    return round(total_cost, 6), breakdown

def estimate_cost_for_text(text: str, model_name: str = "gpt-3.5-turbo") -> Dict[str, float]:
    """
    텍스트 길이를 기반으로 예상 비용 계산
    
    Args:
        text: 분석할 텍스트
        model_name: 사용할 모델명
        
    Returns:
        Dict[str, float]: 예상 비용 정보
        
    Examples:
        >>> cost_info = estimate_cost_for_text("긴 텍스트...", "gpt-4")
        >>> print(f"예상 비용: ${cost_info['estimated_cost']:.4f}")
    """
    # 간단한 토큰 추정 (영어 기준 약 4글자 = 1토큰, 한국어 기준 약 2글자 = 1토큰)
    estimated_tokens = len(text) // 3  # 평균적으로 3글자당 1토큰
    
    # 출력 토큰은 입력의 약 30%로 추정
    estimated_output = int(estimated_tokens * 0.3)
    
    cost, breakdown = calculate_openai_cost(model_name, estimated_tokens, estimated_output)
    
    return {
        "estimated_input_tokens": estimated_tokens,
        "estimated_output_tokens": estimated_output,
        "estimated_cost": cost,
        "model": model_name,
        "text_length": len(text)
    } 