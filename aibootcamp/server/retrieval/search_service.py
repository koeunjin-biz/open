from langchain.schema import Document
from typing import List, Literal
from langchain.schema import HumanMessage, SystemMessage
from utils.config import get_llm
import requests
import json
import time
import random
from duckduckgo_search import DDGS


def improve_search_query(
    topic: str,
    role: Literal["IPO_AGENT"] = "IPO_AGENT",
) -> List[str]:
    print(f"[START]search_service.improve_search_query({topic},{role})")

    template = "'{topic}'에 대해 {perspective} 웹검색에 적합한 3개의 검색어를 제안해주세요. 각 검색어는 25자 이내로 작성하고 콤마로 구분하세요. 검색어만 제공하고 설명은 하지 마세요."

    perspective_map = {
        "IPO_AGENT": "금융시장에 금융자본을 상장하기위한 사실과 정보를 찾고자 합니다."
    }

    prompt = template.format(topic=topic, perspective=perspective_map[role])

    messages = [
        SystemMessage(
            content="당신은 검색 전문가입니다. 주어진 주제에 대해 가장 관련성 높은 검색어를 제안해주세요."
        ),
        HumanMessage(content=prompt),
    ]

    # 스트리밍 응답 받기
    response = get_llm().invoke(messages)

    # ,로 구분된 검색어 추출
    suggested_queries = [q.strip() for q in response.content.split(",")]

    return suggested_queries[:3]




def get_search_content(
    improved_queries: str,
    language: str = "ko",
    max_results: int = 5,
) -> List[Document]:
    print(f"[START]search_service.get_search_content({improved_queries},{language},{max_results})")

    # 1단계: 로컬 PDF 문서에서 검색
    local_documents = search_local_documents(improved_queries, max_results)
    
    # 로컬에서 충분한 결과를 찾았으면 반환
    if len(local_documents) >= 2:
        print(f"로컬 PDF에서 {len(local_documents)}개 문서 발견, 외부 검색 생략")
        return local_documents
    
    # 2단계: 로컬 결과가 부족하면 외부 검색 시도
    print(f"로컬 PDF에서 {len(local_documents)}개 문서 발견, 외부 검색 시도...")
    external_documents = search_external_sources(improved_queries, language, max_results)
    
    # 로컬과 외부 결과 합치기
    all_documents = local_documents + external_documents
    
    if not all_documents:
        print("모든 검색에서 결과 없음, 기본 정보 제공")
        return get_default_documents()
    
    print(f"총 {len(all_documents)}개 문서 검색 완료 (로컬: {len(local_documents)}, 외부: {len(external_documents)})")
    return all_documents


def search_local_documents(
    queries: List[str],
    max_results: int = 5,
) -> List[Document]:
    """로컬 PDF 문서에서 검색"""
    print(f"[START]search_service.search_local_documents({queries},{max_results})")
    
    try:
        from utils.config import load_vectorstore
        
        # 로컬 벡터 스토어 로드
        vectorstore = load_vectorstore()
        
        documents = []
        
        # 각 쿼리에 대해 벡터 검색 수행
        for query in queries:
            try:
                # 벡터 스토어에서 유사도 검색
                results = vectorstore.similarity_search(query, k=max_results)
                if results:
                    # 중복 제거 및 품질 필터링
                    filtered_results = []
                    seen_content = set()
                    
                    for result in results:
                        content_hash = hash(result.page_content[:100])  # 첫 100자로 중복 체크
                        if content_hash not in seen_content and len(result.page_content) > 30:
                            filtered_results.append(result)
                            seen_content.add(content_hash)
                    
                    documents.extend(filtered_results)
                    
                    # 문서 출처 정보 출력
                    file_sources = {}
                    for doc in filtered_results:
                        file_name = doc.metadata.get("file", "Unknown")
                        if file_name not in file_sources:
                            file_sources[file_name] = 0
                        file_sources[file_name] += 1
                    
                    print(f"쿼리 '{query}'에서 {len(filtered_results)}개 문서 발견:")
                    for file_name, count in file_sources.items():
                        print(f"  - {file_name}: {count}개")
                else:
                    print(f"쿼리 '{query}'에서 검색 결과 없음")
                
            except Exception as e:
                print(f"벡터 검색 실패 ({query}): {str(e)}")
                continue
        
        print(f"로컬 PDF에서 총 {len(documents)}개 문서 검색 완료")
        return documents
        
    except Exception as e:
        print(f"로컬 벡터 스토어 로드 실패: {str(e)}")
        print("외부 검색으로 전환합니다...")
        return []


