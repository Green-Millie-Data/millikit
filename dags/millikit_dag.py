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

    # TODO (운영 전환 시): Airflow Variable로 LAST_DOC_ID 관리
    #   from airflow.models import Variable
    #   last_id = int(Variable.get("millikit_last_doc_id", default_var=0))
    #   → 처리 완료 후 Variable.set("millikit_last_doc_id", max(doc_id))
    #   → WHERE doc_id > last_id / ORDER BY doc_id ASC 로 변경

    # 테스트: 최신 10건 조회
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
        ORDER BY ad.doc_id DESC
        LIMIT 10
    """

    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql)
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
{doc['doc_contents']}

반드시 JSON으로만 응답:
{{"doc_id": {doc['doc_id']}, "type": "유형", "reason": "한 줄 근거"}}"""

        msg = client.messages.create(
            model="claude-4.5-haiku",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = msg.content[0].text.strip()
        try:
            if "```" in raw:
                json_str = raw.split("```json")[-1].split("```")[0].strip()
            else:
                start, end = raw.index("{"), raw.rindex("}") + 1
                json_str = raw[start:end]
            result = json.loads(json_str)
        except Exception:
            result = {"doc_id": doc["doc_id"], "type": "기타_특수", "reason": "파싱 실패", "parse_error": True}

        classified.append(result)
        print(f"[{doc['doc_id']}] {result.get('type')} — {result.get('reason')}")

    context["ti"].xcom_push(key="classified_docs", value=classified)
    return classified


# ── Task 3: SQL 생성 (2차 Claude — 스키마 + FewShot 로드) ─
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

    # 스키마 + FewShot 로드 (모든 결재에 공통 적용)
    schema_path = PROMPTS_DIR / "schema.md"
    fewshot_path = PROMPTS_DIR / "fewshot_all.md"
    schema = schema_path.read_text(encoding="utf-8") if schema_path.exists() else "(스키마 없음)"
    fewshot = fewshot_path.read_text(encoding="utf-8") if fewshot_path.exists() else "(FewShot 없음)"

    system_content = (
        "당신은 밀리의서재 개인정보 추출 BigQuery SQL 전문가입니다.\n\n"
        "## 규칙\n"
        "- mem_seq(회원번호)만 추출 — 개인정보 직접 추출 금지\n"
        "- 테이블은 millie-analysis GCP 프로젝트만 사용\n"
        "- 공통 필터 항상 포함: test_yn='N', millie_yn='N', dormant_yn='N', member_status != '탈퇴회원'\n"
        "- 조건 불명확 시 SQL 대신 확인 필요 사항을 명시\n"
        "- BigQuery 표준 SQL 문법 사용 (백틱으로 테이블 경로 감싸기)\n\n"
        "## 테이블 스키마\n"
        f"{schema}\n\n"
        "## 과거 처리 예시\n"
        f"{fewshot}"
    )

    client = anthropic.Anthropic()
    results = []

    for doc in docs:
        doc_type = type_map.get(doc["doc_id"], "기타_특수")

        # 변동 내용(결재 제목·본문)만 user로 분리
        user_content = (
            f"결재 유형: {doc_type}\n"
            f"결재 제목: {doc['doc_title']}\n"
            f"결재 내용:\n{doc['doc_contents']}\n\n"
            f"반드시 JSON으로만 응답:\n"
            f'{{"doc_id": {doc["doc_id"]}, "request_type": "{doc_type}", '
            f'"conditions": "핵심 조건 한 줄 요약", '
            f'"sql_draft": "SQL 또는 확인필요내용", '
            f'"needs_review": true또는false}}'
        )

        msg = client.messages.create(
            model="claude-4.5-sonnet",
            max_tokens=2000,
            system=[{
                "type": "text",
                "text": system_content,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_content}],
        )

        raw = msg.content[0].text.strip()
        try:
            if "```" in raw:
                json_str = raw.split("```json")[-1].split("```")[0].strip()
            else:
                start, end = raw.index("{"), raw.rindex("}") + 1
                json_str = raw[start:end]
            result = json.loads(json_str)
        except Exception as e:
            print(f"[{doc['doc_id']}] JSON 파싱 실패: {e}\nRAW: {raw[:300]}")
            result = {"doc_id": doc["doc_id"], "raw": raw, "parse_error": True}

        results.append(result)
        print(f"[{doc['doc_id']}] SQL 생성 완료 — needs_review={result.get('needs_review')}")

    context["ti"].xcom_push(key="sql_results", value=results)
    return results


# ── Task 4: Jira 하위작업 생성 + SQL 초안 댓글 ───────────
def create_jira_tickets(**context):
    import os
    import json
    import requests
    from requests.auth import HTTPBasicAuth

    docs = context["ti"].xcom_pull(key="new_docs", task_ids="poll_groupware_db")
    sql_results = context["ti"].xcom_pull(key="sql_results", task_ids="generate_sql")

    if not docs or not sql_results:
        print("처리할 데이터 없음")
        return

    base_url = os.environ["JIRA_BASE_URL"]
    auth = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    parent_issue = os.environ["JIRA_PARENT_ISSUE"]

    doc_map = {d["doc_id"]: d for d in docs}
    created_issues = []

    for r in sql_results:
        doc_id     = r.get("doc_id")
        doc        = doc_map.get(doc_id, {})
        req_type   = r.get("request_type", "기타_특수")
        conditions = r.get("conditions", "")
        sql_draft  = r.get("sql_draft", "")
        needs_review = r.get("needs_review", True)
        parse_error  = r.get("parse_error", False)

        doc_title = doc.get("doc_title", f"doc_id {doc_id}")
        requester = f"{doc.get('user_nm', '')} ({doc.get('dept_nm', '')})"

        # 1. 하위작업 생성
        issue_payload = {
            "fields": {
                "project": {"key": "MIDAS"},
                "parent": {"key": parent_issue},
                "summary": f"[개인정보 추출] {doc_title}",
                "issuetype": {"id": "10209"},
                "description": {
                    "type": "doc", "version": 1,
                    "content": [
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": f"그룹웨어 결재 doc_id: {doc_id}"}
                        ]},
                        {"type": "paragraph", "content": [
                            {"type": "text", "text": f"요청자: {requester}"}
                        ]},
                    ]
                }
            }
        }

        resp = requests.post(
            f"{base_url}/rest/api/3/issue",
            auth=auth, headers=headers, data=json.dumps(issue_payload)
        )
        resp.raise_for_status()
        issue_key = resp.json()["key"]
        print(f"[{doc_id}] Jira 하위작업 생성: {issue_key}")

        # 2. SQL 초안 댓글
        review_text = "⚠️ 검토 필요" if needs_review else "✅ 검토 불필요"
        if parse_error:
            comment_text = f"❌ SQL 파싱 오류\n\n원문:\n{sql_draft}"
            comment_blocks = [
                {"type": "paragraph", "content": [{"type": "text", "text": "❌ SQL 파싱 오류 — 수동 확인 필요"}]}
            ]
        else:
            comment_blocks = [
                {"type": "paragraph", "content": [
                    {"type": "text", "text": "📋 SQL 초안 자동 생성", "marks": [{"type": "strong"}]}
                ]},
                {"type": "paragraph", "content": [
                    {"type": "text", "text": f"유형: {req_type}  |  조건: {conditions}  |  {review_text}"}
                ]},
                {"type": "codeBlock", "attrs": {"language": "sql"},
                 "content": [{"type": "text", "text": sql_draft}]},
            ]

        comment_payload = {
            "body": {"type": "doc", "version": 1, "content": comment_blocks}
        }
        resp = requests.post(
            f"{base_url}/rest/api/3/issue/{issue_key}/comment",
            auth=auth, headers=headers, data=json.dumps(comment_payload)
        )
        resp.raise_for_status()
        print(f"[{doc_id}] {issue_key} SQL 댓글 추가 완료")

        # 안내문 댓글
        guide_blocks = [
            {"type": "paragraph", "content": [
                {"type": "text", "text": "📌 검토 안내", "marks": [{"type": "strong"}]}
            ]},
            {"type": "bulletList", "content": [
                {"type": "listItem", "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": "위 SQL 초안이 맞으면 → 상태를 "},
                    {"type": "text", "text": "검토완료", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": "로 전환해주세요. BigQuery 실행이 자동으로 시작됩니다."},
                ]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": "SQL 수정이 필요하면 → 수정된 SQL을 "},
                    {"type": "text", "text": "코드블록 댓글로 추가", "marks": [{"type": "strong"}]},
                    {"type": "text", "text": "한 뒤 검토완료로 전환해주세요. 가장 최근 코드블록 SQL이 실행됩니다."},
                ]}]},
                {"type": "listItem", "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": "조건 불명확 시 → 기안자에게 확인 후 재검토해주세요. 검토완료 전환 전까지 자동 실행되지 않습니다."},
                ]}]},
            ]},
        ]
        guide_payload = {
            "body": {"type": "doc", "version": 1, "content": guide_blocks}
        }
        resp = requests.post(
            f"{base_url}/rest/api/3/issue/{issue_key}/comment",
            auth=auth, headers=headers, data=json.dumps(guide_payload)
        )
        resp.raise_for_status()
        print(f"[{doc_id}] {issue_key} 안내문 댓글 추가 완료")
        created_issues.append(issue_key)

    context["ti"].xcom_push(key="created_issues", value=created_issues)
    return created_issues


# ── DAG 태스크 연결 ────────────────────────────────────
t1 = PythonOperator(task_id="poll_groupware_db",   python_callable=poll_groupware_db,   dag=dag)
t2 = PythonOperator(task_id="classify_doc",        python_callable=classify_doc,        dag=dag)
t3 = PythonOperator(task_id="generate_sql",        python_callable=generate_sql,        dag=dag)
t4 = PythonOperator(task_id="create_jira_tickets", python_callable=create_jira_tickets, dag=dag)

t1 >> t2 >> t3 >> t4
