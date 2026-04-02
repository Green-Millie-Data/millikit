# millikit — 개인정보 추출 자동화 파이프라인

## 프로젝트 개요

밀리의서재 개인정보 추출 업무를 자동화하는 파이프라인.
그룹웨어 전자결재 감지 → Claude 유형 분류 → SQL 초안 생성 → 데이터 담당자 검토·실행 → BigQuery 자동 실행 → 결과 전달 → Jira 기록

- Confluence PoC 문서: https://millietown.atlassian.net/wiki/spaces/Wzz2XB5ywc7i/pages/4505010321/PoC
- Confluence 설계 문서: https://millietown.atlassian.net/wiki/spaces/Wzz2XB5ywc7i/pages/4765680100
- Jira 이력 스토리: MIDAS-2439(Jan), MIDAS-2650(Feb), MIDAS-2701(Mar), MIDAS-2868(Apr 진행중)

---

## 기술 스택

- **오케스트레이션**: Apache Airflow 2.9.3 (로컬 Docker, Celery + Postgres + Redis)
- **AI**: Claude API — 사내 프록시 경유 (`https://publlm.ai.millie.co.kr`)
  - 유형 분류: `claude-4.5-haiku` (1차, 가벼운 호출)
  - SQL 생성: `claude-4.5-sonnet` (2차, FewShot + 프롬프트 캐싱)
- **그룹웨어 DB**: MySQL (pymysql) — 로컬에서만 접근 가능 (포트 13306)
- **데이터 웨어하우스**: BigQuery (`millie-analysis` 프로젝트)
- **알림·승인**: Slack MCP (Phase 2)
- **이력 관리**: Jira MCP (Phase 3)
- **파일 전달**: FTCClientM (개인정보 포함 케이스, CLI 미지원 — 수동)

---

## 프로젝트 구조

```
millie_kit/
├── CLAUDE.md
├── README.md
├── Dockerfile                  # apache/airflow:2.9.3 + pymysql + anthropic
├── docker-compose.yaml         # ANTHROPIC_BASE_URL 포함
├── .env                        # DB 접속정보, API 키 (Git 제외)
├── requirements.txt
└── dags/
    ├── millikit_dag.py         # 메인 DAG
    └── prompts/                # 유형별 FewShot 파일
        ├── fewshot_event.md    # 이벤트_참여자 (12개 예시)
        ├── fewshot_notify.md   # 알림_신청자 (2개 예시)
        ├── fewshot_marketing.md# 마케팅_구독조건 (5개 예시)
        └── fewshot_etc.md      # 기타_특수 (4개 예시)
```

---

## DAG 흐름 (현재 구현 상태)

```
poll_groupware_db       그룹웨어 DB 폴링 (30분 간격, form_id=144, doc_sts IN 30/90)
  ↓
classify_doc            1차 Claude (haiku) — 결재 유형 분류만 (max_tokens=200)
  ↓
generate_sql            2차 Claude (sonnet) — 유형별 FewShot 로드 + 프롬프트 캐싱 + SQL 생성
  ↓
print_results           결과 출력 [임시 — Phase 2에서 Slack으로 교체]
```

**전체 파이프라인 TO-BE:**
```
그룹웨어 결재 (doc_sts IN 30, 90)
  → Claude 유형 분류 + SQL 초안 생성
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

## 결재 요청 유형 분류 (4가지)

| 유형 | 설명 | FewShot 소스 |
|------|------|-------------|
| `이벤트_참여자` | 이벤트 댓글·미션 버튼 활성화 유저 (event_rand_code → event_seq) | MIDAS 서브태스크 12개 |
| `알림_신청자` | 공개예정 페이지 '알림 받기' 신청 유저 (event_seq 고정, 마케팅 동의 불필요) | MIDAS 서브태스크 2개 |
| `마케팅_구독조건` | 구독 상태·채널·기간 기반 LMS·PUSH 대상 (이벤트/도서 조건 없음) | MIDAS 서브태스크 5개 |
| `기타_특수` | 페이지 방문(tracking), 카테고리 대여, 밀리플레이스·북클럽 등 | MIDAS 서브태스크 4개 |

FewShot 원본: MIDAS-2439/2650/2701 서브태스크 — 결재 요청 description + 처리 SQL 댓글

---

## Claude 프롬프트 규칙

- `mem_seq`(회원번호)만 추출 — 개인정보 직접 추출 금지
- 테이블은 `millie-analysis` GCP 프로젝트만 사용
- 공통 필터 항상 포함: `test_yn='N'`, `millie_yn='N'`, `dormant_yn='N'`, `member_status != '탈퇴회원'`
- 조건 불명확 시 SQL 대신 확인 필요 사항 명시
- 응답은 JSON 형식

---

## 그룹웨어 DB 쿼리

```sql
SELECT ad.doc_id, ad.doc_no, ad.user_nm, ad.dept_nm,
       ad.doc_title, ad.doc_sts, adcw.doc_contents, ad.rep_dt, ad.end_dt
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

## 환경변수 (.env)

```
AIRFLOW_UID=501

# 그룹웨어 DB
GW_DB_HOST=
GW_DB_PORT=13306
GW_DB_USER=
GW_DB_PASSWORD=
GW_DB_NAME=neos

# Claude API (사내 프록시)
ANTHROPIC_BASE_URL=<사내_프록시_URL>
ANTHROPIC_API_KEY=

# 마지막 처리한 doc_id
LAST_DOC_ID=0
```

---

## 실행 방법

```bash
docker compose build
docker compose up airflow-init
docker compose up -d airflow-webserver airflow-scheduler airflow-worker airflow-triggerer
# http://localhost:8080  (id: airflow / pw: airflow)
```

---

## 진행 현황

### 완료 (Phase 1)
- [x] Docker 기반 Airflow 2.9.3 환경 구성 (pymysql, anthropic 포함)
- [x] 그룹웨어 DB 연결 (735건 확인)
- [x] 2-step Claude 분석 구조
  - [x] `classify_doc`: 1차 haiku 호출 — 유형 분류
  - [x] `generate_sql`: 2차 sonnet 호출 — FewShot + 프롬프트 캐싱
- [x] FewShot 파일 구성 (MIDAS 실제 처리 기록 23개 기반)
- [x] 사내 프록시 연동 (`ANTHROPIC_BASE_URL`)
- [x] **end-to-end 실행 성공** (SQL 생성 + 조건 불명확 시 확인 요청 정상 동작)

### 다음 단계 (Phase 2)
- [ ] `LAST_DOC_ID` 상태 관리 개선 (현재 .env 하드코딩 → Airflow Variable 또는 DB)
- [ ] Slack MCP 알림 연동 (SQL 초안 → 데이터 담당자)
- [ ] BigQuery 자동 실행 + CSV 추출

### 이후 (Phase 3)
- [ ] Jira MCP 자동 기록
- [ ] FTCClientM 자동화 검토 (CLI 미지원 — IT팀 FTP 서버 접속 정보 확인 필요)
- [ ] 사내 서버 이관 검토