def get_default_documents() -> List[Document]:
    """검색 결과가 없을 때 제공할 기본 문서"""
    default_content = """
    KRX(한국거래소) 상장 절차에 대한 기본 정보입니다.
    
    주요 상장 시장:
    1. 유가증권시장 (KOSPI) - 대형 기업 중심
    2. 코스닥시장 - 기술 중심 기업
    3. 코넥스시장 - 중소기업 및 벤처기업
    4. 채권시장 - 채권 상장
    
    일반적인 상장 절차:
    1. 상장 예비심사 신청
    2. 상장 심사
    3. 상장 결정
    4. 상장 공시
    5. 상장 등록
    
    자세한 정보는 KRX 공식 가이드북을 참조하시기 바랍니다.
    """
    
    return [
        Document(
            page_content=default_content,
            metadata={
                "source": "기본 정보",
                "section": "default",
                "topic": "KRX 상장 기본 정보",
                "query": "기본 정보",
            },
        )
    ]


def search_external_sources(
    queries: List[str],
    language: str = "ko",
    max_results: int = 5,
) -> List[Document]:
    """외부 소스에서 검색 (DuckDuckGo + Wikipedia)"""
    print(f"[START]search_service.search_external_sources({queries},{language},{max_results})")
    
    documents = []
    
    # 1단계: DuckDuckGo 검색 시도 (Rate Limit 방지 로직 포함)
    ddg_documents = search_duckduckgo(queries, language, max_results)
    documents.extend(ddg_documents)
    
    # 2단계: DuckDuckGo 결과가 부족하면 Wikipedia 검색
    if len(documents) < 2:
        wiki_documents = search_wikipedia(queries, max_results)
        documents.extend(wiki_documents)
    
    return documents


def search_duckduckgo(
    queries: List[str],
    language: str = "ko",
    max_results: int = 5,
) -> List[Document]:
    """DuckDuckGo 검색 (Rate Limit 방지 포함)"""
    print(f"[START]search_service.search_duckduckgo({queries},{language},{max_results})")
    
    documents = []
    
    try:
        ddgs = DDGS()
        
        for i, query in enumerate(queries):
            try:
                # Rate Limit 방지를 위한 지연
                if i > 0:
                    delay = random.uniform(3, 6)  # 3-6초 지연
                    print(f"DuckDuckGo Rate Limit 방지를 위해 {delay:.1f}초 대기...")
                    time.sleep(delay)
                
                # 검색 수행
                results = ddgs.text(
                    query,
                    region=language,
                    safesearch="moderate",
                    timelimit="y",
                    max_results=max_results,
                )
                
                if results:
                    for result in results:
                        title = result.get("title", "")
                        body = result.get("body", "")
                        url = result.get("href", "")
                        
                        if body and len(body) > 50:  # 의미있는 내용만 포함
                            documents.append(
                                Document(
                                    page_content=body,
                                    metadata={
                                        "source": url,
                                        "section": "duckduckgo",
                                        "topic": title,
                                        "query": query,
                                    },
                                )
                            )
                    
                    print(f"DuckDuckGo에서 '{query}' 검색 완료: {len([d for d in documents if d.metadata.get('query') == query])}개")
                
            except Exception as e:
                print(f"DuckDuckGo 검색 실패 ({query}): {str(e)}")
                if "202" in str(e) or "ratelimit" in str(e).lower():
                    print("DuckDuckGo Rate Limit 감지, Wikipedia 검색으로 전환")
                    break  # Rate Limit 발생 시 중단
                continue
                
    except Exception as e:
        print(f"DuckDuckGo 검색 서비스 오류: {str(e)}")
    
    return documents


def search_wikipedia(
    queries: List[str],
    max_results: int = 5,
) -> List[Document]:
    """Wikipedia API 검색"""
    print(f"[START]search_service.search_wikipedia({queries},{max_results})")
    
    documents = []
    
    try:
        for query in queries:
            try:
                # Wikipedia API 검색
                search_url = f"https://ko.wikipedia.org/api/rest_v1/page/summary/{query}"
                response = requests.get(search_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'extract' in data and data['extract']:
                        documents.append(
                            Document(
                                page_content=data['extract'],
                                metadata={
                                    "source": data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                                    "section": "wikipedia",
                                    "topic": data.get('title', query),
                                    "query": query,
                                },
                            )
                        )
                        print(f"Wikipedia에서 '{query}' 검색 완료")
                
            except Exception as e:
                print(f"Wikipedia 검색 실패 ({query}): {str(e)}")
                continue
                
    except Exception as e:
        print(f"Wikipedia 검색 서비스 오류: {str(e)}")
    
    return documents
