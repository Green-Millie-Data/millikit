from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# ── 기본 설정 ──────────────────────────────────────────
default_args = {
    "owner": "green",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="millikit_pipeline",
    default_args=default_args,
    description="개인정보 추출 자동화 파이프라인",
    schedule_interval=timedelta(minutes=30),  # 30분마다 폴링
    start_date=datetime(2026, 3, 30),
    catchup=False,
    tags=["millikit", "privacy"],
)

# ── Task 1: 그룹웨어 DB 폴링 ───────────────────────────
def poll_groupware_db(**context):
    import pymysql
    import os

    conn = pymysql.connect(
        host=os.environ["GW_DB_HOST"],
        port=int(os.environ.get("GW_DB_PORT", 13306)),
        user=os.environ["GW_DB_USER"],
        password=os.environ["GW_DB_PASSWORD"],
        database=os.environ["GW_DB_NAME"],
        charset="utf8mb4",
    )

    # 마지막으로 처리한 doc_id (추후 상태 저장 방식으로 개선)
    last_id = int(os.environ.get("LAST_DOC_ID", 0))

    sql = """
        SELECT ad.doc_id,
               ad.doc_no,
               ad.user_nm,
               ad.dept_nm,
               ad.doc_title,
               ad.doc_sts,
               adcw.doc_contents,
               ad.rep_dt,
               ad.end_dt
        FROM neos.teag_appdoc ad
        INNER JOIN neos.teag_appdoc_contents adc
            ON ad.doc_id = adc.doc_id
        INNER JOIN neos.teag_appdoc_contents_word adcw
            ON adc.doc_id = adcw.doc_id
        WHERE ad.form_id = 144
          AND ad.doc_sts IN (30, 90)
          AND ad.doc_id > %s
        ORDER BY ad.doc_id ASC
        LIMIT 10
    """

    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, (last_id,))
        rows = cur.fetchall()

    conn.close()

    if not rows:
        print("신규 결재 없음")
        return []

    print(f"{len(rows)}건 신규 결재 감지")
    # XCom으로 다음 태스크에 전달
    context["ti"].xcom_push(key="new_docs", value=rows)
    return rows


# ── Task 2: Claude 분석 → SQL 초안 생성 ──────────────
def analyze_with_claude(**context):
    import anthropic
    import json

    docs = context["ti"].xcom_pull(key="new_docs", task_ids="poll_groupware_db")
    if not docs:
        print("처리할 결재 없음")
        return

    client = anthropic.Anthropic()
    results = []

    for doc in docs:
        prompt = f"""
당신은 밀리의서재 개인정보 추출 SQL 전문가입니다.

아래 전자결재 내용을 분석하여:
1. 요청 유형을 분류하세요 (이벤트_참여자 / 알림_신청자 / 작품_열람대여자 / 기타)
2. 핵심 추출 조건을 정리하세요
3. BigQuery SQL 초안을 작성하세요

규칙:
- mem_seq(회원번호)만 추출 (개인정보 직접 추출 금지)
- 테이블은 millie-analysis 프로젝트만 사용
- 조건이 불명확하면 SQL 대신 확인 필요 사항을 명시

결재 제목: {doc['doc_title']}
결재 내용:
{doc['doc_contents']}

응답 형식 (JSON):
{{
  "doc_id": {doc['doc_id']},
  "request_type": "유형",
  "conditions": "핵심 조건 요약",
  "sql_draft": "SQL 또는 확인필요내용",
  "needs_review": true/false
}}
"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()
        # JSON 파싱
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
        except Exception:
            result = {"doc_id": doc["doc_id"], "raw": raw, "parse_error": True}

        results.append(result)
        print(f"[{doc['doc_id']}] {result.get('request_type', '?')} — 분석 완료")

    context["ti"].xcom_push(key="claude_results", value=results)
    return results


# ── Task 3: 결과 출력 (임시 — 추후 Slack 알림으로 교체) ─
def print_results(**context):
    import json

    results = context["ti"].xcom_pull(key="claude_results", task_ids="analyze_with_claude")
    if not results:
        print("결과 없음")
        return

    for r in results:
        print("=" * 60)
        print(f"doc_id     : {r.get('doc_id')}")
        print(f"유형       : {r.get('request_type')}")
        print(f"조건 요약  : {r.get('conditions')}")
        print(f"검토 필요  : {r.get('needs_review')}")
        print(f"SQL 초안   :\n{r.get('sql_draft')}")


# ── DAG 태스크 연결 ────────────────────────────────────
t1 = PythonOperator(task_id="poll_groupware_db",    python_callable=poll_groupware_db, dag=dag)
t2 = PythonOperator(task_id="analyze_with_claude",  python_callable=analyze_with_claude, dag=dag)
t3 = PythonOperator(task_id="print_results",        python_callable=print_results, dag=dag)

t1 >> t2 >> t3