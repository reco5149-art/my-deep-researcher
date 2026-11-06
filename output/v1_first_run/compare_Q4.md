# 비교: Q4 — 크로스핏은 어떻게 탄생해 어떤 과정을 거쳐 지금에 이르렀나?

만든 시각 2026-11-06 16:33 · 자료 338건 · 모델 gpt-5-mini

## 1. 비교한 실행

| 변형 | 실행 폴더 | 읽기 사용/총예산 | 목차 | 걸린 시간 |
|---|---|---|---|---|
| 기본 (모든 장치 ON) | `20261106-162615_Q4_full` | 15/40 | new | 50.8초 |
| 남의 구역 알림 OFF | `20261106-162706_Q4_no_peers` | 18/40 | 20261106-162615_Q4_full | 43.5초 |
| 점검·재파견 OFF | `20261106-162750_Q4_no_recheck` | 23/40 | 20261106-162615_Q4_full | 34.0초 |
| 단일 에이전트 대조군 | `20261106-162824_Q4_single` | 10/40 | 20261106-162615_Q4_full | 244.4초 |

> 대조군 예산 확인: 25% 사용. 90% 미만이라 이 비교는 상대를 묶어 둔 비교일 수 있다.

## 2. 경보 — 0이어야 한다

| 경보 | 보는 장치 | 기본 (모든 장치 ON) | 남의 구역 알림 OFF | 점검·재파견 OFF | 단일 에이전트 대조군 |
|---|---|---|---|---|---|
| 안 읽은 문서 인용 | 원고 규칙 (리서처) | 0 | 0 | 0 | 0 |
| 없는 문서 ID | 목차 검사 · 원고 검사 | 0 | 0 | 0 | 0 |
| 예산 초과 | 예산 장치 | 0 | 0 | 0 | 0 |
| 종합 중 잃은 인용 | 종합 (코디네이터) | 0 | 0 | 0 | 0 |
| 종합이 만든 새 인용 | 종합 (코디네이터) | 0 | 0 | 0 | 0 |
| 빈 절 | 리서처 · 점검 | 0 | 0 | 0 | 0 |
| 대조군 예산 미소진 | 비교 공정성 | — | — | — | 🚨 1 |

## 3. 신호 — 순위표가 아니라 어디를 볼지 가리키는 값

| 신호 | 보는 장치 | 한 줄 설명 | 기본 (모든 장치 ON) | 남의 구역 알림 OFF | 점검·재파견 OFF | 단일 에이전트 대조군 |
|---|---|---|---|---|---|---|
| 예산 소진율 | 예산 배분 · 대조군 공정성 | 전체 읽기 예산 중 실제로 읽은 비율 | 38% | 45% | 57% | 25% |
| 읽은 문서 수 | 탐색 (시작 자료·links) | 한 번 이상 연 서로 다른 문서 수 | 15 | 16 | 15 | 9 |
| 링크로 찾아간 비율 | 탐색 (links) | 읽은 문서 중 시작 자료가 아니라 링크를 따라가 연 문서의 비율 | 0% | 12% | 0% | 0% |
| 절 간 읽기 겹침 | 남의 구역 알림 · 목차 분할 | 절끼리 읽은 문서 집합이 겹치는 정도(쌍별 자카드 평균, 낮을수록 잘 갈림) | 0.00 | 0.02 | 0.00 | — |
| 인용된 문서 수 | 원고 규칙 (리서처) | 최종 보고서에 인용된 서로 다른 문서 수 | 15 | 16 | 15 | 9 |
| 인용 밀도 | 원고 규칙 (리서처) | 본문 1,000자당 인용 표시 수 | 10.18 | 10.48 | 10.4 | 10.35 |
| 읽고 안 쓴 비율 | 예산 효율 | 읽었지만 어디에도 인용하지 않은 문서의 비율 | 0% | 0% | 0% | 0% |
| 연도 원문 일치율 | 원문 대조 (리서처 정확성) | 인용 붙은 문장의 연도 중 인용 문서 원문에 실제로 나오는 비율 | 94% | 100% | 90% | 100% |
| 코디네이터가 본 비율 | 격리 (분업 구조) | 코디네이터가 받은 글자 수 ÷ 자료 전체 글자 수 | 5.00% | 5.05% | 4.99% | 4.99% |
| 최대 에이전트가 본 비율 | 격리 (분업 구조) | 가장 많이 받은 에이전트의 글자 수 ÷ 자료 전체 글자 수 | 1.92% | 2.37% | 4.12% | 9.10% |
| 1차 부족 신고 | 점검·재파견 | 1차 원고에서 스스로 '부족'이라 신고한 절 수 | 0 | 0 | 0 | — |
| 재파견 후 해결 | 점검·재파견 | 재파견 뒤 '충분'으로 바뀐 절 수 | 0 | 0 | 0 | — |
| 목차 재작성 | 목차 검사 (코드) | 코디네이터 목차가 코드 검사에 걸려 다시 짠 횟수 | 0 | 0 | 0 | 0 |
| 제출 거절 | 원고 검사 (코드) | 인용 없음·안 읽은 문서 인용 등으로 코드가 제출을 돌려보낸 횟수 | 0 | 1 | 0 | 0 |

