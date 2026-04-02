from datetime import datetime, timedelta
from pathlib import Path
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
    schedule_interval=timedelta(minutes=30),
    start_date=datetime(2026, 3, 30),
    catchup=False,
    tags=["millikit", "privacy"],
)

PROMPTS_DIR = Path(__file__).parent / "prompts"

# 유형 → fewshot 파일명 매핑
FEWSHOT_FILES = {
    "이벤트_참여자":    "fewshot_event.md",
    "알림_신청자":      "fewshot_notify.md",
    "마케팅_구독조건":  "fewshot_marketing.md",
    "기타_특수":        "fewshot_etc.md",
}

# 이벤트_참여자 FewShot은 12개로 크므로 최근 N개만 사용
EVENT_FEWSHOT_LIMIT = 5


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
    context["ti"].xcom_push(key="new_docs", value=rows)
    return rows


# ── Task 2: 유형 분류 (1차 Claude — 가벼운 호출) ──────
def classify_doc(**context):
    import anthropic
    import json

    docs = context["ti"].xcom_pull(key="new_docs", task_ids="poll_groupware_db")
    if not docs:
        print("처리할 결재 없음")
        return

    client = anthropic.Anthropic()
    classified = []

    for doc in docs:
        prompt = f"""아래 전자결재의 추출 요청 유형을 분류하세요.

유형 정의:
- 이벤트_참여자: 이벤트 페이지 댓글 작성·미션 버튼 활성화 유저 (이벤트 시퀀스 + 기간 조건)
- 알림_신청자: 공개예정 페이지 '알림 받기' 신청 유저 (페이지 URL 기반)
- 마케팅_구독조건: 구독 상태·채널·기간 기반 LMS·PUSH 발송 대상 (특정 이벤트/도서 조건 없음)
- 기타_특수: 페이지 방문(tracking), 카테고리 대여, 특수 서비스(밀리플레이스·북클럽 등)

결재 제목: {doc['doc_title']}
결재 내용:
{doc['doc_contents'][:1000]}

반드시 JSON으로만 응답:
{{"doc_id": {doc['doc_id']}, "type": "유형", "reason": "한 줄 근거"}}"""

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = msg.content[0].text.strip()
        try:
            result = json.loads(raw.replace("```json", "").replace("```", "").strip())
        except Exception:
            result = {"doc_id": doc["doc_id"], "type": "기타_특수", "reason": "파싱 실패", "parse_error": True}

        classified.append(result)
        print(f"[{doc['doc_id']}] {result.get('type')} — {result.get('reason')}")

    context["ti"].xcom_push(key="classified_docs", value=classified)
    return classified


# ── Task 3: SQL 생성 (2차 Claude — 유형별 FewShot 로드) ─
def generate_sql(**context):
    import anthropic
    import json

    docs = context["ti"].xcom_pull(key="new_docs", task_ids="poll_groupware_db")
    classified = context["ti"].xcom_pull(key="classified_docs", task_ids="classify_doc")

    if not docs or not classified:
        print("처리할 데이터 없음")
        return

    # doc_id → 분류 결과 매핑
    type_map = {c["doc_id"]: c["type"] for c in classified}

    client = anthropic.Anthropic()
    results = []

    for doc in docs:
        doc_type = type_map.get(doc["doc_id"], "기타_특수")
        fewshot = _load_fewshot(doc_type)

        prompt = f"""당신은 밀리의서재 개인정보 추출 SQL 전문가입니다.

## 규칙
- mem_seq(회원번호)만 추출 — 개인정보 직접 추출 금지
- 테이블은 millie-analysis 프로젝트만 사용
- 공통 필터 항상 포함: test_yn='N', millie_yn='N', dormant_yn='N', member_status != '탈퇴회원'
- 조건 불명확 시 SQL 대신 확인 필요 사항 명시

## 과거 유사 처리 예시 [{doc_type}]
{fewshot}

## 신규 요청
결재 제목: {doc['doc_title']}
결재 내용:
{doc['doc_contents']}

반드시 JSON으로만 응답:
{{
  "doc_id": {doc['doc_id']},
  "request_type": "{doc_type}",
  "conditions": "핵심 조건 한 줄 요약",
  "sql_draft": "SQL 또는 확인필요내용",
  "needs_review": true또는false
}}"""

        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = msg.content[0].text.strip()
        try:
            result = json.loads(raw.replace("```json", "").replace("```", "").strip())
        except Exception:
            result = {"doc_id": doc["doc_id"], "raw": raw, "parse_error": True}

        results.append(result)
        print(f"[{doc['doc_id']}] SQL 생성 완료 — needs_review={result.get('needs_review')}")

    context["ti"].xcom_push(key="sql_results", value=results)
    return results


def _load_fewshot(doc_type: str) -> str:
    """유형에 맞는 FewShot 파일 로드. 이벤트_참여자는 최근 N개만."""
    fname = FEWSHOT_FILES.get(doc_type, "fewshot_etc.md")
    path = PROMPTS_DIR / fname

    if not path.exists():
        return "(FewShot 파일 없음)"

    content = path.read_text(encoding="utf-8")

    # 이벤트_참여자는 예시가 많으므로 마지막 N개만 사용
    if doc_type == "이벤트_참여자":
        sections = content.split("\n## ")
        header = sections[0]
        examples = sections[1:]
        selected = examples[-EVENT_FEWSHOT_LIMIT:]
        content = header + "\n## " + "\n## ".join(selected)

    return content


# ── Task 4: 결과 출력 (추후 Slack 알림으로 교체) ────────
def print_results(**context):
    results = context["ti"].xcom_pull(key="sql_results", task_ids="generate_sql")
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
t1 = PythonOperator(task_id="poll_groupware_db", python_callable=poll_groupware_db, dag=dag)
t2 = PythonOperator(task_id="classify_doc",      python_callable=classify_doc,      dag=dag)
t3 = PythonOperator(task_id="generate_sql",      python_callable=generate_sql,      dag=dag)
t4 = PythonOperator(task_id="print_results",     python_callable=print_results,     dag=dag)

t1 >> t2 >> t3 >> t4
