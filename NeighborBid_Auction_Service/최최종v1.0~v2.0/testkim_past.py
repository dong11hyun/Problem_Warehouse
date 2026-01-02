# auctions/tests.py
from django.test import TransactionTestCase
import threading
import time

class ConcurrencyTestCase(TransactionTestCase):
    """
    TransactionTestCase 사용 이유:
    - 각 테스트 후 DB 롤백이 아닌 truncate 방식 사용
    - 멀티스레드에서 실제 트랜잭션 동작 테스트 가능
    """
    
    def test_double_spending_prevention(self):
        """이중 지출 방지 테스트"""
        # 유저 생성 (잔액 10,000원)
        user = User.objects.create_user(username='tester', password='test')
        Wallet.objects.create(user=user, balance=10000)
        
        # 경매 2개 생성
        seller = User.objects.create_user(username='seller', password='test')
        Wallet.objects.create(user=seller, balance=0)
        
        auction1 = self._create_auction(seller, "상품1")
        auction2 = self._create_auction(seller, "상품2")
        
        results = []
        
        def bid_to_auction(auction_id, amount):
            try:
                msg = place_bid(auction_id, user, amount)
                results.append(('success', auction_id))
            except ValueError as e:
                results.append(('fail', str(e)))
        
        # 동시에 두 경매에 10,000원씩 입찰
        t1 = threading.Thread(target=bid_to_auction, args=(auction1.id, 10000))
        t2 = threading.Thread(target=bid_to_auction, args=(auction2.id, 10000))
        
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        # 검증: 1건만 성공해야 함
        success_count = sum(1 for r in results if r[0] == 'success')
        fail_count = sum(1 for r in results if r[0] == 'fail')
        
        self.assertEqual(success_count, 1, "정확히 1건만 성공해야 함")
        self.assertEqual(fail_count, 1, "1건은 잔액 부족으로 실패해야 함")
        
        # 최종 잔액 확인
        wallet = Wallet.objects.get(user=user)
        self.assertEqual(wallet.balance + wallet.locked_balance, 10000, "총 자산은 유지되어야 함")

    def test_concurrent_bidding_race(self):
        """10명 동시 입찰 경쟁 테스트"""
        seller = User.objects.create_user(username='seller', password='test')
        Wallet.objects.create(user=seller, balance=0)
        auction = self._create_auction(seller, "인기상품")
        
        # 10명의 입찰자 생성
        bidders = []
        for i in range(10):
            user = User.objects.create_user(username=f'bidder{i}', password='test')
            Wallet.objects.create(user=user, balance=50000)
            bidders.append(user)
        
        results = []
        
        def bid_request(user, amount):
            time.sleep(0.001)  # 약간의 랜덤성
            try:
                msg = place_bid(auction.id, user, amount)
                results.append(('success', user.username, amount))
            except ValueError as e:
                results.append(('fail', user.username, str(e)))
        
        threads = []
        for i, bidder in enumerate(bidders):
            # 각자 다른 금액으로 입찰
            amount = 10000 + (i * 1000)
            t = threading.Thread(target=bid_request, args=(bidder, amount))
            threads.append(t)
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 검증
        auction.refresh_from_db()
        successful_bids = [r for r in results if r[0] == 'success']
        
        # 현재가가 가장 높은 입찰 금액이어야 함
        highest_bid = max(r[2] for r in successful_bids)
        self.assertEqual(auction.current_price, highest_bid)

    def _create_auction(self, seller, title):
        return Auction.objects.create(
            seller=seller,
            title=title,
            description="테스트",
            start_price=10000,
            current_price=0,
            bid_unit=1000,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
            status='ACTIVE'
        )