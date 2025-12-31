## 컨슈머 코드리뷰

`import AsyncWebsocketConsumer`: Django Channels가 제공하며, 비동기(Async) 방식으로 웹소켓을 처리합니다. ``connect, receive, disconnect` 같은 메서드 제공

`from channels.db import database_sync_to_async` : 비동기 환경에서 동기 함수를 실행할 수 있도록 합니다. (Django의 ORM(데이터베이스 접근)은 기본적으로 동기) 

`await` : **비동기 함수내에서 해당 작업을 수행하면서(현재 코루틴의 실행을 멈추고 이벤트 루프에 제어권을 넘기는 동작), 다른 작업도 가능하게 합니다.**

>Django Channels 환경에서는 이벤트 루프를 개발자가 직접 관리하지 않고,
>ASGI 서버(Uvicorn, Daphne)가 생성, 실행하며,
> 각 요청은 이벤트 루프에 등록된 코루틴으로 처리됩니다.

> 코루틴은 async 함수로 정의되며, 실행 도중 await 지점에서 중단되었다가
> 이벤트 루프에 의해 다시 실행될 수 있는 비동기 실행 단위

`result_msg = await self.save_bid(self.auction_id, user, amount)` : DB저장은 동기 실행이 기본이므로, 변환 데코레이터를 사용하여 비동기로 실행합니다.
```
 (비동기 래퍼) DB에 입찰 저장하는 함수 호출
    @database_sync_to_async
    def save_bid(self, auction_id, user, amount):
    ...
```
>DB 작업은 반드시 이 변환기를 거쳐서 별도 스레드로 격리해야 서버가 멈추지 않는다

---
## Redis 는 어디서 쓰이는가?

`self.channel_layer.group_add` : channel_layer 메서드를 호출하는 순간 내부적으로 Redis 명령어가 실행됩니다. 

---

- type 함수 (현재 2가지 기능으로 썼다.)
> 'type'에 적힌 문자열과 이름이 똑같은 메서드를 자동으로 찾아서 실행합니다
```
'type': 'auction_update' -> async def auction_update(self, event): 찾아서 실행

'type': 'auction_end_notification'-> async def auction_end_notification(self, event): 찾아서 실행
```
1. group_send 안의 type (서버 내부용): 핸들러가 기능한다.(핸들러는 브라우저(JSON 데이터만 쏴주고 끝남)에게 최종적으로 전달해주는 역할)

2. self.send 안의 type (클라이언트 통신용): 클라이언트가 기능한다.
 
- json 하는 역할

json.loads와 json.dumps : 파이썬과 자바스크립트가 서로 말이 안 통하기 때문입니다.
> 데이터를 주고받으려면 약속된 문자열 형식인 JSON으로 변환

json.dumps() : 파이썬 객체를 JSON 문자열로 변환

> 핸들러가 JSON 문자열을 JS(브라우저)에게 전달
 
> 웹소켓을 통과할때는 언어를 통일해서 json 으로 통과해야한다

json.loads() : JSON 문자열을 파이썬 객체로 변환
