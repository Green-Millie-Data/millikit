# FewShot — 마케팅_구독조건

> 구독 상태·채널·기간 기반 LMS·PUSH. 이벤트/도서 조건 없음.

---

## 1. MIDAS-2440 — 연정기 프로모션 오픈 안내 LMS 발송을 위한 개인정보 추출 요청 (1/16 발송)


**SQL**:
```sql
-- 테이블: sv_user.sv_user_member
-- 조건: B2C/B2BC 90일 이내 해지자, MSEQ 9508 구독권 구매자 제외
SELECT DISTINCT m.mem_seq
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE m.member_status = '해지회원'
  AND m.channel IN ('B2C', 'B2BC')
  AND m.test_yn = 'N'
  AND m.millie_yn = 'N'
  AND m.dormant_yn = 'N'
  AND m.under_14_yn = 'N'
  AND m.marketing_agree_yn = 'Y'
  AND m.phone_yn = 'Y'
  AND m.b2b_yn = 'N'
  -- 90일 이내 해지자 (해지일 기준)
  AND DATE_DIFF(CURRENT_DATE(), m.member_status_dates, DAY) <= 90
  -- MSEQ 9508 구독권 구매자 제외 (NOT EXISTS로 안전하게 처리)
  AND NOT EXISTS (
    SELECT 1
    FROM `millie-analysis.sv_product.sv_product_tb_coupon_publish` cp
    WHERE cp.coupon_master_seq = 9508
      AND cp.reg_mem_seq = m.mem_seq
  )
```


---

## 2. MIDAS-2441 — 연정기 프로모션 오픈 안내 LMS 발송을 위한 개인정보 추출 요청 (1/23 발송)


**SQL**:
```sql
-- (B2C, B2BC)4~6개월 이내 해지자
SELECT DISTINCT m.mem_seq
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE m.member_status = '해지회원'
  AND m.channel IN ('B2C', 'B2BC')
  AND m.test_yn = 'N'
  AND m.millie_yn = 'N'
  AND m.dormant_yn = 'N'
  AND m.under_14_yn = 'N'
  AND m.marketing_agree_yn = 'Y'
  AND m.phone_yn = 'Y'
  AND m.b2b_yn = 'N'
  --4~6개월 이내 해지자 (해지일 기준)
  AND DATE_DIFF(CURRENT_DATE(), m.member_status_dates, DAY) between 120 and 180
  -- MSEQ 9508 구독권 구매자 제외 (NOT EXISTS로 안전하게 처리)
  AND NOT EXISTS (
    SELECT 1
    FROM `millie-analysis.sv_product.sv_product_tb_coupon_publish` cp
    WHERE cp.coupon_master_seq = 9508
      AND cp.reg_mem_seq = m.mem_seq
  )
```


---

## 3. MIDAS-2443 — 연정기 프로모션 오픈 안내 LMS 발송을 위한 개인정보 추출 요청 (1/31 발송)


**SQL 1**:
```sql
SELECT DISTINCT m.mem_seq
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE m.member_status = '구독회원'
  AND m.channel = 'B2C'
  AND m.product_type_detail = '월정기'
  And m.product_type = '정규 상품'
  AND m.test_yn = 'N'
  AND m.millie_yn = 'N'
  AND m.dormant_yn = 'N'
  AND m.under_14_yn = 'N'
  AND m.marketing_agree_yn = 'Y'
  AND m.phone_yn = 'Y'
  AND m.b2b_yn = 'N'
  -- MSEQ 9508 구독권 구매자 제외 (NOT EXISTS로 안전하게 처리)
  AND NOT EXISTS (
    SELECT 1
    FROM `millie-analysis.sv_product.sv_product_tb_coupon_publish` cp
    WHERE cp.coupon_master_seq = 9508
      AND cp.reg_mem_seq = m.mem_seq
  )
  -- 특정구독권(44개) 발행 이력이 있는 회원
  and exists (
    select 1
    from `millie-analysis.sv_product.sv_product_tb_coupon_publish` cp2
    where 1=1 
      and cp2.coupon_master_seq in (4249,3930,5230,5228,5227,5105,4833,4558,4536,4528,4379,4376,5842,5828,5806,5645,5624,5540,5353,5331,5326,5315,7283,7132,7060,7059,6763,6643,6638,6383,6367,6129,9335,8775,8771,8769,8766,7928,7738,7464,7437,7315,8042,8284)
      and cp2.reg_mem_seq = m.mem_seq
  )
```


