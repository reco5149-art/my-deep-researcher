# 비교: Q4 — 크로스핏은 어떻게 탄생해 어떤 과정을 거쳐 지금에 이르렀나?

만든 시각 2026-11-06 17:00 · 자료 338건 · 모델 gpt-5-mini

## 1. 비교한 실행

| 변형 | 실행 ID | 읽기 사용/총예산 | 목차 | 걸린 시간 |
|---|---|---|---|---|
| 기본 (모든 장치 ON) | `20261106-165417_Q4_full` | 29/40 | new | 81.3초 |
| 남의 구역 알림 OFF | `20261106-165538_Q4_no_peers` | 30/40 | 20261106-165417_Q4_full | 54.6초 |
| 점검·재파견 OFF | `20261106-165633_Q4_no_recheck` | 25/40 | 20261106-165417_Q4_full | 42.0초 |
| links 탐색 OFF | `20261106-165715_Q4_no_links` | 28/40 | 20261106-165417_Q4_full | 66.7초 |
| 단일 에이전트 대조군 | `20261106-165821_Q4_single` | 38/40 | 20261106-165417_Q4_full | 100.8초 |

> 대조군 예산 확인: 95% — 공정(예산을 다 씀)

## 2. 경보 — 0이어야 한다

| 경보 | 보는 장치 | 기본 (모든 장치 ON) | 남의 구역 알림 OFF | 점검·재파견 OFF | links 탐색 OFF | 단일 에이전트 대조군 |
|---|---|---|---|---|---|---|
| 안 읽은 문서 인용 | 원고 규칙 (리서처) | 0 | 0 | 0 | 0 | 0 |
| 없는 문서 ID | 목차 검사 · 원고 검사 | 0 | 0 | 0 | 0 | 0 |
| 예산 초과 | 예산 장치 | 0 | 0 | 0 | 0 | 0 |
| 종합 중 잃은 인용 | 종합 (코디네이터) | 0 | 0 | 0 | 0 | 0 |
| 종합이 만든 새 인용 | 종합 (코디네이터) | 0 | 0 | 0 | 0 | 0 |
| 빈 절 | 리서처 · 점검 | 0 | 0 | 0 | 0 | 0 |
| 대조군 예산 미소진 | 비교 공정성 | — | — | — | — | 0 |

## 3. 신호 — 괄호는 기본과의 차이

| 신호 | 보는 장치 | 기본 (모든 장치 ON) | 남의 구역 알림 OFF | 점검·재파견 OFF | links 탐색 OFF | 단일 에이전트 대조군 |
|---|---|---|---|---|---|---|
| 예산 소진율 | 예산 배분 · 대조군 공정성 | 72% | 75% (++2%) | 62% (-10%) | 70% (-2%) | 95% (++22%) |
| 읽은 문서 수 | 탐색 (시작 자료·links) | 17 | 21 (+4) | 18 (+1) | 17 | 37 (+20) |
| 시작 자료 밖 탐색 비율 | 탐색 (links) | 16% | 30% (++15%) | 16% | 11% (-5%) | 57% (++41%) |
| 절 간 읽기 겹침 | 남의 구역 알림 · 목차 분할 | 0.03 | 0.02 (-0.01) | 0.01 (-0.02) | 0.01 (-0.02) | — |
| 인용된 문서 수 | 원고 규칙 (리서처) | 17 | 21 (+4) | 18 (+1) | 16 (-1) | 15 (-2) |
| 인용 밀도 | 원고 규칙 (리서처) | 10.93 | 10.64 (-0.29) | 11.15 (+0.22) | 9.69 (-1.24) | 9.28 (-1.65) |
| 읽고 안 쓴 비율 | 예산 효율 | 0% | 0% | 0% | 6% (++6%) | 60% (++60%) |
| 연도 원문 일치율 | 원문 대조 (리서처 정확성) | 100% | 100% | 100% | 100% | 100% |
| 코디네이터가 본 비율 | 격리 (분업 구조) | 4.91% | 4.93% (+0.02%) | 4.90% (-0.01%) | 4.89% (-0.02%) | 4.83% (-0.08%) |
| 최대 에이전트가 본 비율 | 격리 (분업 구조) | 3.99% | 4.54% (+0.55%) | 3.02% (-0.97%) | 3.32% (-0.67%) | 17.54% (+13.55%) |
| 1차 부족 신고 | 점검·재파견 | 1 | 1 | 0 (-1) | 1 | — |
| 재파견 후 해결 | 점검·재파견 | 1 | 1 | 0 (-1) | 0 (-1) | — |
| 목차 재작성 | 목차 검사 (코드) | 0 | 0 | 0 | 0 | 0 |
| 제출 거절 | 원고 검사 (코드) | 1 | 0 (-1) | 0 (-1) | 0 (-1) | 0 (-1) |
| 예산 관문 반려 | 제출 관문 (코드) | 1 | 2 (+1) | 2 (+1) | 1 | 2 (+1) |

