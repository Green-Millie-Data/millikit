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


# ── Task 2: BQ 실행 → GCS → Jira 댓글 ────────────────
def execute_and_deliver(**context):
    """TODO Phase 2-3: BigQuery 실행 + GCS Signed URL + Jira 댓글"""
    import os
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
        print(f"[{key}] BigQuery 실행 예정 (TODO)")

        # TODO: BigQuery 실행 + CSV 추출
        # TODO: GCS 업로드 + Signed URL 생성 (7일 만료)

        # 임시 댓글
        comment_payload = {
            "body": {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": "⏳ 검토완료 확인. BigQuery 실행 자동화 준비 중입니다."}
                ]}]
            }
        }
        resp = requests.post(
            f"{base_url}/rest/api/3/issue/{key}/comment",
            auth=auth, headers=headers, data=json.dumps(comment_payload)
        )
        resp.raise_for_status()
        print(f"[{key}] 임시 댓글 추가 완료")

        # TODO: 작업 완료 상태로 전환 (BQ 성공 후)
        # transition_payload = {"transition": {"id": "2"}}  # 작업 완료 transition id
        # requests.post(f"{base_url}/rest/api/3/issue/{key}/transitions", ...)


# ── DAG 태스크 연결 ───────────────────────────────────
t1 = PythonOperator(task_id="poll_jira_status",     python_callable=poll_jira_status,     dag=dag)
t2 = PythonOperator(task_id="execute_and_deliver",  python_callable=execute_and_deliver,  dag=dag)

t1 >> t2
