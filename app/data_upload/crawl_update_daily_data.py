import logging
from datetime import datetime
from playwright.sync_api import sync_playwright
from app.database_mongo import db
from app.models.baseball_game_model import VALID_TEAMS
from app.config import settings
from update_google_sheets_to_mongodb import update_sheet_to_mongodb
import schedule
import time
import gc

# MongoDB 컬렉션 설정
collection = db['kbo_all_schedule']
new_collection = db['kbo_team_winrate']
team_line_collection = db['team_line']
keep_notice_comment_collection = db['keep_notice_comment']
kbo_stadium_data_collection = db['kbo_stadium_data']

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 현재 달의 데이터를 삭제하는 함수
def delete_current_month_data():
    now = datetime.now()
    current_year = now.year
    current_month = now.strftime("%m")  # 2자리 월

    # 해당 월의 데이터를 삭제
    collection.delete_many({
        "date": {
            "$regex": f"^{current_year}-{current_month}"  # 현재 년-월로 시작하는 날짜
        }
    })
    logger.info(f"{current_year}년 {current_month}월 데이터를 삭제했습니다.")


# Playwright를 사용해 KBO 스케줄 데이터를 크롤링하는 함수
def crawl_kbo_schedule(year, month, schedule_type):
    logger.info(f"크롤링 시작: {year}년 {month}월 {schedule_type} 시즌 데이터")

    if schedule_type == "regular":
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=0,9,6"
    else:
        url = "https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId=3,4,5,7"

    data_lst = []
    game_data_by_date = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        # 연도와 월 선택
        page.select_option('#ddlYear', year)
        page.select_option('#ddlMonth', month)

        # 테이블을 기다린 후 데이터를 가져옴
        page.wait_for_selector('.tbl-type06')
        rows = page.query_selector_all('.tbl-type06 tr')

        for row in rows:
            columns = row.query_selector_all('td')
            data = [col.inner_text().strip() for col in columns]

            if len(data) == 0:
                continue
            elif len(data) == 9:
                previous_date = data[0]
            elif len(data) == 8:
                data.insert(0, previous_date)

            if len(data) < 9:
                logger.warning(f"Unexpected data format: {data}")
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
                result = "0" if int(team1_score) > int(team2_score) else "1" if int(team1_score) < int(
                    team2_score) else "2"

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

    logger.info(f"{year}년 {month}월 {schedule_type} 시즌 크롤링 완료")
    return data_lst


# MongoDB에 데이터를 저장하는 함수
def save_to_mongodb(data):
    if data:
        collection.insert_many(data)
        logger.info("데이터가 MongoDB에 저장되었습니다.")
        del data  # 메모리 정리
        gc.collect()
    else:
        logger.warning("저장할 데이터가 없습니다.")


# 팀별 승률 크롤링 함수
def crawl_kbo_team_winrate():
    logger.info("팀별 승률 크롤링 시작")

    url = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"
    current_date = datetime.now().strftime("%Y-%m-%d")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        page.wait_for_selector('.tData')
        rows = page.query_selector_all('.tData tr')

        data_lst = []
        for row in rows[1:]:
            columns = row.query_selector_all('td')
            if len(columns) < 7:
                continue

            team = columns[1].inner_text().strip()
            win_rate = columns[6].inner_text().strip()

            if team in VALID_TEAMS:
                data_lst.append({
                    "team": team,
                    "win_rate": win_rate,
                    "date": current_date
                })

        new_collection.delete_many({})

        if data_lst:
            new_collection.insert_many(data_lst)
            logger.info(f"팀별 승률 데이터를 {current_date}에 MongoDB에 저장했습니다.")
        else:
            logger.warning("저장할 데이터가 없습니다.")


# 기존 Google Sheets 데이터 업로드하는 메인 함수
def google_sheet_upload():
    logger.info("Google Sheets 데이터를 MongoDB로 업로드 시작")

    sheet_id = settings.google_sheet_id

    # 시트 1 -> team_line 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트1", "team_line")

    # 시트 2 -> kbo_stadium_data 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트2", "kbo_stadium_data")

    # 시트 3 -> keep_notice_comment 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트3", "keep_notice_comment")

    logger.info("Google Sheets 데이터를 MongoDB로 업로드 완료")


# 모든 데이터를 업데이트하는 함수
def update_all_data():
    now = datetime.now()
    current_year = now.year
    current_month = now.strftime("%m")

    logger.info(f"데이터 업데이트 시작: {current_year}년 {current_month}월")

    # 1. 현재 월의 정규 시즌 및 포스트 시즌 데이터 업데이트
    delete_current_month_data()

    try:
        schedule_data = crawl_kbo_schedule(str(current_year), current_month, "regular")
        if schedule_data:
            save_to_mongodb(schedule_data)
        else:
            logger.warning("정규 시즌 데이터를 가져오지 못했습니다.")

        schedule_data_post = crawl_kbo_schedule(str(current_year), current_month, "postseason")
        if schedule_data_post:
            save_to_mongodb(schedule_data_post)
        else:
            logger.warning("포스트 시즌 데이터를 가져오지 못했습니다.")
    except Exception as e:
        logger.error(f"데이터 크롤링 중 오류 발생: {e}")

    # 2. 팀별 승률 업데이트
    try:
        crawl_kbo_team_winrate()
    except Exception as e:
        logger.error(f"팀별 승률 크롤링 중 오류 발생: {e}")

    # 3. Google Sheets 데이터 업로드
    try:
        google_sheet_upload()
    except Exception as e:
        logger.error(f"Google Sheets 데이터 업로드 중 오류 발생: {e}")

    gc.collect()
    logger.info(f"{current_year}년 {current_month}월 데이터 업데이트 완료")


# 스케줄 설정 및 실행 함수
def run_scheduler():
    # 스케줄을 매일 특정 시간에 설정
    schedule.every(1).minutes.do(update_all_data)
    # schedule.every().day.at("02:00").do(update_all_data)
    # schedule.every().day.at("14:00").do(update_all_data)
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"스케줄 실행 중 오류 발생: {e}")
            time.sleep(60)


# 스케줄러 실행
if __name__ == "__main__":
    #run_scheduler()
    update_all_data()
