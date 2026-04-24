# millikit — 개인정보 추출 자동화 파이프라인

그룹웨어 전자결재 감지 → Claude 유형 분류 + SQL 초안 생성 → Jira 하위작업 등록 → 데이터 담당자 검토 → BigQuery 실행 → 결과 전달

---

## 아키텍처

### DAG 1: `millikit_pipeline` (30분 간격)

```
poll_groupware_db   그룹웨어 DB 폴링 (form_id=144, doc_sts IN 30/90)
  ↓
classify_doc        1차 Claude (haiku) — 결재 유형 분류
  ↓
generate_sql        2차 Claude (sonnet) — 스키마 + FewShot + 프롬프트 캐싱 → SQL 초안
  ↓
create_jira_tickets Jira 하위작업 자동 생성 (MIDAS-3014 하위) + SQL 초안 댓글 등록
```

### DAG 2: `millikit_reviewer` (30분 간격, 평일 9-18시)

```
poll_jira_status    Jira에서 "검토완료" 상태 하위작업 감지
  ↓
execute_and_deliver [TODO] BigQuery 실행 + CSV 추출 + GCS Signed URL → Jira 댓글
```

---

## 결재 요청 유형 (4가지)

| 유형 | 설명 |
|------|------|
| `이벤트_참여자` | 이벤트 댓글·미션 참여 유저 |
| `알림_신청자` | 공개예정 페이지 알림 신청 유저 |
| `마케팅_구독조건` | 구독 상태·채널·기간 기반 LMS·PUSH 대상 |
| `기타_특수` | 페이지 방문, 카테고리 대여, 특수 서비스 등 |

SQL 생성 시 `dags/prompts/schema.md` (테이블 스키마) + `dags/prompts/fewshot_all.md` (처리 예시) 로드. 두 파일은 보안상 Git 제외 (`.gitignore`).

---

## 프로젝트 구조

```
millie_kit/
├── Dockerfile                  # apache/airflow:2.9.3 + pymysql + anthropic
├── docker-compose.yaml
├── .env                        # 환경변수 (Git 제외)
├── requirements.txt
└── dags/
    ├── millikit_dag.py         # 메인 파이프라인 DAG
    ├── millikit_reviewer_dag.py# 검토완료 감지 + 실행 DAG
    └── prompts/                # Git 제외
        ├── schema.md           # BigQuery 테이블 스키마
        └── fewshot_all.md      # 처리 예시 (25개+)
```

---

## 실행 방법

```bash
# 1. 환경변수 설정 (.env 참고)

# 2. 빌드 및 초기화
docker compose build
docker compose up airflow-init

# 3. 기동
docker compose up -d airflow-webserver airflow-scheduler airflow-worker airflow-triggerer

# 4. 웹 UI
# http://localhost:8080  (id: airflow / pw: airflow)

# 5. 수동 트리거 (테스트)
docker compose exec airflow-scheduler airflow dags trigger millikit_pipeline
```

---

## Claude API 설정

사내 프록시 경유. `.env`와 `docker-compose.yaml`에 `ANTHROPIC_BASE_URL` 설정 필요.

| 용도 | 모델 |
|------|------|
| `classify_doc` (유형 분류) | `claude-4.5-haiku` |
| `generate_sql` (SQL 생성) | `claude-4.5-sonnet` |

`generate_sql`은 system에 `cache_control: ephemeral` 적용 — 스키마+FewShot 반복 전송 비용 절감.

---

## 환경변수 (.env)

| 변수 | 설명 |
|------|------|
| `AIRFLOW_UID` | Docker 실행 UID |
| `GW_DB_HOST/PORT/USER/PASSWORD/NAME` | 그룹웨어 DB (포트 13306) |
| `ANTHROPIC_BASE_URL` | 사내 프록시 URL |
| `ANTHROPIC_API_KEY` | 사내 부서 키 |
| `JIRA_BASE_URL` | Jira 인스턴스 URL |
| `JIRA_EMAIL` | Jira 계정 이메일 |
| `JIRA_API_TOKEN` | Jira API 토큰 |
| `JIRA_PARENT_ISSUE` | 하위작업 생성 대상 부모 이슈 (예: MIDAS-3014) |
| `LAST_DOC_ID` | 마지막 처리 doc_id (초기값 0) |

---

## 진행 현황

### 완료 (Phase 1)
- [x] Docker Airflow 2.9.3 환경 구성
- [x] 그룹웨어 DB 연결
- [x] 2-step Claude 분석 (classify → generate)
- [x] 사내 프록시 연동 + 프롬프트 캐싱
- [x] end-to-end 실행 성공

### 완료 (Phase 2)
- [x] Jira 하위작업 자동 생성 + SQL 초안 댓글
- [x] `millikit_reviewer_dag` — 검토완료 상태 폴링
- [x] 스키마 + 통합 FewShot으로 SQL 품질 개선

### 진행중 / 이후
- [ ] `execute_and_deliver`: BigQuery 자동 실행 + CSV 추출
- [ ] GCS Signed URL 생성 (7일 만료) → Jira 댓글 전달
- [ ] `LAST_DOC_ID` → Airflow Variable로 관리
- [ ] FTCClientM 자동화 검토 (IT팀 FTP 접속 정보 필요)
- [ ] 사내 서버 이관
