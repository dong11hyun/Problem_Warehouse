# auctions/tests.py

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import threading
import time

from .models import Auction, Bid
from .services import place_bid
from wallet.models import Wallet, Transaction
from common.models import Region, Category

User = get_user_model()


class ConcurrencyTestCase(TransactionTestCase):
    """
    동시성 테스트는 TransactionTestCase를 사용해야 합니다.
    - TestCase: 각 테스트를 트랜잭션으로 감싸서 롤백 (스레드 간 DB 공유 안됨)
    - TransactionTestCase: 실제 커밋이 일어나서 스레드 간 DB 공유 가능
    """
    
    def setUp(self):
        """테스트 데이터 준비"""
        # 1. 지역, 카테고리 생성
        self.region = Region.objects.create(name="서울", depth=1)
        self.category = Category.objects.create(name="전자기기", slug="electronics")
        
        # 2. 사용자 생성 (입찰자 1명, 판매자 1명)
        self.seller = User.objects.create_user(
            username='seller',
            password='testpass123',
            email='seller@test.com',
            region=self.region
        )
        self.bidder = User.objects.create_user(
            username='bidder',
            password='testpass123',
            email='bidder@test.com',
            region=self.region
        )
        
        # 3. 지갑 생성 - 입찰자에게 10,000원만 지급
        Wallet.objects.create(user=self.seller, balance=0)
        self.bidder_wallet = Wallet.objects.create(
            user=self.bidder, 
            balance=Decimal('10000')  # 딱 10,000원만!
        )
        
        # 4. 경매 2개 생성 (각각 10,000원씩 입찰 가능하게)
        self.auction1 = Auction.objects.create(
            title="경매 A",
            description="테스트 경매 A",
            seller=self.seller,
            start_price=Decimal('10000'),
            current_price=Decimal('0'),
            bid_unit=Decimal('1000'),
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status='ACTIVE',
            region=self.region,
            category=self.category
        )
        self.auction2 = Auction.objects.create(
            title="경매 B",
            description="테스트 경매 B",
            seller=self.seller,
            start_price=Decimal('10000'),
            current_price=Decimal('0'),
            bid_unit=Decimal('1000'),
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status='ACTIVE',
            region=self.region,
            category=self.category
        )
    
    def test_double_spending_prevention(self):
        """
        이중 지출 방지 테스트
        
        시나리오:
        - 잔액 10,000원인 사용자가 있음
        - 경매 A, B에 동시에 10,000원씩 입찰 시도
        - 기대 결과: 1개만 성공, 1개는 잔액 부족으로 실패
        """
        results = []
        errors = []
        
        def bid_on_auction(auction, amount):
            """스레드에서 실행될 입찰 함수"""
            try:
                place_bid(auction.id, self.bidder, Decimal(str(amount)))
                results.append({
                    'auction': auction.title,
                    'status': 'success'
                })
            except ValueError as e:
                results.append({
                    'auction': auction.title,
                    'status': 'fail',
                    'error': str(e)
                })
            except Exception as e:
                errors.append(str(e))
        
        # 두 스레드를 거의 동시에 시작
        t1 = threading.Thread(target=bid_on_auction, args=(self.auction1, 10000))
        t2 = threading.Thread(target=bid_on_auction, args=(self.auction2, 10000))
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        # 결과 출력
        print("\n" + "="*60)
        print(" 동시성 테스트 결과")
        print("="*60)
        print(f"초기 잔액: 10,000원")
        print(f"입찰 시도: 경매 A에 10,000원, 경매 B에 10,000원 (동시)")
        print("-"*60)
        
        for r in results:
            status_icon = "" if r['status'] == 'success' else "x"
            print(f"{status_icon} {r['auction']}: {r['status']}")
            if 'error' in r:
                print(f"   → 사유: {r['error']}")
        
        # 최종 지갑 상태 확인
        self.bidder_wallet.refresh_from_db()
        print("-"*60)
        print(f"최종 잔액(balance): {self.bidder_wallet.balance}원")
        print(f"잠긴 금액(locked): {self.bidder_wallet.locked_balance}원")
        print(f"총 자산: {self.bidder_wallet.balance + self.bidder_wallet.locked_balance}원")
        print("="*60)
        
        #  검증: 정확히 1개만 성공해야 함
        success_count = sum(1 for r in results if r['status'] == 'success')
        self.assertEqual(success_count, 1, 
            f"1개만 성공해야 하는데 {success_count}개 성공함!")
        
        #  검증: 잔액이 음수가 되면 안 됨
        self.assertGreaterEqual(self.bidder_wallet.balance, 0,
            f"잔액이 음수가 됨! balance={self.bidder_wallet.balance}")
        
        #  검증: 총 자산은 여전히 10,000원이어야 함
        total = self.bidder_wallet.balance + self.bidder_wallet.locked_balance
        self.assertEqual(total, Decimal('10000'),
            f"총 자산이 변함! {total}원")
        
        print(" 테스트 통과: 이중 지출이 정상적으로 차단됨!")


class BasicBidTestCase(TestCase):
    """기본 입찰 테스트 (동시성 없이)"""
    
    def setUp(self):
        self.region = Region.objects.create(name="서울", depth=1)
        self.category = Category.objects.create(name="전자기기", slug="electronics2")
        
        self.seller = User.objects.create_user(
            username='seller', password='test', email='s@t.com', region=self.region
        )
        self.bidder = User.objects.create_user(
            username='bidder', password='test', email='b@t.com', region=self.region
        )
        
        Wallet.objects.create(user=self.seller, balance=0)
        self.wallet = Wallet.objects.create(user=self.bidder, balance=Decimal('50000'))
        
        self.auction = Auction.objects.create(
            title="테스트 경매",
            description="설명",
            seller=self.seller,
            start_price=Decimal('10000'),
            current_price=Decimal('0'),
            bid_unit=Decimal('1000'),
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=1),
            status='ACTIVE',
            region=self.region,
            category=self.category
        )
    
    def test_successful_bid(self):
        """정상 입찰 테스트"""
        place_bid(self.auction.id, self.bidder, Decimal('10000'))
        
        self.wallet.refresh_from_db()
        self.auction.refresh_from_db()
        
        self.assertEqual(self.wallet.balance, Decimal('40000'))
        self.assertEqual(self.wallet.locked_balance, Decimal('10000'))
        self.assertEqual(self.auction.current_price, Decimal('10000'))
    
    def test_insufficient_balance(self):
        """잔액 부족 테스트"""
        self.wallet.balance = Decimal('5000')
        self.wallet.save()
        
        with self.assertRaises(ValueError) as ctx:
            place_bid(self.auction.id, self.bidder, Decimal('10000'))
        
        self.assertIn("잔액", str(ctx.exception))
    
    def test_bid_below_minimum(self):
        """최소 입찰가 미만 테스트"""
        with self.assertRaises(ValueError) as ctx:
            place_bid(self.auction.id, self.bidder, Decimal('5000'))
        
        self.assertIn("최소", str(ctx.exception))
