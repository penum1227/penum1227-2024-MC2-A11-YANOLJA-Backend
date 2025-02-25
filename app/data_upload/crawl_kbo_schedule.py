from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
import os

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from app.utils.retry_decorator import retry_sync
from app.models.baseball_game_model import VALID_TEAMS

@retry_sync(max_retries=3, delay=2)
def crawl_kbo_schedule(start_date: datetime, end_date: datetime, schedule_type: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Playwright를 사용해 KBO 스케줄 데이터를 동기적으로 크롤링합니다.
    지정한 기간 동안의 데이터를 크롤링합니다.
    
    Parameters:
        start_date (datetime): 크롤링 시작 날짜
        end_date (datetime): 크롤링 종료 날짜
        schedule_type (str): 시즌 타입 ("regular", "postseason", "trial")
        logger (logging.Logger): 로거 인스턴스
    
    Returns:
        List[Dict[str, Any]]: 크롤링된 게임 데이터 리스트
    """
    logger.info(f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} {schedule_type} 시즌 데이터 크롤링 시작")

    # 시즌 타입에 따라 series_ids 설정
    if schedule_type == "regular":
        series_ids = ["0", "9", "6"]
    elif schedule_type == "postseason":
        series_ids = ["3", "4", "5", "7"]
    elif schedule_type == "trial":
        series_ids = ["1"]
    else:
        logger.error(f"알 수 없는 시즌 타입: {schedule_type}")
        return []

    # 여러 series_ids를 쉼표로 구분하여 하나의 URL로 결합
    series_ids_str = ",".join(series_ids)
    url = f"https://www.koreabaseball.com/Schedule/Schedule.aspx?seriesId={series_ids_str}"
    logger.info(f"접속 중: {url}")

    crawled_data = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, timeout=60000)  # 60초 타임아웃

                # 연도와 월 선택
                current_year = start_date.year
                current_month = start_date.month

                try:
                    page.select_option('#ddlYear', value=str(current_year))
                    page.select_option('#ddlMonth', value=str(current_month).zfill(2))
                    logger.info(f"선택된 연도: {current_year}, 선택된 월: {current_month:02d} ({schedule_type} 시즌)")
                except Exception as e:
                    logger.warning(f"{current_year}년 {current_month}월 {schedule_type} 시즌 선택 불가: {e}")
                    return []  # 시즌 선택에 실패하면 전체 크롤링 중단

                # 테이블이 로드될 때까지 대기
                try:
                    page.wait_for_selector('.tbl-type06', timeout=30000)
                    logger.info(f"{current_year}년 {current_month}월 {schedule_type} 시즌 테이블 로드 완료")
                except PlaywrightTimeoutError:
                    logger.warning(f"테이블 로드 대기 중 타임아웃 발생: {current_year}년 {current_month}월 {schedule_type} 시즌 데이터가 없습니다.")
                    return []  # 테이블 로드 실패 시 크롤링 중단
                except Exception as e:
                    logger.warning(f"테이블 로드 대기 중 오류 발생: {e}")
                    return []  # 테이블 로드 실패 시 크롤링 중단

                rows = page.query_selector_all('.tbl-type06 tr')

                previous_date = ""
                game_data_by_date = []

                for row in rows:
                    columns = row.query_selector_all('td')
                    data = [col.inner_text().strip() for col in columns]

                    if not data:
                        continue
                    elif len(data) == 9:
                        previous_date = data[0]
                    elif len(data) == 8:
                        data.insert(0, previous_date)

                    if len(data) < 9:
                        logger.warning(f"예상치 못한 데이터 형식: {data}")
                        continue

                    raw_date, game_time, game_info, _, _, tv, _, stadium, note = data

                    try:
                        date_str = raw_date.split('(')[0].strip()
                        game_date = datetime.strptime(f"{current_year}-{date_str}", "%Y-%m.%d").strftime("%Y-%m-%d")
                        game_date_dt = datetime.strptime(game_date, "%Y-%m-%d")
                        if not (start_date <= game_date_dt <= end_date):
                            continue  # 지정한 기간에 해당하지 않는 게임은 제외
                    except ValueError:
                        logger.warning(f"잘못된 날짜 형식: {raw_date}")
                        continue

                    if 'vs' in game_info:
                        teams_score = game_info.split('vs')
                        if len(teams_score) != 2:
                            logger.warning(f"잘못된 팀 정보 형식: {game_info}")
                            continue
                        team1_info, team2_info = teams_score[0], teams_score[1]
                        team1 = ''.join(filter(str.isalpha, team1_info)).strip()
                        team1_score = ''.join(filter(str.isdigit, team1_info))
                        team2 = ''.join(filter(str.isalpha, team2_info)).strip()
                        team2_score = ''.join(filter(str.isdigit, team2_info))
                    else:
                        continue

                    # note에 "-" 외에 다른 문자열이 있다면 취소로 간주합니다.
                    is_cancelled = (note.strip() != "-")
                    cancel_reason = note if is_cancelled else "-"
                    # 취소된 경우, 점수는 "-"로 설정
                    if is_cancelled:
                        team1_score = "-"
                        team2_score = "-"

                    result = "-"
                    if team1_score != "-" and team2_score != "-":
                        if int(team1_score) > int(team2_score):
                            result = "0"  # 팀1 승리
                        elif int(team1_score) < int(team2_score):
                            result = "1"  # 팀2 승리
                        else:
                            result = "2"  # 무승부

                    game_data_by_date.append({
                        "date": game_date,
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

                # 더블 헤더 순서 지정: 팀과 날짜별로 그룹화하여 순서를 부여합니다.
                from collections import defaultdict

                team_date_game_times = defaultdict(list)
                for game in game_data_by_date:
                    key = (game['team1'], game['date'])
                    team_date_game_times[key].append(game['game_time'])

                for game in game_data_by_date:
                    key = (game['team1'], game['date'])
                    if len(team_date_game_times[key]) > 1:
                        sorted_times = sorted(team_date_game_times[key])
                        double_header_order = sorted_times.index(game['game_time'])
                        game["doubleHeaderGameOrder"] = double_header_order
                    else:
                        game["doubleHeaderGameOrder"] = -1
                    crawled_data.append(game)

            except PlaywrightTimeoutError:
                logger.error(f"페이지 로딩 중 타임아웃 발생: {url}")
            except Exception as e:
                logger.error(f"KBO 스케줄 크롤링 중 오류 발생: {e}")
            finally:
                browser.close()

    except Exception as e:
        logger.error(f"Playwright 실행 중 오류 발생: {e}")

    logger.info(f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} {schedule_type} 시즌 데이터 크롤링 완료")
    return crawled_data

def experimental_update(seasons: List[str], years: List[int], months: List[int], logger: logging.Logger):
    """
    사용자가 원하는 시즌, 연도, 월의 데이터를 삭제하고 업데이트하는 실험 함수입니다.
    
    Parameters:
        seasons (List[str]): 시즌 타입 리스트 (예: ["regular", "postseason", "trial"])
        years (List[int]): 연도 리스트 (예: [2023, 2024])
        months (List[int]): 월 리스트 (예: [1, 2, 3])
        logger (logging.Logger): 로거 인스턴스
    """
    from app.database_mongo import db_pymongo
    from datetime import datetime

    # MongoDB 컬렉션 설정
    kbo_all_schedule_collection = db_pymongo['kbo_all_schedule']

    for season in seasons:
        for year in years:
            for month in months:
                logger.info(f"=== {season.capitalize()} 시즌, {year}년 {month}월 데이터 삭제 및 업데이트 시작 ===")

                # 1. 데이터 삭제
                try:
                    year_str = str(year)
                    month_str = str(month).zfill(2)
                    regex_pattern = f"^{year_str}-{month_str}"
                    result = kbo_all_schedule_collection.delete_many({
                        "date": {
                            "$regex": regex_pattern  # 지정한 년-월로 시작하는 날짜
                        },
                        "schedule_type": season
                    })
                    logger.info(f"{year_str}년 {month_str}월 {season} 시즌의 {result.deleted_count}개 데이터를 삭제했습니다.")
                except Exception as e:
                    logger.error(f"{year}년 {month}월 {season} 시즌 데이터 삭제 중 오류 발생: {e}")
                    continue  # 삭제에 실패하면 다음 조합으로 넘어감

                # 2. 데이터 크롤링
                try:
                    # 기간 설정: 해당 연도와 월의 첫 날과 마지막 날
                    start_date = datetime(year, month, 1)
                    if month == 12:
                        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

                    logger.info(f"크롤링 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

                    crawled_data = crawl_kbo_schedule(start_date, end_date, season, logger)

                    # 3. 데이터 삽입
                    if crawled_data:
                        kbo_all_schedule_collection.insert_many(crawled_data)
                        logger.info(f"{year_str}년 {month_str}월 {season} 시즌 데이터를 MongoDB에 저장했습니다.")
                    else:
                        logger.warning(f"{year_str}년 {month_str}월 {season} 시즌에 저장할 데이터가 없습니다.")

                except Exception as e:
                    logger.error(f"{year}년 {month}월 {season} 시즌 데이터 크롤링 및 저장 중 오류 발생: {e}")

    logger.info("=== 실험 데이터 삭제 및 업데이트 완료 ===")

if __name__ == "__main__":
    from app.utils.logger import setup_logger

    # 로거 설정
    logger = setup_logger("crawl_kbo_schedule", "logs/crawl_kbo_schedule.log")

    # 실험을 위한 시즌, 연도, 월 리스트 설정
    experiment_seasons = ["regular", "postseason", "trial"]  # 원하는 시즌 타입 리스트
    experiment_years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]  # 원하는 연도 리스트
    experiment_months = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # 원하는 월 리스트

    # 실험 함수 실행
    experimental_update(experiment_seasons, experiment_years, experiment_months, logger)

#python -m app.data_upload.crawl_kbo_schedule