## 4. 절별로 누가 얼마나 읽고 썼나

### 기본 (모든 장치 ON)

| 절 | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 창립과 초기 역사 (기원·창업자·초기 철학) | 2/6회, 문서 2건 | 2 | sufficient | - |
| S2 방법론과 트레이닝 원리 | 3/6회, 문서 3건 | 3 | sufficient | - |
| S3 확산과 비즈니스 모델(계열화·라이선스·장비·브랜드) | 3/8회, 문서 3건 | 3 | sufficient | - |
| S4 CrossFit Games와 경쟁의 전개(대회사·확장) | 4/8회, 문서 4건 | 4 | sufficient | - |
| S5 비판·안전 문제·문화적 논쟁 | 3/6회, 문서 3건 | 3 | sufficient | - |

### 남의 구역 알림 OFF

| 절 | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 창립과 초기 역사 (기원·창업자·초기 철학) | 2/6회, 문서 2건 | 2 | sufficient | - |
| S2 방법론과 트레이닝 원리 | 5/6회, 문서 4건 | 4 | sufficient | - |
| S3 확산과 비즈니스 모델(계열화·라이선스·장비·브랜드) | 3/8회, 문서 3건 | 3 | sufficient | - |
| S4 CrossFit Games와 경쟁의 전개(대회사·확장) | 5/8회, 문서 5건 | 5 | sufficient | - |
| S5 비판·안전 문제·문화적 논쟁 | 3/6회, 문서 3건 | 3 | sufficient | - |

### 점검·재파견 OFF

| 절 | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 창립과 초기 역사 (기원·창업자·초기 철학) | 4/6회, 문서 2건 | 2 | sufficient | - |
| S2 방법론과 트레이닝 원리 | 4/6회, 문서 3건 | 3 | sufficient | - |
| S3 확산과 비즈니스 모델(계열화·라이선스·장비·브랜드) | 8/8회, 문서 3건 | 3 | sufficient | - |
| S4 CrossFit Games와 경쟁의 전개(대회사·확장) | 4/8회, 문서 4건 | 4 | sufficient | - |
| S5 비판·안전 문제·문화적 논쟁 | 3/6회, 문서 3건 | 3 | sufficient | - |

### 단일 에이전트 대조군

| 절 | 읽기 | 인용 문서 | 신고 흐름 | 두 번째 원고 처리 |
|---|---|---|---|---|
| S1 창립과 초기 역사 (기원·창업자·초기 철학) | (단일 에이전트가 함께 읽음) | 2 | sufficient | - |
| S2 방법론과 트레이닝 원리 | (단일 에이전트가 함께 읽음) | 4 | sufficient | - |
| S3 확산과 비즈니스 모델(계열화·라이선스·장비·브랜드) | (단일 에이전트가 함께 읽음) | 4 | sufficient | - |
| S4 CrossFit Games와 경쟁의 전개(대회사·확장) | (단일 에이전트가 함께 읽음) | 3 | sufficient | - |
| S5 비판·안전 문제·문화적 논쟁 | (단일 에이전트가 함께 읽음) | 3 | sufficient | - |

## 5. 인용 대조 표본 (원문과 직접 대조)

인용 붙은 문장마다 인용 문서에서 단서(연도·숫자·영문 고유명사)가 가장 많이 겹치는 대목을 찾아 붙였다.
읽은 문서를 엉뚱한 문장에 붙인 것은 코드가 못 잡는다. 아래에서 직접 판단해 [ ] 에 표시한다.

