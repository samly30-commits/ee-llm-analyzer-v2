import io
import numpy as np
import pandas as pd
import scipy.fft as fft
from scipy.signal import windows


def parse_oscilloscope_csv(file_buffer):
    """계측기 메타데이터(상단 텍스트)를 자동 스킵하고 수치 데이터만 정밀 파싱합니다."""
    if isinstance(file_buffer, str):
        with open(file_buffer, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    else:
        content = file_buffer.getvalue().decode("utf-8", errors="ignore")
        lines = content.splitlines()

    header_idx = 0
    for idx, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in ["time", "sec", "volt", "v("]):
            header_idx = idx
            break

    clean_csv = "\n".join(lines[header_idx:])
    df = pd.read_csv(io.StringIO(clean_csv))
    df.columns = [col.strip() for col in df.columns]
    df = df.dropna().reset_index(drop=True)
    return df


def calculate_electrical_metrics(df):
    """전압 및 선택적 전류 데이터를 기반으로 핵심 전기적 파라미터와 전력 손실을 계산합니다."""
    volt_cols = [c for c in df.columns if "volt" in c.lower() or "v(" in c.lower()]
    curr_cols = [c for c in df.columns if "curr" in c.lower() or "i(" in c.lower()]

    if not volt_cols:
        raise ValueError("전압(Voltage) 데이터 열을 찾을 수 없습니다.")

    v = df[volt_cols[0]].values
    v_max = np.max(v)
    v_min = np.min(v)
    v_pp = v_max - v_min
    v_rms = np.sqrt(np.mean(v**2))
    v_dc = np.mean(v)
    ripple_factor = ((v_pp / 2) / abs(v_dc) * 100) if abs(v_dc) > 1e-6 else 0.0

    metrics = {
        "Vpp": v_pp,
        "Vrms": v_rms,
        "Vdc": v_dc,
        "RippleFactor": ripple_factor,
        "HasCurrent": False,
        "Pavg": 0.0,
        "Irms": 0.0,
    }

    if curr_cols:
        i = df[curr_cols[0]].values
        p_inst = v * i
        metrics["HasCurrent"] = True
        metrics["Irms"] = np.sqrt(np.mean(i**2))
        metrics["Pavg"] = np.mean(p_inst)

    return metrics


def analyze_frequency_domain(times, voltages):
    """해닝 윈도우(Hanning Window)를 적용한 정밀 FFT 및 THD(총고조파왜곡) 산출."""
    n = len(voltages)
    dt = np.mean(np.diff(times))

    v_detrend = voltages - np.mean(voltages)
    win = windows.hann(n)
    v_windowed = v_detrend * win

    fft_values = fft.fft(v_windowed)
    fft_frequencies = fft.fftfreq(n, d=dt)

    half_n = n // 2
    freqs = fft_frequencies[:half_n]
    mags = (np.abs(fft_values[:half_n]) * 2 / n) * 2.0

    valid_idx = np.where(freqs > 0)[0]
    if len(valid_idx) > 0:
        fund_idx = valid_idx[np.argmax(mags[valid_idx])]
        fund_freq = freqs[fund_idx]
        fund_mag = mags[fund_idx]

        harmonic_sq_sum = 0.0
        for h in range(2, 6):
            target_f = fund_freq * h
            if target_f < freqs[-1]:
                h_idx = np.argmin(np.abs(freqs - target_f))
                harmonic_sq_sum += mags[h_idx] ** 2

        thd = (np.sqrt(harmonic_sq_sum) / fund_mag * 100) if fund_mag > 0 else 0.0
    else:
        fund_freq, thd = 0.0, 0.0

    return freqs, mags, fund_freq, thd
