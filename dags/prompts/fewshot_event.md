# FewShot — 이벤트_참여자

> 이벤트 페이지 댓글·미션 참여 유저. event_rand_code → event_seq 기반.

---

## 1. MIDAS-2446 — 신작감상×네이버포인트 [진소예] 올인원 팩 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
with event_member as (
    select
        mem_seq
    from millie-analysis.sv_contents.sv_contents_tb_event_member
    where event_seq = 681
        and reg_date >= date('2025-12-01')
        and reg_date < date('2025-12-15')
    group by mem_seq
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180127917, 180127918, 180128038, 180128037, 180128039)
        and lb.reg_date >= date('2025-12-01')
        and lb.reg_date < date('2025-12-15')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2025-12-01')
        and view_date < date('2025-12-15')
        and bei.book_seq in  (180127917, 180127918, 180128038, 180128037, 180128039)
    group by erd.member_seq
)

select
    m.mem_seq,
    m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.member_status
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---

## 2. MIDAS-2447 — 올해 웹툰웹소 핫.톱.픽 보고 포인트 받고 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = 'jo73343383qw064r'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2025-12-05')
    AND reg_date < DATE('2025-12-19')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180116273, 180117707, 180123822, 180120054, 180117139, 180116267, 180122936, 180119903, 180114989, 180119509, 180116265, 180123550, 180123366, 180123367, 180117775, 180123538, 180120051, 180123534, 180123533, 180119707, 180114280, 180114226, 180120037, 180116271, 180114267, 180121227, 180116266, 180119705, 180116274, 180119706, 180119799, 180123302, 180118105, 180104373, 180123243, 180111667, 180119802, 180119485, 180121145, 180119977, 180102090, 180116644, 180123625, 180122858, 180089633, 180103907, 180109803, 180115742, 180088073, 180124175, 180099395, 180115743, 180109520, 180115746, 180114554, 180104676, 180109804, 180116842, 180104622, 180114677)
        and lb.reg_date >= date('2025-12-05')
        and lb.reg_date < date('2025-12-19')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2025-12-05')
        and view_date < date('2025-12-19')
        and bei.book_seq in  (180116273, 180117707, 180123822, 180120054, 180117139, 180116267, 180122936, 180119903, 180114989, 180119509, 180116265, 180123550, 180123366, 180123367, 180117775, 180123538, 180120051, 180123534, 180123533, 180119707, 180114280, 180114226, 180120037, 180116271, 180114267, 180121227, 180116266, 180119705, 180116274, 180119706, 180119799, 180123302, 180118105, 180104373, 180123243, 180111667, 180119802, 180119485, 180121145, 180119977, 180102090, 180116644, 180123625, 180122858, 180089633, 180103907, 180109803, 180115742, 180088073, 180124175, 180099395, 180115743, 180109520, 180115746, 180114554, 180104676, 180109804, 180116842, 180104622, 180114677)
    group by erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.member_status
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---

## 3. MIDAS-2448 — <재능만렙 플레이어> 포인트백 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '02397g48a643022r'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2025-12-08')
    AND reg_date < DATE('2025-12-22')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180129725)
        and lb.reg_date >= date('2025-12-08')
        and lb.reg_date < date('2025-12-22')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2025-12-08')
        and view_date < date('2025-12-22')
        and bei.book_seq in  (180129725)
    group by erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.member_status
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---

