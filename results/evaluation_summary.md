# Priced Deferral — benchmark summary

## clinic/cases.json (n=60, calibration error 0.076)

| policy | total cost | error rate (answered) | defer rate | gather rate |
|---|---|---|---|---|
| priced | 303536.30 | 0.182 | 0.817 | 0.183 |
| always_answer | 1400000.00 | 0.233 | 0.000 | 0.000 |
| fixed_threshold_062 | 900420.00 | 0.167 | 0.100 | 0.000 |
| oracle | 980.00 | 0.000 | 0.233 | 0.000 |

- Priced saving vs always-answer: 78.3%
- Priced saving vs fixed threshold (0.62): 66.3%
- Priced regret vs oracle: 30873.1%
- Verdict agreement with oracle: 0.350
- Packet: sufficient 0.633, mean 3.5 items, compression 0.64

## clinic/hand_cases.json (n=12, calibration error 0.296)

| policy | total cost | error rate (answered) | defer rate | gather rate |
|---|---|---|---|---|
| priced | 100961.00 | 0.000 | 0.667 | 0.167 |
| always_answer | 600000.00 | 0.500 | 0.000 | 0.000 |
| fixed_threshold_062 | 300350.00 | 0.286 | 0.417 | 0.000 |
| oracle | 100420.00 | 0.000 | 0.500 | 0.000 |

- Priced saving vs always-answer: 83.2%
- Priced saving vs fixed threshold (0.62): 66.4%
- Priced regret vs oracle: 0.5%
- Verdict agreement with oracle: 0.833
- Packet: sufficient 0.750, mean 4.0 items, compression 0.97

## ops/cases.json (n=60, calibration error 0.076)

| policy | total cost | error rate (answered) | defer rate | gather rate |
|---|---|---|---|---|
| priced | 436.20 | 0.136 | 0.267 | 0.250 |
| always_answer | 700.00 | 0.233 | 0.000 | 0.000 |
| fixed_threshold_062 | 492.00 | 0.167 | 0.100 | 0.000 |
| oracle | 98.00 | 0.000 | 0.233 | 0.000 |

- Priced saving vs always-answer: 37.7%
- Priced saving vs fixed threshold (0.62): 11.3%
- Priced regret vs oracle: 345.1%
- Verdict agreement with oracle: 0.767
- Packet: sufficient 0.812, mean 3.5 items, compression 0.67

## ops/hand_cases.json (n=12, calibration error 0.296)

| policy | total cost | error rate (answered) | defer rate | gather rate |
|---|---|---|---|---|
| priced | 93.50 | 0.000 | 0.500 | 0.167 |
| always_answer | 300.00 | 0.500 | 0.000 | 0.000 |
| fixed_threshold_062 | 185.00 | 0.286 | 0.417 | 0.000 |
| oracle | 92.00 | 0.000 | 0.500 | 0.000 |

- Priced saving vs always-answer: 68.8%
- Priced saving vs fixed threshold (0.62): 49.5%
- Priced regret vs oracle: 1.6%
- Verdict agreement with oracle: 1.000
- Packet: sufficient 0.667, mean 4.0 items, compression 0.97

## research/cases.json (n=60, calibration error 0.076)

| policy | total cost | error rate (answered) | defer rate | gather rate |
|---|---|---|---|---|
| priced | 2231.35 | 0.097 | 0.483 | 0.483 |
| always_answer | 7000.00 | 0.233 | 0.000 | 0.000 |
| fixed_threshold_062 | 4620.00 | 0.167 | 0.100 | 0.000 |
| oracle | 280.00 | 0.000 | 0.233 | 0.000 |

- Priced saving vs always-answer: 68.1%
- Priced saving vs fixed threshold (0.62): 51.7%
- Priced regret vs oracle: 696.9%
- Verdict agreement with oracle: 0.650
- Packet: sufficient 0.655, mean 3.5 items, compression 0.63

## research/hand_cases.json (n=12, calibration error 0.296)

| policy | total cost | error rate (answered) | defer rate | gather rate |
|---|---|---|---|---|
| priced | 661.00 | 0.000 | 0.667 | 0.083 |
| always_answer | 3000.00 | 0.500 | 0.000 | 0.000 |
| fixed_threshold_062 | 1600.00 | 0.286 | 0.417 | 0.000 |
| oracle | 620.00 | 0.000 | 0.500 | 0.000 |

- Priced saving vs always-answer: 78.0%
- Priced saving vs fixed threshold (0.62): 58.7%
- Priced regret vs oracle: 6.6%
- Verdict agreement with oracle: 0.833
- Packet: sufficient 0.750, mean 4.0 items, compression 0.97
