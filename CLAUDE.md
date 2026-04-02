# millikit — 개인정보 추출 자동화 파이프라인

## 프로젝트 개요

밀리의서재 개인정보 추출 업무를 자동화하는 파이프라인.
그룹웨어 전자결재 감지 → Claude 분석 → SQL 생성 → 데이터 담당자 검토·실행 → BigQuery 자동 실행 → 결과 전달 → Jira 기록

Confluence 문서: https://millietown.atlassian.net/wiki/spaces/Wzz2XB5ywc7i/pages/4765680100

---

## 기술 스택

- **오케스트레이션**: Apache Airflow 2.9.3 (로컬 Docker)
- **AI**: Claude API (claude-sonnet-4-20250514)
- **그룹웨어 DB**: MySQL (pymysql) — 로컬에서만 접근 가능
- **데이터 웨어하우스**: BigQuery Python SDK
- **알림·승인**: Slack MCP
- **이력 관리**: Jira MCP
- **파일 전달**: FTCClientM (개인정보 포함 케이스, CLI 미지원 — 수동)
- **설정 관리**: python-dotenv

---

## 프로젝트 구조

```
millie_kit/
├── CLAUDE.md
├── Dockerfile
├── docker-compose.yaml
├── .env                        # DB 접속정보, API 키 (Git 제외)
├── requirements.txt
└── dags/
    └── millikit_dag.py         # 메인 DAG (현재 작업 중)
```

---

## 파이프라인 흐름 (TO-BE)

```
그룹웨어 결재 (doc_sts IN 30, 90)
  → Jira 자동 생성
  → Claude 분석 (유형 분류 + 쿼리 템플릿 조건 치환 → SQL 초안)
  → Slack 알림 (데이터 담당자에게 SQL 초안 전송)
  → 데이터 담당자 검토·실행  ← 유일한 수동 개입
    └─ 예외 복잡 케이스 → AX 데이터팀 요청
  → BigQuery 자동 실행 + CSV 추출
  → 추출 유형 분기
      A. 회원번호(mem_seq)만 → CSV 자동 전달
      B. 개인정보 포함 → FTCClientM 수동 전달 (담당자 → 기안자)
  → Jira 자동 기록
```

---

## 그룹웨어 DB 쿼리

```sql
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
INNER JOIN neos.teag_appdoc_contents adc ON ad.doc_id = adc.doc_id
INNER JOIN neos.teag_appdoc_contents_word adcw ON adc.doc_id = adcw.doc_id
WHERE ad.form_id = 144          -- 개인정보 추출 양식
  AND ad.doc_sts IN (30, 90)    -- 30: 진행, 90: 종결
  AND ad.doc_id > %(last_id)s
ORDER BY ad.doc_id ASC
LIMIT 10
```

---

## 결재 요청 유형 분류 (3가지)

| 유형 | 설명 | 주요 조건 |
|------|------|-----------|
| 이벤트_참여자 | 댓글 작성 · 미션 버튼 활성화 유저 | 이벤트 시퀀스 + 기간 |
| 알림_신청자 | 공개예정 페이지 알림 받기 신청 유저 | 페이지 URL + 추출 시점 |
| 작품_열람대여자 | 특정 도서 열람 또는 대여 유저 | 도서코드 + 기간 + 행동 유형 |

템플릿 소스: 최근 3개월 Jira 티켓 + 3~6개월 md 파일

---

## Claude 프롬프트 규칙

- `mem_seq`(회원번호)만 추출 — 개인정보 직접 추출 금지
- 테이블은 `millie-analysis` GCP 프로젝트만 사용
- 조건 불명확 시 SQL 대신 확인 필요 사항 명시
- 응답은 JSON 형식

---

## 환경변수 (.env)

```
AIRFLOW_UID=...

# 그룹웨어 DB
GW_DB_HOST=
GW_DB_PORT=3306
GW_DB_USER=
GW_DB_PASSWORD=
GW_DB_NAME=neos

# Claude API
ANTHROPIC_API_KEY=

# 마지막 처리한 doc_id
LAST_DOC_ID=0
```

---

## 현재 진행 상황

### 완료
- [x] 프로젝트 설계 · Confluence 문서 작성
- [x] Docker Desktop 설치
- [x] Airflow 2.9.3 초기화 완료
- [x] `dags/millikit_dag.py` 기본 구조 작성 (DB 폴링 → Claude 분석 → 결과 출력)

### 현재 작업 중 (Phase 1)
- [ ] Dockerfile + `pymysql`, `anthropic` 패키지 설치 문제 해결
- [ ] Airflow 정상 기동 확인
- [ ] 그룹웨어 DB 연결 테스트
- [ ] Claude API 연동 테스트
- [ ] 첫 번째 DAG 실행 확인

### 다음 단계 (Phase 2)
- [ ] Slack MCP 알림 연동
- [ ] BigQuery 자동 실행
- [ ] CSV 추출 및 전달 분기

### 이후 (Phase 3)
- [ ] Jira MCP 자동 기록
- [ ] FTCClientM 자동화 검토 (현재 CLI 미지원 — IT팀 FTP 서버 접속 정보 확인 필요)
- [ ] 사내 서버 이관 검토

---

## 현재 막힌 문제

Dockerfile 방식으로 pymysql, anthropic 패키지 설치 시도 중.
`docker-compose.yaml`에서 `airflow-webserver`, `airflow-scheduler`, `airflow-worker`, `airflow-triggerer` 서비스의
`image: ${AIRFLOW_IMAGE_NAME:-apache/airflow:2.9.3}` 를 `build: .` 으로 교체 후
`docker compose build && docker compose up airflow-init` 실행 필요.