## 4. MIDAS-2520 — 12월 월간 스포트라이트 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '6x05kt26j155m5d1'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2025-11-28')
    AND reg_date < DATE('2026-01-01')
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.member_status
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
where 1=1
```


---

## 5. MIDAS-2521 — 산타는 선물을 싣고 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '44m5gcj1y2zg3u62'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2025-12-19')
    AND reg_date < DATE('2025-12-29')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180121163, 180116277, 180128992, 180116267, 180116265, 180116883)
        and lb.reg_date >= date('2025-12-19')
        and lb.reg_date < date('2025-12-29')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2025-12-19')
        and view_date < date('2025-12-29')
        and bei.book_seq in  (180121163, 180116277, 180128992, 180116267, 180116265, 180116883)
    group by erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.member_status
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---

## 6. MIDAS-2522 — 올해 마지막 찬스! 1화 감상하고 1천원 받자 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '1461a5v852y63yq4'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2025-12-26')
    AND reg_date < DATE('2026-01-01')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180104373, 180128016, 180124874, 180123302, 180124175, 180123625, 180127400, 180123599, 180124174, 180124173, 180131171, 180129054, 180128904, 180128762, 180128369, 180127997, 180127964, 180123822, 180123821, 180122936)
        and lb.reg_date >= date('2025-12-26')
        and lb.reg_date < date('2026-01-01')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2025-12-26')
        and view_date < date('2026-01-01')
        and bei.book_seq in  (180104373, 180128016, 180124874, 180123302, 180124175, 180123625, 180127400, 180123599, 180124174, 180124173, 180131171, 180129054, 180128904, 180128762, 180128369, 180127997, 180127964, 180123822, 180123821, 180122936)
    group by erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.member_status
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---

## 7. MIDAS-2579 — 12/12에는 포인트 이리이리 오너라 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '151151z202g61b08'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2025-12-12')
    AND reg_date < DATE('2025-12-26')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180116148,180102956,180116843,180118310,180104588,180104544,180104671,180104678,180117956,180103502,180111670,180104626,180118307,180116654,180116646,180104782,180103157,180109527,180103162,180104772,180116650,180113602,180104777,180109403,180111269,180104592,180119485,180119803,180122533,180119944,180122861,180122860,180119943,180127823,180121146,180121143,180121144,180119710,180120152,180111968,180119980,180120147,180120150,180124163,180121291,180119978,180121289,180119805,180119744,180119742,180120154,180120156,180124174,180123206,180123221,180123219,180123220,180115745,180128016,180128017,180128018,180124874,180123683,180118104,180118112,180114726,180120136,180120003,180115744,180118113,180118108,180115383,180118109,180118107,180118110,180124480,180118106,180118111,180127861,180127862,180127863,180127873)
        and lb.reg_date >= date('2025-12-12')
        and lb.reg_date < date('2025-12-26')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2025-12-12')
        and view_date < date('2025-12-26')
        and bei.book_seq in  (180116148,180102956,180116843,180118310,180104588,180104544,180104671,180104678,180117956,180103502,180111670,180104626,180118307,180116654,180116646,180104782,180103157,180109527,180103162,180104772,180116650,180113602,180104777,180109403,180111269,180104592,180119485,180119803,180122533,180119944,180122861,180122860,180119943,180127823,180121146,180121143,180121144,180119710,180120152,180111968,180119980,180120147,180120150,180124163,180121291,180119978,180121289,180119805,180119744,180119742,180120154,180120156,180124174,180123206,180123221,180123219,180123220,180115745,180128016,180128017,180128018,180124874,180123683,180118104,180118112,180114726,180120136,180120003,180115744,180118113,180118108,180115383,180118109,180118107,180118110,180124480,180118106,180118111,180127861,180127862,180127863,180127873)
    group by erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---

## 8. MIDAS-2624 — 새해 첫 금요일엔 19금! 어른 비법서 공개 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = 'f66up1p30drb1155'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2026-01-02')
    AND reg_date < DATE('2026-01-16')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180116265,180132421,180131942,180116267,180123550,180120037,180131171,180123366,180129052,180128904,180129051,180119509,180121163,180116271,180123538,180129053,180116277,180123367,180120039,180117775,180117210,180117010,180117354,180130583,180121227,180119911,180127534,180128275,180124342,180123373,180123372,180121252,180121248,180121247,180132222,180131931,180132423,180131947,180132425,180132309,180132215,180131704,180131919,180127917,180125834,180116148,180131925,180123621,180102956,180122533,180116843,180124163,180089633,180122858,180104671,180104588,180127388,180104288,180132816,180132814,180116646,180127257,180118307,180120158,180104626,180121145,180104591,180125836,180123704,180127459,180128180,180129232,180131560,180131561,180132644,180132643)
        and lb.reg_date >= date('2026-01-02')
        and lb.reg_date < date('2026-01-16')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2026-01-02')
        and view_date < date('2026-01-16')
        and bei.book_seq in  (180116265,180132421,180131942,180116267,180123550,180120037,180131171,180123366,180129052,180128904,180129051,180119509,180121163,180116271,180123538,180129053,180116277,180123367,180120039,180117775,180117210,180117010,180117354,180130583,180121227,180119911,180127534,180128275,180124342,180123373,180123372,180121252,180121248,180121247,180132222,180131931,180132423,180131947,180132425,180132309,180132215,180131704,180131919,180127917,180125834,180116148,180131925,180123621,180102956,180122533,180116843,180124163,180089633,180122858,180104671,180104588,180127388,180104288,180132816,180132814,180116646,180127257,180118307,180120158,180104626,180121145,180104591,180125836,180123704,180127459,180128180,180129232,180131560,180131561,180132644,180132643)
    group by erd.member_seq
)

,
last_episode as (
select book_seq, max(episode_seq) as last_episode_seq
  from `millie-analysis.sv_contents.sv_contents_book_episode_info`
where 1=1
and book_seq in  (180116265,180132421,180131942,180116267,180123550,180120037,180131171,180123366,180129052,180128904,180129051,180119509,180121163,180116271,180123538,180129053,180116277,180123367,180120039,180117775,180117210,180117010,180117354,180130583,180121227,180119911,180127534,180128275,180124342,180123373,180123372,180121252,180121248,180121247,180132222,180131931,180132423,180131947,180132425,180132309,180132215,180131704,180131919,180127917,180125834,180116148,180131925,180123621,180102956,180122533,180116843,180124163,180089633,180122858,180104671,180104588,180127388,180104288,180132816,180132814,180116646,180127257,180118307,180120158,180104626,180121145,180104591,180125836,180123704,180127459,180128180,180129232,180131560,180131561,180132644,180132643)
group by 1
)


-- 완결 에피소드 열람 수 (각 작품의 마지막 에피소드만)
, view_complete_target AS (
    SELECT
        erd.member_seq AS mem_seq
        , COUNT(DISTINCT erd.episode_seq) AS complete_cnt
    FROM millie-analysis.sv_service.sv_service_stat_member_episode_read_daily AS erd
        INNER JOIN last_episode AS le ON erd.episode_seq = le.last_episode_seq
    WHERE 1=1
        AND erd.member_seq IN (SELECT mem_seq FROM event_member)
        AND view_date >= DATE('2026-01-02')
        AND view_date < DATE('2026-01-16')
    GROUP BY erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , vct.complete_cnt as `완결 에피소드 열람 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
    left join view_complete_target as vct on et.mem_seq = vct.mem_seq
