# app/data_upload/crawl_update_daily_data.py

import logging
import gc
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

import schedule
from pymongo import ASCENDING

from app.database_mongo import db_pymongo
from app.utils.logger import setup_logger
from app.data_upload.crawl_kbo_schedule import crawl_kbo_schedule
from app.data_upload.crawl_kbo_team_winrate import crawl_kbo_team_winrate
from app.data_upload.update_google_sheets_to_mongodb import google_sheet_upload

# 로깅 설정
logger = setup_logger("kbo_crawler", "logs/kbo_crawler.log")

# MongoDB 컬렉션 설정
kbo_all_schedule_collection = db_pymongo['kbo_all_schedule']
kbo_team_winrate_collection = db_pymongo['kbo_team_winrate']
team_line_collection = db_pymongo['team_line']
keep_notice_comment_collection = db_pymongo['keep_notice_comment']
kbo_stadium_data_collection = db_pymongo['kbo_stadium_data']


def setup_indexes():
    """
    MongoDB 인덱스를 설정합니다.
    """
    try:
        kbo_all_schedule_collection.create_index([("date", ASCENDING)])
        kbo_team_winrate_collection.create_index([("team", ASCENDING), ("date", ASCENDING)])
        logger.info("MongoDB 인덱스 설정 완료")
    except Exception as e:
        logger.error(f"MongoDB 인덱스 설정 중 오류 발생: {e}")


def delete_current_day_data():
    """
    현재 날짜의 데이터를 MongoDB에서 삭제합니다.
    """
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        result = kbo_all_schedule_collection.delete_many({"date": today})
        logger.info(f"{today}의 {result.deleted_count}개 데이터를 삭제했습니다.")
    except Exception as e:
        logger.error(f"현재 날짜의 데이터 삭제 중 오류 발생: {e}")


def update_daily_data():
    """
    당일 데이터를 업데이트하는 함수입니다.
    """
    logger.info("당일 데이터 업데이트 시작")

    # 1. 현재 날짜의 데이터 삭제
    delete_current_day_data()

    # 2. 시범, 정규, 포스트 시즌 데이터 크롤링 및 저장
    seasons = ["trial", "regular", "postseason"]

    today = datetime.now()
    start_date = today
    end_date = today

    for season_type in seasons:
        try:
            logger.info(f"{season_type.capitalize()} 시즌 데이터 크롤링 시작")
            crawled_data = crawl_kbo_schedule(start_date, end_date, season_type, logger)
            if crawled_data:
                kbo_all_schedule_collection.insert_many(crawled_data)
                logger.info(f"{season_type.capitalize()} 시즌 데이터를 MongoDB에 저장했습니다.")
            else:
                logger.warning(f"{season_type.capitalize()} 시즌에 저장할 데이터가 없습니다.")
        except Exception as e:
            logger.error(f"{season_type.capitalize()} 시즌 데이터 크롤링 및 저장 중 오류 발생: {e}")

    # 3. 팀별 승률 업데이트 (컬렉션 전체 삭제 후 최신 승률 데이터만 저장)
    try:
        winrate_data = crawl_kbo_team_winrate(logger)
        if winrate_data:
            # 전체 컬렉션 삭제 (업데이트 시 이전 승률 데이터 모두 제거)
            kbo_team_winrate_collection.delete_many({})
            kbo_team_winrate_collection.insert_many(winrate_data)
            logger.info("팀별 승률 데이터를 MongoDB에 저장했습니다.")
        else:
            logger.warning("팀별 승률 데이터를 저장할 데이터가 없습니다.")
    except Exception as e:
        logger.error(f"팀별 승률 크롤링 및 저장 중 오류 발생: {e}")

    # 4. Google Sheets 데이터 업로드
    try:
        google_sheet_upload()
    except Exception as e:
        logger.error(f"Google Sheets 데이터 업로드 중 오류 발생: {e}")

    # 5. Garbage Collection
    gc.collect()
    logger.info("당일 데이터 업데이트 완료")


def run_scheduler():
    """
    스케줄러를 설정하고 실행합니다.
    """
    # 경기 전후 중요 업데이트
    schedule.every().day.at("02:00").do(update_daily_data)  # 새벽: 전날 경기 결과 최종 반영
    schedule.every().day.at("10:00").do(update_daily_data)  # 오전: 경기 일정 업데이트
    schedule.every().day.at("00:30").do(update_daily_data)  # 연장전 반영 및 승률 업데이트

    # 경기 진행 중 (13:00~22:00) 10분 단위 업데이트
    for hour in range(13, 23):  # 13시 ~ 22시 (22시 50분까지)
        for minute in range(0, 60, 10):  # 매 10분마다
            schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(update_daily_data)

    logger.info("스케줄러가 시작되었습니다")

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"스케줄러 실행 중 오류 발생: {e}")
            time.sleep(60)


if __name__ == "__main__":
    # MongoDB 인덱스 설정
    setup_indexes()
    # 필요 시 아래 update_daily_data()의 주석을 해제하여 즉시 업데이트 실행 가능
    #update_daily_data()
    # 스케줄러 실행 (데일리 업데이트를 자동으로 수행)
    run_scheduler()
