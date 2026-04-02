# FewShot — 알림_신청자

> 공개예정 페이지 '알림 받기' 신청 유저. 마케팅 동의 조건 불필요.

---

## 1. MIDAS-2558 — 공개예정 페이지 업데이트 푸시 발송의 건 (1월 4주)


**SQL**:
```sql
select m.mem_seq, m.member_status 
from `millie-analysis.sv_user.sv_user_member` m
where 1=1
and m.mem_seq IN (
                  select mem_seq 
                  from `millie-analysis.sv_contents.sv_contents_tb_event_member`
                  where event_seq = 375
              )
-- 회원이 알림을 신청한 것이므로 마케팅, 이벤트 푸시 알림 수신 여부, 14세 미만여부와 상관없음
and m.millie_yn = 'N'
and m.test_yn = 'N'
and m.dormant_yn = 'N'
and m.member_status != '탈퇴회원'
group by m.mem_seq, m.member_status
```


---

## 2. MIDAS-2754 — 공개예정 페이지 업데이트 푸시 발송의 건 (3월 4주)


**SQL**:
```sql
SELECT m.mem_seq, m.member_status 
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE 1=1
AND m.mem_seq IN (
    SELECT mem_seq 
    FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
    WHERE event_seq = 375
    )
-- 회원이 알림을 신청한 것이므로 마케팅, 이벤트 푸시 알림 수신 여부, 14세 미만여부와 상관없음
AND m.millie_yn = 'N'
AND m.test_yn = 'N'
AND m.dormant_yn = 'N'
AND m.member_status != '탈퇴회원'
GROUP BY m.mem_seq, m.member_status
```


---
