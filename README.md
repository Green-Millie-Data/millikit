# millikit — 개인정보 추출 자동화 파이프라인

그룹웨어 전자결재 감지 → Claude 유형 분류 + SQL 초안 생성 → 데이터 담당자 검토·실행 → BigQuery 실행 → Jira 기록

---

## 아키텍처

```
poll_groupware_db   그룹웨어 DB 폴링 (30분 간격)
  ↓
classify_doc        1차 Claude (haiku) — 결재 유형 분류 (max_tokens=200)
  ↓
generate_sql        2차 Claude (sonnet) — 유형별 FewShot + 프롬프트 캐싱 → SQL 초안
  ↓
[TODO] Slack 알림   데이터 담당자에게 SQL 초안 전송 → 검토·실행
  ↓
[TODO] BigQuery     자동 실행 + CSV 추출
  ↓
[TODO] Jira 기록    요청 조건 / SQL / 결과 티켓 기록
```

---

## 결재 요청 유형 (4가지)

| 유형 | 설명 | FewShot |
|------|------|---------|
| `이벤트_참여자` | 이벤트 댓글·미션 참여 유저 | `fewshot_event.md` (12개) |
| `알림_신청자` | 공개예정 페이지 알림 신청 유저 | `fewshot_notify.md` (2개) |
| `마케팅_구독조건` | 구독 상태·채널·기간 기반 LMS·PUSH | `fewshot_marketing.md` (5개) |
| `기타_특수` | 페이지 방문, 카테고리 대여, 특수 서비스 | `fewshot_etc.md` (4개) |

FewShot 소스: MIDAS-2439(Jan)/2650(Feb)/2701(Mar) 서브태스크 실제 처리 기록 23개

---

## 프로젝트 구조

```
millie_kit/
├── Dockerfile                  # apache/airflow:2.9.3 + pymysql + anthropic
├── docker-compose.yaml
├── .env                        # 환경변수 (Git 제외)
├── requirements.txt
└── dags/
    ├── millikit_dag.py
    └── prompts/
        ├── fewshot_event.md
        ├── fewshot_notify.md
        ├── fewshot_marketing.md
        └── fewshot_etc.md
```

---

## 실행 방법

```bash
# 1. 환경변수 설정 (.env)
ANTHROPIC_BASE_URL=<사내_프록시_URL>
ANTHROPIC_API_KEY=<사내 부서 키>
GW_DB_HOST=...  GW_DB_USER=...  GW_DB_PASSWORD=...

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

사내 프록시 경유 (`https://publlm.ai.millie.co.kr`). `.env`와 `docker-compose.yaml`에 `ANTHROPIC_BASE_URL` 추가 필요.

| 용도 | 모델 | 이유 |
|------|------|------|
| `classify_doc` (유형 분류) | `claude-4.5-haiku` | 가볍고 빠름, 분류만 |
| `generate_sql` (SQL 생성) | `claude-4.5-sonnet` | FewShot 이해 + SQL 품질 |

`generate_sql`은 system에 `cache_control: ephemeral` 적용 — FewShot 반복 전송 비용 절감.

---

## 환경변수 (.env)

| 변수 | 설명 |
|------|------|
| `AIRFLOW_UID` | Docker 실행 UID |
| `GW_DB_HOST/PORT/USER/PASSWORD/NAME` | 그룹웨어 DB (포트 13306) |
| `ANTHROPIC_BASE_URL` | 사내 프록시 URL |
| `ANTHROPIC_API_KEY` | 사내 부서 키 |
| `LAST_DOC_ID` | 마지막 처리 doc_id (초기값 0) |

---

## 진행 현황

### 완료 (Phase 1)
- [x] Docker Airflow 2.9.3 환경 구성
- [x] 그룹웨어 DB 연결 (735건 확인)
- [x] 2-step Claude 분석 (classify → generate)
- [x] FewShot 파일 구성 (23개 실제 처리 기록)
- [x] 사내 프록시 연동 + 프롬프트 캐싱
- [x] **end-to-end 실행 성공**

### 다음 (Phase 2)
- [ ] `LAST_DOC_ID` 상태 관리 개선 (Airflow Variable)
- [ ] Slack 알림 연동 (SQL 초안 → 담당자)
- [ ] BigQuery 자동 실행 + CSV 추출

### 이후 (Phase 3)
- [ ] Jira MCP 자동 기록
- [ ] FTCClientM 자동화 (IT팀 FTP 접속 정보 확인 필요)
- [ ] 사내 서버 이관
