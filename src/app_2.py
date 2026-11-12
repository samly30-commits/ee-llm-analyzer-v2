import os, sys, subprocess
if __name__ == "__main__":
    if "streamlit" not in sys.modules or not os.environ.get("STREAMLIT_RUN"):
        os.environ["STREAMLIT_RUN"] = "1"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
        sys.exit()

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from analyzer_2 import analyze_frequency_domain, calculate_electrical_metrics, parse_oscilloscope_csv
from bom_verifier_2 import verify_design_integrity

# 페이지 기본 설정
st.set_page_config(
    page_title="EE Engineering Automation Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 브라우저 자동 번역 차단 및 상단 여백·카드 스타일 커스텀 CSS
st.markdown("""
<meta name="google" content="notranslate">
<style>
    .block-container {
        padding-top: 3.8rem;
        padding-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem;
        color: #475569;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.55rem;
        color: #0f172a;
        font-weight: 700;
    }
    .header-badge {
        display: inline-block;
        padding: 4px 12px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #1d4ed8;
        background-color: #dbeafe;
        border-radius: 999px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# 상단 헤더 영역
st.markdown('<span class="header-badge" translate="no">Python 3.13 • SciPy • Pandas • Plotly</span>', unsafe_allow_html=True)
st.title("⚡ LLM 기반 전기·전자 엔지니어링 통합 분석 및 검증 대시보드")
st.caption("다중 채널 파형 신호처리(FFT / THD / 전력손실) 및 PCB Gerber-BOM 이중 정합성 자동 검증 툴킷")

tab1, tab2 = st.tabs(["📊 1. 파형 신호처리 및 전력 분석기", "🔍 2. Gerber-BOM 정합성 정밀 검증기"])

# ==============================================================================
# TAB 1: 다중 채널 파형 신호처리 및 전력 분석기
# ==============================================================================
with tab1:
    with st.container(border=True):
        col_mode, col_desc = st.columns([1.2, 2.3])
        with col_mode:
            st.markdown("**1️⃣ 데이터 입력 모드 선택**")
            try:
                input_mode = st.segmented_control(
                    "데이터 소스",
                    options=["📂 CSV 파일 업로드", "🧪 다중 채널 샘플 테스트"],
                    default="📂 CSV 파일 업로드",
                    label_visibility="collapsed"
                )
            except AttributeError:
                input_mode = st.radio(
                    "데이터 소스",
                    ["📂 CSV 파일 업로드", "🧪 다중 채널 샘플 테스트"],
                    horizontal=True,
                    label_visibility="collapsed"
                )

        if input_mode is None:
            input_mode = "📂 CSV 파일 업로드"

        with col_desc:
            if input_mode == "📂 CSV 파일 업로드":
                desc_text = "💡 오실로스코프(Tektronix, Keysight) 또는 LTspice에서 추출한 다중 채널 <b>.csv</b> 파형 파일을 업로드하세요."
            else:
                desc_text = "🧪 <b>다중 채널 샘플 모드 활성:</b> 벅 컨버터(5kHz) 및 스위칭 리플(10kHz)이 포함된 4채널 가상 파형이 로드되었습니다."

            st.markdown(
                f'<div translate="no" style="background-color:#eff6ff; border-left:4px solid #3b82f6; padding:12px 16px; border-radius:6px; color:#1e3a8a; font-size:0.92rem; margin-top:4px;">{desc_text}</div>',
                unsafe_allow_html=True
            )

        df_wave = None
        if input_mode == "📂 CSV 파일 업로드":
            uploaded_csv = st.file_uploader(
                "파형 CSV 파일 선택 (Time, Voltage, [선택] Current 열 자동 감지)",
                type=["csv"],
                label_visibility="collapsed"
            )
            if uploaded_csv is not None:
                df_wave = parse_oscilloscope_csv(uploaded_csv)

        elif input_mode == "🧪 다중 채널 샘플 테스트":
            t = np.linspace(0, 0.002, 2000)
            v1 = 12.0 + 4.0 * np.sin(2 * np.pi * 5000 * t) + 0.6 * np.sin(2 * np.pi * 15000 * t)
            v2 = 5.0 + 1.2 * np.sin(2 * np.pi * 10000 * t) + 0.3 * np.sin(2 * np.pi * 30000 * t)
            i1 = 1.5 + 0.5 * np.sin(2 * np.pi * 5000 * t - np.pi / 6)
            i2 = 0.8 + 0.2 * np.sin(2 * np.pi * 10000 * t - np.pi / 4)
            df_wave = pd.DataFrame({
                "Time(s)": t,
                "Voltage_CH1(V)": v1,
                "Voltage_CH2(V)": v2,
                "Current_CH1(A)": i1,
                "Current_CH2(A)": i2
            })

    # 데이터가 준비된 경우에만 분석 대시보드 렌더링
    if df_wave is not None:
        time_cols = [c for c in df_wave.columns if "time" in c.lower()]
        volt_cols = [c for c in df_wave.columns if any(k in c.lower() for k in ["volt", "v(", "v_", "vin", "vout", "vsw"])]
        curr_cols = [c for c in df_wave.columns if any(k in c.lower() for k in ["curr", "i(", "i_"])]

        if not volt_cols:
            volt_cols = [c for c in df_wave.columns if c not in time_cols and c not in curr_cols]

        with st.container(border=True):
            st.markdown("**2️⃣ 분석 채널 및 차트 옵션 설정**")
            c1, c2, c3 = st.columns([1.2, 1.2, 1.0])
            with c1:
                selected_volt = st.selectbox("전압(Voltage) 채널 선택", volt_cols)
            with c2:
                selected_curr = st.selectbox("전류(Current) 채널 선택 (전력 손실 연산용)", ["없음"] + curr_cols)
            with c3:
                st.write("")
                st.write("")
                overlay_curr = st.toggle("시간 차트에 전류 파형 겹치기", value=(selected_curr != "없음"), disabled=(selected_curr == "없음"))

        df_selected = pd.DataFrame()
        df_selected["Time(s)"] = df_wave[time_cols[0]]
        df_selected["Voltage(V)"] = df_wave[selected_volt]
        if selected_curr != "없음":
            df_selected["Current(A)"] = df_wave[selected_curr]

        metrics = calculate_electrical_metrics(df_selected)
        freqs, mags, fund_freq, thd = analyze_frequency_domain(df_selected["Time(s)"].values, df_selected["Voltage(V)"].values)

        # 핵심 전기적 파라미터 카드 그리드
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Vpp (첨두간 전압)", f"{metrics['Vpp']:.3f} V")
        m2.metric("Vrms (실효 전압)", f"{metrics['Vrms']:.3f} V")
        m3.metric("리플율 (Ripple)", f"{metrics['RippleFactor']:.2f} %")
        m4.metric("기본 주파수 (f0)", f"{fund_freq:,.1f} Hz")
        m5.metric("총고조파왜곡 (THD)", f"{thd:.2f} %")

        if metrics["HasCurrent"] and selected_curr != "없음":
            st.markdown(
                f'<div translate="no" style="background-color:#f0fdf4; border-left:4px solid #16a34a; padding:12px 16px; border-radius:6px; color:#14532d; font-size:0.95rem; margin:10px 0;">⚡ <b>전력 손실 자동 연산 ({selected_volt} × {selected_curr}):</b> 실효 전류(Irms) = <code>{metrics["Irms"]:.3f} A</code> &nbsp;|&nbsp; 평균 전력 손실(Pavg) = <code>{metrics["Pavg"]:.3f} W</code></div>',
                unsafe_allow_html=True
            )

        # 듀얼 인터랙티브 차트 영역
        g1, g2 = st.columns(2)
        with g1:
            with st.container(border=True):
                fig_time = make_subplots(specs=[[{"secondary_y": True}]])
                fig_time.add_trace(
                    go.Scatter(x=df_selected["Time(s)"] * 1000, y=df_selected["Voltage(V)"], mode="lines", name=selected_volt, line=dict(color="#2563eb", width=2)),
                    secondary_y=False
                )
                if overlay_curr and selected_curr != "없음":
                    fig_time.add_trace(
                        go.Scatter(x=df_selected["Time(s)"] * 1000, y=df_selected["Current(A)"], mode="lines", name=selected_curr, line=dict(color="#10b981", width=1.8, dash="dot")),
                        secondary_y=True
                    )
                    fig_time.update_yaxes(title_text="Current (A)", secondary_y=True, showgrid=False)

                fig_time.update_layout(
                    title=f"📈 시간 도메인 파형 ({selected_volt})",
                    xaxis_title="Time (ms)",
                    yaxis_title="Voltage (V)",
                    template="plotly_white",
                    height=370,
                    margin=dict(l=20, r=20, t=45, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_time, use_container_width=True)

        with g2:
            with st.container(border=True):
                mask = freqs <= (fund_freq * 6 if fund_freq > 0 else 50000)
                fig_fft = go.Figure()
                fig_fft.add_trace(
                    go.Scatter(x=freqs[mask], y=mags[mask], mode="lines", fill="tozeroy", name="FFT Magnitude", line=dict(color="#dc2626", width=2), fillcolor="rgba(220, 38, 38, 0.15)")
                )
                fig_fft.update_layout(
                    title=f"📊 주파수 스펙트럼 (Hanning FFT - {selected_volt})",
                    xaxis_title="Frequency (Hz)",
                    yaxis_title="Amplitude (V)",
                    template="plotly_white",
                    height=370,
                    margin=dict(l=20, r=20, t=45, b=20)
                )
                st.plotly_chart(fig_fft, use_container_width=True)

        with st.expander("📋 원본 파형 수치 데이터 미리보기 (상위 100행)"):
            st.dataframe(df_wave.head(100), use_container_width=True)

# ==============================================================================
# TAB 2: Gerber-BOM 정합성 정밀 검증기
# ==============================================================================
with tab2:
    with st.container(border=True):
        st.subheader("PCB Gerber 좌표 데이터 vs 구매용 BOM 이중 교차 검증")
        st.caption("부품 부호(`RefDes`) 누락 및 초과뿐만 아니라, `R1:0603` 형식으로 입력 시 **패키지(Footprint) 규격 불일치**까지 자동 탐지합니다.")

        c_left, c_right = st.columns(2)
        with c_left:
            default_gerber = "R1:0603, R2:0603, R3:0805\nR4-R5\nC1:0603, C2:0805, U1:LQFP48, L1:1210"
            gerber_text = st.text_area("1️⃣ Gerber Pick-and-Place 추출 텍스트 입력", value=default_gerber, height=160)
        with c_right:
            uploaded_bom = st.file_uploader("2️⃣ 구매팀 제출용 Excel BOM 업로드 (.xlsx)", type=["xlsx"])
            st.markdown(
                '<div translate="no" style="background-color:#eff6ff; border-left:4px solid #3b82f6; padding:10px 14px; border-radius:6px; color:#1e3a8a; font-size:0.88rem;">💡 <code>data/bom_verification_test_case.xlsx</code> 파일을 올리면 누락·초과·패키지 불일치 오류 탐지를 즉시 테스트할 수 있습니다.</div>',
                unsafe_allow_html=True
            )

        scan_btn = st.button("🔍 정합성 정밀 스캐닝 실행", type="primary", use_container_width=True)

    if scan_btn:
        if not uploaded_bom:
            st.warning("⚠️ 먼저 Excel BOM(`.xlsx`) 파일을 업로드해 주세요.")
        else:
            res = verify_design_integrity(gerber_text, uploaded_bom)
            if "error" in res:
                st.error(res["error"])
            else:
                s1, s2, s3 = st.columns(3)
                s1.metric("Gerber 총 부품 수", f"{res['total_gerber']} 개")
                s2.metric("BOM 총 부품 수", f"{res['total_bom']} 개")
                total_errors = len(res["missing_in_bom"]) + len(res["extra_in_bom"]) + len(res["pkg_mismatches"])
                s3.metric(
                    "탐지된 설계 오류",
                    f"{total_errors} 건",
                    delta="이상 없음 (Perfect)" if total_errors == 0 else f"-{total_errors} Errors 감지",
                    delta_color="normal" if total_errors == 0 else "inverse"
                )

                st.markdown("---")
                r1, r2, r3 = st.columns(3)
                with r1:
                    with st.container(border=True):
                        st.error(f"🚨 BOM 누락 부품 ({len(res['missing_in_bom'])}건)")
                        if res["missing_in_bom"]:
                            st.dataframe(pd.DataFrame(res["missing_in_bom"], columns=["누락 RefDes"]), use_container_width=True, hide_index=True)
                        else:
                            st.caption("누락된 부품이 없습니다.")
                with r2:
                    with st.container(border=True):
                        st.warning(f"⚠️ 미배치 초과 부품 ({len(res['extra_in_bom'])}건)")
                        if res["extra_in_bom"]:
                            st.dataframe(pd.DataFrame(res["extra_in_bom"], columns=["초과 RefDes"]), use_container_width=True, hide_index=True)
                        else:
                            st.caption("초과 발주된 부품이 없습니다.")
                with r3:
                    with st.container(border=True):
                        st.info(f"📐 패키지 규격 불일치 ({len(res['pkg_mismatches'])}건)")
                        if res["pkg_mismatches"]:
                            st.dataframe(pd.DataFrame(res["pkg_mismatches"]), use_container_width=True, hide_index=True)
                        else:
                            st.caption("패키지 규격이 모두 일치합니다.")
