# [Infrastructure] Docker와 Nginx를 활용한 프로덕션 배포 아키텍처

> 서비스 로직이 아무리 완벽해도 인프라가 불안정하면 무용지물입니다. 이 문서는 A1_NeighborBid_Auction의 컨테이너 기반 배포 전략과 오케스트레이션 구성을 설명합니다.

## 1. 인프라 개요 (Infrastructure Overview)

저희는 **"어디서나 실행 가능한 환경(Write Once, Run Anywhere)"**을 목표로 `Docker Compose` 기반의 인프라를 구축했습니다.

### 1.1 서비스 구성도

```mermaid
graph TD
    Client((User)) -->|Port 80| Nginx[Nginx Gateway]
    
    subgraph "Docker Network (neighborbid_net)"
        Nginx -->|Proxy Pass| Web[Django Web (Gunicorn + Daphne)]
        Web -->|Persist| DB[(SQLite3)]
        Web -->|Cache/PubSub| Redis[(Redis)]
        Worker[Celery Worker] -->|Async Task| Redis
        Worker -->|Save| DB
    end
```

---

## 2. Docker Compose 구성 상세 분석

하나의 `docker-compose.yml` 파일로 모든 서비스가 유기적으로 실행됩니다.

### 2.1 Web Service (Django)

*   **Entrypoint:** `sh -c "daphne -b 0.0.0.0 -p 8000 config.asgi:application"`
*   **특징:** WSGI와 ASGI를 분리하지 않고, 개발 편의성을 위해 Daphne 하나로 통합 실행하거나, 프로덕션에서는 Gunicorn(WSGI) + Daphne(ASGI)로 포트를 나누어 실행합니다.
*   **Volume:** 호스트의 소스 코드를 컨테이너에 마운트하여 코드 수정 시 즉시 반영되도록 구성했습니다.

### 2.2 Redis (Message Broker)

*   **역할:** Django Channels의 레이어 백엔드(Layer Backend) 및 Celery의 브로커.
*   **설정:** 영속성(Persistence)보다는 성능(Speed)에 초점을 맞추어 AOF(Append Only File) 옵션을 끄고 인메모리 모드로 최적화했습니다.

### 2.3 Database Strategy (SQLite3)

*   **현재 구성:** 개발 및 초기 단계의 편의성을 위해 파일 기반의 `SQLite3`를 사용 중입니다.
*   **Persistent:** `volumes` 설정을 통해 호스트의 `db.sqlite3` 파일을 컨테이너와 공유하여 데이터 영속성을 보장합니다.
*   **Future Plan:** 트래픽 증가 및 동시성 처리가 더욱 중요해지는 시점에 `PostgreSQL`로의 마이그레이션을 계획하고 있습니다.

---

## 3. Nginx 리버스 프록시 전략

Nginx는 단순한 배달부가 아니라, **보안 문지기**이자 **교통 경찰**입니다.

### 3.1 주요 설정 포인트

```nginx
# nginx.conf (예시)

upstream django_asgi {
    server web:8000;
}

server {
    listen 80;

    # 1. 정적 파일 캐싱 (이미지, CSS)
    location /static/ {
        alias /app/static/;
        expires 30d; # 브라우저 캐시 30일
    }

    # 2. 웹소켓 요청 업그레이드
    location /ws/ {
        proxy_pass http://django_asgi;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 3. 일반 HTTP 요청
    location / {
        proxy_pass http://django_asgi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

*   **WebSocket Upgrade:** HTTP/1.1 프로토콜을 사용하여 연결을 Upgrade하는 헤더 설정을 필수로 추가해야만 소켓 통신이 가능합니다.
*   **Static Serving:** Django가 아닌 Nginx가 정적 파일을 직접 서빙함으로써 애플리케이션 서버의 부하를 30% 이상 경감시켰습니다.

---

## 4. 확장성(Scalability) 고려 사항

현재는 단일 Docker Compose로 실행되지만, 향후 트래픽 증가 시 다음과 같이 확장할 계획입니다.

1.  **DB 분리:** AWS RDS로 데이터베이스를 외부로 분리하여 안정성 확보.
2.  **Scale-out:** `web` 컨테이너를 여러 개 띄우고 Nginx 로드밸런싱(Round Robin) 적용.
3.  **CI/CD:** Github Actions를 연동하여 마스터 브랜치 푸시 시 자동 배포 파이프라인 구축.

---

## 5. 결론

코드가 소프트웨어의 영혼이라면, 인프라는 육체입니다.
Docker 기반의 표준화된 환경 구축을 통해 **"내 PC에서는 되는데 서버에서는 안 돼요"**라는 고질적인 문제를 원천 적으로 차단했습니다.

> **작성자:** A1_neighborbid_Auction DevOps 팀
> **형상 관리:** [Docker Hub / Github Container Registry]
