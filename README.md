# millikit — 개인정보 추출 자동화 파이프라인

그룹웨어 전자결재 감지 → Claude 분석 → SQL 초안 생성 → Slack 알림 → BigQuery 실행 → Jira 기록

---

## 아키텍처

```
그룹웨어 DB 폴링 (30분 간격)
  ↓
classify_doc       1차 Claude — 결재 유형 분류 (가벼운 호출)
  ↓
generate_sql       2차 Claude — 유형별 FewShot 로드 후 SQL 초안 생성
  ↓
[TODO] Slack 알림  데이터 담당자에게 SQL 초안 전송 → 검토·실행
  ↓
[TODO] BigQuery    자동 실행 + CSV 추출
  ↓
[TODO] Jira 기록   요청 조건 / SQL / 결과 모두 티켓에 기록
```

## 결재 요청 유형 분류 (4가지)

| 유형 | 설명 | FewShot |
|------|------|---------|
| `이벤트_참여자` | 이벤트 댓글·미션 버튼 활성화 유저 | `fewshot_event.md` (12개) |
| `알림_신청자` | 공개예정 페이지 알림 받기 신청 유저 | `fewshot_notify.md` (2개) |
| `마케팅_구독조건` | 구독 상태·채널·기간 기반 LMS·PUSH 대상 | `fewshot_marketing.md` (5개) |
| `기타_특수` | 페이지 방문(tracking), 카테고리 대여 등 | `fewshot_etc.md` (4개) |

FewShot 소스: MIDAS-2439(Jan), MIDAS-2650(Feb), MIDAS-2701(Mar) 서브태스크 실제 처리 기록

---

## 프로젝트 구조

```
millie_kit/
├── Dockerfile                  # apache/airflow:2.9.3 + pymysql + anthropic
├── docker-compose.yaml         # Airflow 2.9.3 (Celery + Postgres + Redis)
├── .env                        # 환경변수 (Git 제외)
├── requirements.txt
└── dags/
    ├── millikit_dag.py         # 메인 DAG
    └── prompts/
        ├── fewshot_event.md    # 이벤트_참여자 FewShot (12개)
        ├── fewshot_notify.md   # 알림_신청자 FewShot (2개)
        ├── fewshot_marketing.md# 마케팅_구독조건 FewShot (5개)
        └── fewshot_etc.md      # 기타_특수 FewShot (4개)
```

---

## 실행 방법

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 에 GW_DB_*, ANTHROPIC_API_KEY 입력

# 2. 빌드 및 초기화
docker compose build
docker compose up airflow-init

# 3. 기동
docker compose up -d airflow-webserver airflow-scheduler airflow-worker airflow-triggerer

# 4. 웹 UI 접속
# http://localhost:8080  (id: airflow / pw: airflow)
```

---

## 환경변수 (.env)

| 변수 | 설명 |
|------|------|
| `AIRFLOW_UID` | Docker 실행 UID |
| `GW_DB_HOST` | 그룹웨어 DB 호스트 |
| `GW_DB_PORT` | 그룹웨어 DB 포트 (기본 13306) |
| `GW_DB_USER` | 그룹웨어 DB 사용자 |
| `GW_DB_PASSWORD` | 그룹웨어 DB 비밀번호 |
| `GW_DB_NAME` | 그룹웨어 DB 명 (neos) |
| `ANTHROPIC_API_KEY` | Claude API 키 |
| `LAST_DOC_ID` | 마지막 처리한 doc_id (초기값 0) |

---

## 진행 현황

### 완료
- [x] Docker 기반 Airflow 2.9.3 환경 구성
- [x] 그룹웨어 DB 폴링 (`poll_groupware_db`)
- [x] 2-step Claude 분석 구조
  - [x] `classify_doc`: 1차 호출 — 유형 분류만 (max_tokens=200)
  - [x] `generate_sql`: 2차 호출 — 유형별 FewShot 로드 후 SQL 생성
- [x] FewShot 파일 구성 (MIDAS 2439/2650/2701 실제 처리 기록 23개)
- [x] Docker 기동 및 DB 연결 확인 (735건)

### 진행 중 (Phase 1)
- [ ] Anthropic API 크레딧 충전 후 end-to-end 실행 확인
- [ ] `LAST_DOC_ID` 상태 관리 개선 (현재 .env 하드코딩)

### 다음 단계 (Phase 2)
- [ ] Slack MCP 알림 연동 (SQL 초안 → 데이터 담당자)
- [ ] BigQuery 자동 실행 + CSV 추출

### 이후 (Phase 3)
- [ ] Jira MCP 자동 기록
- [ ] FTCClientM 자동화 검토
- [ ] 사내 서버 이관

---

## Claude 프롬프트 규칙

- `mem_seq`(회원번호)만 추출 — 개인정보 직접 추출 금지
- 테이블은 `millie-analysis` GCP 프로젝트만 사용
- 공통 필터 항상 포함: `test_yn='N'`, `millie_yn='N'`, `dormant_yn='N'`, `member_status != '탈퇴회원'`
- 조건 불명확 시 SQL 대신 확인 필요 사항 명시
- 응답은 JSON 형식