## 4. 절별로 누가 얼마나 읽고 썼나

### 기본 (모든 장치 ON)

| 절 [역할] | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 크로스핏의 창립과 운동 방법론(정의·철학·운동 기원) [기원·방법론] | 6/7회, 문서 3건 | 3 | sufficient | - |
| S2 프랜차이즈·라이선스·브랜드 제휴와 상업적 확장 [확산·비즈니스] | 8/9회, 문서 4건 | 4 | insufficient → sufficient | 교체 |
| S3 크로스핏 게임즈와 경쟁구조의 발전(오픈→예선→게임즈) 및 주요 선수들 [대회·선수] | 5/6회, 문서 3건 | 3 | sufficient | - |
| S4 부상·건강 문제와 사회적 논란(과학적 근거 및 위기 사례) [안전·논쟁] | 3/5회, 문서 2건 | 2 | sufficient | - |
| S5 크로스핏과 유사·대체되는 그룹 피트니스 비즈니스 비교 [인접 종목·시장] | 4/5회, 문서 4건 | 4 | sufficient | - |
| S6 중심 인물 경력 추적: Rich Froning Jr. 사례로 본 크로스핏 생태계 변화 [인물 추적] | 3/5회, 문서 3건 | 3 | sufficient | - |

### 남의 구역 알림 OFF

| 절 [역할] | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 크로스핏의 창립과 운동 방법론(정의·철학·운동 기원) [기원·방법론] | 5/7회, 문서 5건 | 5 | sufficient | - |
| S2 프랜차이즈·라이선스·브랜드 제휴와 상업적 확장 [확산·비즈니스] | 9/9회, 문서 5건 | 5 | insufficient → sufficient | 교체 |
| S3 크로스핏 게임즈와 경쟁구조의 발전(오픈→예선→게임즈) 및 주요 선수들 [대회·선수] | 5/6회, 문서 3건 | 3 | sufficient | - |
| S4 부상·건강 문제와 사회적 논란(과학적 근거 및 위기 사례) [안전·논쟁] | 3/5회, 문서 2건 | 2 | sufficient | - |
| S5 크로스핏과 유사·대체되는 그룹 피트니스 비즈니스 비교 [인접 종목·시장] | 3/5회, 문서 3건 | 3 | sufficient | - |
| S6 중심 인물 경력 추적: Rich Froning Jr. 사례로 본 크로스핏 생태계 변화 [인물 추적] | 5/5회, 문서 5건 | 5 | sufficient | - |

### 점검·재파견 OFF

| 절 [역할] | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 크로스핏의 창립과 운동 방법론(정의·철학·운동 기원) [기원·방법론] | 6/7회, 문서 3건 | 3 | sufficient | - |
| S2 프랜차이즈·라이선스·브랜드 제휴와 상업적 확장 [확산·비즈니스] | 5/6회, 문서 4건 | 4 | sufficient | - |
| S3 크로스핏 게임즈와 경쟁구조의 발전(오픈→예선→게임즈) 및 주요 선수들 [대회·선수] | 4/6회, 문서 4건 | 4 | sufficient | - |
| S4 부상·건강 문제와 사회적 논란(과학적 근거 및 위기 사례) [안전·논쟁] | 4/5회, 문서 2건 | 2 | sufficient | - |
| S5 크로스핏과 유사·대체되는 그룹 피트니스 비즈니스 비교 [인접 종목·시장] | 3/5회, 문서 3건 | 3 | sufficient | - |
| S6 중심 인물 경력 추적: Rich Froning Jr. 사례로 본 크로스핏 생태계 변화 [인물 추적] | 3/5회, 문서 3건 | 3 | sufficient | - |

