import time
import pybithumb
import datetime

# 구매 하루 한번  : 골든크로스, 아래로볼록
# 구매 실시간     : 장대양봉
# 판매 하루 한번  : 데드크로스, 위로볼록, 십자가 판매
# 판매 실시간     : 장대음봉, 익절, 손절 판매

major_ticker = ["BTC", "LINK", "XRP", "ETH", "EOS", "BCH", "TRX", "BSV", "LTC", "ETC", "XLM", "QTUM", "ADA"]

ticker = "BTC"

# 상수
bene_cnst = 1.37  # 익절조건 예상 : 1.3
cross_cnst = 0.0032  # 십자가조건 예상 : 0.003
stop_loss_cnst = 0.019  # 손절조건 예상 : 0.03
jang_plus_cnst = 0.052  # 장대양봉조건 예상 : 0.05
jang_minus_cnst = 0.055  # 장대음봉조건 예상 : 0.05

# 개인 API 가져옴
with open("bithumb.txt") as f:
    lines = f.readlines()
    key = lines[1].strip()  # 메모장 상태에 따라 다름
    secret = lines[3].strip()  # 메모장 상태에 따라 다름
    bithumb = pybithumb.Bithumb(key, secret)


# num=-2 : yesterday
# num=-3 : yesterday2
# num=-4 : yesterday3
def get_yesterday_ma5(num):
    close = df['close']
    ma = close.rolling(window=5).mean()
    return ma[num]


# num=-2 : yesterday
# num=-3 : yesterday2
def get_yesterday_ma20(num):
    close = df['close']
    ma = close.rolling(window=20).mean()
    return ma[num]


# 오늘 시가 함수
def get_today_open():
    open_to = df['open']
    return open_to[-1]


# 1일전 시가 함수
def get_yesterday_open():
    open_yes = df['open']
    return open_yes[-2]


# 1일전 종가 함수
def get_yesterday_close():
    close = df['close']
    return close[-2]


# 30일 평균 거래량 함수
def get_aver_volume():
    volume_aver_30 = df['volume'].rolling(window=30).mean()
    return volume_aver_30[-2]


# 오늘 거래량 함수
def get_to_volume():
    volume = df['volume']
    return volume[-1]


# 구매 함수(시장가)
def buy_crypto_currency(ticker):
    orderbook = pybithumb.get_orderbook(ticker)
    buy_price = orderbook['asks'][0]['price']
    buy_unit = krw_by_coin[ticker] / float(buy_price)

    order_buy = bithumb.buy_market_order(ticker, buy_unit)
    print(order_buy)
    # print(buy_price, buy_unit)# 테스트용, 실사용시 위 2줄 사용

    # 구매후 지갑상태, 가격 갱신
    wallet_bull[ticker] = False
    krw_by_coin[ticker] = krw_by_coin[ticker] - buy_unit * buy_price
    return buy_price


# 판매 함수(시장가)
def sell_crypto_currency(ticker):
    sell_unit = bithumb.get_balance(ticker)[0]
    orderbook = pybithumb.get_orderbook(ticker)
    sell_price = orderbook['bids'][0]['price']

    order_sell = bithumb.sell_market_order(ticker, sell_unit)
    print(order_sell)
    # print(sell_unit, sell_price)# 테스트용, 실사용시 위 2줄 사용

    # 판매후 지갑상태, 가격 갱신
    wallet_bull[ticker] = True
    krw_by_coin[ticker] = krw_by_coin[ticker] + sell_unit * sell_price
    if krw_by_coin[ticker] <= 1000:
        wallet_bull[ticker] = False

    return sell_price


# 초기화, 초기 설정(실행시 한번)
now = datetime.datetime.now()
mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)
count = 0
current_price = {}
real_buy_current = {}
wallet_bull = {}
beneath = {}
stop_loss = {}
golden_cross = {}
convex_down = {}

dead_cross = {}
convex_up = {}
cross = {}
jang_dae_plus = {}
jang_dae_minus = {}

jang_dae_plus_volume = {}
jang_dae_minus_volume = {}

unit_c = {}
krw_by_coin = {}