### 기본 (모든 장치 ON)

1. **문장**: 2019년에는 기존 리저널을 대체하는 ‘Sanctionals’와 오픈·초청 병행 방식으로 자격 제도가 재편되었고, 팀 구성 규정이 바뀌어 소속 체육관(affiliate) 기반의 어필리에이트컵을 폐지하는 등 참여 방식에 큰 변화가 있었다
   - 인용: `2019_crossfit_games` 2019 CrossFit Games · 단서: Sanctionals, affiliate, 2019
   - 원문 대목: …Toomey, and CrossFit Mayhem Freedom won the Team competition, all of whom also won the 2018 games. The 2019 Games operated under a new set of qualification rules this year, allowing athletes to qualify for the Games via three different methods: the Open, the Sanctionals and invitations, replacing the Regionals of previous seasons. It was also the first year to allow a team to be composed of members who did not share a gym affiliation, thereby removing the Affiliate Cup. This year the Games was not broadcast on ESPN or CBS,…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: 크로스핏 게임은 2007년 아로마스(Aromas)에 있는 개인 농장에서 ‘우드스톡 오브 피트니스’ 성격의 소규모 대회로 시작되었다. 초회에는 별도의 예선 없이 약 70명의 선수가 참가했으며 첫 이벤트는 창립자 그레그 글래스먼의 취지에 따라 당일 호퍼(무작위 추첨)로 결정되었다
   - 인용: `2007_crossfit_games` 2007 CrossFit Games · 단서: Aromas, 2007, 70
   - 원문 대목: The 2007 CrossFit Games were the inaugural CrossFit Games, which were held on June 30 and July 1, 2007, on a ranch in Aromas, California. There was no qualification process for the first Games, and around 70 athletes turned up to participate in the Games, along with around 150 spectators. There were three events, the first one selected at random on the day. The men's individual co…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: . 풀업·머슬업 등 체중을 이용한 운동(칼리스데닉스)은 상대적 근력과 체간 안정성 강화를 위해 사용되며
   - 인용: `high_intensity_interval_training` High-intensity interval training · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: . 또한 리복과 같은 대형 브랜드의 타이틀 스폰서십과 상금 확대는 대회의 상업적 매력과 미디어 노출을 증대시켰으며
   - 인용: `reebok` Reebok · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . 방법론적으로는 기능적 트레이닝 원리에 기반하여 HIIT·서킷 트레이닝 요소를 결합한 고강도·다변형의 워크아웃 체계가 특징이다
   - 인용: `high_intensity_interval_training` High-intensity interval training · 단서: HIIT
   - 원문 대목: High-intensity interval training (HIIT) is a training protocol alternating short periods of intense or explosive anaerobic exercise with brief recovery periods until the point of exhaustion. HIIT involves exercises performed in repeated quick bursts at maximum or near maximal effort with periods o…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

### 남의 구역 알림 OFF