### links 탐색 OFF

| 절 [역할] | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 크로스핏의 창립과 운동 방법론(정의·철학·운동 기원) [기원·방법론] | 6/7회, 문서 3건 | 3 | sufficient | - |
| S2 프랜차이즈·라이선스·브랜드 제휴와 상업적 확장 [확산·비즈니스] | 7/12회, 문서 4건 | 4 | insufficient → insufficient → insufficient | 교체; 교체 |
| S3 크로스핏 게임즈와 경쟁구조의 발전(오픈→예선→게임즈) 및 주요 선수들 [대회·선수] | 5/6회, 문서 3건 | 3 | sufficient | - |
| S4 부상·건강 문제와 사회적 논란(과학적 근거 및 위기 사례) [안전·논쟁] | 3/5회, 문서 2건 | 2 | sufficient | - |
| S5 크로스핏과 유사·대체되는 그룹 피트니스 비즈니스 비교 [인접 종목·시장] | 4/5회, 문서 3건 | 3 | sufficient | - |
| S6 중심 인물 경력 추적: Rich Froning Jr. 사례로 본 크로스핏 생태계 변화 [인물 추적] | 3/5회, 문서 3건 | 2 | sufficient | - |

### 단일 에이전트 대조군

| 절 [역할] | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 크로스핏의 창립과 운동 방법론(정의·철학·운동 기원) [기원·방법론] | (단일 에이전트가 함께 읽음) | 3 | sufficient | - |
| S2 프랜차이즈·라이선스·브랜드 제휴와 상업적 확장 [확산·비즈니스] | (단일 에이전트가 함께 읽음) | 4 | sufficient | - |
| S3 크로스핏 게임즈와 경쟁구조의 발전(오픈→예선→게임즈) 및 주요 선수들 [대회·선수] | (단일 에이전트가 함께 읽음) | 2 | sufficient | - |
| S4 부상·건강 문제와 사회적 논란(과학적 근거 및 위기 사례) [안전·논쟁] | (단일 에이전트가 함께 읽음) | 3 | sufficient | - |
| S5 크로스핏과 유사·대체되는 그룹 피트니스 비즈니스 비교 [인접 종목·시장] | (단일 에이전트가 함께 읽음) | 4 | sufficient | - |
| S6 중심 인물 경력 추적: Rich Froning Jr. 사례로 본 크로스핏 생태계 변화 [인물 추적] | (단일 에이전트가 함께 읽음) | 3 | sufficient | - |

## 5. 인용 대조 표본 (원문과 직접 대조)

인용 붙은 문장마다 인용 문서에서 단서(연도·숫자·영문 고유명사)가 가장 많이 겹치는 대목을 붙였다.
읽은 문서를 엉뚱한 문장에 붙인 것은 코드가 못 잡는다. 아래에서 직접 판단해 [ ] 에 표시한다.

### 기본 (모든 장치 ON)

