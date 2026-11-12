import numpy as np
from src.analyzer import analyze_frequency_domain
from src.bom_verifier import expand_refdes_string, parse_gerber_bom_text


def test_fft_frequency_accuracy():
    """10kHz 정현파 입력 시 FFT 피크 주파수가 오차 1% 이내로 검출되는지 검증."""
    fs = 100000
    t = np.arange(0, 0.01, 1 / fs)
    v = 5.0 * np.sin(2 * np.pi * 10000 * t)

    freqs, mags, fund_freq, _ = analyze_frequency_domain(t, v)
    assert abs(fund_freq - 10000) < 100


def test_refdes_range_expansion():
    """R1-R5 콤팩트 문자열이 정확히 5개 배열로 전개되는지 검증."""
    result = expand_refdes_string("R1-R5, C1, U10")
    assert result == ["C1", "R1", "R2", "R3", "R4", "R5", "U10"]


def test_gerber_footprint_parsing():
    """부품 번호와 패키지 규격이 결합된 문자열 파싱 정확도 검증."""
    parsed = parse_gerber_bom_text("R1:0603, C2:0805")
    assert parsed["R1"] == "0603"
    assert parsed["C2"] == "0805"