**SQL 2**:
```sql
SELECT DISTINCT m.mem_seq
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE m.member_status = '구독회원'
  AND m.channel = 'B2C'
  AND m.product_type_detail = '월정기'
  And m.product_type = '정규 상품'
  AND m.test_yn = 'N'
  AND m.millie_yn = 'N'
  AND m.dormant_yn = 'N'
  AND m.under_14_yn = 'N'
  AND m.marketing_agree_yn = 'Y'
  AND m.phone_yn = 'Y'
  AND m.b2b_yn = 'N'
  -- 12개월 미만 이내 구독회원 (구독일 기준)
  AND DATE_DIFF(CURRENT_DATE(), m.member_status_dates, DAY) < 365
  -- MSEQ 9508 구독권 구매자 제외 (NOT EXISTS로 안전하게 처리)
  AND NOT EXISTS (
    SELECT 1
    FROM `millie-analysis.sv_product.sv_product_tb_coupon_publish` cp
    WHERE cp.coupon_master_seq = 9508
      AND cp.reg_mem_seq = m.mem_seq
  )
```


---

## 4. MIDAS-2585 — 연정기 프로모션 오픈 안내 LMS 발송을 위한 개인정보 추출 요청 (1/31 발송)


**SQL**:
```sql
-- 테이블: sv_user.sv_user_member
-- 조건: B2C/B2BC 90일 이내 해지자, MSEQ 9508 구독권 구매자 제외
SELECT DISTINCT m.mem_seq
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE m.member_status = '해지회원'
  AND m.channel IN ('B2C', 'B2BC')
  AND m.test_yn = 'N'
  AND m.millie_yn = 'N'
  AND m.dormant_yn = 'N'
  AND m.under_14_yn = 'N'
  AND m.marketing_agree_yn = 'Y'
  AND m.phone_yn = 'Y'
  AND m.b2b_yn = 'N'
  -- 90일 이내 해지자 (해지일 기준)
  AND DATE_DIFF(CURRENT_DATE(), m.member_status_dates, DAY) <= 90
  -- MSEQ 9508 구독권 구매자 제외 (NOT EXISTS로 안전하게 처리)
  AND NOT EXISTS (
    SELECT 1
    FROM `millie-analysis.sv_product.sv_product_tb_coupon_publish` cp
    WHERE cp.coupon_master_seq = 9508
      AND cp.reg_mem_seq = m.mem_seq
  )
```


---

## 5. MIDAS-2586 — 연정기 프로모션 오픈 안내 LMS 발송을 위한 개인정보 추출 요청 (1/23 발송)


**SQL**:
```sql
-- 2. 구독회원중, B2C 월정기 정규상품 10개월이하
SELECT DISTINCT m.mem_seq
FROM `millie-analysis.sv_user.sv_user_member` m
WHERE m.member_status = '구독회원'
  AND m.channel = 'B2C'
  AND m.product_type_detail = '월정기'
  And m.product_type = '정규 상품'
  AND m.test_yn = 'N'
  AND m.millie_yn = 'N'
  AND m.dormant_yn = 'N'
  AND m.under_14_yn = 'N'
  AND m.marketing_agree_yn = 'Y'
  AND m.phone_yn = 'Y'
  AND m.b2b_yn = 'N'
  -- 180일 이내 구독회원 (구독일 기준)
  AND DATE_DIFF(CURRENT_DATE(), m.member_status_dates, DAY) <= 300
  -- MSEQ 9508 구독권 구매자 제외 (NOT EXISTS로 안전하게 처리)
  AND NOT EXISTS (
    SELECT 1
    FROM `millie-analysis.sv_product.sv_product_tb_coupon_publish` cp
    WHERE cp.coupon_master_seq = 9508
      AND cp.reg_mem_seq = m.mem_seq
  )
```


---
