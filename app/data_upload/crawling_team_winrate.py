from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import schedule
from app.database_mongo import db



# 크롤링 함수
def crawl_kbo_team_winrate():
    """
    KBO 정규 시즌 팀별 승률 데이터를 크롤링하여 새로운 MongoDB 컬렉션에 저장하는 함수.
    과거 데이터를 삭제하고 새로운 데이터를 저장함.
    """

    new_collection = db['new_team_winrate']  # 새로운 컬렉션 설정

    url = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"  # 팀 순위 페이지
    current_date = datetime.now().strftime("%Y-%m-%d")  # 현재 날짜를 "yyyy-mm-dd" 형식으로 저장

    # 웹 드라이버 실행 및 페이지 열기
    driver = webdriver.Chrome()  # 크롬 드라이버 경로 설정 필요
    driver.get(url)

    try:
        # 순위 테이블이 로드될 때까지 대기
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tData")))

        # 순위 테이블 추출
        table = driver.find_element(By.CLASS_NAME, "tData")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # 데이터를 저장할 리스트
        data_lst = []

        # 팀별 데이터 추출
        for row in rows[1:]:  # 첫 번째 행은 헤더이므로 건너뛰기
            columns = row.find_elements(By.TAG_NAME, "td")

            if len(columns) < 7:
                continue  # 팀명이나 승률 데이터가 없으면 건너뛰기

            team = columns[1].text.strip()  # 팀명
            win_rate = columns[6].text.strip()  # 승률

            data_lst.append({
                "team": team,
                "win_rate": win_rate,
                "date": current_date  # 날짜 형식은 "yyyy-mm-dd"로 저장
            })

        # 현재 날짜에 해당하는 기존 데이터를 삭제
        new_collection.delete_many({"date": current_date})

        # MongoDB에 새로운 데이터 저장
        if data_lst:
            new_collection.insert_many(data_lst)
            print(f"팀별 승률 데이터를 {current_date}에 MongoDB의 새로운 컬렉션에 저장했습니다.")
        else:
            print("저장할 데이터가 없습니다.")

    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")

    finally:
        # 크롤링 완료 후 브라우저 종료
        driver.quit()

# 1분마다 실행되도록 스케줄링 (실험용)
schedule.every(1).minutes.do(crawl_kbo_team_winrate)

# 스케줄러가 실행되도록 루프
while True:
    schedule.run_pending()
    time.sleep(1)