# FewShot — 기타_특수

> 페이지 방문(tracking), 카테고리 대여, 특수 서비스 대상.

---

## 1. MIDAS-2451 — 자기계발 오디오북 기획전 홍보 PUSH 발송 목적의 회원 정보 추출 요청


**SQL**:
```sql
SELECT DISTINCT m.mem_seq
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE m.mem_seq IN (
    SELECT DISTINCT crl.mem_seq
    FROM `millie-analysis.sv_contents.sv_contents_book_rent` crl
    INNER JOIN `millie-analysis.sv_contents.sv_contents_tb_content` c 
        ON crl.book_seq = c.book_seq
    WHERE c.content_code = 806
        AND c.category_seq = 1474
        AND crl.dates >= DATE('2025-12-01')
        AND crl.dates < DATE('2026-01-01')
)
AND m.mem_seq NOT IN (
    SELECT DISTINCT mem_seq
    FROM `millie-analysis.sv_behavior.sv_behavior_millie_tracking`
    WHERE LOWER(event) IN ('pageview', 'page_view')
        AND target LIKE '%v3/post/1240030%'
        AND dates >= DATE('2025-12-01')
        AND dates < DATE('2026-01-01')
        AND mem_seq > 0
)
AND m.test_yn = 'N'
AND m.millie_yn = 'N'
AND m.member_status = '구독회원'
AND m.dormant_yn = 'N'
AND m.under_14_yn = 'N'
AND m.marketing_agree_yn = 'Y'
AND m.event_push_yn = 'Y'
```


---

## 2. MIDAS-2632 — 밀리플레이스 당첨자 안내를 위한 개인정보 추출 요청


**SQL**:
```sql
Select mem_seq, mem_nickname
  from `millie-327302.br_rds_millie.tb_member` tm
inner join `millie-analysis.sv_service.sv_service_customer_book_recommed_comment_info` pc on 1=1
  and tm.mem_seq = pc.regist_id
  and pc.recommend_seq = 100429
  and pc.comment_depth = 1

where 1=1
  and mem_nickname in () -- 특정 닉네임 입력
```


---

## 3. MIDAS-2698 — 북클럽 2기 액션 회원 개인 정보 추출 요청


**SQL**:
```sql
-- 11,228
with tb_target as (
select distinct mem_seq
  from `millie-analysis.sv_behavior.sv_behavior_millie_tracking` mt
where 1=1
  and dates between date('2026-02-09') and date('2026-02-23')
  and event = 'click'
  and JSON_VALUE(mt.query_string, '$.content_type') = 'out_link'
  and JSON_VALUE(mt.query_string, '$.content_name') = "북클럽 신청하기"
  and JSON_VALUE(mt.query_string, '$.section_type') = "218w62gq61z0gi2l" -- event_seq
  and JSON_VALUE(mt.query_string, '$.section_name') = "<참새 환영> 밀리 북클럽 2기 모집"
)

-- 10.555
select 
  tt.mem_seq,
  um.sex,
  um.age_band,
  um.member_status,
  tm.mem_nickname,
  from tb_target tt
left join `millie-327302.br_rds_millie.tb_member` tm on 1=1
  and tt.mem_seq = tm.mem_seq
left join `millie-analysis.sv_user.sv_user_member` um on 1=1
  and tt.mem_seq = um.mem_seq
where 1=1
  and member_status = '구독회원'
```


---

## 4. MIDAS-2755 — 이벤트 당첨자 개인정보 추출 요청의 건 (독서 취향 테스트)


**SQL**:
```sql
with tb_target as (
select mem_seq, min(date(reg_date)) as first_participate_date
from `millie-analysis.sv_behavior.sv_behavior_millie_tracking`
where 1=1
  and target like 'https://www.millie.co.kr/v4/event/24r43e0c626bp06g%'
  and dates between '2025-12-10' and '2026-03-11'  -- 사전 참여자 감지를 위해 넓게 설정
  and event = 'click'
  and json_extract_scalar(query_string, '$.content_type') = 'in_link'
group by mem_seq
having first_participate_date between DATE('2026-02-25') and DATE('2026-03-11')
),
tb_event_join as (
select mem_seq
  from (
select mem_seq, min(date(reg_date)) as reg_date
FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
WHERE event_seq = 820
group by all
  )
where 1=1
  and reg_date between '2026-02-25' and '2026-03-11'
group by all
)

select tt.mem_seq, if(ej.mem_seq is not null, 'Y','N') as event_join_yn
  from tb_target tt
inner join `millie-analysis.sv_user.sv_user_member` um on 1=1
  and tt.mem_seq = um.mem_seq
left join tb_event_join ej on 1=1
  and tt.mem_seq = ej.mem_seq
where 1=1
  and um.member_status = '구독회원'
  and um.millie_yn = 'N'
  and um.test_yn = 'N'
  and um.dormant_yn = 'N'
  and um.under_14_yn = 'N'
```


---
