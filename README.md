<img width="900" height="300" alt="시연영상 (2)+00-00-00 000-00-03-02 160" src="https://github.com/user-attachments/assets/6b0a3e85-373b-4946-a602-35a0c20ebefb" />

# ee-llm-analyzer-v2
# ⚡ LLM 기반 전기·전자 엔지니어링 통합 분석 및 검증 대시보드 (EE Engineering Automation Suite)

> **다중 채널 파형 신호처리(FFT / THD / 전력손실) 및 PCB Gerber-BOM 이중 정합성 자동 검증 툴킷**  
> **과목명:** 인공지능특론세미나 프로젝트 과제 | **제출자:** 2025300309 이정후 | **개발 환경:** Python 3.13, Streamlit, SciPy, Pandas, Plotly

---

## 📌 1. 프로젝트 개요 및 기획 의도

현업 전기·전자 회로 설계 및 계측(Oscilloscope / LTspice) 공정에서 발생하는 반복적인 데이터 후처리와 휴먼 에러를 해결하기 위해 구축된 엔지니어링 자동화 대시보드입니다.

* **계측 파형 자동 분석:** 오실로스코프·LTspice CSV 파일의 상단 메타데이터를 자동 스킵하고, 다중 채널(전압·전류) 선택을 통해 `Vpp`, `Vrms`, `Ripple(%)`, `Hanning Window FFT`, `THD(총고조파왜곡)`, `평균 전력 손실(Pavg)`을 즉시 산출합니다.
* **Gerber-BOM 이중 교차 검증:** PCB 발주 전 Gerber Pick-and-Place 좌표 텍스트와 구매용 Excel BOM(`.xlsx`)을 대조하여 **BOM 누락 부품**, **미배치 초과 부품**, **패키지 규격(Footprint) 불일치**를 자동 탐지합니다.
* **직관적인 무상태(Stateless) UI/UX:** `st.segmented_control` 기반 데이터 소스 전환, 시간 도메인 차트 내 전류 파형 보조 Y축 오버레이, Python IDLE 실행 시 자동 Streamlit 서버 구동 래퍼를 지원합니다.

---

## 📂 2. 저장소 디렉토리 구조 (Repository Structure)

```text
ee-llm-analyzer_2/
├── src/
│   ├── analyzer_2.py                   # 메타데이터 스킵, Hanning FFT, THD 및 전력 손실 연산 엔진
│   ├── bom_verifier_2.py               # 비정형 RefDes 확장(R1-R5) 및 Footprint 이중 검증 엔진
│   └── app_2.py                        # Streamlit + Plotly 통합 대시보드 UI 및 상태 제어
├── data/                               # 실무 회로 시나리오별 테스트 데이터셋 (총 10종)
│   ├── sample_oscilloscope.csv         # 기본 단일 채널 파형 (5kHz 기본파 + 15kHz 고조파)
│   ├── multichannel_buck_converter.csv # 5채널 벅 컨버터 파형 (Vin, Vout, Vsw, IL, Iload)
│   ├── three_phase_inverter_waveform.csv # 60Hz 3상 인버터 A·B·C상 전압/전류 (6채널)
│   ├── switching_ripple_noise_100khz.csv # 100kHz 고속 스위칭 리플 및 1MHz 링잉 노이즈 파형
│   ├── noisy_vs_filtered_signal.csv    # 센서 노이즈 포함 원본 vs 필터링 비교 파형 (4채널)
│   ├── sample_bom.xlsx                 # 기본 표준 Excel BOM 샘플
│   ├── bom_verification_test_case.xlsx # 누락·초과·패키지 불일치 오류 탐지 검증용 BOM
│   ├── power_supply_buck_bom.xlsx      # DC-DC 벅 컨버터 전원 회로용 BOM
│   ├── bldc_motor_driver_bom.xlsx      # 3상 BLDC 모터 드라이버 보드용 BOM
│   └── iot_sensor_node_bom.xlsx        # ESP32 기반 IoT 센서 노드 보드용 BOM
├── tests/
│   └── test_core.py                    # PyTest 기반 주파수 정확도 및 파싱 단위 테스트
├── docs/
│   └── ee_llm_analyzer_presentation_v2.pptx # 최종 프로젝트 발표 자료
├── prompts/
│   └── prompt_history.md               # LLM 디버깅 및 프롬프트 엔지니어링 이력
├── requirements.txt                    # 필수 Python 패키지 목록
└── README.md                           # 프로젝트 개요 및 실행 가이드 (본 문서)
```