1. **문장**: . 운영·표준화 측면에서 Hyrox는 경기 규칙과 장비·코스가 전역 동일해 경쟁성과 기록 비교가 가능한 ‘스포츠형’ 표준화를 추구하는 반면, F45·Orangetheory는 본사에서 프로그램과 기술(OTF의 심박 모니터 화면·F45의 세션 템플릿)을 표준화해 프랜차이즈 품질을 유지한다
   - 인용: `orangetheory_fitness` Orangetheory Fitness · 단서: Orangetheory, Hyrox, OTF, 45
   - 원문 대목: Orangetheory Fitness (OTF) is a boutique fitness studio franchise, operating globally and based in Boca Raton, Florida. The first studio was established in Fort Lauderdale, Florida, in 2010 by founder, Ellen Latham. The signature classes are one hour long and involve two…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: 크로스핏은 전직 체조 선수인 그렉 글래스먼(Greg Glassman)과 로렌 제네이(Lauren Jenai)가 2000년에 법인으로 설립하고 2001년 캘리포니아 산타크루즈에 체육관을 연 것에서 시작되었다
   - 인용: `crossfit` CrossFit · 단서: Glassman, Lauren, Jenai, 2001, Greg, 2000
   - 원문 대목: …eg Glassman, a former gymnast, created his first CrossFit-style workout when he was 16 by combining elements of gymnastics with weightlifting. The workout he created, called Fran, added thrusters (a combination of front squat and push press) to pull-ups. Greg Glassman and Lauren Jenai incorporated CrossFit, Inc. in 2000. They opened a gym in Santa Cruz, California, in 2001, and posted their workouts on the Internet for their clients. These workouts were then quickly adopted by individuals in the police, military, and firef…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: . 마지막으로 크로스핏은 표준화·프랜차이즈형 모델을 택한 다른 그룹 피트니스(예: Hyrox·F45·Orangetheory)와는 운영·대회화·참가자 경험 측면에서 차이를 보였고, 대표 선수의 경력(예: Rich Froning Jr.)은 개인 성취에서 애필리에이트 창업·브랜드화·팀 경쟁으로 이어지는 생태계 변화를 잘 드러낸다
   - 인용: `crossfit_mayhem` CrossFit Mayhem · 단서: Orangetheory, Froning, Hyrox, Rich, 45
   - 원문 대목: CrossFit Mayhem is a CrossFit affiliate located in Cookeville, Tennessee. Mayhem was started in 2009 by Rich Froning Jr. in his father's barn as a place to train. In 2012, Rich opened the original downtown facility, but almost immediately began plans to expand. That relocation/expansion occurred in 2016. Due in large part to Froning's success at the CrossFit Games, Crossfit…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: . 예방을 위해서는 훈련강도·볼륨의 점진적 증대, 휴식과 회복의 확보, 탈수·고온 환경의 회피, 증상 발생 시 조기 진단(색 변한 소변, 과도한 근육통·무력감 등)과 즉각적 의료 대응이 권고된다
   - 인용: `rhabdomyolysis` Rhabdomyolysis · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . 참가자 경험은 크로스핏이 박스별 재량과 WOD의 변동성·경쟁적 커뮤니티를 강조하는 반면
   - 인용: `crossfit` CrossFit · 단서: WOD
   - 원문 대목: …gram as one that can best prepare its trainees for any physical contingency, preparing them for what may be "unknown" and "unknowable". It is practiced by members in CrossFit-affiliated gyms, and by individuals who complete daily workouts (otherwise known as "WODs" or "Workouts of the Day"). Studies indicate that CrossFit can have positive effects on a number of physical fitness parameters and body composition, as well as on the mental state and social life of its participants. CrossFit has been criticized for causing…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

### 남의 구역 알림 OFF

