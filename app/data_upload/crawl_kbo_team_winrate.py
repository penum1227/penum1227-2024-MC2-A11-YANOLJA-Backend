# app/data_upload/crawl_kbo_team_winrate.py

from typing import List, Dict, Any
from datetime import datetime
import logging

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from app.utils.retry_decorator import retry_sync
from app.models.baseball_game_model import VALID_TEAMS

@retry_sync(max_retries=3, delay=2)
def crawl_kbo_team_winrate(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    팀별 승률을 크롤링하여 MongoDB에 저장합니다.
    """
    logger.info("팀별 승률 크롤링 시작")
    url = "https://www.koreabaseball.com/Record/TeamRank/TeamRankDaily.aspx"
    current_date = datetime.now().strftime("%Y-%m-%d")
    winrate_data = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(url, timeout=60000)

                # 테이블 로드 대기
                try:
                    page.wait_for_selector('.tData', timeout=60000)
                    logger.info("팀별 승률 테이블 로드 완료")
                except PlaywrightTimeoutError:
                    logger.error(f"팀별 승률 페이지 로딩 중 타임아웃 발생: {url}")
                    return []
                except Exception as e:
                    logger.error(f"팀별 승률 페이지 로딩 중 오류 발생: {e}")
                    return []

                rows = page.query_selector_all('.tData tr')

                for row in rows[1:]:
                    columns = row.query_selector_all('td')
                    if len(columns) < 7:
                        continue

                    team = columns[1].inner_text().strip()
                    win_rate = columns[6].inner_text().strip()

                    if team in VALID_TEAMS:
                        winrate_data.append({
                            "team": team,
                            "win_rate": win_rate,
                            "date": current_date
                        })

                logger.info("팀별 승률 크롤링 완료")
                return winrate_data

            except PlaywrightTimeoutError:
                logger.error(f"팀별 승률 페이지 로딩 중 타임아웃 발생: {url}")
            except Exception as e:
                logger.error(f"팀별 승률 크롤링 중 오류 발생: {e}")
            finally:
                browser.close()

    except Exception as e:
        logger.error(f"Playwright 실행 중 오류 발생: {e}")

    return winrate_data