1. **문장**: . 과도한 운동이 횡문근융해증을 촉발할 수 있다는 점에서 과훈련과 횡문근융해증은 연속선상에 놓인 위험으로 인식된다
   - 인용: `rhabdomyolysis` Rhabdomyolysis · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: . 2010년 대회는 처음으로 온라인 생중계되었고 우승자 상금이 스폰서 프로제넥스와 함께 개인별 $25,000로 증가했다
   - 인용: `2010_crossfit_games` 2010 CrossFit Games · 단서: 25,000, 25000, 2010
   - 원문 대목: …ndividual athletes are narrowed down to 50 men and 50 women for the finals at the Games. The number of scored events in the Games was increased to nine spread over three days of competition. With sponsorship from Progenex, each individual winner was awarded $25,000. The 2010 Games featured the debut of Rich Froning Jr., who would go on to win the Games the following four years. He had a lead going into the final event of the 2010 Games, but climbed the rope legless when he could use his legs to help with the climb, and…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: 크로스핏은 전 체육인 그레그 글래스먼(Greg Glassman)이 1996년경 '크로스-피트' 개념을 처음 고안한 데서 출발했다. 글래스먼은 16세 때 체조와 역도 요소를 결합한 최초의 유사 크로스핏 운동을 만들었고, 이는 이후 그의 대표적인 벤치마크 WOD인 'Fran'으로 알려진 프로그램의 기초가 되었다
   - 인용: `crossfit` CrossFit · 단서: Glassman, Fran, Greg, 1996, WOD, 16
   - 원문 대목: …abdomyolysis, a possible life-threatening condition also found in other sports, resulting from a breakdown of muscle from extreme exertion. == History == CrossFit, meaning cross-discipline fitness, was first conceived as a company in 1996 as Cross-Fit. Greg Glassman, a former gymnast, created his first CrossFit-style workout when he was 16 by combining elements of gymnastics with weightlifting. The workout he created, called Fran, added thrusters (a combination of front squat and push press) to pull-ups. Greg Glassman an…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: , 지역(Regionals)의 체계는 2019년 지역 예선 대신 전 세계에서 각기 운영되는 ‘샌셔널스(Sanctionals)’로 전환되며 자격 방식이 재편되었다
   - 인용: `2019_crossfit_games` 2019 CrossFit Games · 단서: Sanctionals, Regionals, 2019
   - 원문 대목: …Toomey, and CrossFit Mayhem Freedom won the Team competition, all of whom also won the 2018 games. The 2019 Games operated under a new set of qualification rules this year, allowing athletes to qualify for the Games via three different methods: the Open, the Sanctionals and invitations, replacing the Regionals of previous seasons. It was also the first year to allow a team to be composed of members who did not share a gym affiliation, thereby removing the Affiliate Cup. This year the Games was not broadcast on ESPN or CBS,…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: 대표적 동작으로 버피는 전신의 심폐·근지구력을 동시에 자극하는 토탈 바디 동작으로 WOD에서 메타콘 요소로 쓰인다.
   - 인용: `circuit_training` Circuit training · 단서: WOD
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

### 점검·재파견 OFF

1. **문장**: . 또한 참가자 수가 급증함에 따라 2019년 대회에서는 초반 여러 차례에 걸친 선수 컷(cut) 제도를 도입해 중도 탈락으로 최종 선수층을 압축하는 방식으로 경기 운영을 바꾸었다(초반 75→50명 등, 최종 10명까지 축소)
   - 인용: `2019_crossfit_games` 2019 CrossFit Games · 단서: 2019, cut, 50, 75, 10
   - 원문 대목: …paigns. == Individual == Following the qualification procedure, there were 148 men and 134 women that had qualified for the CrossFit Games in the Individual competition (143 men and 117 women turned up at the Games). In the previous 4 Games, no athletes were cut during the competition; this year due to the significantly higher number of participants, the Games implemented cuts after each of the first 6 events. The field was cut to 75 competitors after the first event, and 50 competitors after the second. 10 athletes…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: 크로스핏 게임은 2007년 아로마스(Aromas)의 한 농장(ranch)에서 ‘피트니스의 우드스톡’ 콘셉트로 시작되어 창립자들이 현장추첨(hopper)을 통해 즉석으로 워크아웃을 내는 등 소규모 축제형 대회로 운영되었다
   - 인용: `2007_crossfit_games` 2007 CrossFit Games · 단서: Aromas, hopper, ranch, 2007
   - 원문 대목: The 2007 CrossFit Games were the inaugural CrossFit Games, which were held on June 30 and July 1, 2007, on a ranch in Aromas, California. There was no qualification process for the first Games, and around 70 athletes turned up to participate in the Games, along with around 150 spectators. There were three events, the first one selected at random on the day. The men's individual co…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: 대표적 동작은 문서들에서 직접 언급된 예로 버피가 있으며(전신 동작·심폐·근지구력 동시 자극) 서킷·HIIT 문맥에서 핵심 훈련 요소로 사용된다
   - 인용: `circuit_training` Circuit training · 단서: HIIT
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: 이들 흐름은 가맹·라이선스 수수료, 대회 스폰서십·중계권, 신발·장비·용품 판매, 선수·이벤트 스폰서십 등 다각적 수익 구조를 만들며 크로스핏 생태계의 상업화를 촉진했다
   - 인용: `reebok` Reebok · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . 상업적으로는 지역별 affiliate 네트워크와 CrossFit Games, 그리고 리복·Rogue와 같은 기업 제휴를 통해 생태계가 확장되었다
   - 인용: `reebok` Reebok · 단서: affiliate, CrossFit, Games, Rogue
   - 원문 대목: …the highest-paid hockey equipment endorser at the time. CCM became Reebok-CCM Hockey in 2007. Reebok moved most of its hockey equipment lines to CCM after 2015. === 2010s === In 2010, under the ownership of Adidas, Reebok announced a 10-year partnership with CrossFit, becoming the official footwear and apparel provider of the CrossFit Games. In 2011, Reebok launched the Nano, the first shoe specifically designed for CrossFit, developed with input from CrossFit athletes to support high-impact movements, weightlifting, and…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

