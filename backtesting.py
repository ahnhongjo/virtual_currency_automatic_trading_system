import numpy as np
import pybithumb
import time

major_ticker = ["BTC", "LINK", "XRP", "ETH", "EOS", "BCH", "TRX", "BSV", "LTC", "ETC", "XLM", "QTUM", "ADA"]
#수익률을 계산하는 함수get_hpr

#현재 적용중 : 구매 : 골든 크로스, 5일평균 아래로볼록, 장대양봉(k)
#            판매 : 데드 크로스, 5일평균 위로볼록, 십자가(k), 장대음봉(k), 손절(k), 익절(k)
#            +수수료

def get_hpr(ticker):
    time.sleep(0.1)
    try:
        bene = 1.33  #익절조건 예상 : 1.3
        cross = 0.0012  #십자가조건 예상 : 0.003
        stop_loss = 0.021  #손절조건 예상 : 0.03
        jang_plus = 0.027  #장대양봉조건 예상 : 0.05
        jang_minus = 0.022  #장대음봉조건 예상 : 0.05

        real_buy_price = 1  #실제로 구매했을때 가격 저장용, 초기화
        wallet_bull = False  #지갑상태 초기화
        df = pybithumb.get_candlestick(ticker)  #가상화폐의 open,high,low,close,volume 가져옴, 함수 수정으로 단위 변경 가능
        #df = df['2020']  #기간 설정 가능

        df['ma5_yes'] = df['close'].rolling(window=5).mean().shift(1)  #1일전 5일 평균(종가기준)
        df['ma5_yes2'] = df['close'].rolling(window=5).mean().shift(2)  #2일전 5일 평균
        df['ma5_yes3'] = df['close'].rolling(window=5).mean().shift(3)  # 3일전 5일 평균

        df['ma20_yes'] = df['close'].rolling(window=20).mean().shift(1)  #1일전 20일 평균(종가기준)
        df['ma20_yes2'] = df['close'].rolling(window=20).mean().shift(2)  #2일전 20일 평균

        #거래량 평균값 저장
        df['volume_aver'] = 0  #총 거래량 초기화
        df['vr'] = df['volume'].rolling(window=len(df)).mean()  #총 거래량 평균
        vr = df['vr'].iloc[len(df)-1]  #총 거래량 평균 값 지정
        for i in range(0, len(df)):
            df['volume_aver'].iloc[i] = vr

        #평균 거래량*2배 가 넘을때 True, 아니면 False
        df['bull_volume_2over'] = np.where(df['volume'].shift(1) > 2*df['volume_aver'],
                                     True,
                                     False)

        #장대양봉, 장대음봉(k)
        df['jang_dae_p'] = df['close'].shift(1) - df['open'].shift(1) > df['open'].shift(1) * jang_plus
        df['jang_dae_m'] = np.where(((df['close'].shift(1) - df['open'].shift(1)) < 0) & (abs(df['close'].shift(1) - df['open'].shift(1)) > df['open'].shift(1) * jang_minus),
                                    True,
                                    False)

        #손절 장대음봉(k)
        df['jang_dae_m_stop'] = np.where(((df['close'] - df['open']) < 0) & (abs(df['close'] - df['open']) > df['open'] * stop_loss),
                                       True,
                                       False)

        #장대양봉, 장대음봉 + 평균 2배 거래량
        df['jang_dae_plus'] = np.where(df['bull_volume_2over'] & df['jang_dae_p'],
                                       True,
                                       False)
        df['jang_dae_minus'] = np.where(df['bull_volume_2over'] & df['jang_dae_m'],
                                        True,
                                        False)

        df['wallet_bull'] = wallet_bull  # 지갑상태 초기화
        df['real_buy_price'] = real_buy_price  #실제 구매 가격 초기화

        #골든크로스 조건
        df['buy_bull_yes'] = df['ma5_yes'] > df['ma20_yes']  #어제 5일평균 > 어제 20일평균
        df['buy_bull_yes2'] = df['ma5_yes2'] < df['ma20_yes2']  #2일전 5일평균 < 2일전 20일평균

        # 5일평균 아래로 볼록
        df['convex_down'] = np.where((df['ma5_yes'] > df['ma5_yes2']) & (df['ma5_yes2'] < df['ma5_yes3']),
                                     True,
                                     False)
        #5일평균 위로 볼록
        df['convex_up'] = np.where((df['ma5_yes'] < df['ma5_yes2']) & (df['ma5_yes2'] > df['ma5_yes3']),
                                     True,
                                     False)
        #5일평균 상승장
        df['up_market'] = np.where((df['ma5_yes'] > df['ma5_yes2']) & (df['ma5_yes2'] > df['ma5_yes3']),
                                   True,
                                   False)##현재 사용 X

        # 데드 크로스 일때 상태 표시
        df['dead_cross'] = np.where((df['ma5_yes'] < df['ma20_yes']) & (df['ma5_yes2'] > df['ma20_yes2']),
                                    True,
                                    False)

        #십자가조건일때(k)
        df['sell_bull_cross'] = abs(df['close'].shift(1) - df['open'].shift(1)) < df['open'].shift(1)*cross

        # 골든 크로스, 장대양봉, 아래로 볼록 일때 시가로 구매(구매조건은 여기에 추가)
        df['buy_price'] = np.where((df['buy_bull_yes'] & df['buy_bull_yes2']) | df['jang_dae_plus'] | df['convex_down'],
                                   df['open'],
                                   1)

        # 골든 크로스, 장대양봉, 아래로 볼록 일때 상태 표시(구매조건은 여기에 추가)
        df['buy_state'] = np.where((df['buy_bull_yes'] & df['buy_bull_yes2']) | df['jang_dae_plus'] | df['convex_down'],
                                   True,
                                   False)

        # 십자가, 데드크로스, 장대음봉, 위로 볼록 일때 시가로 판매(판매조건은 여기에 추가)
        df['sell_price'] = np.where(df['sell_bull_cross'] | df['dead_cross'] | df['jang_dae_minus'] | df['convex_up'],
                                    df['open'],
                                    1)

        # 십자가, 데드크로스, 장대음봉, 위로 볼록 일때 판매 상태 표시(판매조건은 여기에 추가)
        df['sell_state'] = np.where(df['sell_bull_cross'] | df['dead_cross'] | df['jang_dae_minus'] | df['convex_up'],
                                    True,
                                    False)

        #손절, 익절, 구매, 판매 실행(지갑상태 영향 받음)
        for i in range(0, len(df)):

            # 손절 : 장대음봉(거래량 상관X)이면 시가의 1-stop_loss(기존 sell_price, sell_state에 덮어씌움)
            if df['jang_dae_m_stop'].iloc[i]:
                df['sell_price'].iloc[i] = df['open'].iloc[i] * (1-stop_loss)
                df['sell_state'].iloc[i] = True

            # 실제로 구매 할때 df['wallet_bull']에 True입력, 실제로 판매 했을때 False입력(지갑상태 영향 받음)
            if (i < len(df)-1):
                if not(df['wallet_bull'].iloc[i]) and df['buy_state'].iloc[i]:
                    wallet_bull = True
                if df['wallet_bull'].iloc[i] and df['sell_state'].iloc[i]:
                    wallet_bull = False
                df['wallet_bull'].iloc[i+1] = wallet_bull

            #실제로 구매 했을때 df['real_buy_price']에 구매가격 저장
            if not(df['wallet_bull'].iloc[i]) and df['buy_state'].iloc[i]:
                real_buy_price = df['buy_price'].iloc[i]
            df['real_buy_price'].iloc[i] = real_buy_price

            #익절 : 현재가가 구매가격*bene배가 넘었을때(기존 sell_price, sell_state에 덮어씌움)
            if (i < len(df)-1) and df['wallet_bull'].iloc[i] and (df['real_buy_price'].iloc[i] * bene < df['high'].iloc[i]):
                df['sell_price'].iloc[i] = df['real_buy_price'].iloc[i] * bene
                df['sell_state'].iloc[i] = True
                wallet_bull = False
                df['wallet_bull'].iloc[i+1] = wallet_bull

        fee = 0.995  #수수료

        #실제로 판매 했을때 수익률 계산
        df['ror'] = np.where(df['sell_state'] & df['wallet_bull'],
                             df['sell_price'] * fee / df['real_buy_price'],
                             1)

        df['hpr'] = df['ror'].cumprod()  #총 수익률 계산
        #df.to_excel("btc.xlsx")  #앞의 내용을 엑셀에 저장, candlestick과 사용할 경우 오류

        return df['hpr'][-2]  #총 수익률 반환

    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        print('예외가 발생했습니다.', e)

