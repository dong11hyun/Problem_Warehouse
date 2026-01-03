# E-Commerce Crawler Project Summary

> **프로젝트 전체 버전별 개발 과정 및 기술적 의사결정 기록**  
> 버전: v0.9 ~ v2.1 (총 6개 버전)

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택 총괄](#2-기술-스택-총괄)
3. [버전별 개발 히스토리](#3-버전별-개발-히스토리)
   - [v0.9 - 동기식 크롤러 (Sync Bot)](#v09---동기식-크롤러-sync-bot)
   - [v1.0 - 비동기 크롤러 (Async Bot)](#v10---비동기-크롤러-async-bot)
   - [v1.1 - 최적화 및 안정성 강화](#v11---최적화-및-안정성-강화)
   - [v1.2 - 분산 처리 아키텍처 (Celery + Redis)](#v12---분산-처리-아키텍처-celery--redis)
   - [v2.0 - 무신사 크롤러 + OpenSearch 파이프라인](#v20---무신사-크롤러--opensearch-파이프라인)
   - [v2.1 - 검색 엔진 API 서비스 구축](#v21---검색-엔진-api-서비스-구축)
4. [핵심 문제 해결 로그](#4-핵심-문제-해결-로그)
5. [아키텍처 진화 과정](#5-아키텍처-진화-과정)
6. [회고 및 교훈](#6-회고-및-교훈)

---

## 1. 프로젝트 개요

### 1.1 프로젝트 배경
이커머스 플랫폼에서 **판매자 메타데이터**(상호, 사업자번호, 연락처 등)를 수집하여 분석하는 데이터 파이프라인 구축 프로젝트입니다.

### 1.2 개발 여정

> 쿠팡 (v0.9 ~ v1.1) → ip차단(vpn) → 무신사 (v2.0 ~ v2.1)


| 단계 | 타겟 플랫폼 | 버전 | 결과 |
|------|-------------|------|------|
| 초기 개발 | 쿠팡 | v0.9 ~ v1.1 | 봇 탐지 시스템에 의해 IP 차단 |
| 아키텍처 고도화 | Books to Scrape (Sandbox) | v1.2 | 분산 처리 시스템 검증 |
| 타겟 변경 | 무신사 | v2.0 ~ v2.1 | 검색 엔진 서비스 구축 성공 |

### 1.3 핵심 성과
- **속도 개선**: 5건당 50초(Sync) → 5초(Async) 
- **안정성**: CSV 파일 충돌 → SQLite Batch → OpenSearch Bulk Insert
- **확장성**: 단일 스크립트 → Django + Celery + Redis 분산 처리
- **서비스화**: ETL 파이프라인 + FastAPI REST API + 웹 프론트엔드

---

## 2. 기술 스택 총괄

### 2.1 버전별 기술 스택 진화

| 구분 | v0.9 | v1.0 | v1.1 | v1.2 | v2.0 | v2.1 |
|------|------|------|------|------|------|------|
| **실행 방식** | Sync | Async | Async | Async + Celery | Async | Async |
| **브라우저** | Playwright CDP | Playwright CDP | Playwright CDP | Playwright | Playwright | Playwright |
| **데이터 저장** | CSV | CSV + Lock | SQLite Batch | Django ORM | OpenSearch | OpenSearch |
| **메시지 브로커** | - | - | - | Redis | - | - |
| **웹 프레임워크** | - | - | - | Django | - | FastAPI |
| **검색 엔진** | - | - | - | - | OpenSearch | OpenSearch |
| **컨테이너** | - | - | - | Docker (Redis) | Docker (OpenSearch) | Docker |

### 2.2 주요 라이브러리 의존성
```
# Core
playwright==1.56.0          # 브라우저 자동화
asyncio                      # 비동기 처리

# Backend Framework
Django==5.2.8               # 웹 프레임워크 (v1.2)
FastAPI                      # REST API (v2.1)
celery==5.5.3               # 분산 작업 큐 (v1.2)

# Database & Search
sqlite3                      # 로컬 DB (v1.1)
opensearch-py               # 검색 엔진 클라이언트 (v2.0+)
redis==7.1.0                # 메시지 브로커 (v1.2)

# Utilities
pandas                       # 데이터 처리
uvicorn                      # ASGI 서버
```

---

## 3. 버전별 개발 히스토리

---

### v0.9 - 동기식 크롤러 (Sync Bot)
```
`v0.9_sync_bot.py`
🔹목표
쿠팡 검색 결과에서 상품 목록과 판매자 정보를 수집하는 MVP(Minimum Viable Product) 개발

🔹아키텍처
[크롬 CDP 연결] → [검색 결과 수집] → [상세 페이지 순회] → [CSV 저장]
```

####  핵심 구현 사항

**1. Chrome DevTools Protocol (CDP) 연결**
```python
# 봇 탐지 회피를 위해 사용자가 직접 실행한 크롬에 연결
browser = p.chromium.connect_over_cdp("http://localhost:9222")
```
- **문제**: Playwright 기본 브라우저 사용 시 봇 탐지 차단
- **해결**: 사용자가 직접 실행한 크롬 브라우저에 기생하는 방식 
- **실행 방법**: `chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_temp"`

**2. XPath 기반 데이터 추출**
```python
# 고정된 라벨 텍스트를 기준으로 값 추출 (클래스명 변경 대비)
seller = page.locator("//th[contains(., '상호')]/following-sibling::td[1]").inner_text()
```

**3. 데이터 저장**
```python
def save_to_csv(data):
    with open(FILE_NAME, mode='a', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([...])
```

####  문제점
| 문제 | 원인 | 영향 |
|------|------|------|
| **느린 속도** | 동기식 처리 (순차 실행) | 5건당 약 50초 소요 |
| **봇 탐지 차단** | User-Agent, 행동 패턴 감지 | Access Denied 발생 |
| **동적 렌더링 이슈** | Lazy Loading 컨텐츠 | 판매자 정보 미로딩 |
| **새 탭 이슈** | `target="_blank"` 링크 | 크롤러가 새 탭 추적 실패 |

####  성능 지표
- **처리 속도**: 5건/50초 (10초/건)
- **안정성**: 낮음 (봇 탐지 빈번)
- **확장성**: 없음 (단일 프로세스)

---

### v1.0 - 비동기 크롤러 (Async Bot)
```
- `v1.0_async_bot.py`
🔹목표
동기식 처리의 성능 한계를 극복하고, 병렬 수집을 통한 속도 개선

🔹아키텍처 개선

                    ┌─ [Tab 1] → 상품 A 수집 ─┐
[URL 수집] → [분배] ─┼─ [Tab 2] → 상품 B 수집 ─┼→ [CSV 저장]
                    ├─ [Tab 3] → 상품 C 수집 ─┤
                    ├─ [Tab 4] → 상품 D 수집 ─┤
                    └─ [Tab 5] → 상품 E 수집 ─┘
                    
                    (Semaphore: 동시 5개 제한)
```

#### 💡 핵심 구현 사항

**1. 비동기 아키텍처 전환 (Sync → Async)**
```python
# v0.9 (동기)
from playwright.sync_api import sync_playwright
time.sleep(1)

# v1.0 (비동기)
from playwright.async_api import async_playwright
await asyncio.sleep(1)
```

**2. Semaphore를 활용한 동시성 제어**
```python
semaphore = asyncio.Semaphore(5)  # 동시 5개 탭 제한

async def process_product(context, prod, semaphore):
    async with semaphore:
        page = await context.new_page()
        # ... 수집 로직
```
- **이유**: 무제한 동시 접속 시 메모리 폭주 및 봇 탐지 위험 증가

**3. asyncio.gather를 활용한 병렬 실행**
```python
tasks = [process_product(context, prod, semaphore) for prod in product_list]
await asyncio.gather(*tasks)
```

**4. 리소스 차단을 통한 속도 최적화**
```python
await page.route("**/*", lambda route: route.abort() 
    if route.request.resource_type in ["image", "media", "font"] 
    else route.continue_())
```
- 이미지, 미디어, 폰트 로딩 차단 → 네트워크 대역폭 절약

**5. 파일 쓰기 충돌 방지 (asyncio.Lock)**
```python
file_lock = asyncio.Lock()

async def save_to_csv(data):
    async with file_lock:
        with open(FILE_NAME, mode='a', ...) as f:
            writer.writerow([...])
```

#### ⚠️ 발견된 문제점
| 문제 | 상세 | 해결 방향 |
|------|------|----------|
| **파일 충돌** | 여러 탭이 동시에 CSV 파일 접근 시 `PermissionError` | v1.1에서 DB 전환 |
| **쿠키 기반 차단** | 쿠팡이 쿠키에 신뢰점수를 부여하여 차단 | 쿠키 주기적 초기화 |
| **gather 한계** | 모든 작업 완료까지 대기해야 함 | v1.1에서 as_completed 전환 |

#### 📊 성능 지표
- **처리 속도**: 5건/5초 (**10배 개선**)
- **안정성**: 중간 (파일 충돌 가능성)
- **확장성**: 제한적 (단일 프로세스 내 병렬화)

---

### v1.1 - 최적화 및 안정성 강화

#### 📁 관련 파일
- `v1.1_async_bot.py`
- `프로젝트기록/v1.1_크롤링_속도개선.md`
- `프로젝트기록/v1.1_issue.md`

#### 🎯 목표
파일 I/O 병목 해소 및 대량 데이터 처리 안정성 확보

#### 🏗️ 아키텍처 개선
```
[수집 Worker Pool]
       │
       ▼
[메모리 Buffer] ──(10개 모이면)──→ [SQLite Batch Insert]
```

#### 💡 핵심 구현 사항

**1. CSV → SQLite DB 전환**
```python
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER,
            product_name TEXT,
            seller_name TEXT,
            biz_no TEXT,
            contact TEXT,
            url TEXT UNIQUE,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
```
- **장점**: 파일 잠금 충돌 해소, 중복 데이터 자동 처리 (`UNIQUE` 제약)

**2. Batch 저장 전략 (10건 단위)**
```python
def save_batch_to_db(batch_data):
    cursor.executemany('''
        INSERT OR REPLACE INTO sellers (rank, product_name, ...)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', batch_data)
    conn.commit()
```
- **장점**: 트랜잭션 오버헤드 감소, I/O 최적화

**3. asyncio.as_completed로 실시간 결과 처리**
```python
# v1.0: gather (일괄 대기)
await asyncio.gather(*tasks)

# v1.1: as_completed (완료 순 처리)
for future in asyncio.as_completed(tasks):
    result = await future
    if result:
        batch_buffer.append(result)
    
    if len(batch_buffer) >= 10:
        save_batch_to_db(batch_buffer)
        batch_buffer = []
```
- **장점**: 메모리 효율성 향상, 실시간 진행 상황 확인 가능

**4. 스마트 웨이팅 적용**
```python
# v1.0: 단순 존재 여부 확인
if await page.locator(...).count() > 0:

# v1.1: 타임아웃 기반 대기
await page.wait_for_selector(..., timeout=3000)
```

**5. 추가 리소스 차단**
```python
# v1.0: 이미지, 미디어, 폰트
# v1.1: + 스타일시트(CSS) 추가
if route.request.resource_type in ["image", "media", "font", "stylesheet"]
```

#### ⚠️ v1.1 차단 사건 (Critical)
```
📌 상황: VPN 적용 후 50건 수집 중 Access Denied 발생
📌 시도: 쿠키/캐시 삭제, 시크릿 모드 → 여전히 차단
📌 결론: IP 차단 + VPN 대역 전체 차단
```

**쿠팡 차단 매커니즘 분석**
```
1. 식별용 쿠키 발급
2. 이상 징후 감지 → 쿠키 신뢰점수 하락
3. 임계치 도달 → 세션 차단
4. VPN 대역 감지 → IP 대역 전체 차단
```

#### 📊 버전 비교표

| 구분 | v1.0 | v1.1 |
|------|------|------|
| **저장소** | CSV 파일 | SQLite DB |
| **저장 방식** | 1건씩 (Lock) | 10건씩 (Batch) |
| **속도 최적화** | 이미지/폰트 차단 | + CSS 차단, 대기 0.5초 |
| **병렬 처리** | `gather` | `as_completed` |
| **안정성** | 파일 충돌 가능 | DB 트랜잭션 안전 |

---

### v1.2 - 분산 처리 아키텍처 (Celery + Redis)

#### 📁 관련 파일
- `config/celery.py`
- `config/settings.py`
- `crawler/tasks.py`
- `crawler/models.py`
- `프로젝트기록/v1.2_celery_etl_redis.md`
- `docker-compose.yml` (Redis용)

#### 🎯 목표
- 쿠팡 차단으로 인한 타겟 변경 (Books to Scrape 샌드박스 환경)
- 확장 가능한 분산 처리 시스템 아키텍처 검증
- 웹 서버와 크롤링 워커 분리

#### 🏗️ 아키텍처 (Producer-Consumer 패턴)
```
┌─────────────────────────────────────────────────────────────┐
│                        [User/Admin]                          │
│                              │                               │
│                              ▼                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              Django Web Server (Producer)                │ │
│ │  - Task 발행: start_book_crawler.delay()                 │ │
│ │  - 데이터 조회: Django Admin                             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                              │                               │
│                    Publish Task (Message)                    │
│                              │                               │
│                              ▼                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              Redis (Message Broker)                      │ │
│ │  - In-Memory 고속 메시지 큐                               │ │
│ │  - Port: 6379                                            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                              │                               │
│                    Consume Task                              │
│                              │                               │
│                              ▼                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              Celery Worker (Consumer)                    │ │
│ │  - Playwright 비동기 크롤링                               │ │
│ │  - Django ORM으로 DB 저장                                 │ │
│ └─────────────────────────────────────────────────────────┘ │
│                              │                               │
│                              ▼                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │              SQLite / Database                           │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 💡 핵심 구현 사항

**1. Celery 설정 (config/celery.py)**
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

**2. Django 설정 연동 (settings.py)**
```python
INSTALLED_APPS = [
    ...
    'crawler',
    'django_celery_results',
]

# Celery 설정
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = 'Asia/Seoul'
```

**3. Celery Task 정의 (crawler/tasks.py)**
```python
from celery import shared_task
from playwright.async_api import async_playwright
import asyncio
from asgiref.sync import sync_to_async

@shared_task
def start_book_crawler():
    """Django에서 호출하는 진입점"""
    asyncio.run(crawl_books_logic())
    return "책 수집 작업 완료"

async def crawl_books_logic():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # ... 크롤링 로직
        
        # Django ORM 비동기 호출
        await sync_to_async(Book.objects.update_or_create)(
            url=clean_url,
            defaults={'title': title, 'price': price, ...}
        )
```

**4. Django Model 정의 (crawler/models.py)**
```python
class Book(models.Model):
    title = models.CharField(max_length=500)
    price = models.CharField(max_length=50)
    rating = models.CharField(max_length=50)
    stock = models.CharField(max_length=50)
    url = models.URLField(unique=True)
    crawled_at = models.DateTimeField(auto_now=True)
```

#### ⚠️ Windows 환경 이슈 해결
```
📌 문제: Celery 4.x + Windows에서 prefork 풀 충돌
📌 증상: 프로세스 멈춤, multiprocessing 에러
📌 해결: solo 풀 모드 사용
```

```bash
# Windows 환경 실행 명령
celery -A config worker -l info -P solo
```

#### 🐳 Docker 인프라
```yaml
# docker-compose.yml (Redis)
version: '3'
services:
  redis:
    image: redis
    ports:
      - "6379:6379"
```

#### 📊 성능 지표
- **확장성**: 워커 수평 확장 가능 (여러 서버에 분산)
- **안정성**: 웹 서버 부하와 크롤링 작업 분리
- **모니터링**: Django Admin을 통한 실시간 데이터 확인

---

### v2.0 - 무신사 크롤러 + OpenSearch 파이프라인

#### 📁 관련 파일
- `v2.0_musinsa.py`
- `init_opensearch.py`
- `docker-compose.yml`
- `프로젝트기록/v2.0_musinsa_project.md`

#### 🎯 목표
- 쿠팡 차단으로 인한 타겟 변경 (무신사)
- RDBMS 한계 극복을 위한 검색 엔진(OpenSearch) 도입
- 한국어 형태소 분석기 적용

#### 🏗️ 아키텍처
```
┌─────────────────────────────────────────────────────────────┐
│                    [무신사 웹사이트]                          │
│                           │                                  │
│                 (1. 비동기 수집: Playwright)                  │
│                           │                                  │
│                           ▼                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │            데이터 전처리 (ETL Worker)                     │ │
│ │  - HTML 파싱 (Meta Tag & XPath 활용)                     │ │
│ │  - 데이터 정제 (가격 숫자 변환, 불용어 처리)                 │ │
│ │  - 구조화 (JSON Serialize)                               │ │
│ └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                 (2. Bulk Insert)                             │
│                           │                                  │
│                           ▼                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │     OpenSearch (Docker Container) + Nori Analyzer        │ │
│ │  - 역색인(Inverted Index) 기반 전문 검색                  │ │
│ │  - 한국어 복합명사 분리 (여성패딩 → 여성, 패딩)             │ │
│ └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                 (3. 시각화 및 모니터링)                       │
│                           │                                  │
│                           ▼                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │            OpenSearch Dashboards (Port: 5601)            │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 💡 MySQL vs OpenSearch 비교

| 특징 | MySQL (RDBMS) | OpenSearch (NoSQL/검색엔진) |
|------|---------------|----------------------------|
| **주요 목적** | 데이터 저장, 수정, 삭제, 무결성 | 빠른 검색, 대용량 로그 분석 |
| **데이터 구조** | 테이블 (행/열) | 문서 (JSON Document) |
| **검색 능력** | 정확한 값 찾기에 유리 | 전문 검색, 유사도 검색, 오타 보정 |
| **속도** | 복잡한 검색 시 느려짐 | 대용량에서도 매우 빠름 |
| **트랜잭션** | 지원 (ACID) | 미지원 (Eventual Consistency) |

#### 💡 핵심 구현 사항

**1. OpenSearch 인덱스 설정 (init_opensearch.py)**
```python
index_body = {
    "settings": {
        "index": {
            "analysis": {
                "tokenizer": {
                    "nori_user_dict": {
                        "type": "nori_tokenizer",
                        "decompound_mode": "mixed"  # 합성어 분리
                    }
                },
                "analyzer": {
                    "korean_analyzer": {
                        "type": "custom",
                        "tokenizer": "nori_user_dict"
                    }
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "title": {"type": "text", "analyzer": "korean_analyzer"},
            "brand": {"type": "keyword"},  # 정확 일치용
            "price": {"type": "integer"}   # 범위 검색용
        }
    }
}
```

**2. 동적 클래스명 대응 전략**
```python
# 문제: CSS 클래스명이 랜덤 생성 (sc-m8pxwf-2)
# 해결 1: Meta Tag 활용
title = await page.locator("meta[property='og:title']").first.get_attribute("content")

# 해결 2: XPath Relative Query (라벨 기준 상대 위치)
async def get_value(label):
    locator = page.locator(f"//dt[contains(., '{label}')]/following-sibling::dd[1]")
    if await locator.count() > 0:
        return await locator.inner_text()
    return ""
```

**3. Playwright Strict Mode 대응**
```python
# 문제: 동일 속성 태그 2개 이상 시 에러
# "resolved to 2 elements"

# 해결: .first 체이닝
title_loc = page.locator("meta[property='og:title']").first
title = await title_loc.get_attribute("content")
```

**4. 판매자 정보 아코디언 처리**
```python
# 숨겨진 판매자 정보 펼치기
seller_btn = page.locator("button", has_text="판매자 정보")
if await seller_btn.count() > 0:
    expanded = await seller_btn.get_attribute("aria-expanded")
    if expanded != "true":
        await seller_btn.click()
        await asyncio.sleep(0.5)
```

**5. Bulk Insert를 통한 효율적 적재**
```python
from opensearchpy import helpers

docs = []
for url in url_list:
    doc = {
        "_index": INDEX_NAME,
        "_source": {
            "url": url,
            "title": title,
            "brand": brand,
            "price": price,
            "seller_info": {...}
        }
    }
    docs.append(doc)

# 한 번에 밀어넣기
success, failed = helpers.bulk(client, docs)
```

#### 🐳 Docker 인프라 (OpenSearch + Dashboards)
```yaml
version: '3'
services:
  opensearch-node:
    image: opensearchproject/opensearch:2.11.0
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
    ports:
      - "9200:9200"  # REST API

  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:2.11.0
    ports:
      - "5601:5601"  # Web UI
    environment:
      OPENSEARCH_HOSTS: '["http://opensearch-node:9200"]'
```

#### ⚠️ 발견된 문제 및 해결

**Dashboards 데이터 미표시 이슈**
```
📌 문제: 데이터 적재 로그는 Success인데 Discover에서 안 보임
📌 원인: 기본 필터가 "Last 15 minutes"로 설정됨
📌 해결: 
  1. Index Pattern 생성 시 created_at 필드를 Time Filter로 지정
  2. 조회 범위를 Last 24 Hours로 확장
```

---

### v2.1 - 검색 엔진 API 서비스 구축

#### 📁 관련 파일
- `v2.1_musinsa.py`
- `api_server.py`
- `index.html`
- `프로젝트기록/v2.1_musinsa.md`

#### 🎯 목표
End-to-End 검색 서비스 구축 (크롤링 → 저장 → API → 웹 UI)

#### 🏗️ 아키텍처
```
┌─────────────────────────────────────────────────────────────┐
│     [무신사 웹사이트]                                         │
│            │                                                 │
│            │ (1. 비동기 수집: Playwright)                     │
│            ▼                                                 │
│     [데이터 전처리 Worker]                                    │
│            │                                                 │
│            │ (2. Bulk Insert)                                │
│            ▼                                                 │
│     [OpenSearch + Nori]                                      │
│            │                                                 │
│            │ (3. Search Query)                               │
│            ▼                                                 │
│     [FastAPI Server] ─────────────────────────               │
│            │                      │                          │
│            │ REST API             │ Swagger UI               │
│            │                      │                          │
│            ▼                      ▼                          │
│     [Web Frontend]        [API Docs]                         │
│     (index.html)          (/docs)                            │
└─────────────────────────────────────────────────────────────┘
```

#### 💡 핵심 구현 사항

**1. FastAPI 서버 구축 (api_server.py)**
```python
from fastapi import FastAPI, Query
from opensearchpy import OpenSearch
from pydantic import BaseModel

app = FastAPI(
    title="Musinsa Search Engine",
    description="무신사 크롤링 데이터를 검색하는 API입니다.",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Pydantic 스키마 정의**
```python
class SellerInfo(BaseModel):
    company: str
    brand: str
    contact: Optional[str] = None

class ProductSchema(BaseModel):
    title: str
    brand: str
    price: int
    url: str
    seller_info: Optional[SellerInfo] = None
```

**3. 검색 API 엔드포인트**
```python
@app.get("/search", response_model=List[ProductSchema])
def search_products(
    keyword: str = Query(..., description="검색할 상품명"),
    min_price: int = Query(None, description="최소 가격"),
    max_price: int = Query(None, description="최대 가격")
):
    search_query = {
        "query": {
            "bool": {
                "must": [{
                    "multi_match": {
                        "query": keyword,
                        "fields": ["title^2", "brand"],  # 제목 가중치 2배
                        "analyzer": "nori"
                    }
                }],
                "filter": []
            }
        }
    }
    
    # 가격 범위 필터
    if min_price or max_price:
        price_range = {"range": {"price": {}}}
        if min_price: price_range["range"]["price"]["gte"] = min_price
        if max_price: price_range["range"]["price"]["lte"] = max_price
        search_query["query"]["bool"]["filter"].append(price_range)
    
    response = client.search(body=search_query, index=INDEX_NAME)
    return [hit["_source"] for hit in response["hits"]["hits"]]
```

**4. 웹 프론트엔드 (index.html)**
```javascript
async function doSearch() {
    const keyword = document.getElementById('keyword').value;
    
    // FastAPI 서버 호출
    const response = await fetch(`http://127.0.0.1:8000/search?keyword=${keyword}`);
    const data = await response.json();
    
    // 결과 렌더링
    data.forEach(item => {
        const html = `
            <a href="${item.url}" target="_blank">
                <div class="card">
                    <div class="card-brand">${item.brand}</div>
                    <h3 class="card-title">${item.title}</h3>
                    <div class="card-price">${item.price.toLocaleString()}원</div>
                </div>
            </a>
        `;
        resultDiv.innerHTML += html;
    });
}
```

#### ⚠️ 데이터 정합성 이슈 해결

```
📌 문제: API 500 에러 발생
📌 원인: 크롤러에서 brand, price 필드 누락 → Pydantic 검증 실패
📌 해결:
  1. OpenSearch Mapping과 Pydantic Schema 일치시킴
  2. 크롤러에서 필드 누락 시 기본값 할당
```

---

## 4. 핵심 문제 해결 로그

### 4.1 봇 탐지 차단 문제 (v0.9 ~ v1.1)

| 시도 | 방법 | 결과 |
|------|------|------|
| 1차 | User-Agent 변경 | ❌ 실패 |
| 2차 | Referer 헤더 조작 | ❌ 실패 |
| 3차 | playwright-stealth 라이브러리 | ❌ 실패 |
| 4차 | **Chrome CDP (기생 모드)** | ✅ 성공 |

**최종 해결책**: 사용자가 직접 실행한 크롬 브라우저에 Playwright가 연결
```bash
# 크롬 디버깅 모드 실행
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_temp"
```

### 4.2 동적 렌더링 및 새 탭 이슈 (v0.9)

| 문제 | 원인 | 해결책 |
|------|------|--------|
| 판매자 정보 미로딩 | Lazy Loading | `mouse.wheel` + `keyboard.press("End")` |
| 새 탭에서 봇 이탈 | `target="_blank"` | URL 수집 후 직접 이동 방식 |

### 4.3 파일 동시 쓰기 충돌 (v1.0 → v1.1)

```python
# v1.0: asyncio.Lock() - 여전히 PermissionError 가능
async with file_lock:
    with open(FILE_NAME, ...) as f:

# v1.1: SQLite DB 전환 + Batch Insert
def save_batch_to_db(batch_data):
    cursor.executemany('''
        INSERT OR REPLACE INTO sellers (...)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', batch_data)
```

### 4.4 쿠팡 최종 차단 사건 (v1.1)

```
📅 시점: v1.1 VPN 적용 후 50건 수집 중
📌 증상: Access Denied
📌 시도: 쿠키 삭제, 시크릿 모드 → 여전히 차단
📌 결론: IP 차단 + VPN 서버 대역 전체 차단
📌 결정: 타겟 변경 (쿠팡 → 무신사)
```

**쿠팡 보안 매커니즘 분석**
```
1. 식별용 쿠키 발급
2. 이상 행동 감지 → 신뢰점수 하락
3. 세션/쿠키 차단 (IP는 유지 - 다수 사용자 고려)
4. 반복 시 IP 차단 → VPN 감지 시 대역 차단
```

### 4.5 동적 클래스명 대응 (v2.0)

```python
# 문제: 클래스명이 배포마다 변경 (sc-m8pxwf-2)

# 해결 1: 불변하는 Meta Tag 활용
title = await page.locator("meta[property='og:title']").first.get_attribute("content")

# 해결 2: XPath Relative Query
locator = page.locator(f"//dt[contains(., '{label}')]/following-sibling::dd[1]")
```

### 4.6 Playwright Strict Mode Violation (v2.0)

```python
# 문제: "resolved to 2 elements" 에러

# 해결: .first 명시적 선택
title_loc = page.locator("meta[property='og:title']").first
```

---

## 5. 아키텍처 진화 과정

### 5.1 데이터 저장소 진화
```
CSV 파일 (v0.9, v1.0)
     │
     │ 파일 충돌 문제
     ▼
SQLite DB + Batch (v1.1)
     │
     │ 검색 기능 한계
     ▼
Django ORM (v1.2)
     │
     │ 전문 검색 요구
     ▼
OpenSearch (v2.0, v2.1)
```

### 5.2 처리 방식 진화
```
Sync (v0.9)
  │
  │ 10배 성능 개선 필요
  ▼
Async + Semaphore (v1.0)
  │
  │ 실시간 처리 필요
  ▼
Async + as_completed + Batch (v1.1)
  │
  │ 웹 서버 분리 필요
  ▼
Celery + Redis (v1.2)
```

### 5.3 서비스 형태 진화
```
스크립트 (v0.9 ~ v1.1)
     │
     │ 관리 기능 필요
     ▼
Django Admin (v1.2)
     │
     │ API 서비스 필요
     ▼
FastAPI + Web UI (v2.1)
```

---

## 6. 회고 및 교훈

### 6.1 기술적 교훈

| 영역 | 교훈 |
|------|------|
| **봇 탐지 회피** | 라이브러리 수준의 회피는 한계가 있음. 실제 사용자 브라우저 세션을 활용하는 것이 효과적 |
| **비동기 프로그래밍** | `asyncio.gather` vs `as_completed` - 실시간 처리 필요 여부에 따라 선택 |
| **데이터 저장** | 대량 데이터는 Batch 처리가 필수. 파일보다 DB, DB보다 검색 엔진 |
| **확장성 설계** | 초기부터 Producer-Consumer 패턴을 고려하면 나중에 확장이 쉬움 |

### 6.2 아키텍처 설계 교훈

```
"단순 기능 구현"을 넘어 "시스템 설계"의 중요성
```

- 초기: 단순 스크립트로 시작
- 중기: 차단, 성능, 안정성 문제 직면
- 현재: 분산 처리 + 검색 엔진 + REST API 아키텍처

### 6.3 프로젝트 결정 사항

| 결정 | 이유 | 결과 |
|------|------|------|
| **CDP 방식 도입** | 일반 방법으로는 봇 탐지 회피 불가 | 쿠팡 일시적 수집 성공 |
| **타겟 변경 (쿠팡 → 무신사)** | IP 차단 + VPN 대역 차단 | 안정적 수집 환경 확보 |
| **OpenSearch 도입** | RDBMS의 전문 검색 한계 | 고속 검색 서비스 구축 |
| **FastAPI 선택** | Django보다 빠른 API 개발 | 실시간 검색 API 구축 |

### 6.4 향후 개선 계획

1. **Airflow 도입**: 주기적 자동 수집 스케줄링
2. **Fuzzy Search**: 오타 교정 검색 기능
3. **Synonym 사전**: 동의어 검색 지원
4. **Kibana 대시보드**: 브랜드별 상품 수, 가격대 분포 시각화
5. **Redis 캐싱**: 검색 결과 캐싱으로 응답 속도 개선

---

## 📎 부록: 실행 가이드

### A. 크롬 디버깅 모드 실행
```bash
# Windows
chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\chrome_debug_temp"
```

### B. OpenSearch 환경 구성
```bash
# 컨테이너 실행
docker-compose up -d

# Nori 분석기 설치 (최초 1회)
docker exec -it opensearch-node ./bin/opensearch-plugin install analysis-nori
docker-compose restart

# 인덱스 초기화
python init_opensearch.py
```

### C. 데이터 수집 및 API 실행
```bash
# 데이터 수집 (v2.1)
python v2.1_musinsa.py

# API 서버 실행
python api_server.py

# 웹 UI 접속
# index.html 파일을 브라우저로 열기
```

### D. Celery 환경 실행 (v1.2)
```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker (Windows)
celery -A config worker -l info -P solo

# Terminal 3: Task 실행
python manage.py shell
>>> from crawler.tasks import start_book_crawler
>>> start_book_crawler.delay()
```

---

> **문서 작성**: Senior Developer Level  
> **마지막 업데이트**: 2026-01-03  
> **프로젝트 기간**: 2025-11 ~ 2026-01 (약 2개월)