# 원화 코인 분배
total_krw = bithumb.get_balance(ticker)[2]
for ticker in major_ticker:
    krw_by_coin[ticker] = total_krw/len(major_ticker)
    if krw_by_coin[ticker] > 1000:
        wallet_bull[ticker] = True
    else:
        wallet_bull[ticker] = False

# print(wallet_bull)
# print(krw_by_coin)

# 딕셔너리 초기화(실행시 한번)
for ticker in major_ticker:
    df = pybithumb.get_candlestick(ticker)
    current_price[ticker] = pybithumb.get_current_price(ticker)
    real_buy_current[ticker] = current_price[ticker]
    beneath[ticker] = False
    stop_loss[ticker] = False

    # 각종 이동평균(실행시 한번)
    yes_ma5 = get_yesterday_ma5(-2)
    yes2_ma5 = get_yesterday_ma5(-3)
    yes3_ma5 = get_yesterday_ma5(-4)
    yes_ma20 = get_yesterday_ma20(-2)
    yes2_ma20 = get_yesterday_ma20(-3)

    # 오늘 시가, 어제 시가, 종가, 거래량, 년 평균 거래량(실행시 한번)
    to_open = get_today_open()
    yes_open = get_yesterday_open()
    yes_close = get_yesterday_close()
    volume_aver = get_aver_volume()
    to_volume = get_to_volume()

    # 골든크로스, 아래로 볼록(실행시 한번)
    golden_cross[ticker] = (yes2_ma5 < yes2_ma20) and (yes_ma5 > yes_ma20)
    convex_down[ticker] = (yes3_ma5 > yes2_ma5) and (yes2_ma5 < yes_ma5)

    # 데드크로스, 위로 볼록, 십자가(실행시 한번)
    dead_cross[ticker] = (yes2_ma5 > yes2_ma20) and (yes_ma5 < yes_ma20)
    convex_up[ticker] = (yes3_ma5 < yes2_ma5) and (yes2_ma5 > yes_ma5)
    cross[ticker] = abs(yes_close - yes_open) < yes_open * cross_cnst

    # 장대양봉, 장대음봉(실행시 한번)
    jang_dae_plus = abs(current_price[ticker] - to_open) > to_open * jang_plus_cnst
    jang_dae_minus = (to_open > current_price[ticker]) and (abs(to_open - current_price[ticker]) > to_open * jang_minus_cnst)

    # 장대양봉 + 거래량, 장대음봉+거래량(실행시 한번)
    jang_dae_plus_volume[ticker] = jang_dae_plus and (to_volume > volume_aver * 2)
    jang_dae_minus_volume[ticker] = jang_dae_minus and (to_volume > volume_aver * 2)

    time.sleep(0.1)