1. **문장**: . 과훈련의 기전으로는 근육 미세손상 축적, 영양부족, 전신 염증반응 등이 제시된다
   - 인용: `overtraining` Overtraining · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: 크로스핏은 그렉 글래스먼(Greg Glassman)과 로렌 제나이(Lauren Jenai)가 2000년에 CrossFit, Inc.로 법인화하며 공식 창립한 브랜드화된 피트니스 방법론으로, 글래스먼이 16세에 체조와 역도 요소를 결합해 만든 초창기 운동에서 출발했다
   - 인용: `crossfit` CrossFit · 단서: CrossFit, Glassman, Lauren, Jenai, Greg, 2000
   - 원문 대목: …his first CrossFit-style workout when he was 16 by combining elements of gymnastics with weightlifting. The workout he created, called Fran, added thrusters (a combination of front squat and push press) to pull-ups. Greg Glassman and Lauren Jenai incorporated CrossFit, Inc. in 2000. They opened a gym in Santa Cruz, California, in 2001, and posted their workouts on the Internet for their clients. These workouts were then quickly adopted by individuals in the police, military, and firefighting services. Those who used Glassm…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: . 동시에 과훈련과 횡문근융해증 등의 안전 문제가 논의되었고, 지도자의 점진적 강도 조절·회복·수분 관리 등이 예방의 핵심으로 제시되었다
   - 인용: `rhabdomyolysis` Rhabdomyolysis · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: 대회 장소는 아로마스→카슨(2010~2016)→매디슨(2017~2023) 등으로 이동했고, 2024년에는 텍사스 포트워스의 딕키스 아레나에서 열렸으며 2026년에는 산호세에서 20주년을 기념해 개최될 예정이라고 보고되었다
   - 인용: `crossfit_games` CrossFit Games · 단서: 2023, 2016, 2024, 2017, 2010, 2026
   - 원문 대목: …easing to $300,000 in 2019. The prize purse of the 2010 Games was sponsored by Progenex that provided $25,000 for the winners. The following year saw the largest jump in prize money when Reebok sponsored its first Games, and the prize money for first place in 2011 increased to $250,000. The total prize payout in 2016 was $2,200,000, rising to 3 million in 2020. The prize payout increased again in 2021 when NoBull became the title sponsor of the Games. There was no title sponsor for the 2024 CrossFit Games. == Qualif…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . 과훈련의 극단적 형태인 운동유발 횡문근융해증은 빠른 진단과 수액치료가 회복에 필수이며 전형적 임상증상(근통·권태·홍차색 소변 등)을 보인다
   - 인용: `overtraining` Overtraining · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

### 점검·재파견 OFF

1. **문장**: . 진단에는 혈중 크레아틴키나아제(CK) 상승이 핵심으로, CK 1,000 U/L 이상을 횡문근융해증의 지표로 보며 5,000–15,000 U/L 이상은 중증 범주로 분류된다
   - 인용: `rhabdomyolysis` Rhabdomyolysis · 단서: 15,000, 5,000, 1,000, 15000, 1000, 5000
   - 원문 대목: …. The diagnosis is supported by a urine test strip which is positive for "blood" but the urine contains no red blood cells when examined with a microscope. Blood tests show a creatine kinase activity greater than 1000 U/L, with severe disease being above 5000–15000 U/L. The mainstay of treatment is large quantities of intravenous fluids. Other treatments may include dialysis or hemofiltration in more severe cases. Once urine output is established, sodium bicarbonate and mannitol are commonly used but they are poorly sup…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: 크로스핏은 전 체조 선수였던 그렉 글래스먼(Greg Glassman)과 로렌 제나이(Lauren Jenai)가 2000년에 법인으로 설립한 브랜드화된 피트니스 방법론으로, 글래스먼이 1996년경 고안한 교차(크로스)훈련 개념에서 출발했다
   - 인용: `crossfit` CrossFit · 단서: Glassman, Lauren, Jenai, 1996, Greg, 2000
   - 원문 대목: CrossFit is a branded fitness regimen that involves constantly varied functional movements performed at high intensity. The method was developed by Greg Glassman, who founded CrossFit with Lauren Jenai in 2000, with CrossFit as its registered trademark. The company forms what has been described as the biggest fitness chain in the world, with around 10,000 affiliated gyms in over 150 countries as of 2025, about 40% of…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: , 오렌지띠어리는 자체 심박 모니터·앱·데이터(스플랫 포인트)로 회원 경험을 표준화한다
   - 인용: `orangetheory_fitness` Orangetheory Fitness · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: . 장소 변화는 아로마스→2010년 카슨(Home Depot Center)→2017년 매디슨(Alliant Energy Center)으로 이어졌고, 2019년에는 매디슨에서 대회가 열렸다
   - 인용: `crossfit_games` CrossFit Games · 단서: Alliant, Energy, Center, Depot, 2019, Home
   - 원문 대목: …as held at a ranch in Aromas, California, with small groups of participants and spectators, but the CrossFit Games rapidly grew, and within a few years, the competition was moved to larger venues at the Home Depot Center in Carson, California, followed by the Alliant Energy Center in Madison, Wisconsin. It was held in the Dickies Arena in Fort Worth, Texas in 2024. The Games were sponsored by Reebok from 2011 to 2020, and by Nobull from 2021 to 2023. The CrossFit Games season consists of four stages; the first qualificati…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . 반대로 F45·오렌지띠어리는 프랜차이즈 표준화와 기술(심박수 지표)으로 대중적 체험을 균일화해 크로스핏식 박스(개별 지도·비표준화)와 다른 시장 포지셔닝을 취한다
   - 인용: `orangetheory_fitness` Orangetheory Fitness · 단서: 45
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

