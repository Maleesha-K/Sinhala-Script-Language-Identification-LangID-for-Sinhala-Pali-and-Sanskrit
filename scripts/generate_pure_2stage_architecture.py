import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import os

def create_pure_two_stage(dark_mode=False, output_path='figures/two_stage_architecture_only.png'):
    os.makedirs('figures', exist_ok=True)
    
    mpl.rcParams['font.sans-serif'] = ['Segoe UI', 'Nirmala UI', 'Arial', 'DejaVu Sans']
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'

    if dark_mode:
        bg_color = '#0B0F19'
        card_bg = '#111827'
        card_sub = '#1F2937'
        text_title = '#F9FAFB'
        text_body = '#E5E7EB'
        text_muted = '#9CA3AF'
        border_col = '#374151'
        col_blue = '#38BDF8'
        col_purple = '#A855F7'
        col_green = '#22C55E'
        col_amber = '#F59E0B'
        col_red = '#EF4444'
        arrow_col = '#60A5FA'
    else:
        bg_color = '#FFFFFF'
        card_bg = '#F8FAFC'
        card_sub = '#F1F5F9'
        text_title = '#0F172A'
        text_body = '#1E293B'
        text_muted = '#64748B'
        border_col = '#CBD5E1'
        col_blue = '#0284C7'
        col_purple = '#9333EA'
        col_green = '#16A34A'
        col_amber = '#D97706'
        col_red = '#DC2626'
        arrow_col = '#2563EB'

    fig, ax = plt.subplots(figsize=(16, 9), dpi=300)
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9)
    ax.axis('off')

    def draw_box(x, y, w, h, bg, border, lw=1.5, rad=0.2):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad={rad},rounding_size=0.15",
            facecolor=bg, edgecolor=border, linewidth=lw, zorder=2
        )
        ax.add_patch(box)
        return box

    # Header Title
    ax.text(8.0, 8.45, "Two-Stage Specialist Routing Architecture", 
            ha='center', va='center', fontsize=19, weight='bold', color=text_title)
    ax.text(8.0, 8.08, "Mitigating Catastrophic Forgetting in Massive Multilingual Language Identification", 
            ha='center', va='center', fontsize=11.5, color=text_muted, style='italic')

    # ========================================================
    # 1. INPUT QUERY (x in [0.7, 3.5])
    # ========================================================
    draw_box(0.7, 4.3, 2.8, 2.9, card_bg, border_col, lw=1.5)
    ax.text(2.1, 6.75, "Input Query (x)", ha='center', va='center', fontsize=12.5, weight='bold', color=col_blue)
    ax.text(2.1, 6.35, "Raw Multilingual Text Stream", ha='center', va='center', fontsize=9.5, color=text_muted)
    
    draw_box(0.9, 4.6, 2.4, 1.4, card_sub, border_col, lw=0.8, rad=0.08)
    ax.text(2.1, 5.65, "English (eng), Tamil (tam),", ha='center', va='center', fontsize=8.5, color=text_body)
    ax.text(2.1, 5.35, "Hindi (hin), Arabic (ara),", ha='center', va='center', fontsize=8.5, color=text_body)
    ax.text(2.1, 5.05, "Sinhala, Pali, Sanskrit...", ha='center', va='center', fontsize=8.5, weight='bold', color=col_purple)

    # Arrow: Input -> Stage 1
    ax.annotate('', xy=(4.4, 5.75), xytext=(3.6, 5.75),
                arrowprops=dict(facecolor=arrow_col, edgecolor=arrow_col, width=2.8, headwidth=9, shrink=0.05))
    ax.text(4.0, 6.1, "Text\nStream", ha='center', va='bottom', fontsize=8.5, color=text_muted, weight='bold')

    # ========================================================
    # 2. STAGE 1: FROZEN GLOBAL ROUTER (x in [4.5, 8.7])
    # ========================================================
    draw_box(4.5, 4.1, 4.2, 3.1, card_bg, col_blue, lw=2.0)
    
    # Stage 1 Badge
    draw_box(4.8, 6.8, 3.6, 0.46, col_blue, col_blue, rad=0.08)
    ax.text(6.6, 7.03, "STAGE 1: FROZEN GLOBAL ROUTER", ha='center', va='center', fontsize=9.5, weight='bold', color='#FFFFFF')
    
    ax.text(6.6, 6.38, "Pretrained Foundation Backbone", ha='center', va='center', fontsize=10.5, weight='bold', color=text_title)
    ax.text(6.6, 6.08, "fastText LID-176 / OpenLID-v2 / NLLB-218", ha='center', va='center', fontsize=8.5, color=text_muted)
    
    # Frozen condition badge
    draw_box(4.9, 5.35, 3.4, 0.45, card_sub, col_green, lw=1.2, rad=0.08)
    ax.text(6.6, 5.58, r"Weights Frozen:  $\Delta\theta_{\mathrm{global}} = 0$", ha='center', va='center', fontsize=9, weight='bold', color=col_green)
    
    # Routing gate
    draw_box(4.9, 4.35, 3.4, 0.75, card_sub, col_amber, lw=1.2, rad=0.08)
    ax.text(6.6, 4.85, "ROUTING GATE: Script Detection", ha='center', va='center', fontsize=8.2, weight='bold', color=col_amber)
    ax.text(6.6, 4.55, r"Is Predicted Script $\in \{ \mathrm{sin}, \mathrm{sin\_Sinh} \}$ ?", ha='center', va='center', fontsize=8.8, weight='bold', color=text_title)

    # BRANCH A (Downward): Non-Sinhala -> Direct Global Output
    ax.annotate('', xy=(6.6, 2.75), xytext=(6.6, 4.05),
                arrowprops=dict(facecolor=col_green, edgecolor=col_green, width=2.8, headwidth=9, shrink=0.05))
    ax.text(6.75, 3.45, "NO: Non-Sinhala Script\n(eng, tam, hin, deu, fra...)", ha='left', va='center', fontsize=8.5, weight='bold', color=col_green)

    draw_box(4.1, 1.05, 5.0, 1.6, card_bg, col_green, lw=1.8)
    ax.text(6.6, 2.25, "Direct Global Language Output", ha='center', va='center', fontsize=11, weight='bold', color=col_green)
    ax.text(6.6, 1.90, "English, Tamil, Hindi, Arabic, German, French...", ha='center', va='center', fontsize=8.5, color=text_body)
    
    draw_box(4.4, 1.25, 4.4, 0.42, col_green, col_green, rad=0.08)
    ax.text(6.6, 1.46, "0.0% Degradation Guarantee  |  Zero Forgetting", ha='center', va='center', fontsize=8.3, weight='bold', color='#FFFFFF')

    # BRANCH B (Right): Sinhala Script Detected -> Stage 2
    ax.annotate('', xy=(10.5, 5.75), xytext=(8.8, 5.75),
                arrowprops=dict(facecolor=col_purple, edgecolor=col_purple, width=3.0, headwidth=10, shrink=0.05))
    ax.text(9.65, 6.35, "YES: Sinhala Script\n('sin' / 'sin_Sinh')", ha='center', va='center', fontsize=8.8, weight='bold', color=col_purple)
    ax.text(9.65, 5.3, "Diverted to\nSpecialist", ha='center', va='center', fontsize=8.0, color=text_muted, style='italic')

    # ========================================================
    # 3. STAGE 2: SPECIALIST MODEL (x in [10.6, 15.0])
    # ========================================================
    draw_box(10.6, 4.1, 4.4, 3.1, card_bg, col_purple, lw=2.0)
    
    # Stage 2 Badge
    draw_box(11.0, 6.8, 3.6, 0.46, col_purple, col_purple, rad=0.08)
    ax.text(12.8, 7.03, "STAGE 2: SPECIALIST DISAMBIGUATOR", ha='center', va='center', fontsize=9.5, weight='bold', color='#FFFFFF')
    
    ax.text(12.8, 6.38, r"Isolated Specialist Head ($\theta_{\mathrm{spec}}$)", ha='center', va='center', fontsize=10.5, weight='bold', color=text_title)
    ax.text(12.8, 6.08, "Trained on Tri-Language Intra-Script Split (N=60,285)", ha='center', va='center', fontsize=8.2, color=text_muted)

    draw_box(11.0, 5.0, 3.6, 0.85, card_sub, border_col, lw=0.8, rad=0.06)
    ax.text(12.8, 5.55, "Morphosyntactic N-gram & Subword Model", ha='center', va='center', fontsize=8.5, weight='bold', color=col_purple)
    ax.text(12.8, 5.25, "Diagnostic Affixes (-ssa, -mha), Conjuncts (ksetra), Low Vowels (ae)", ha='center', va='center', fontsize=7.6, color=text_body)

    draw_box(11.0, 4.3, 3.6, 0.5, card_sub, col_purple, lw=1.0, rad=0.06)
    ax.text(12.8, 4.55, r"Quarantined Parameters:  $\theta_{\mathrm{spec}}$ never alters $\theta_{\mathrm{global}}$", ha='center', va='center', fontsize=8.2, weight='bold', color=col_purple)

    # Connectors from Stage 2 to Final 3 Targets (Downwards)
    ax.annotate('', xy=(11.27, 2.7), xytext=(12.0, 4.05),
                arrowprops=dict(facecolor=col_blue, edgecolor=col_blue, width=2.2, headwidth=8, shrink=0.05))
    ax.annotate('', xy=(12.8, 2.7), xytext=(12.8, 4.05),
                arrowprops=dict(facecolor=col_amber, edgecolor=col_amber, width=2.2, headwidth=8, shrink=0.05))
    ax.annotate('', xy=(14.32, 2.7), xytext=(13.6, 4.05),
                arrowprops=dict(facecolor=col_red, edgecolor=col_red, width=2.2, headwidth=8, shrink=0.05))

    # ========================================================
    # 4. THREE TARGET CLASSES (Below Stage 2)
    # ========================================================
    # Sinhala
    draw_box(10.6, 1.05, 1.35, 1.6, card_bg, col_blue, lw=1.6, rad=0.1)
    ax.text(11.27, 2.25, "Sinhala", ha='center', va='center', fontsize=10.5, weight='bold', color=col_blue)
    ax.text(11.27, 1.88, "Sinh-Sinh", ha='center', va='center', fontsize=8.5, color=text_muted)
    ax.text(11.27, 1.46, "0.967 F1", ha='center', va='center', fontsize=9.2, weight='bold', color=col_green)

    # Pali
    draw_box(12.12, 1.05, 1.35, 1.6, card_bg, col_amber, lw=1.6, rad=0.1)
    ax.text(12.8, 2.25, "Pali", ha='center', va='center', fontsize=10.5, weight='bold', color=col_amber)
    ax.text(12.8, 1.88, "Pali-Sinh", ha='center', va='center', fontsize=8.5, color=text_muted)
    ax.text(12.8, 1.46, "0.974 F1", ha='center', va='center', fontsize=9.2, weight='bold', color=col_green)

    # Sanskrit
    draw_box(13.65, 1.05, 1.35, 1.6, card_bg, col_red, lw=1.6, rad=0.1)
    ax.text(14.32, 2.25, "Sanskrit", ha='center', va='center', fontsize=10.5, weight='bold', color=col_red)
    ax.text(14.32, 1.88, "San-Sinh", ha='center', va='center', fontsize=8.5, color=text_muted)
    ax.text(14.32, 1.46, "0.970 F1", ha='center', va='center', fontsize=9.2, weight='bold', color=col_green)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=bg_color)
    plt.close()
    print(f"Saved: {output_path}")

if __name__ == '__main__':
    create_pure_two_stage(dark_mode=False, output_path='figures/two_stage_architecture_only.png')
    create_pure_two_stage(dark_mode=True, output_path='figures/two_stage_architecture_only_dark.png')
