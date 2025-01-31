# app/data_upload/update_google_sheets_to_mongodb.py

import pandas as pd
import requests
import io
from typing import Optional
from pymongo.database import Database
from fastapi import HTTPException

from app.utils.retry_decorator import retry_sync
from app.database_mongo import db_pymongo
from app.config import settings
from app.utils.logger import setup_logger
import logging

# 로거 설정
logger = setup_logger("update_google_sheets", "logs/update_google_sheets.log")

@retry_sync(max_retries=3, delay=2)
def fetch_google_sheet_csv(sheet_id: str, sheet_name: str, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Google Sheets에서 CSV 파일을 다운로드하여 DataFrame으로 반환.
    """
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        logger.info(f"Successfully fetched CSV from sheet: {sheet_name}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch CSV file from {sheet_name}: {e}")
        return None

@retry_sync(max_retries=3, delay=2)
def upload_to_mongodb(dataframe: pd.DataFrame, db: Database, collection_name: str, logger: logging.Logger):
    """
    데이터프레임을 MongoDB에 업로드 (기존 데이터를 삭제하고 새 데이터 삽입).
    """
    try:
        data_records = dataframe.to_dict(orient="records")
        collection = db[collection_name]
        collection.delete_many({})
        if data_records:
            collection.insert_many(data_records)
            logger.info(f"Data successfully uploaded to MongoDB in collection: {collection_name}")
        else:
            logger.warning(f"No data to upload for collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to upload data to MongoDB in collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload data to MongoDB: {collection_name}")

def update_sheet_to_mongodb(sheet_id: str, sheet_name: str, collection_name: str, logger: logging.Logger):
    """
    특정 시트의 데이터를 MongoDB에 업데이트.
    """
    df = fetch_google_sheet_csv(sheet_id, sheet_name, logger)
    if df is not None:
        logger.info(f"CSV data fetched successfully from {sheet_name}.")
        upload_to_mongodb(df, db_pymongo, collection_name, logger)
    else:
        logger.error(f"Failed to fetch CSV data from {sheet_name}.")

def google_sheet_upload():
    """
    Google Sheets 데이터를 MongoDB에 업로드하는 함수입니다.
    """
    logger.info("Google Sheets 데이터를 MongoDB로 업로드 시작")

    sheet_id = settings.google_sheet_id

    # 시트 1 -> team_line 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트1", "team_line", logger)

    # 시트 2 -> kbo_stadium_data 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트2", "kbo_stadium_data", logger)

    # 시트 3 -> keep_notice_comment 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트3", "keep_notice_comment", logger)

    logger.info("Google Sheets 데이터를 MongoDB로 업로드 완료")

def main():
    google_sheet_upload()

if __name__ == "__main__":
    main()


# python -m app.update_google_sheets_to_mongodb