# #1가지 가상화폐 테스트는 아래 이용
# tic = "BTC"
# hpr = get_hpr(tic)
# print(tic, hpr)

#메이저 가상화폐는 아래 이용
hprs = []
benefit = 0
for ticker in major_ticker:
    hpr = get_hpr(ticker)
    hprs.append((ticker, hpr))
    benefit = benefit+hpr
sorted_hprs = sorted(hprs, key=lambda x: x[1], reverse=True)
#print(sorted_hprs[:5])
print(sorted_hprs)
print(benefit/len(major_ticker))

# #테스트용(메이져)
# for i in range(10, 40):
#     benefit = 0
#     hprs = []
#     for ticker in major_ticker:
#         hpr = get_hpr(ticker, i/1000)
#         hprs.append((ticker, hpr))
#         benefit = benefit + hpr
#
#     sorted_hprs = sorted(hprs, key=lambda x: x[1], reverse=True)
#     print(i, sorted_hprs)
#     print(benefit / len(major_ticker))

# #모든 가상화폐 테스트는 아래 이용(1~2분 걸림,candlestick이용 권장,to_excel사용 미권장) 지금 안됌. 이유 모름
# tickers = pybithumb.get_tickers()
#
# hprs = []
# benefit = 0
# for ticker in tickers:
#     hpr = get_hpr(ticker)
#     hprs.append((ticker, hpr))
#     benefit = benefit + hpr
#
# sorted_hprs = sorted(hprs, key=lambda x: x[1], reverse=True)
# print(sorted_hprs[:5])
# print(sorted_hprs)
# print(benefit/len(tickers))