where 1=1
```


---

## 9. MIDAS-2663 — 오직 밀리 로맨스만 쪼르르 모아 밀착 리뷰 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '1j63e30479k26u01'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND date(reg_date) >= DATE('2026-01-16')
    AND date(reg_date) < DATE('2026-01-30')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180116148,180102956,180116843,180104671,180104588,180104678,180104626,180103502,180104592,180104544,180111670,180103157,180116646,180103162,180118307,180104777,180113602,180104782,180117956,180116650,180109403,180118310,180111269,180109527,180104772,180116654)
        and lb.reg_date >= date('2026-01-16')
        and lb.reg_date < date('2026-01-30')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2026-01-16')
        and view_date < date('2026-01-30')
        and bei.book_seq in  (180116148,180102956,180116843,180104671,180104588,180104678,180104626,180103502,180104592,180104544,180111670,180103157,180116646,180103162,180118307,180104777,180113602,180104782,180117956,180116650,180109403,180118310,180111269,180109527,180104772,180116654)
    group by erd.member_seq
)
,
review_target as (
  select em.mem_seq, count(distinct cr.review_seq) as review_cnt
    from event_member em
    inner join `millie-analysis.sv_contents.sv_contents_tb_content_review` cr on 1=1
    and em.mem_seq = cr.mem_seq
  where 1=1
      and content_seq in (180116148,180102956,180116843,180104671,180104588,180104678,180104626,180103502,180104592,180104544,180111670,180103157,180116646,180103162,180118307,180104777,180113602,180104782,180117956,180116650,180109403,180118310,180111269,180109527,180104772,180116654)
  and status_code = 0 -- 리뷰상태:정상
  AND date(cr.created_at) >= DATE('2026-01-16')
  AND date(cr.created_at) < DATE('2026-01-30')
  group by em.mem_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , rt.review_cnt as `리뷰 작성 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
    left join review_target as rt on et.mem_seq = rt.mem_seq