### links 탐색 OFF

1. **문장**: 브랜드 제휴는 스폰서십·라이선스·공동제품개발 형태로 진행되었다. Reebok은 2010년 크로스핏과 10년 파트너십을 맺고 CrossFit Games 공식 의류·신발 파트너로서 Nano를 공동 개발해 문화를 소비재로 상업화했고, Games 상금·노출 확대에 기여했다
   - 인용: `crossfit_games` CrossFit Games · 단서: CrossFit, Reebok, Games, 2010, Nano, 10
   - 원문 대목: …The quarterfinals were removed in 2025, and athletes moved directly from the Open to the semifinals, but are restored in 2026. === Regionals, Sanctionals, and Semifinals === Between 2009 and 2018, competitors qualified for the Games through participation at CrossFit Games regional events around the world. The top men and women from the Sectional in 2010, and the Open from 2011 to 2018, participated in the Regionals to qualify for the Games. There were 17 Regionals most years until 2015, when athletes from the 17 regions…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: 크로스핏과 횡문근융해증의 연관성은 논쟁적이며 일부 보고에서 급증 가설이 제기됐으나, 관련 연구는 결론이 일치하지 않고 한 연구는 잘못된 수행·환경이 아니라면 심각한 위협은 아니라고 보고했다
   - 인용: `overtraining` Overtraining · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: . 글래스먼은 체조 배경의 운동선수였고 16세 때 체조적 움직임과 역도 요소를 결합한 첫 운동(예: 프랜)을 만들며 체조와 역도의 결합을 이론화했다
   - 인용: `crossfit` CrossFit · 단서: 16
   - 원문 대목: …esulting from a breakdown of muscle from extreme exertion. == History == CrossFit, meaning cross-discipline fitness, was first conceived as a company in 1996 as Cross-Fit. Greg Glassman, a former gymnast, created his first CrossFit-style workout when he was 16 by combining elements of gymnastics with weightlifting. The workout he created, called Fran, added thrusters (a combination of front squat and push press) to pull-ups. Greg Glassman and Lauren Jenai incorporated CrossFit, Inc. in 2000. They opened a gym in Sa…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: 프로닝은 선수 활동으로 1,050,000달러 이상의 상금과 리복·오클리·로그(Rogue Fitness) 같은 스폰서십을 확보했으며, 2015년 리복이 그의 참여로 설계된 신발을 출시하는 등 엘리트 선수의 상업적 역할을 확대했다
   - 인용: `rich_froning_jr` Rich Froning Jr. · 단서: 1,050,000, 1050000, Fitness, Rogue, 2015
   - 원문 대목: …ired from individual competitions after 2014, and led a team from CrossFit Mayhem to first-place finishes in the Team category in 2015, 2016, 2018, 2019, 2021, and 2022, at the CrossFit Games. In addition to making a living off CrossFit, Froning has won over $1,050,000 in prize money from winning the CrossFit Games four times. Additionally, he has accumulated significant sponsorships from brands like Reebok, Oakley, and Rogue Fitness. In early 2015, Reebok released a shoe designed, in part, by Froning. Froning owns and oper…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . Rogue Fitness는 박스 장비 일괄 공급과 자체 제조로 박스 표준화를 주도하고 Games 장비·이벤트를 통한 수익 다각화를 실행했다
   - 인용: `rogue_fitness` Rogue Fitness · 단서: Fitness, Games, Rogue
   - 원문 대목: …lifting equipment manufacturer Ghost Strong in 2022. Rogue was a contender for Inc.'s 2018 Company of the Year. Rogue Fitness had 200 employees in 2014, increasing to 600 in 2019, and 850 in 2020. It has 1,400 employees worldwide as of 2022. == Activities == Rogue has been associated with CrossFit from its beginning. Rogue is one of the primary suppliers for equipment for CrossFit boxes (gyms) around the world. It started supplying equipment for the CrossFit Games in 2009, before becoming the sole provider to the Games…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

