import pandas as pd
import requests
import io
from app.database_mongo import db
from fastapi import HTTPException
from app.config import settings

# Google Sheets에서 CSV 파일을 다운로드하는 함수
def fetch_google_sheet_csv(sheet_id: str, sheet_name: str):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # 요청이 실패하면 예외를 발생시킵니다.
        # io.StringIO로 텍스트를 pandas DataFrame으로 변환
        df = pd.read_csv(io.StringIO(response.text))
        return df
    except Exception as e:
        print(f"Failed to fetch CSV file from {sheet_name}: {e}")
        return None


# 데이터베이스에 데이터를 업로드하는 함수 (기존 데이터를 지우고 새 데이터를 삽입)
def upload_to_mongodb(df: pd.DataFrame, db, collection_name: str):
    try:
        # 데이터프레임을 리스트 형태로 변환하여 MongoDB에 삽입
        data_dict = df.to_dict(orient="records")

        # 지정된 컬렉션에 데이터 삽입 전 기존 데이터 삭제
        collection = db[collection_name]
        collection.delete_many({})  # 컬렉션의 모든 문서를 삭제합니다.
        collection.insert_many(data_dict)  # 새 데이터를 삽입합니다.

        print(f"Data successfully uploaded to MongoDB in collection: {collection_name}")
    except Exception as e:
        print(f"Failed to upload data to MongoDB in collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload data to MongoDB: {collection_name}")


# 시트 데이터를 가져와 MongoDB에 업데이트하는 함수
def update_sheet_to_mongodb(sheet_id: str, sheet_name: str, collection_name: str):
    df = fetch_google_sheet_csv(sheet_id, sheet_name)
    if df is not None:
        print(f"CSV data fetched successfully from {sheet_name}.")
        upload_to_mongodb(df, db, collection_name)
    else:
        print(f"Failed to fetch CSV data from {sheet_name}.")


# 메인 함수
def main():
    sheet_id = settings.google_sheet_id

    # 시트 1 -> team_line 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트1", "team_line")

    # 시트 2 -> kbo_stadium_data 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트2", "kbo_stadium_data")

    # 시트 3 -> keep_notice_comment 컬렉션에 저장
    update_sheet_to_mongodb(sheet_id, "시트3", "keep_notice_comment")


if __name__ == "__main__":
    main()
