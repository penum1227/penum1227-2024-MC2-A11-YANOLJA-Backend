from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from app.database_mongo import db
import schedule
import time
import pandas as pd


collection = db['kbo_all_schedule']
new_collection = db['kbo_team_winrate']  # 새로운 컬렉션 설정
excel_collection = db['team_line']
file_path = '승리지쿄대사.xlsx'

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


# 정규 시즌과 포스트 시즌 크롤링을 위한 통합 함수
def crawl_kbo_schedule(year, month, schedule_type):
    """
    정규 시즌과 포스트 시즌 크롤링을 위한 통합 함수.
    schedule_type에 따라 정규 시즌과 포스트 시즌 URL을 선택.
    """
    if schedule_type == "regular":
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=0,9,6"  # 정규 시즌
    else:
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=3,4,5,7"  # 포스트 시즌

    driver = webdriver.Chrome()  # 크롬 드라이버 경로 설정 필요
    driver.get(url)

    try:
        # 년도와 월 선택
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ddlYear")))
        year_dropdown = Select(driver.find_element(By.ID, "ddlYear"))
        year_dropdown.select_by_value(year)

        month_dropdown = Select(driver.find_element(By.ID, "ddlMonth"))
        month_dropdown.select_by_value(month)

        # 경기 일정 테이블 추출
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tbl-type06")))
        table = driver.find_element(By.CLASS_NAME, "tbl-type06")
        rows = table.find_elements(By.TAG_NAME, "tr")

        # 데이터를 저장할 리스트
        data_lst = []
        game_data_by_date = {}

        for row in rows:
            columns = row.find_elements(By.TAG_NAME, "td")
            data = [column.text for column in columns]
            if len(data) == 0:
                continue
            elif len(data) == 9:
                previous_date = data[0]
            elif len(data) == 8:
                data.insert(0, previous_date)

            if len(data) < 9:
                print("예상치 못한 데이터 형식:", data)
                continue

            raw_date = data[0]
            game_time = data[1]
            game_info = data[2]
            tv = data[5]
            stadium = data[7]
            note = data[8]

            try:
                date_str = raw_date.split('(')[0].strip()
                date = datetime.strptime(date_str, "%m.%d").replace(year=int(year)).strftime("%Y-%m-%d")
            except ValueError:
                continue

            if 'vs' in game_info:
                teams_score = game_info.split('vs')
                team1_info = teams_score[0]
                team2_info = teams_score[1]
                team1 = ''.join([i for i in team1_info if not i.isdigit()]).strip()
                team1_score = ''.join([i for i in team1_info if i.isdigit()])
                team2 = ''.join([i for i in team2_info if not i.isdigit()]).strip()
                team2_score = ''.join([i for i in team2_info if i.isdigit()])
            else:
                continue

            is_cancelled = '취소' in note
            cancel_reason = note if is_cancelled else "-"
            team1_score = "-" if is_cancelled else team1_score or "-"
            team2_score = "-" if is_cancelled else team2_score or "-"

            result = "-"
            if team1_score != "-" and team2_score != "-":
                result = "0" if int(team1_score) > int(team2_score) else "1" if int(team1_score) < int(team2_score) else "2"

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
                "schedule_type": schedule_type
            })

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
                double_header_order = -1
                if team_count[team1] > 1:
                    if game['game_time'] == min([g['game_time'] for g in games if g['team1'] == team1]):
                        double_header_order = 0
                    else:
                        double_header_order = 1

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


# 정규 시즌 팀별 승률 크롤링 함수
def crawl_kbo_team_winrate():
    url = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"
    current_date = datetime.now().strftime("%Y-%m-%d")

    driver = webdriver.Chrome()  # 크롬 드라이버 경로 설정 필요
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "tData")))
        table = driver.find_element(By.CLASS_NAME, "tData")
        rows = table.find_elements(By.TAG_NAME, "tr")

        data_lst = []
        for row in rows[1:]:
            columns = row.find_elements(By.TAG_NAME, "td")
            if len(columns) < 7:
                continue

            team = columns[1].text.strip()
            win_rate = columns[6].text.strip()

            data_lst.append({
                "team": team,
                "win_rate": win_rate,
                "date": current_date
            })

        new_collection.delete_many({})

        if data_lst:
            new_collection.insert_many(data_lst)
            print(f"팀별 승률 데이터를 {current_date}에 MongoDB에 저장했습니다.")
        else:
            print("저장할 데이터가 없습니다.")

    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")

    finally:
        driver.quit()
# 엑셀 파일 데이터를 처리하는 함수
def process_excel_file():
    """
    엑셀 파일을 읽어와 'date' 열을 추가하고 데이터를 MongoDB에 저장하는 함수.
    과거 데이터를 삭제하고 새 데이터를 저장.
    """
    df = pd.read_excel(file_path)
    # 현재 날짜를 "yyyy-mm-dd" 형태로 저장
    current_date = datetime.now().strftime("%Y-%m-%d")
    # 'date' 열 추가
    df['date'] = current_date
    # MongoDB에 저장하기 전에 과거 데이터를 삭제 (현재 날짜보다 이전 날짜의 모든 데이터 삭제)
    excel_collection.delete_many({})
    # MongoDB에 저장
    if not df.empty:
        data_dict = df.to_dict("records")
        excel_collection.insert_many(data_dict)
        print(f"팀별 대사 데이터를 {current_date}에 MongoDB에 저장했습니다.")
    else:
        print("팀별 대사 데이터가 없습니다.")

# 모든 데이터를 업데이트하는 함수
def update_all_data():
    now = datetime.now()
    current_year = now.year
    current_month = now.strftime("%m")
    # 1. 현재 월의 정규 시즌 및 포스트 시즌 데이터 업데이트
    delete_current_month_data()
    print(f"{current_year}년 {current_month}월 정규 시즌 데이터를 수집합니다.")
    schedule_data = crawl_kbo_schedule(str(current_year), current_month, "regular")
    save_to_mongodb(schedule_data)

    print(f"{current_year}년 {current_month}월 포스트 시즌 데이터를 수집합니다.")
    schedule_data = crawl_kbo_schedule(str(current_year), current_month, "postseason")
    save_to_mongodb(schedule_data)
    # 2. 팀별 승률 데이터 업데이트
    crawl_kbo_team_winrate()
    # 3. 대사 업데이트
    process_excel_file()


# 매일 22시에 모든 데이터를 업데이트하도록 설정
#schedule.every().day.at("17:00").do(update_all_data)
#schedule.every().day.at("17:00").do(update_all_data)
#schedule.every().day.at("17:00").do(update_all_data)
#schedule.every().day.at("20:00").do(update_all_data)
#schedule.every().day.at("20:00").do(update_all_data)
#schedule.every().day.at("20:00").do(update_all_data)
#schedule.every().day.at("22:00").do(update_all_data)
#schedule.every().day.at("22:00").do(update_all_data)
#schedule.every().day.at("22:00").do(update_all_data)
schedule.every(1).minutes.do(update_all_data)

# 스케줄러가 실행되도록 루프
while True:
    schedule.run_pending()
    time.sleep(1)