```


---

## 10. MIDAS-2676 — 26년 1월 웹툰 나잇 100% 포인트 파티 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '02152a65750dk4t9'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2026-01-19')
    AND reg_date < DATE('2026-02-02')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180127532,180132102,180130329,180121061,180116274,180119401,180117137,180117138,180117140,180117141,180119394,180117148,180117139,180119399,180119395,180119392,180119402,180119397,180117147,180119391,180119398,180119400,180119393,180119396,180117146,180117142,180117143,180117144,180117145)
        and lb.reg_date >= date('2026-01-19')
        and lb.reg_date < DATE('2026-02-02')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2026-01-19')
        and view_date < DATE('2026-02-02')
        and bei.book_seq in  (180127532,180132102,180130329,180121061,180116274,180119401,180117137,180117138,180117140,180117141,180119394,180117148,180117139,180119399,180119395,180119392,180119402,180119397,180117147,180119391,180119398,180119400,180119393,180119396,180117146,180117142,180117143,180117144,180117145)
    group by erd.member_seq
)

,
last_episode as (
select book_seq, max(episode_seq) as last_episode_seq
  from `millie-analysis.sv_contents.sv_contents_book_episode_info`
where 1=1
and book_seq in  (180127532,180132102,180130329,180121061,180116274,180119401,180117137,180117138,180117140,180117141,180119394,180117148,180117139,180119399,180119395,180119392,180119402,180119397,180117147,180119391,180119398,180119400,180119393,180119396,180117146,180117142,180117143,180117144,180117145)
group by 1
)


-- 완결 에피소드 열람 수 (각 작품의 마지막 에피소드만)
, view_complete_target AS (
    SELECT
        erd.member_seq AS mem_seq
        , COUNT(DISTINCT erd.episode_seq) AS complete_cnt
    FROM millie-analysis.sv_service.sv_service_stat_member_episode_read_daily AS erd
        INNER JOIN last_episode AS le ON erd.episode_seq = le.last_episode_seq
    WHERE 1=1
        AND erd.member_seq IN (SELECT mem_seq FROM event_member)
        AND view_date >= DATE('2026-01-19')
        AND view_date < DATE('2026-02-02')
    GROUP BY erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , vct.complete_cnt as `완결 에피소드 열람 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
    left join view_complete_target as vct on et.mem_seq = vct.mem_seq
