import matplotlib.pyplot as plt
import koreanize_matplotlib

# --- 🎨 색상 팔레트 (Color Palette) ---
PRIMARY_COLOR = "#4C78A8"       # 차분한 파란색 (메인)
# SECONDARY_COLOR = "#F58518"     # 안전한 주황색 (보조)
SECONDARY_COLOR = "#5FAAE6"     # 안전한 주황색 (보조)
NAVY_ACCENT_COLOR =  "#2F31A8" 
ACCENT_COLOR_1 = "#54A24B"      # 녹색 (강조 1)
ACCENT_COLOR_2 = "#E45756"      # 붉은색 (강조 2)
NEUTRAL_COLOR = "#727272"       # 중간 회색 (중립/텍스트)
BACKGROUND_COLOR = "#FFFFFF"    # 흰색 배경
TEXT_COLOR = "#333333"          # 어두운 회색 텍스트

HIGHLIGHT_COLOR = "skyblue"
DIVERGING_PALETTE = "coolwarm"
SEQUENTIAL_PALETTE = "Blues"
CATEGORICAL_PALETTE = "viridis"

# --- ✍️ 폰트 속성 (Font Properties) ---
TITLE_FONT = {'size': 16, 'weight': 'bold', 'color': TEXT_COLOR}
LABEL_FONT = {'size': 12, 'weight': 'normal'}
TICK_FONT_SIZE = 10

def apply_common_style(fig, ax, title=""):
    """Matplotlib Figure와 Axis에 공통 스타일을 적용합니다."""
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)

    # 제목 설정
    ax.set_title(title, fontdict=TITLE_FONT, pad=20)

    # 축 레이블 폰트 설정
    ax.xaxis.label.set_fontproperties(LABEL_FONT)
    ax.yaxis.label.set_fontproperties(LABEL_FONT)
    ax.xaxis.label.set_color(NEUTRAL_COLOR)
    ax.yaxis.label.set_color(NEUTRAL_COLOR)
    # 축 틱(tick) 색상 및 크기 설정
    ax.tick_params(axis='x', colors=NEUTRAL_COLOR, labelsize=TICK_FONT_SIZE)
    ax.tick_params(axis='y', colors=NEUTRAL_COLOR, labelsize=TICK_FONT_SIZE)

    # 축 선(spine) 색상 설정
    for spine in ax.spines.values():
        spine.set_edgecolor(NEUTRAL_COLOR)
    
    # 그리드 추가 (선택 사항)
    # ax.grid(axis='y', linestyle='--', alpha=0.6, color=NEUTRAL_COLOR)