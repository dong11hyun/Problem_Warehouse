config / urls.py

```
from django.contrib import admin
from django.urls import path, include # include 추가!
from django.conf import settings
from django.conf.urls.static import static
```

- admin: 관리자실로 가는 문을 만들기 위해 가져왔습니다.
- path: "이 주소로 오면 여기로 가세요"라고 표지판을 세우는 도구입니다.
- include: "여기서부터는 저쪽 부서 안내 데스크에서 물어보세요"라고 책임을 넘기는(위임하는) 도구입니다(중요)
> "users/로 시작하는 건 users 앱 네가 알아서 처리해!" (딱 한 줄)

- 장고의 기본 원칙은 "파일을 직접 보여주지 않는다" >> Auction 모델에 이미지를 업로드하면 보여야 하는데 장고에서 무시됨.

장고 서버는 보안상의 이유로 **사용자가 업로드한 파일(이미지 등)**을 보여주지 않습니다. (HTML, CSS만 보여줌)

사용자 요청: jpg 이미지 보여달라 요청.
static 함수: 파일을 임시로 꺼내서 보여준다.


맨 아래 `settings.DEBUG` 를 통해 이미지 또한 제공해준다

실제 배포에서 static 함수는 느리고 비효율적이라 사용하지 않는다. 실제에선 AWS S3, Nginx 가 대신한다.

```
urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')), 
    path('', include('auctions.urls')), 
]
```

urlpatterns : (users/) -  위임(Include) 받는다.
> include('users.urls')를 보고, users 앱 안에 있는 urls.py로 가게한다.

path('', ...)는 **"아무것도 안 썼을 때(홈페이지)"**를 의미합니다.
> include('auctions.urls')를 보고, auctions 앱 안에 있는 acutions.urls 로 가게한다