### 단일 에이전트 대조군

1. **문장**: 장소와 포맷은 성장 과정에서 여러 차례 변화했다. 2010년에는 카슨(Carson, 캘리포니아)의 홈디포 센터로 옮겨 대회 규모를 확장했고, 2017년부터는 매디슨(위스콘신)의 얼리언트 에너지 센터로 이전해 6년간 개최했다가 2024년 포트워스의 Dickies Arena, 2025년 올버니로 재배치되는 등 개최지가 이동했다
   - 인용: `crossfit_games` CrossFit Games · 단서: Dickies, Carson, Arena, 2024, 2017, 2010
   - 원문 대목: …articipants and spectators, but the CrossFit Games rapidly grew, and within a few years, the competition was moved to larger venues at the Home Depot Center in Carson, California, followed by the Alliant Energy Center in Madison, Wisconsin. It was held in the Dickies Arena in Fort Worth, Texas in 2024. The Games were sponsored by Reebok from 2011 to 2020, and by Nobull from 2021 to 2023. The CrossFit Games season consists of four stages; the first qualification stage, the Open, is billed as the largest participatory sport…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

2. **문장**: 요약하면, 크로스핏은 그레그 글래스먼이 체조·역도 요소를 결합한 훈련에서 기원하여 CrossFit, Inc. 설립과 온라인 WOD 게시를 통해 확산되었다
   - 인용: `crossfit` CrossFit · 단서: CrossFit, WOD, Inc
   - 원문 대목: …order to perform certain movements such as pull-up faster, "kipping" that relies on the momentum of the kip to move faster may be employed, although its use for these purposes is considered controversial to non-practitioners of CrossFit. === Gym classes === CrossFit-affiliated gyms, or "boxes", have considerable freedom in how their classes are organized; therefore, there can be significant differences in their classes. In general, classes last an hour and typically include a warm-up, a 10–30-minute WOD, and a cool-down/…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

3. **문장**: 훈련 강도·구성 측면에서 크로스핏은 고강도 인터벌 트레이닝(HIIT)과 유사한 간헐적 고강도 구간을 빈번히 활용하며, HIIT의 ‘짧고 강렬한 운동과 짧은 회복’이라는 특징이 크로스핏 WOD의 시간·강도 설계에 반영된다
   - 인용: `crossfit` CrossFit · 단서: HIIT, WOD
   - 원문 대목: …0 affiliated gyms in over 150 countries as of 2025, about 40% of which are located in the United States. CrossFit is promoted as both a physical exercise philosophy and a competitive fitness sport, incorporating elements from high-intensity interval training (HIIT), Olympic weightlifting, plyometrics, powerlifting, gymnastics, kettlebell lifting, calisthenics, strongman, and other exercises. CrossFit presents its training program as one that can best prepare its trainees for any physical contingency, preparing them for…
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

4. **문장**: . 결론적으로 횡문근융해증 등 특정 심각한 부작용 사례는 보고되어 왔고, 일반적인 부상률·건강 효과에 대해서는 연구별로 결론이 엇갈리므로 상황별 위험요인(운동 강도·환경·개인적 질환 등)을 고려한 지도와 단계적 적응이 중요하다
   - 인용: `crossfit` CrossFit · 단서: 없음
   - 원문 대목: (자동으로 찾을 단서가 없음 — 문서를 직접 열어 확인)
   - 판단: [ ] 제자리  [ ] 엉뚱한 문장  [ ] 원문에 없음

5. **문장**: . 사업적으로는 가맹 제도·교육·대회·제품 파이프라인을 결합한 생태계를 형성했고, Reebok·Rogue 등 파트너십이 산업적 확장에 기여했다
   - 인용: `reebok` Reebok · 단서: Reebok, Rogue
   - 원문 대목: Reebok International Limited ( REE-bok) is an American apparel, accessories and sports equipment brand that is a part of Authentic Brands Group. Since its acquisition by Authentic in 2022, Reebok has re-entered performance sport and meaningfully expanded its Classi…
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