---

## 🚀 3. 설치 및 실행 방법 (Quick Start)

### 3.1 필수 라이브러리 설치
Python 3.10 이상(권장: **Python 3.13**) 환경에서 아래 명령어로 필요한 패키지를 설치합니다.

```bash
pip install streamlit numpy pandas scipy plotly openpyxl pytest
```
*(또는 `requirements.txt`가 있는 경우 `pip install -r requirements.txt` 실행)*

### 3.2 대시보드 실행
터미널(CMD / PowerShell)에서 `src` 폴더로 이동한 뒤 Streamlit 명령어로 실행합니다.

```bash
cd src
streamlit run app_2.py
```
> **💡 Tip:** `app_2.py` 상단에는 자동 실행 래퍼(`subprocess`)가 내장되어 있어, Python IDLE(`F5`)이나 일반 터미널(`python app_2.py`)로 실행하더라도 자동으로 로컬 웹 서버(`http://localhost:8501`)가 구동됩니다.

---

## 🖥️ 4. 주요 기능 상세 가이드

### 📊 Tab 1: 다중 채널 파형 신호처리 및 전력 분석기
1. **데이터 입력 모드 선택 (`st.segmented_control`):**
   * **`📂 CSV 파일 업로드`:** 계측기 또는 LTspice에서 추출한 `.csv` 파일을 업로드하여 분석합니다.
   * **`🧪 다중 채널 샘플 테스트`:** 별도 파일 없이 내장된 4채널 가상 파형(`CH1: 5kHz`, `CH2: 10kHz` 전압 및 전류)을 즉시 로드하여 테스트합니다.
2. **채널 선택 및 전류 오버레이:**
   * 다중 채널 파일에서 분석할 **전압(Voltage)**과 **전류(Current)** 채널을 드롭다운으로 각각 선택할 수 있습니다.
   * **시간 차트에 전류 파형 겹치기** 토글을 활성화하면 보조 Y축(Secondary Y-axis)으로 전류 파형이 동시에 표시되어 위상차를 직관적으로 확인할 수 있습니다.
3. **핵심 지표 및 스펙트럼 산출:**
   * **Vpp, Vrms, 리플율(%), 기본 주파수(f0), THD(%)**가 카드 형태로 자동 계산되며, 전류 채널 선택 시 **실효 전류(Irms)**와 **평균 전력 손실(Pavg)**이 자동 산출됩니다.

### 🔍 Tab 2: PCB Gerber-BOM 정합성 정밀 검증기
1. **Gerber Pick-and-Place 텍스트 입력:**
   * `R1:0603, R2:0603` 형태의 패키지 매핑 표기와 `R4-R5` 같은 하이픈 범위 표기법을 동시에 인식합니다.
2. **Excel BOM 업로드 및 스캐닝:**
   * 구매팀 제출용 `.xlsx` 파일을 업로드한 후 **`🔍 정합성 정밀 스캐닝 실행`** 버튼을 클릭합니다.
   * **테스트 팁:** 기본 입력된 Gerber 텍스트 상태에서 `data/bom_verification_test_case.xlsx`를 업로드하면 **BOM 누락 부품(4건), 미배치 초과 부품(1건), 패키지 규격 불일치(2건)** 탐지 결과를 즉시 확인할 수 있습니다.

---

## 🛠️ 5. 주요 트러블슈팅 및 엔지니어링 개선 이력

* **FFT 주파수 축 스케일 왜곡 해결 (`analyzer_2.py`):** 타임스탬프 인접 차이 평균(`dt = np.mean(np.diff(times))`)을 동적으로 계산해 `fftfreq(n, d=dt)`에 바인딩하고, DC 성분 제거 및 Hanning Window를 적용하여 스펙트럼 누설을 방지했습니다.
* **비정형 압축 문자열 확장 (`bom_verifier_2.py`):** 정규표현식 그룹 캡처(`r"\b([A-Z]+)(\d+)\s*-\s*([A-Z]+)?(\d+)\b"`)를 적용해 `R1-R5` 표기를 개별 부품 리스트로 100% 복원했습니다.
* **UI 상태 관리 및 DOM 충돌 방지 (`app_2.py`):** 토글 버튼 간 `st.session_state` 꼬임과 React `removeChild` DOM 충돌을 해결하기 위해 `st.segmented_control` 기반 무상태 분기 구조와 단일 `st.info` 컨테이너를 적용했습니다.