### 단일 에이전트 대조군

1. **문장**: 크로스핏의 경쟁구조는 2007년 아로마스에서 열린 초대 CrossFit Games에서 출발해 점차 계층적 예선 체계로 발전했다. 초대 대회는 누구나 참가 가능한 공개 형식이었으나 참가자가 급증하자 2009년 지역(Regionals)을 도입했고, 2011년에는 온라인 예선인 오픈(Open)을 도입해 전 세계 참여를 확대했다
   - 인용: `crossfit_games` CrossFit Games · 단서: Regionals, CrossFit, Games, 2011, 2007, 2009
   - 원문 대목: …the Regionals, was initiated in 2009 to winnow down the number of athletes who could take part in the Games. This was further expanded into a two-stage process in 2010 with the introduction of Sectionals where competitors were first selected to compete in the Regionals. The Sectionals became the Open the following year, and between 2011 and 2018, all athletes had to go through the same two-stage qualification process, the Open and Regionals, apart from a few who received special invites in some years. In the 2019 CrossFit G…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: . 그의 경력은 크로스핏이 단순한 운동 프로그램을 넘어선 커뮤니티 기반의 비즈니스·경쟁·교육 생태계로 확장된 것을 반영하며, 선수 스폰서십(리복·로그 등)과 체육관 운영을 통한 수익 모델 상의 전환을 드러낸다
   - 인용: `rich_froning_jr` Rich Froning Jr. · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: . Orangetheory Fitness는 시간당 심박수 기반의 스테이션 순환형 HIIT 클래스를 기술(심박수 모니터)로 표준화하고 회원 관리를 중심으로 확장한 프랜차이즈 모델을 갖춘다
   - 인용: `orangetheory_fitness` Orangetheory Fitness · 단서: Orangetheory, Fitness, HIIT
   - 원문 대목: Orangetheory Fitness (OTF) is a boutique fitness studio franchise, operating globally and based in Boca Raton, Florida. The first studio was established in Fort Lauderdale, Florida, in 2010 by founder, Ellen Latham. The signature classes are one hour long and involve two…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: . 2021년부터 2023년까지는 Nobull이 게임스의 타이틀 스폰서로 활동하며 크로스핏 커뮤니티를 겨냥한 미니멀·내구성 중심의 의류·신발을 전개했다
   - 인용: `nobull` Nobull · 단서: Nobull, 2023, 2021
   - 원문 대목: …an athletics company based in Boston, Massachusetts, that makes sportswear. Founded in 2015 by Marcus Wilson and Michael Schaeffer, the brand was closely associated with CrossFit but it has since expanded into other sports. Starting with the 2023 NFL season, Nobull became the official sponsor of the NFL Scouting Combine, and also sponsors the PGA Tour, and San Francisco 49ers quarterback Mac Jones. It also sponsored the UFL for the 2026 season. It was the title sponsor of the CrossFit Games from 2021 to 2023. == Etymol…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . 그의 경력은 크로스핏이 단순한 운동 프로그램을 넘어선 커뮤니티 기반의 비즈니스·경쟁·교육 생태계로 확장된 것을 반영하며, 선수 스폰서십(리복·로그 등)과 체육관 운영을 통한 수익 모델 상의 전환을 드러낸다
   - 인용: `rogue_fitness` Rogue Fitness · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

## 6. 내 판단 (직접 적기)

보고서들을 나란히 읽은 뒤 자기 말로 적는다. 지표 표는 명백한 실패를 거르는 데만 쓴다.

- 어느 쪽이 나은가:
- 그렇게 판단한 이유(구체적인 대목을 들어):

### 마음에 안 드는 대목 → 어디서 비롯됐나

| 대목(인용) | 보고서 | 절 | 리서처 원고(v1/v2)에도 있었나 | 근거 문서 | 원인 추정(목차·탐색·원고·종합) |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
|  |  |  |  |  |  |