while True:
    for ticker in major_ticker:
        try:
            # 현재가 받아옴(실시간)
            current_price[ticker] = pybithumb.get_current_price(ticker)

            # 현재시간(실시간)
            now = datetime.datetime.now()

            # 차트 받아옴(실시간)
            df = pybithumb.get_candlestick(ticker)

            # 계산(실시간)
            to_open = get_today_open()
            volume_aver = get_aver_volume()
            to_volume = get_to_volume()

            # 자정이 넘어가면 정보 최신화, 조건 만족시 구매 or 판매(하루 한번)
            if mid < now < mid + datetime.timedelta(seconds=20):
                # 차트 받아옴(하루 한번)
                df = pybithumb.get_candlestick(ticker)

                # 각종 이동평균(하루 한번)
                yes_ma5 = get_yesterday_ma5(-2)
                yes2_ma5 = get_yesterday_ma5(-3)
                yes3_ma5 = get_yesterday_ma5(-4)
                yes_ma20 = get_yesterday_ma20(-2)
                yes2_ma20 = get_yesterday_ma20(-3)

                # 오늘 시가, 어제 시가, 종가, 거래량, 년 평균 거래량(하루 한번)
                to_open = get_today_open()
                yes_open = get_yesterday_open()
                yes_close = get_yesterday_close()
                volume_aver = get_aver_volume()
                to_volume = get_to_volume()

                # 골든크로스, 아래로 볼록(하루 한번)
                golden_cross[ticker] = (yes2_ma5 < yes2_ma20) and (yes_ma5 > yes_ma20)
                convex_down[ticker] = (yes3_ma5 > yes2_ma5) and (yes2_ma5 < yes_ma5)

                # 데드크로스, 위로 볼록, 십자가(하루 한번)
                dead_cross[ticker] = (yes2_ma5 > yes2_ma20) and (yes_ma5 < yes_ma20)
                convex_up[ticker] = (yes3_ma5 < yes2_ma5) and (yes2_ma5 > yes_ma5)
                cross[ticker] = abs(yes_close - yes_open) < yes_open * cross_cnst

                # 골든크로스, 아래로 볼록 구매(하루 한번)
                if wallet_bull[ticker] and (golden_cross[ticker] or convex_down[ticker]):
                    real_buy_current[ticker] = buy_crypto_currency(ticker)
                    print(ticker, real_buy_current[ticker], "골든크로스, 아래로 볼록 구매")
                    print(now)

                # 판매 가능한지 수량 판별(하루 한번)
                unit = bithumb.get_balance(ticker)
                if unit[0] * current_price[ticker] <= 1000:
                    unit_c[ticker] = False
                else:
                    unit_c[ticker] = True

                # 데드크로스, 위로볼록, 십자가 판매(하루 한번)
                if unit_c[ticker] and (dead_cross[ticker] or convex_up[ticker] or cross[ticker]):
                    sell_crypto_currency(ticker)
                    real_sell_current = pybithumb.get_current_price(ticker)
                    print(ticker, real_sell_current, "데드크로스 ,위로볼록 ,십자가 판매")
                    print(now)

                # 자정 업데이트(하루 한번)
                mid = datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(1)

            # 장대양봉, 장대음봉(실시간)
            jang_dae_plus = abs(current_price[ticker] - to_open) > to_open * jang_plus_cnst
            jang_dae_minus = (to_open > current_price[ticker]) and (abs(to_open - current_price[ticker]) > to_open * jang_minus_cnst)

            # 장대양봉 + 거래량, 장대음봉+거래량(실시간)
            jang_dae_plus_volume[ticker] = jang_dae_plus and (to_volume > volume_aver * 2)
            jang_dae_minus_volume[ticker] = jang_dae_minus and (to_volume > volume_aver * 2)

            # 장대양봉 구매(실시간)
            if wallet_bull[ticker] and jang_dae_plus_volume[ticker]:
                real_buy_current[ticker] = buy_crypto_currency(ticker)
                print(ticker, real_buy_current[ticker], "장대양봉 구매")
                print(now)

            # 익절(실시간)
            if current_price[ticker] >= real_buy_current[ticker] * bene_cnst:
                beneath[ticker] = True
            else:
                beneath[ticker] = False

            # 손절(실시간)
            if current_price[ticker] <= real_buy_current[ticker] * (1-stop_loss_cnst):
                stop_loss[ticker] = True
            else:
                stop_loss[ticker] = False

            # 판매 가능한지 수량 판별(실시간)
            unit = bithumb.get_balance(ticker)
            if unit[0] * current_price[ticker] <= 1000:
                unit_c[ticker] = False
            else:
                unit_c[ticker] = True

            # 장대음봉, 익절, 손절 판매(실시간)
            if unit_c[ticker] and (jang_dae_minus_volume[ticker] or beneath[ticker] or stop_loss[ticker]):
                real_sell_current = sell_crypto_currency(ticker)
                print(ticker, real_sell_current, "장대음봉, 익절, 손절 판매")
                print(now)

        except:
            print("에러발생")
        # 코인별 시간차
        time.sleep(0.1)

    # print(wallet_bull)
    # print(krw_by_coin)
    # 모든 코인 실행 뒤 시간차
    time.sleep(0.3)
    # count = count + 1
    # print(count)

# # 현재 구매 가능 상태, 코인별 원화 확인시 사용
# print(wallet_bull)
# print(krw_by_coin)