where 1=1
```


---

## 11. MIDAS-2677 — 26년 1월 랭킹 고공 행진 작품 감상하고 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '26jol92707410f20'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2026-01-22')
    AND reg_date < DATE('2026-02-05')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180122936,180129054,180123366,180129052,180123550,180116267,180120037,180119509,180121163,180117775,180116277,180123538,180128904,180131171,180132242,180116266,180130869,180127964,180123533,180128762,180114154,180124175,180128801,180131986,180129645,180132898,180132671,180132913,180134534,180132915,180127917,180124163,180123621,180131919,180131925,180127388,180127257,180132814,180124173,180132816)
        and lb.reg_date >= date('2026-01-22')
        and lb.reg_date < DATE('2026-02-05')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt
    from millie-analysis.sv_service.sv_service_stat_member_episode_read_daily as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2026-01-22')
        and view_date < DATE('2026-02-05')
        and bei.book_seq in  (180122936,180129054,180123366,180129052,180123550,180116267,180120037,180119509,180121163,180117775,180116277,180123538,180128904,180131171,180132242,180116266,180130869,180127964,180123533,180128762,180114154,180124175,180128801,180131986,180129645,180132898,180132671,180132913,180134534,180132915,180127917,180124163,180123621,180131919,180131925,180127388,180127257,180132814,180124173,180132816)
    group by erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt as `뷰어 오픈 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---

## 12. MIDAS-2714 — 26년 2월 내 맘 속 #키워드 이벤트 참여조건 충족자 개인정보 추출 요청


**SQL**:
```sql
WITH event_info AS (
  SELECT event_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event`
  WHERE event_rand_code = '1p6u1622451l1pfc'
),
event_member AS (
  SELECT DISTINCT mem_seq
  FROM `millie-analysis.sv_contents.sv_contents_tb_event_member`
  WHERE event_seq = (SELECT event_seq FROM event_info)
    AND reg_date >= DATE('2026-02-03')
    AND reg_date < DATE('2026-02-17')
)
, library_target as (
    select
        et.mem_seq
        , count(book_seq) as library_cnt
    from event_member as et
        inner join millie-analysis.sv_contents.sv_contents_tb_library_book as lb on et.mem_seq = lb.reg_mem_seq
    where 1=1
        and lb.book_seq in  (180089648,180127257,180132425,180116277,180132642,180103162,180129053,180121163,180128181,180124169,180127963,180132987)
        and lb.reg_date >= date('2026-02-03')
        and lb.reg_date < DATE('2026-02-17')
    group by et.mem_seq
)

, view_target as 
(
    select
        erd.member_seq as mem_seq
        , count(distinct erd.episode_seq) as cnt_epi
        , count(distinct bei.book_seq) as cnt_book
    from `millie-analysis.sv_service.sv_service_stat_member_episode_read_daily` as erd
        inner join millie-analysis.sv_contents.sv_contents_book_episode_info as bei on erd.episode_seq = bei.episode_seq
    where 1=1
        and erd.member_seq in (select mem_seq from event_member)
        and view_date >= date('2026-02-03')
        and view_date < DATE('2026-02-17')
        and bei.book_seq in  (180089648,180127257,180132425,180116277,180132642,180103162,180129053,180121163,180128181,180124169,180127963,180132987)
    group by erd.member_seq
)

select
    m.mem_seq
    , m.age_band as `연령대`
    , lt.library_cnt as `서재 담은 수`
    , vt.cnt_epi as `에피소드 수`
    , vt.cnt_book as `도서 수`
    , m.marketing_agree_yn as `마케팅 수신 동의`
    , m.event_push_yn as `푸시 수신 동의`
    , m.phone_yn as `문자 수신 동의`
    , m.under_14_yn as `14세 미만 여부`
    , m.member_status as `구독 상태`
    , m.b2b_yn
    , m.dormant_yn as `휴면회원`
    , m.millie_yn as `테스트회원 1`
    , m.test_yn as `테스트 회원 2`
from `millie-analysis.sv_user.sv_user_member` as m
    inner join event_member as et on m.mem_seq = et.mem_seq
    left join library_target as lt on et.mem_seq = lt.mem_seq
    left join view_target as vt on et.mem_seq = vt.mem_seq
where 1=1
```


---
