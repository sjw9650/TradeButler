#!/usr/bin/env python3
"""
비용 최적화 서비스

AI 호출 최소화 및 캐싱 전략을 제공합니다.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import hashlib
import json

from ..models.content import Content
from ..models.cost_log import CostLog
from ..repo.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CostOptimizerService:
    """비용 최적화 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = get_redis_client()
    
    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        비용 요약을 조회합니다.
        
        Parameters
        ----------
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            비용 요약 정보
        """
        try:
            # 분석 기간 설정
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 비용 로그 조회
            cost_logs = self.db.query(CostLog).filter(
                and_(
                    CostLog.created_at >= start_date,
                    CostLog.created_at <= end_date
                )
            ).all()
            
            if not cost_logs:
                return {
                    "analysis_period": f"{days}일",
                    "total_cost": 0.0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "avg_cost_per_request": 0.0,
                    "cost_by_model": {},
                    "cost_by_task": {},
                    "daily_costs": [],
                    "optimization_suggestions": []
                }
            
            # 기본 통계 계산
            total_cost = sum(log.cost for log in cost_logs)
            total_requests = len(cost_logs)
            total_tokens = sum(log.total_tokens for log in cost_logs)
            avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
            
            # 모델별 비용
            cost_by_model = {}
            for log in cost_logs:
                model = log.model_name
                if model not in cost_by_model:
                    cost_by_model[model] = {"cost": 0.0, "requests": 0, "tokens": 0}
                cost_by_model[model]["cost"] += log.cost
                cost_by_model[model]["requests"] += 1
                cost_by_model[model]["tokens"] += log.total_tokens
            
            # 태스크별 비용
            cost_by_task = {}
            for log in cost_logs:
                task = log.task_name
                if task not in cost_by_task:
                    cost_by_task[task] = {"cost": 0.0, "requests": 0, "tokens": 0}
                cost_by_task[task]["cost"] += log.cost
                cost_by_task[task]["requests"] += 1
                cost_by_task[task]["tokens"] += log.total_tokens
            
            # 일별 비용
            daily_costs = {}
            for log in cost_logs:
                date = log.created_at.date().isoformat()
                if date not in daily_costs:
                    daily_costs[date] = {"cost": 0.0, "requests": 0}
                daily_costs[date]["cost"] += log.cost
                daily_costs[date]["requests"] += 1
            
            daily_costs_list = [
                {"date": date, "cost": data["cost"], "requests": data["requests"]}
                for date, data in sorted(daily_costs.items())
            ]
            
            # 최적화 제안
            optimization_suggestions = self._generate_optimization_suggestions(
                cost_by_model, cost_by_task, total_cost, total_requests
            )
            
            return {
                "analysis_period": f"{days}일",
                "total_cost": round(total_cost, 4),
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "avg_cost_per_request": round(avg_cost_per_request, 4),
                "cost_by_model": {
                    model: {
                        "cost": round(data["cost"], 4),
                        "requests": data["requests"],
                        "tokens": data["tokens"],
                        "avg_cost_per_request": round(data["cost"] / data["requests"], 4) if data["requests"] > 0 else 0
                    }
                    for model, data in cost_by_model.items()
                },
                "cost_by_task": {
                    task: {
                        "cost": round(data["cost"], 4),
                        "requests": data["requests"],
                        "tokens": data["tokens"],
                        "avg_cost_per_request": round(data["cost"] / data["requests"], 4) if data["requests"] > 0 else 0
                    }
                    for task, data in cost_by_task.items()
                },
                "daily_costs": daily_costs_list,
                "optimization_suggestions": optimization_suggestions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"비용 요약 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    def _generate_optimization_suggestions(
        self, 
        cost_by_model: Dict[str, Dict], 
        cost_by_task: Dict[str, Dict], 
        total_cost: float, 
        total_requests: int
    ) -> List[Dict[str, Any]]:
        """최적화 제안 생성"""
        suggestions = []
        
        # 모델별 최적화 제안
        if cost_by_model:
            most_expensive_model = max(cost_by_model.items(), key=lambda x: x[1]["cost"])
            if most_expensive_model[1]["cost"] > total_cost * 0.5:  # 전체 비용의 50% 이상
                suggestions.append({
                    "type": "model_optimization",
                    "priority": "high",
                    "title": "고비용 모델 최적화",
                    "description": f"{most_expensive_model[0]} 모델이 전체 비용의 {most_expensive_model[1]['cost']/total_cost*100:.1f}%를 차지합니다.",
                    "suggestion": "더 저렴한 모델로 전환하거나 요청 빈도를 줄이는 것을 고려하세요.",
                    "potential_savings": f"${most_expensive_model[1]['cost'] * 0.3:.2f}/월"
                })
        
        # 태스크별 최적화 제안
        if cost_by_task:
            most_expensive_task = max(cost_by_task.items(), key=lambda x: x[1]["cost"])
            if most_expensive_task[1]["cost"] > total_cost * 0.3:  # 전체 비용의 30% 이상
                suggestions.append({
                    "type": "task_optimization",
                    "priority": "medium",
                    "title": "고비용 태스크 최적화",
                    "description": f"{most_expensive_task[0]} 태스크가 전체 비용의 {most_expensive_task[1]['cost']/total_cost*100:.1f}%를 차지합니다.",
                    "suggestion": "태스크 실행 빈도를 조정하거나 캐싱을 활용하세요.",
                    "potential_savings": f"${most_expensive_task[1]['cost'] * 0.2:.2f}/월"
                })
        
        # 캐싱 제안
        if total_requests > 100:
            suggestions.append({
                "type": "caching",
                "priority": "high",
                "title": "캐싱 전략 도입",
                "description": f"일일 {total_requests//30}회의 요청이 있습니다.",
                "suggestion": "중복 요청을 방지하기 위해 Redis 캐싱을 활용하세요.",
                "potential_savings": f"${total_cost * 0.4:.2f}/월"
            })
        
        # 배치 처리 제안
        if total_requests > 50:
            suggestions.append({
                "type": "batch_processing",
                "priority": "medium",
                "title": "배치 처리 도입",
                "description": "여러 개별 요청을 하나의 배치로 처리할 수 있습니다.",
                "suggestion": "유사한 요청들을 그룹화하여 처리 효율성을 높이세요.",
                "potential_savings": f"${total_cost * 0.15:.2f}/월"
            })
        
        return suggestions
    
    def get_cache_hit_rate(self, days: int = 7) -> Dict[str, Any]:
        """
        캐시 적중률을 조회합니다.
        
        Parameters
        ----------
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            캐시 적중률 정보
        """
        try:
            # Redis에서 캐시 통계 조회
            cache_stats = self.redis_client.hgetall("cache_stats")
            
            if not cache_stats:
                return {
                    "analysis_period": f"{days}일",
                    "cache_hit_rate": 0.0,
                    "total_requests": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "cache_size": 0,
                    "memory_usage": "0MB"
                }
            
            total_requests = int(cache_stats.get("total_requests", 0))
            cache_hits = int(cache_stats.get("cache_hits", 0))
            cache_misses = int(cache_stats.get("cache_misses", 0))
            
            cache_hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
            
            # 캐시 크기 조회
            cache_size = self.redis_client.dbsize()
            
            # 메모리 사용량 조회
            memory_info = self.redis_client.info("memory")
            memory_usage = memory_info.get("used_memory_human", "0MB")
            
            return {
                "analysis_period": f"{days}일",
                "cache_hit_rate": round(cache_hit_rate, 2),
                "total_requests": total_requests,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "cache_size": cache_size,
                "memory_usage": memory_usage,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"캐시 적중률 조회 실패: {str(e)}")
            return {"error": str(e)}
    
    def optimize_content_processing(self, content_id: int) -> Dict[str, Any]:
        """
        콘텐츠 처리 최적화를 수행합니다.
        
        Parameters
        ----------
        content_id : int
            콘텐츠 ID
            
        Returns
        -------
        Dict[str, Any]
            최적화 결과
        """
        try:
            # 콘텐츠 조회
            content = self.db.query(Content).filter(Content.id == content_id).first()
            if not content:
                return {"error": "콘텐츠를 찾을 수 없습니다."}
            
            # 캐시 키 생성
            cache_key = f"content_analysis:{content_id}"
            
            # 캐시에서 기존 분석 결과 조회
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                return {
                    "content_id": content_id,
                    "optimization_type": "cache_hit",
                    "message": "캐시에서 기존 분석 결과를 사용합니다.",
                    "cached_data": json.loads(cached_result),
                    "savings": "AI 호출 비용 절약"
                }
            
            # 중복 처리 방지
            processing_key = f"processing:{content_id}"
            if self.redis_client.exists(processing_key):
                return {
                    "content_id": content_id,
                    "optimization_type": "duplicate_prevention",
                    "message": "이미 처리 중인 콘텐츠입니다.",
                    "savings": "중복 처리 방지"
                }
            
            # 처리 중 플래그 설정 (5분 TTL)
            self.redis_client.setex(processing_key, 300, "processing")
            
            return {
                "content_id": content_id,
                "optimization_type": "new_processing",
                "message": "새로운 분석을 시작합니다.",
                "processing_started": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"콘텐츠 처리 최적화 실패: {str(e)}")
            return {"error": str(e)}
    
    def get_duplicate_content_detection(self, days: int = 7) -> Dict[str, Any]:
        """
        중복 콘텐츠 감지를 수행합니다.
        
        Parameters
        ----------
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            중복 콘텐츠 감지 결과
        """
        try:
            # 분석 기간 설정
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 최근 콘텐츠 조회
            recent_contents = self.db.query(Content).filter(
                and_(
                    Content.published_at >= start_date,
                    Content.published_at <= end_date,
                    Content.is_active == "active"
                )
            ).all()
            
            # 제목 기반 중복 감지
            title_hashes = {}
            duplicates = []
            
            for content in recent_contents:
                # 제목 해시 생성
                title_hash = hashlib.md5(content.title.lower().encode()).hexdigest()
                
                if title_hash in title_hashes:
                    duplicates.append({
                        "content_id": content.id,
                        "title": content.title,
                        "url": content.url,
                        "published_at": content.published_at.isoformat(),
                        "duplicate_of": title_hashes[title_hash],
                        "similarity_score": 1.0
                    })
                else:
                    title_hashes[title_hash] = content.id
            
            # 중복 제거 제안
            optimization_suggestions = []
            if duplicates:
                optimization_suggestions.append({
                    "type": "duplicate_removal",
                    "priority": "medium",
                    "title": "중복 콘텐츠 제거",
                    "description": f"{len(duplicates)}개의 중복 콘텐츠가 발견되었습니다.",
                    "suggestion": "중복 콘텐츠를 제거하여 처리 비용을 절약하세요.",
                    "potential_savings": f"${len(duplicates) * 0.01:.2f}/월"
                })
            
            return {
                "analysis_period": f"{days}일",
                "total_contents": len(recent_contents),
                "duplicates_found": len(duplicates),
                "duplicate_rate": round(len(duplicates) / len(recent_contents) * 100, 2) if recent_contents else 0,
                "duplicates": duplicates,
                "optimization_suggestions": optimization_suggestions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"중복 콘텐츠 감지 실패: {str(e)}")
            return {"error": str(e)}
    
    def get_processing_efficiency(self, days: int = 7) -> Dict[str, Any]:
        """
        처리 효율성을 분석합니다.
        
        Parameters
        ----------
        days : int
            분석 기간 (일)
            
        Returns
        -------
        Dict[str, Any]
            처리 효율성 분석 결과
        """
        try:
            # 분석 기간 설정
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # 콘텐츠 처리 통계
            content_stats = self.db.query(
                func.count(Content.id).label('total_contents'),
                func.count(Content.id).filter(Content.ai_summary_status == 'completed').label('processed_contents'),
                func.count(Content.id).filter(Content.ai_summary_status == 'pending').label('pending_contents'),
                func.count(Content.id).filter(Content.ai_summary_status == 'failed').label('failed_contents')
            ).filter(
                and_(
                    Content.published_at >= start_date,
                    Content.published_at <= end_date
                )
            ).first()
            
            # 처리율 계산
            total_contents = content_stats.total_contents or 0
            processed_contents = content_stats.processed_contents or 0
            pending_contents = content_stats.pending_contents or 0
            failed_contents = content_stats.failed_contents or 0
            
            processing_rate = (processed_contents / total_contents * 100) if total_contents > 0 else 0
            failure_rate = (failed_contents / total_contents * 100) if total_contents > 0 else 0
            
            # 효율성 제안
            efficiency_suggestions = []
            
            if failure_rate > 10:
                efficiency_suggestions.append({
                    "type": "error_reduction",
                    "priority": "high",
                    "title": "처리 실패율 개선",
                    "description": f"처리 실패율이 {failure_rate:.1f}%입니다.",
                    "suggestion": "에러 로그를 확인하고 재시도 로직을 개선하세요.",
                    "potential_improvement": "처리 성공률 20% 향상"
                })
            
            if pending_contents > total_contents * 0.3:
                efficiency_suggestions.append({
                    "type": "queue_optimization",
                    "priority": "medium",
                    "title": "처리 큐 최적화",
                    "description": f"처리 대기 중인 콘텐츠가 {pending_contents}개입니다.",
                    "suggestion": "워커 수를 증가시키거나 배치 처리를 도입하세요.",
                    "potential_improvement": "처리 시간 50% 단축"
                })
            
            return {
                "analysis_period": f"{days}일",
                "total_contents": total_contents,
                "processed_contents": processed_contents,
                "pending_contents": pending_contents,
                "failed_contents": failed_contents,
                "processing_rate": round(processing_rate, 2),
                "failure_rate": round(failure_rate, 2),
                "efficiency_suggestions": efficiency_suggestions,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"처리 효율성 분석 실패: {str(e)}")
            return {"error": str(e)}
