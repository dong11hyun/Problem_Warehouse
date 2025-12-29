```
from .services import place_bid
from wallet.models import Wallet, Transaction
from django.db.models import Q
```
---
```
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
render: HTML 파일을 화면에 보여줄 때 사용합니다. (가장 기본!)
```

> 파이썬(장고 포함)에서는
“내 파일에 없는 걸 쓰려면 무조건 import 해야 한다.”

> views.py에 다 적으면 코드가 너무 길어지고 지저분해집니다. 그래서 services.py라는 별도의 파일에 로직을 만들어두고 여기서는 가져다 쓰기만 하는 것이다.
입찰(place_bid)은 로직이 복잡합니다. (가격 비교, 시간 체크, 즉시 구매가 확인, 내 지갑 차감 등)

> 돈 관리는 항상 지갑(wallet) 앱으로 분리

> 데이터베이스에서 검색할 때 'OR' 조건을 쓰기 위한 도구입니다.

- get_object_or_404: 데이터를 찾다가 없으면 에러 페이지 대신 깔끔하게 '404 없음' 페이지를 보여주는 안전장치입니다. (예: 존재하지 않는 경매 번호로 접속했을 때)

- redirect: 처리가 끝나고 다른 주소로 튕겨 보낼 때 씁니다. (예: 입찰 성공 후 다시 상세 페이지로 이동)

- login_required: "로그인 안 한 사람은 못 들어옴!" 하고 막아주는 문지기(데코레이터)입니다. 경매 입찰은 로그인한 사람만 해야 하니까요.

- messages: 화면 상단에 잠깐 떴다 사라지는 알림창("입찰 성공!", "잔액이 부족합니다" 등)을 띄워주는 도구입니다.


#### 재귀 함수 사용

```
region_instance = {

'id': 1, # PK (내 주민등록번호)

'name': "서울특별시", # 내 이름

'depth': 1, # 내 깊이

'parent_id': None # 부모의 ID (부모 객체 자체가 아님! 그냥 숫자만!)

}
```
> region 안에 "서울" 이렇게만 있더라도 실제로는 해당 컬럼들이 모두 채워진다
> region.sub_regions.all() 을 수행하면 자동으로 FK를 찾아간다!!

> region.depth이렇게 해도 값을 불러올 수 있다


> 성능 고려 (Performance) 이 방식은 코드는 직관적이고 깔끔하지만, 데이터가 아주 많아지면 DB 성능 이슈가 발생할 수 있습니다.

> 문제점: 함수가 재귀 호출될 때마다 DB에 쿼리를 날립니다. (N+1 문제와 유사)

> 해결책(나중에): 지금처럼 지역 데이터가 수백 개 수준이면 전혀 문제없습니다. 하지만 수만 개가 넘어가면 django-mptt 같은 라이브러리를 쓰거나, 처음부터 모든 지역을 한 번에 가져와서 파이썬 메모리 상에서 정렬하는 방식을 고려해야 합니다.

---

`request.GET.get('region')` 

- request : 사용자가 장고에게 특정 정보를 요청한다.

- **request.GET** : 사용자가 URL에 특정 정보를 포함하여 요청한다.
> ex) auction?region=서울&category=노트북  ? 뒤에오는 정보 요청

- **request.POST** : 사용자가 폼(로그인, 회원가입 등)을 통해 특정 정보를 포함하여 요청한다.
> 일반적으로 GET이 주소창에 다 보이는 '공개된' 정보 요청이라면, POST는 '비공개된' 정보 요청이다.

- **.get()** : 적힌 값이 있으면 가져오고, 없으면 에러없이 넘어간다 None

- **__gte: Greater than or Equal (이상)**

- **__lte: Less than or Equal (이하)**

- **__icontains: (i ==대소문자 구분 없이) (contains문자열 포함하는지)**

---

- **def auction_list(request)** : request 는 매개변수이고,
> 누가 넣어주나?: 우리가 함수를 직접 호출하는 게 아니라, **Django(장고)**가 알아서 넣어줍니다.

>뭐가 들어오나?: 아까 설명한 **'요청서(HttpRequest 객체)'**가 통째로 들어옵니다. (개인 정보, URL 정보, 데이터 등등)

- **request.GET.get('region')** : region 은 문자열이고, 어디에서부터 왔나?

> HTML에서 이름을 region이라고 지었기 때문에, 파이썬에서도 'region'이라는 문자열로 찾는 것입니다.

- **region_id에는 결국 어떤 데이터 형태가 들어가나?** : 
> "문자열(String)" 또는 **"None"**이 들어갑니다.

> 웹사이트 주소창에 적힌 숫자는 우리 눈엔 숫자처럼 보여도, 컴퓨터(HTTP 통신)는 무조건 문자로 취급합니다.
---

__의 두 번째 역할은 **"SQL 명령어(조건)를 붙이는 역할"**입니다.
> ex) __abc True False 판단 

__ 왜 두번쓰나? : 여러번도 사용 가능. 하지만 DB가 무거워짐

slug(슬러그) : 주소창(URL)을 깔끔하고 알아보기 쉽게만든 별명

_ _ 자체는 `관계` 가 있으면 모두 건너갈 수 있다
> **1:1 , 1:N , N:M 그리고 자기자신한테 조건 걸때 ex) __gte, __lte**

**장고 내부에서 표현 OneToOneField(), ForeignKey(), ManyToManyField()**

---

.get('q'): 서랍에서 'q' (검색어, Query의 약자)라는 이름표가 붙은 값을 꺼냅니다.

`sort = request.GET.get('sort', 'recent')` : 첫 번째 인자 'sort': "주소창에서 sort라는 값을 찾아와라."

두 번째 인자 'recent': "만약 sort 값이 없으면(사용자가 아무것도 안 눌렀으면), 기본값으로 'recent'(최신순)를 가져와라."

base 파일에 'q' 로 name 만들어서 현재 'q'로 사용한다.

---

`@login_required` : Django에서 제공하는 데코레이터


동작원리
1. 사용자가 /auction/3/ 접근

2. Django가 login_required 먼저 실행

3. 로그인 X → 로그인 페이지로 리다이렉트

4. 로그인 O → auction_detail 실행

```
@login_required
def auction_detail(..):

⬇️ 실제로 이렇게 바꿔서 처리한다.

auction_detail = login_required(auction_detail)
```
```
# '이름(Key)': 실제내용(Value)
context = {
    
    'auction': auction,      
    # 이제부터 HTML에서 'auction'이라고 부른다!
    'other_items': other_items,    
    # 이제부터 HTML에서 'other_items'라고 부른다!
}
```
여기서 정한 **Key('auction')**가 HTML에서 변수 이름이 됩니다.

---

.select_related('auction') : "입찰 정보 가져올 때, 그 경매 물품 정보(Auction)도 미리 같이 챙겨와"
> 안쓰면 DB에서 N+1 문제 발생, 해당 코드로 DB를 1번만 다녀와서 정보를 다가져옴 문제해결

### 동시성 문제와 더블클릭으로 인한 충전 오류 방지책!

깃허브 코드_리뷰 Level_3 에 등록

### form.is_valid()
필수 항목이 비었는지, 숫자에 문자가 들어오진 않았는지 등 기본적인 검사를 수행합니다.


ManyToManyField() : 장고에서 테이블을 자동으로 하나 더 만듭니다.(중간테이블 생성)


