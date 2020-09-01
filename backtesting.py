import numpy as np
import pybithumb

major_ticker = ["BTC", "LINK", "XRP", "ETH", "EOS", "BCH", "TRX", "BSV", "LTC", "ETC", "XLM", "QTUM", "ADA"]
#수익률을 계산하는 함수get_hpr

#현재 적용중 : 구매 : 골든 크로스, 장대양봉
#            판매 : 십자가(수정필요), 데드 크로스, 장대음봉
#            +수수료

def get_hpr(ticker):
    try:
        real_buy_price = 1  #실제로 구매했을때 가격 저장용
        wallet_bull = False  #매수 했을때 True, 매도 했을때 False
        df = pybithumb.get_ohlcv(ticker, interval="day")  #가상화폐의 open,high,low,close,volume 가져옴, 함수 수정으로 단위 변경 가능
        df = df['2019']  #기간 설정 가능

        df['ma5_yes'] = df['close'].rolling(window=5).mean().shift(1)  #어제 5일 평균(종가기준)
        df['ma20_yes'] = df['close'].rolling(window=20).mean().shift(1)  #어제 20일 평균(종가기준)
        df['ma5_yes2'] = df['close'].rolling(window=5).mean().shift(2)  #2일전 5일평균
        df['ma20_yes2'] = df['close'].rolling(window=20).mean().shift(2)  #2일전 20일평균

        df['volume_aver'] = 0  #총 거래량 초기화
        df['vr'] = df['volume'].rolling(window=len(df)).mean()  #총 거래량 평균
        vr = df['vr'].iloc[len(df)-1]  #총 거래량 평균 값 지정

        #총 거래량 저장
        for i in range(0, len(df)):
            df['volume_aver'].iloc[i] = vr

        #평균 거래량*2배 가 넘을때 True, 아니면 False
        df['bull_volume_2over'] = np.where(df['volume'].shift(1) > 2*df['volume_aver'],
                                     True,
                                     False)

        #장대양봉, 장대음봉(수정필요)
        df['jang_dae_p'] = df['close'].shift(1) - df['open'].shift(1) > df['open'].shift(1) * 0.005
        df['jang_dae_m'] = df['close'].shift(1) - df['open'].shift(1) < df['open'].shift(1) * 0.005

        #장대양봉, 장대음봉 + 평균 2배 거래량
        df['jang_dae_plus'] = np.where(df['bull_volume_2over'] & df['jang_dae_p'],
                                       True,
                                       False)
        df['jang_dae_minus'] = np.where(df['bull_volume_2over'] & df['jang_dae_m'],
                                        True,
                                        False)

        df['wallet_bull'] = wallet_bull  #지갑상태 초기화
        df['real_buy_price'] = real_buy_price  #실제 구매 가격 초기화

        #골든크로스 조건
        df['buy_bull_to'] = df['ma5_yes'] > df['ma20_yes']  #어제 5일평균 > 어제 20일평균
        df['buy_bull_yes'] = df['ma5_yes2'] < df['ma20_yes2']  #2일전 어제 5일평균 < 2일전 20일평균

        # 골든 크로스일때 시가, 장대양봉일때 종가로 구매(구매조건은 여기에 추가)
        df['buy_price'] = np.where((df['buy_bull_to'] & df['buy_bull_yes']) | df['jang_dae_plus'],
                                    df['open'],
                                    1)
        # 골든 크로스,장대양봉일때 상태 표시(구매조건은 여기에 추가)
        df['buy_state'] = np.where((df['buy_bull_to'] & df['buy_bull_yes']) | df['jang_dae_plus'],
                                   True,
                                   False)
        # 데드 크로스 일때 상태 표시
        df['dead_cross'] = np.where((df['ma5_yes'] < df['ma20_yes']) & (df['ma5_yes2'] > df['ma20_yes2']),
                                    True,
                                    False)

        #십자가조건일때(범위 수정 필요)
        df['sell_bull_cross'] = abs(df['close'].shift(1) - df['open'].shift(1)) < df['open'].shift(1)*0.001

        # 십자가, 데드크로스, 장대음봉 일때 종가로 판매(판매조건은 여기에 추가)
        df['sell_price'] = np.where(df['sell_bull_cross'] | df['dead_cross'] | df['jang_dae_minus'],
                                    df['open'],
                                    1)

        # 십자가, 데드크로스, 장대음봉 일때 판매 상태 표시(판매조건은 여기에 추가)
        df['sell_state'] = np.where(df['sell_bull_cross'] | df['dead_cross'] | df['jang_dae_minus'],
                               True,
                               False)

        # 구매 했을때 df['wallet_bull']에 True입력, 판매 했을때 False입력
        for i in range(0, len(df)-1):
            if not(df['wallet_bull'].iloc[i]) and df['buy_state'].iloc[i]:
                wallet_bull = True
            if df['wallet_bull'].iloc[i] and df['sell_state'].iloc[i]:
                wallet_bull = False
            df['wallet_bull'].iloc[i+1] = wallet_bull

        # 구매 했을때 df['real_buy_price']에 구매가격 저장
        for i in range(0, len(df)):
            if not(df['wallet_bull'].iloc[i]) and df['buy_state'].iloc[i]:
                real_buy_price = df['buy_price'].iloc[i]
            df['real_buy_price'].iloc[i] = real_buy_price

        fee = 0.995  #수수료

        #판매 했을때 수익률 계산
        df['ror'] = np.where(df['sell_state'] & df['wallet_bull'],
                             df['sell_price'] * fee / df['real_buy_price'],
                             1)

        df['hpr'] = df['ror'].cumprod()  #총 수익률 계산
        #df.to_excel("btc.xlsx")  #앞의 내용을 엑셀에 저장

        return df['hpr'][-2]  #총 수익률 반환
    except:
        return print("오류")

#1가지 가상화폐 테스트는 아래 3줄 이용
# tic = "BTC"
# hpr = get_hpr(tic)
# print(tic, hpr)

#모든 가상화폐 테스트는 아래 이용(2~3분걸림)
# tickers = pybithumb.get_tickers()
#
# hprs = []
# for ticker in tickers:
#     hpr = get_hpr(ticker)
#     hprs.append((ticker, hpr))
#
# sorted_hprs = sorted(hprs, key=lambda x:x[1], reverse=True)
# print(sorted_hprs[:5])
# print(sorted_hprs)

#메이저 가상화폐는 아래를 이용
hprs = []
benefit = 0
for ticker in major_ticker:
    hpr = get_hpr(ticker)
    hprs.append((ticker, hpr))
    benefit = benefit+hpr

sorted_hprs = sorted(hprs, key=lambda x:x[1], reverse=True)
print(sorted_hprs[:5])
print(sorted_hprs)
print(benefit/len(major_ticker))
