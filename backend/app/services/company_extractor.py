#!/usr/bin/env python3
"""
기업 추출 서비스

1단계: 수집된 뉴스에서 관련 기업명을 자동으로 추출하고 데이터베이스에 저장
"""

import openai
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.company import Company, CompanyMention
from ..models.content import Content
from ..core.config import settings
from ..utils.cost_calculator import calculate_openai_cost
import logging

logger = logging.getLogger(__name__)

# OpenAI 클라이언트 초기화
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


class CompanyExtractor:
    """기업 추출 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.model = "gpt-3.5-turbo"
    
    def extract_companies_from_content(self, content: Content) -> List[Dict[str, Any]]:
        """
        콘텐츠에서 기업명을 추출합니다.
        
        Parameters
        ----------
        content : Content
            추출할 콘텐츠
            
        Returns
        -------
        List[Dict[str, Any]]
            추출된 기업 정보 목록
        """
        try:
            # 텍스트 전처리
            text = self._preprocess_text(content.raw_text or content.title)
            
            # AI를 통한 기업 추출
            companies = self._extract_with_ai(text, content.title)
            
            # 기존 기업과 매칭
            matched_companies = self._match_existing_companies(companies)
            
            # 새로운 기업 저장
            new_companies = self._save_new_companies(companies, matched_companies)
            
            # 기업 언급 저장
            mentions = self._save_company_mentions(content, companies)
            
            logger.info(f"콘텐츠 {content.id}에서 {len(companies)}개 기업 추출 완료")
            
            return {
                "extracted_count": len(companies),
                "matched_count": len(matched_companies),
                "new_count": len(new_companies),
                "mentions_count": len(mentions)
            }
            
        except Exception as e:
            logger.error(f"기업 추출 실패 (콘텐츠 {content.id}): {str(e)}")
            return {"error": str(e)}
    
    def _preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 특수 문자 정리
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_with_ai(self, text: str, title: str) -> List[Dict[str, Any]]:
        """AI를 사용하여 기업명 추출"""
        try:
            prompt = f"""
다음 뉴스에서 언급된 기업명을 추출해주세요.

제목: {title}
내용: {text[:2000]}  # 텍스트 길이 제한

다음 JSON 형식으로 응답해주세요:
{{
    "companies": [
        {{
            "name": "기업명",
            "aliases": ["별칭1", "별칭2"],
            "industry": "업종",
            "relevance_score": 0.95,
            "confidence_score": 0.90,
            "mention_context": "언급된 문맥",
            "sentiment": "positive/negative/neutral"
        }}
    ]
}}

