# [QA] 무결점 서비스를 위한 테스트 전략 (Testing Strategy)

> "테스트 없는 코드는 빚이다."
> 금융 성격을 띤 경매 시스템에서 버그는 곧 금전적 피해로 이어집니다. 이 문서는 A1_NeighborBid_Auction의 안정성을 검증하기 위해 수행한 **단위 테스트, 통합 테스트, 그리고 동시성 부하 테스트** 시나리오를 기술합니다.

## 1. 테스트 피라미드 (Test Pyramid)

저희 팀은 빠른 피드백을 위해 **단위 테스트**의 비중을 높이고, 핵심 시나리오에 대해 **통합 테스트**를 수행하는 전략을 취했습니다.

*   **Unit Test (70%):** Model 메서드, Service 함수 개별 검증
*   **Integration Test (20%):** View ~ Service ~ DB 간의 연동 검증
*   **Load/Concurrency Test (10%):** 다수 사용자의 동시 입찰 시뮬레이션

---

## 2. 단위 테스트: 비즈니스 로직 검증

가장 중요한 `place_bid` 함수의 검증 케이스입니다. `TestCase` 클래스를 상속받아 시나리오별로 테스트를 작성했습니다.

### 2.1 주요 테스트 케이스 (TC)

| TC ID | 시나리오 | 예상 결과 | 비고 |
| :--- | :--- | :--- | :--- |
| **TC-001** | 정상 입찰 | 입찰 레코드 생성, Wallet 잔액 차감, Locked 잔액 증가 | Happy Path |
| **TC-002** | 잔액 부족 입찰 | `ValueError` 발생, 잔액 변동 없음 | 예외 처리 |
| **TC-003** | 마감된 경매 입찰 | `ValueError` 발생 | 상태 체크 |
| **TC-004** | 낮은 금액 재입찰 | `ValueError` 발생 (현재가 + 단위보다 낮음) | 룰 검증 |
| **TC-005** | 상위 입찰 발생 시 환불 | 이전 1등의 Locked 잔액 감소, Balance 증가 | **가장 중요** |

---

## 3. 동시성 테스트 (Concurrency Stress Test)

일반적인 테스트로는 잡을 수 없는 **Race Condition**을 검증하기 위해 특수한 테스트 환경을 구축했습니다.

### 3.1 도구 및 시나리오

*   **JMeter / Python Threading:** 100~1,000명의 가상 유저(Virtual User) 생성
*   **시나리오:** 인기 아이폰 경매 시작과 동시에 100명이 0.01초 간격으로 동일 금액 입찰 시도 & 금액 상향 입찰 시도.

### 3.2 테스트 코드 예시 (개념적 코드)

```python
import threading
from django.test import TransactionTestCase

class RaceConditionTest(TransactionTestCase):
    def test_concurrent_bidding(self):
        def bid_request():
            place_bid(auction_id, user, amount)

        threads = []
        # 10개의 스레드가 동시에 입찰 시도
        for _ in range(10):
            t = threading.Thread(target=bid_request)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
            
        # 검증: 입찰은 10번 시도했으나, 유효한 최종 입찰은 1건이어야 함
        # 검증: 지갑 잔액이 정확하게 맞아야 함 (이중 차감 X)
```

이 테스트를 통과하지 못하면 해당 코드는 머지(Merge)되지 않도록 엄격하게 관리했습니다.

---

## 4. 수동 검증 프로세스 (Manual QA)

자동화 테스트가 놓칠 수 있는 **UX 이슈**를 잡기 위해 배포 전 체크리스트를 수행합니다.

1.  **WebSocket 연결:** 네트워크를 끊었다 붙였을 때 재연결(Reconnection)이 잘 되는가?
2.  **알림 UX:** 낙찰 성공 시, 유찰 시 알림이 팝업으로 적절히 뜨는가?
3.  **반응 속도:** 입찰 버튼 클릭 후 화면 갱신까지의 지연 시간(Latency) 체감 확인.

---

## 5. 결론

완벽한 테스트는 없지만, **"가장 치명적인 실패"**를 예방하는 테스트는 필수입니다.
저희는 특히 **'돈(Wallet)'**과 관련된 로직에 대해서는 편집증에 가까울 정도로 반복적인 테스트를 수행하여, 오픈 이후 무사고 시스템을 운영할 수 있었습니다.

> **작성자:** A1_NeighborBid_Auction QA팀
> **관련 문서:** [01_DATABASE_DESIGN_DEEP_DIVE.md](file:///c:/A1_NeighborBid_Auction/01_DATABASE_DESIGN_DEEP_DIVE.md)
