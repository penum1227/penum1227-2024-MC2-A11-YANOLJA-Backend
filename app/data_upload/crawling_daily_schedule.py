from datetime import datetime
import schedule
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from app.database_mongo import db

# 사용할 컬렉션 이름 설정 (정규 시즌과 포스트 시즌 통합)
collection = db['kbo_schedule']


# 현재 달의 데이터를 삭제하는 함수
def delete_current_month_data():
    """
    MongoDB에서 현재 년도와 월에 해당하는 데이터를 삭제하는 함수
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.strftime("%m")  # 2자리 월

    # 해당 월의 데이터를 삭제
    collection.delete_many({
        "date": {
            "$regex": f"^{current_year}-{current_month}"  # 현재 년-월로 시작하는 날짜
        }
    })
    print(f"{current_year}년 {current_month}월 데이터를 삭제했습니다.")


# 크롤링 함수 정의 (정규 시즌과 포스트 시즌 통합)
def crawl_kbo_schedule(year, month, schedule_type):
    """
    정규 시즌과 포스트 시즌 크롤링을 위한 통합 함수.
    schedule_type에 따라 정규 시즌과 포스트 시즌 URL을 선택.

    :param year: 수집할 년도
    :param month: 수집할 월
    :param schedule_type: 'regular' 또는 'postseason'으로 시즌 구분
    """
    if schedule_type == "regular":
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=0,9,6"  # 정규 시즌
    else:
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=3,4,5,7"  # 포스트 시즌

    # 웹 드라이버 실행 및 페이지 열기
    driver = webdriver.Chrome()  # 경로 수정 필요
    driver.get(url)

    try:
        # 년도와 월 선택 요소가 로드될 때까지 대기
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ddlYear")))

        # 년도와 월 선택
        year_dropdown = Select(driver.find_element(By.ID, "ddlYear"))
        year_dropdown.select_by_value(year)

        month_dropdown = Select(driver.find_element(By.ID, "ddlMonth"))
        month_dropdown.select_by_value(month)

        # 경기 일정 테이블이 로드될 때까지 대기
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tbl-type06")))
        table = driver.find_element(By.CLASS_NAME, "tbl-type06")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # 데이터를 저장할 리스트
        data_lst = []
        game_data_by_date = {}  # 날짜별 경기를 저장할 딕셔너리

        # 경기 일정 정보 처리
        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            data = [column.text for column in columns]

            if len(data) == 0:
                continue  # 빈 행 건너뛰기
            elif len(data) == 9:
                previous_date = data[0]  # 날짜 저장
            elif len(data) == 8:
                data.insert(0, previous_date)  # 날짜가 생략된 행에 이전 날짜 삽입

            # 데이터 길이를 체크하여 처리
            if len(data) < 9:
                print("예상치 못한 데이터 형식:", data)
                continue  # 잘못된 데이터 형식은 건너뛰기

            # 날짜 및 경기 정보 가져오기
            raw_date = data[0]  # 날짜 형식: "08.02(금)"
            game_time = data[1]
            game_info = data[2]
            tv = data[5]
            stadium = data[7]
            note = data[8]

            # 날짜 형식을 "yyyy-mm-dd"로 변환
            try:
                date_str = raw_date.split('(')[0].strip()  # "08.02"로 변환
                date = datetime.strptime(date_str, "%m.%d").replace(year=int(year)).strftime("%Y-%m-%d")
            except ValueError:
                continue  # 날짜 형식이 맞지 않으면 해당 데이터는 건너뛰기

            # 경기 정보 분리 (team1 vs team2)
            if 'vs' in game_info:
                teams_score = game_info.split('vs')
                team1_info = teams_score[0]
                team2_info = teams_score[1]

                # 팀1과 점수 분리
                team1 = ''.join([i for i in team1_info if not i.isdigit()]).strip()
                team1_score = ''.join([i for i in team1_info if i.isdigit()])

                # 팀2와 점수 분리
                team2 = ''.join([i for i in team2_info if not i.isdigit()]).strip()
                team2_score = ''.join([i for i in team2_info if i.isdigit()])
            else:
                continue  # 경기 정보가 제대로 분리되지 않은 경우 건너뛰기

            # 취소된 경기 처리
            is_cancelled = False
            if '취소' in note:
                is_cancelled = True
                cancel_reason = note
                team1_score = "-"
                team2_score = "-"
            else:
                cancel_reason = "-"

                # 점수 정보가 없는 경우 "-"로 설정
                if not team1_score:
                    team1_score = "-"
                if not team2_score:
                    team2_score = "-"

            # 경기 결과 처리 (0: 승리, 1: 패배, 2: 무승부, -: 취소)
            if team1_score != "-" and team2_score != "-":
                if int(team1_score) > int(team2_score):
                    result = "0"  # team1 승리
                elif int(team1_score) < int(team2_score):
                    result = "1"  # team1 패배
                else:
                    result = "2"  # 무승부
            else:
                result = "-"

            # 날짜별 경기 저장
            if date not in game_data_by_date:
                game_data_by_date[date] = []
            game_data_by_date[date].append({
                "date": date,
                "team1": team1,
                "team1_score": team1_score,
                "team2": team2,
                "team2_score": team2_score,
                "result": result,
                "stadium": stadium,
                "cancel": is_cancelled,
                "cancelReason": cancel_reason,
                "game_time": game_time,
                "schedule_type": schedule_type  # 시즌 구분 추가
            })

        # 더블헤더 여부 처리
        for date, games in game_data_by_date.items():
            team_count = {}
            for game in games:
                team1 = game['team1']
                if team1 in team_count:
                    team_count[team1] += 1
                else:
                    team_count[team1] = 1

            for game in games:
                team1 = game['team1']
                if team_count[team1] > 1:
                    if game['game_time'] == min([g['game_time'] for g in games if g['team1'] == team1]):
                        double_header_order = 0  # 앞 경기
                    else:
                        double_header_order = 1  # 뒷 경기
                else:
                    double_header_order = -1  # 더블헤더 아님

                game["doubleHeaderGameOrder"] = double_header_order
                data_lst.append(game)

        return data_lst

    except TimeoutException:
        print(f"{year}년 {month}월에 경기가 없습니다.")
        return []

    finally:
        driver.quit()


# MongoDB에 데이터를 저장하는 함수
def save_to_mongodb(data):
    if data:
        collection.insert_many(data)
        print("데이터가 MongoDB에 저장되었습니다.")
    else:
        print("저장할 데이터가 없습니다.")


# 정규 시즌과 포스트 시즌 데이터를 수집하여 MongoDB에 저장하고 업데이트하는 함수
def update_kbo_schedule():
    now = datetime.now()
    current_year = now.year
    current_month = now.strftime("%m")  # 현재 월

    # 현재 월의 데이터를 삭제
    delete_current_month_data()

    # 정규 시즌 데이터 수집 및 저장
    print(f"{current_year}년 {current_month}월 정규 시즌 데이터를 수집합니다.")
    schedule_data = crawl_kbo_schedule(str(current_year), current_month, "regular")
    save_to_mongodb(schedule_data)

    # 포스트 시즌 데이터 수집 및 저장
    print(f"{current_year}년 {current_month}월 포스트 시즌 데이터를 수집합니다.")
    schedule_data = crawl_kbo_schedule(str(current_year), current_month, "postseason")
    save_to_mongodb(schedule_data)


# 매일 22시에 스케줄 업데이트
#schedule.every().day.at("22:00").do(update_kbo_schedule)
schedule.every(1).minutes.do(update_kbo_schedule)

# 스케줄러가 실행되도록 루프
while True:
    schedule.run_pending()
    time.sleep(1)