주의사항:
- 확실한 기업명만 추출
- 정부기관, 단체는 제외
- 주식 심볼이나 코드는 별칭에 포함
- 관련도와 신뢰도는 0-1 사이 값
- 감정은 기업에 대한 언급의 톤
"""

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 뉴스에서 기업명을 정확하게 추출하는 AI입니다."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            companies = result.get("companies", [])
            
            # 비용 로깅
            self._log_cost(response.usage, "company_extraction")
            
            return companies
            
        except Exception as e:
            logger.error(f"AI 기업 추출 실패: {str(e)}")
            return []
    
    def _match_existing_companies(self, extracted_companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """기존 기업과 매칭"""
        matched = []
        
        for company in extracted_companies:
            # 정확한 이름으로 검색
            existing = self.db.query(Company).filter(
                Company.name == company["name"]
            ).first()
            
            if existing:
                matched.append({
                    "extracted": company,
                    "existing": existing,
                    "match_type": "exact"
                })
                continue
            
            # 별칭으로 검색
            for alias in company.get("aliases", []):
                existing = self.db.query(Company).filter(
                    Company.aliases.contains([alias])
                ).first()
                
                if existing:
                    matched.append({
                        "extracted": company,
                        "existing": existing,
                        "match_type": "alias",
                        "matched_alias": alias
                    })
                    break
        
        return matched
    
    def _save_new_companies(self, extracted_companies: List[Dict[str, Any]], 
                           matched_companies: List[Dict[str, Any]]) -> List[Company]:
        """새로운 기업 저장"""
        matched_names = {m["extracted"]["name"] for m in matched_companies}
        new_companies = []
        
        for company in extracted_companies:
            if company["name"] in matched_names:
                continue
            
            # 신뢰도가 높은 기업만 저장
            if company.get("confidence_score", 0) < 0.7:
                continue
            
            new_company = Company(
                name=company["name"],
                display_name=company["name"],
                industry=company.get("industry"),
                aliases=company.get("aliases", []),
                keywords=company.get("keywords", []),
                confidence_score=company.get("confidence_score"),
                total_mentions=1,
                last_mentioned_at=datetime.utcnow()
            )
            
            self.db.add(new_company)
            new_companies.append(new_company)
        
        self.db.commit()
        return new_companies
    
    def _save_company_mentions(self, content: Content, 
                              companies: List[Dict[str, Any]]) -> List[CompanyMention]:
        """기업 언급 저장"""
        mentions = []
        
        for company in companies:
            # 기업 조회
            db_company = self.db.query(Company).filter(
                Company.name == company["name"]
            ).first()
            
            if not db_company:
                continue
            
            mention = CompanyMention(
                company_id=db_company.id,
                content_id=content.id,
                mention_text=company.get("mention_context", ""),
                mention_context=company.get("mention_context", ""),
                sentiment=company.get("sentiment"),
                relevance_score=company.get("relevance_score"),
                confidence_score=company.get("confidence_score"),
                extraction_method="ai",
                extraction_model=self.model
            )
            
            self.db.add(mention)
            mentions.append(mention)
            
            # 기업 통계 업데이트
            db_company.total_mentions += 1
            db_company.last_mentioned_at = datetime.utcnow()
        
        self.db.commit()
        return mentions
    
    def _log_cost(self, usage, request_type: str):
        """비용 로깅"""
        try:
            from ..models.cost_log import CostLog
            
            cost = calculate_openai_cost(
                tokens_in=usage.prompt_tokens,
                tokens_out=usage.completion_tokens
            )
            
            cost_log = CostLog(
                model_name=self.model,
                tokens_in=usage.prompt_tokens,
                tokens_out=usage.completion_tokens,
                cost_usd=cost,
                request_type=request_type,
                status="success"
            )
            
            self.db.add(cost_log)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"비용 로깅 실패: {str(e)}")
    
    def process_all_pending_content(self) -> Dict[str, Any]:
        """처리되지 않은 모든 콘텐츠에서 기업 추출"""
        try:
            # 기업 추출이 안된 콘텐츠 조회 (pending_summary 태그가 있는 것들)
            pending_contents = self.db.query(Content).filter(
                Content.tags.contains(["pending_summary"])
            ).limit(100).all()
            
            results = {
                "processed": 0,
                "extracted_companies": 0,
                "new_companies": 0,
                "mentions": 0,
                "errors": 0
            }
            
            for content in pending_contents:
                try:
                    result = self.extract_companies_from_content(content)
                    
                    if "error" not in result:
                        results["processed"] += 1
                        results["extracted_companies"] += result.get("extracted_count", 0)
                        results["new_companies"] += result.get("new_count", 0)
                        results["mentions"] += result.get("mentions_count", 0)
                        
                        # 태그 업데이트
                        if "pending_summary" in (content.tags or []):
                            content.tags = [tag for tag in (content.tags or []) 
                                          if tag != "pending_summary"]
                            content.tags.append("company_extracted")
                    else:
                        results["errors"] += 1
                        
                except Exception as e:
                    logger.error(f"콘텐츠 {content.id} 처리 실패: {str(e)}")
                    results["errors"] += 1
            
            self.db.commit()
            return results
            
        except Exception as e:
            logger.error(f"일괄 기업 추출 실패: {str(e)}")
            return {"error": str(e)}


def extract_companies_from_content(content_id: int, db: Session) -> Dict[str, Any]:
    """콘텐츠에서 기업 추출 (외부 호출용)"""
    extractor = CompanyExtractor(db)
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        return {"error": "콘텐츠를 찾을 수 없습니다"}
    
    return extractor.extract_companies_from_content(content)


def process_all_pending_companies(db: Session) -> Dict[str, Any]:
    """처리되지 않은 모든 콘텐츠에서 기업 추출 (외부 호출용)"""
    extractor = CompanyExtractor(db)
    return extractor.process_all_pending_content()
