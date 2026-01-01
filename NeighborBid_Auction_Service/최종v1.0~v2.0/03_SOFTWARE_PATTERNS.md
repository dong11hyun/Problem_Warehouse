# [Architecture] 유지보수성을 높이는 소프트웨어 패턴의 적용

> 좋은 코드는 기능 구현을 넘어, 유지보수가 쉽고 확장에 열려 있어야 합니다. 이 문서는 A1_NeighborBid_Auction 프로젝트에 적용된 주요 **디자인 패턴(Design Pattern)**과 **아키텍처 패턴**을 소개합니다.

## 1. 서비스 계층 패턴 (Service Layer Pattern)

초기 개발 단계에서는 Django의 관행대로 `views.py`에 비즈니스 로직을 작성했습니다. 하지만 입찰 로직이 복잡해지면서 View가 너무 비대해지는 **'Fat View'** 현상이 발생했습니다.

### 1.1 적용 전 (Fat View) vs 적용 후 (Thin View)

*   **Before:** View에서 유효성 검사, DB 조회, 결제 처리, 알림 발송을 모두 수행. 코드가 200줄이 넘어가며 가독성이 떨어짐.
*   **After:** 비즈니스 로직을 `services.py`로 격리. View는 단순히 요청을 받아 Service에 넘기고, 결과만 받아 응답하는 역할에 집중.

```python
# auctions/views.py (깔끔해진 통제탑)
def bid_view(request, auction_id):
    try:
        # 복잡한 로직은 service 함수 하나로 캡슐화
        msg = AuctionService.place_bid(auction_id, request.user, amount)
        return JsonResponse({'status': 'success', 'msg': msg})
    except ValueError as e:
        return JsonResponse({'status': 'fail', 'msg': str(e)})
```

이 패턴의 도입으로 `place_bid` 로직을 **HTTP View**에서도 호출하고, **WebSocket Consumer**에서도 재사용할 수 있게 되었습니다. **(코드 재사용성 100% 증가)**

---

## 2. 옵저버 패턴 (Observer Pattern in WebSocket)

실시간 경매 시스템은 본질적으로 **옵저버 패턴**의 구현체입니다.

*   **Subject (주체):** `Auction` (경매 물품)
*   **Observer (구독자):** 경매 페이지를 보고 있는 `User Clients`

Django Channels의 `Group` 기능이 이 패턴을 인프라 레벨에서 지원합니다.

1.  **구독(Subscribe):** 클라이언트가 `ws://auction/1/`에 접속하면, 채널 레이어가 해당 소켓을 `group_1` 리스트에 등록합니다.
2.  **통지(Notify):** 상태가 변하면(누군가 입찰하면), 주체는 루프를 돌며 `group_1`에 속한 모든 소켓에게 `message`를 발행(Publish)합니다.

이 패턴 덕분에 입찰자 A는 다른 입찰자 B, C, D의 존재를 모르더라도(Loosely Coupled), 데이터 변경 사항을 실시간으로 전달받을 수 있습니다.

---

## 3. 리버스 프록시 패턴 (Reverse Proxy Pattern - API Gateway)

프로덕션 환경을 모사하기 위해 `Nginx`를 웹 서버 앞단에 배치했습니다.

```mermaid
graph LR
    User --> Nginx[Nginx (Reverse Proxy)]
    Nginx -->|/static| StaticFiles[정적 파일]
    Nginx -->|/ws| Daphne[ASGI Server]
    Nginx -->|/| Gunicorn[WSGI Server]
```

*   **부하 분산:** 정적 파일(이미지, CSS) 요청이 Python 애플리케이션까지 도달하지 않고 Nginx에서 즉시 처리되어 서버 부하를 줄였습니다.
*   **라우팅:** 외부에서는 하나의 포트(80)로 접속하지만, 내부적으로는 URL 패턴에 따라 동기 서버(8000)와 비동기 서버(8001)로 트래픽을 교통 정리합니다.

---

## 4. 트랜잭션 스크립트 패턴 (Transaction Script Pattern)

복잡한 도메인 모델(DDD)을 도입하기보다, 절차지향적이지만 직관적인 **트랜잭션 스크립트** 패턴을 적극 활용했습니다.

*   `place_bid`, `buy_now`, `close_auction` 등 하나의 트랜잭션 단위가 하나의 함수로 명확하게 정의되어 있습니다.
*   스타트업이나 MVP(Minimum Viable Product) 단계처럼 빠른 기능 구현과 명확한 흐름 파악이 중요할 때 매우 효과적인 패턴임을 확인했습니다.

---

## 5. 결론

패턴을 위한 패턴은 지양했습니다.
**"코드를 재사용하고 싶다"**는 욕구가 **서비스 레이어**를 불렀고, **"실시간으로 알리고 싶다"**는 요구사항이 **옵저버 패턴**을 불렀습니다. 문제 해결을 위해 자연스럽게 도출된 이 구조들은 프로젝트의 유지보수성을 한 단계 끌어올렸습니다.

> **작성자:** A1_NeighborBid_Auction 백엔드 개발팀
> **관련 문서:** [04_TRIALS_AND_ERRORS.md](file:///c:/A1_NeighborBid_Auction/04_TRIALS_AND_ERRORS.md)
