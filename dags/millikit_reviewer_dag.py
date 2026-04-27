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
    dag_id="millikit_reviewer",
    default_args=default_args,
    description="검토완료 Jira 하위작업 감지 → BigQuery 실행 → GCS → Jira 댓글",
    schedule_interval="0,30 0-9 * * 1-5",  # KST 09:00~18:30, 평일
    start_date=datetime(2026, 4, 23),
    catchup=False,
    tags=["millikit", "privacy"],
)


# ── Task 1: 검토완료 티켓 폴링 ────────────────────────
def poll_jira_status(**context):
    import os
    import requests
    from requests.auth import HTTPBasicAuth

    base_url = os.environ["JIRA_BASE_URL"]
    auth = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
    headers = {"Accept": "application/json"}

    jql = 'project = MIDAS AND issuetype = "하위 작업" AND status = "검토완료" AND summary ~ "[개인정보 추출]"'
    params = {"jql": jql, "fields": "summary,status,parent", "maxResults": 50}

    resp = requests.get(
        f"{base_url}/rest/api/3/search",
        auth=auth, headers=headers, params=params
    )
    resp.raise_for_status()
    issues = resp.json().get("issues", [])

    if not issues:
        print("검토완료 티켓 없음 — 스킵")
        return []

    keys = [i["key"] for i in issues]
    print(f"{len(keys)}건 검토완료 감지: {keys}")
    context["ti"].xcom_push(key="review_ready_issues", value=keys)
    return keys


# ── Task 2: 댓글에서 최종 SQL 추출 → BQ 실행 → GCS → Jira 댓글 ────
def execute_and_deliver(**context):
    import os
    import re
    import json
    import requests
    from requests.auth import HTTPBasicAuth

    issue_keys = context["ti"].xcom_pull(key="review_ready_issues", task_ids="poll_jira_status")
    if not issue_keys:
        print("처리할 티켓 없음")
        return

    base_url = os.environ["JIRA_BASE_URL"]
    auth = HTTPBasicAuth(os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    for key in issue_keys:
        # ── 댓글 목록 조회 ─────────────────────────────
        resp = requests.get(
            f"{base_url}/rest/api/3/issue/{key}/comment?orderBy=created",
            auth=auth, headers=headers
        )
        resp.raise_for_status()
        comments = resp.json().get("comments", [])

        # ── 가장 최근 코드블록 SQL 추출 ────────────────
        # Jira ADF: codeBlock 노드에서 SQL 추출 (역순 탐색)
        final_sql = None
        for comment in reversed(comments):
            sql = _extract_sql_from_adf(comment.get("body", {}))
            if sql:
                final_sql = sql
                print(f"[{key}] 최종 SQL 추출 완료 (댓글 id={comment['id']})")
                break

        if not final_sql:
            print(f"[{key}] SQL 코드블록 없음 — 스킵")
            _post_comment(base_url, key, auth, headers,
                          "⚠️ 검토완료 상태이나 SQL 코드블록을 찾을 수 없습니다. 댓글에 SQL을 추가 후 다시 전환해주세요.")
            continue

        print(f"[{key}] 실행할 SQL:\n{final_sql[:300]}")

        # TODO: BigQuery 실행 + CSV 추출
        # TODO: GCS 업로드 + Signed URL 생성 (7일 만료)
        # TODO: 작업 완료 상태로 전환

        # 임시: SQL 확인 댓글
        _post_comment(base_url, key, auth, headers,
                      f"⏳ SQL 확인 완료. BigQuery 실행 자동화 준비 중입니다.\n\n실행 예정 SQL:\n```sql\n{final_sql}\n```")
        print(f"[{key}] SQL 확인 댓글 추가 완료")


def _extract_sql_from_adf(body: dict) -> str:
    """Jira ADF body에서 codeBlock 노드의 텍스트를 추출."""
    if not body:
        return ""
    for block in body.get("content", []):
        if block.get("type") == "codeBlock":
            texts = [n.get("text", "") for n in block.get("content", []) if n.get("type") == "text"]
            sql = "".join(texts).strip()
            if sql:
                return sql
    return ""


def _post_comment(base_url, issue_key, auth, headers, text: str):
    payload = {
        "body": {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [
                {"type": "text", "text": text}
            ]}]
        }
    }
    requests.post(
        f"{base_url}/rest/api/3/issue/{issue_key}/comment",
        auth=auth, headers=headers, data=json.dumps(payload)
    ).raise_for_status()


# ── DAG 태스크 연결 ───────────────────────────────────
t1 = PythonOperator(task_id="poll_jira_status",     python_callable=poll_jira_status,     dag=dag)
t2 = PythonOperator(task_id="execute_and_deliver",  python_callable=execute_and_deliver,  dag=dag)

t1 >> t2
