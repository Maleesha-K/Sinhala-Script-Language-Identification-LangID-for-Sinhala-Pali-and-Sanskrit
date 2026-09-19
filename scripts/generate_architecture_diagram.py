import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib as mpl
import os

def create_architecture_diagram(dark_mode=False, output_path='figures/two_stage_routing_architecture.png'):
    os.makedirs('figures', exist_ok=True)
    
    # Configure font fallback: Segoe UI handles latin & symbols, Nirmala UI handles Indic scripts
    mpl.rcParams['font.sans-serif'] = ['Segoe UI', 'Nirmala UI', 'Arial', 'DejaVu Sans']
    mpl.rcParams['font.family'] = 'sans-serif'
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'
    
    # Palette definition
    if dark_mode:
        bg_color = '#0B0F19'
        card_bg = '#111827'
        card_sub_bg = '#1F2937'
        text_title = '#FFFFFF'
        text_body = '#E5E7EB'
        text_muted = '#9CA3AF'
        border_color = '#374151'
        accent_blue = '#38BDF8'
        accent_purple = '#A855F7'
        accent_green = '#22C55E'
        accent_amber = '#F59E0B'
        accent_red = '#EF4444'
        arrow_color = '#60A5FA'
    else:
        bg_color = '#FFFFFF'
        card_bg = '#F8FAFC'
        card_sub_bg = '#F1F5F9'
        text_title = '#0F172A'
        text_body = '#1E293B'
        text_muted = '#64748B'
        border_color = '#CBD5E1'
        accent_blue = '#0284C7'
        accent_purple = '#9333EA'
        accent_green = '#16A34A'
        accent_amber = '#D97706'
        accent_red = '#DC2626'
        arrow_color = '#2563EB'

    fig, ax = plt.subplots(figsize=(19, 11), dpi=300)
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 19)
    ax.set_ylim(0, 11)
    ax.axis('off')

    def draw_card(x, y, w, h, bg, border, lw=1.5, radius=0.22):
        box = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad={radius},rounding_size=0.18",
            facecolor=bg, edgecolor=border, linewidth=lw, zorder=2
        )
        ax.add_patch(box)
        return box

    # Title & Header
    ax.text(9.5, 10.4, "Two-Stage Specialist Routing: Catastrophic Forgetting Mitigation", 
            ha='center', va='center', fontsize=21, weight='bold', color=text_title)
    ax.text(9.5, 10.0, "Decoupling Planetary Multilingual Classification from Fine-Grained Intra-Script Morphosyntactic Disambiguation", 
            ha='center', va='center', fontsize=12, color=text_muted, style='italic')

    # ==========================================
    # 1. INPUT STREAM (Col 1: x in [0.5, 3.2])
    # ==========================================
    draw_card(0.5, 4.0, 2.7, 5.2, card_bg, border_color)
    ax.text(1.85, 8.85, "Input Text Stream (x)", ha='center', va='center', fontsize=12.5, weight='bold', color=accent_blue)
    ax.text(1.85, 8.52, "Raw Multilingual Text Corpus", ha='center', va='center', fontsize=9.5, color=text_muted)
    
    examples = [
        ("English (Latn)", '"Natural language query"', accent_blue),
        ("Tamil (Taml)", '"iyarkai mozhi aayvu"', accent_blue),
        ("Hindi (Deva)", '"prakrtik bhasa sansadhan"', accent_blue),
        ("Sinhala (Sinh)", '"api sinhalen kiyavamu"', accent_purple),
        ("Pali (Sinh)", '"evam me sutam ekam samayam"', accent_purple),
        ("Sanskrit (Sinh)", '"dharma-ksetre kuru-ksetre"', accent_purple),
        ("Global Web (170+)", '"Arabic, French, German..."', text_muted),
    ]
    y_pos = 7.85
    for lang, sample, col in examples:
        draw_card(0.7, y_pos - 0.28, 2.3, 0.45, card_sub_bg, border_color, lw=0.8, radius=0.08)
        ax.text(0.85, y_pos - 0.05, lang, fontsize=8.5, weight='bold', color=col, va='center')
        ax.text(0.85, y_pos - 0.25, sample, fontsize=7.5, color=text_body, va='center')
        y_pos -= 0.62

    # Arrow from Input to Stage 1
    ax.annotate('', xy=(4.0, 6.6), xytext=(3.3, 6.6),
                arrowprops=dict(facecolor=arrow_color, edgecolor=arrow_color, width=3, headwidth=10, shrink=0.05))
    ax.text(3.65, 6.95, "Text\nStream", ha='center', va='bottom', fontsize=8.5, color=text_muted, weight='bold')

    # ==========================================
    # 2. STAGE 1: GLOBAL ROUTER (Col 2: x in [4.1, 7.9])
    # ==========================================
    draw_card(4.1, 4.2, 3.8, 5.0, card_bg, accent_blue, lw=2.0)
    
    # Header badge
    draw_card(4.4, 8.6, 3.2, 0.48, accent_blue, accent_blue, radius=0.1)
    ax.text(6.0, 8.84, "STAGE 1: FROZEN GLOBAL ROUTER", ha='center', va='center', fontsize=10, weight='bold', color='#FFFFFF')
    
    ax.text(6.0, 8.18, "Pretrained Planetary-Scale Backbone", ha='center', va='center', fontsize=10.5, weight='bold', color=text_title)
    ax.text(6.0, 7.88, "fastText LID-176 / OpenLID-v2 / NLLB-218", ha='center', va='center', fontsize=8.5, color=text_muted)
    
    # Internal router architecture representation
    draw_card(4.4, 5.95, 3.2, 1.6, card_sub_bg, border_color, lw=1.0)
    ax.text(6.0, 7.25, "Global Manifold: 176 - 201 Languages", ha='center', va='center', fontsize=9.5, weight='bold', color=accent_blue)
    ax.text(6.0, 6.9, "Dense Character & Subword Projections", ha='center', va='center', fontsize=8.5, color=text_body)
    
    # Frozen parameter badge
    draw_card(4.7, 6.15, 2.6, 0.45, card_bg, accent_green, lw=1.2, radius=0.08)
    ax.text(6.0, 6.37, r"Weights Frozen:  $\Delta\theta_{\mathrm{global}} = 0$", ha='center', va='center', fontsize=9, weight='bold', color=accent_green)

    # Decision router logic box
    draw_card(4.4, 4.45, 3.2, 1.25, card_sub_bg, accent_amber, lw=1.5)
    ax.text(6.0, 5.35, "ROUTING DECISION GATE", ha='center', va='center', fontsize=8.5, weight='bold', color=accent_amber)
    ax.text(6.0, 4.98, r"Is Predicted Script $\in \{ \mathrm{sin}, \mathrm{sin\_Sinh} \}$ ?", ha='center', va='center', fontsize=9.2, weight='bold', color=text_title)
    ax.text(6.0, 4.65, "Fast Unicode block filter & script identification", ha='center', va='center', fontsize=7.8, color=text_muted)

    # ==========================================
    # BRANCH A: NON-SINHALA DIRECT OUTPUT (Downward)
    # ==========================================
    ax.annotate('', xy=(6.0, 2.95), xytext=(6.0, 4.35),
                arrowprops=dict(facecolor=accent_green, edgecolor=accent_green, width=3, headwidth=10, shrink=0.05))
    ax.text(6.15, 3.65, "NO: Non-Sinhala Script\n(e.g., eng, tam, hin, deu, fra...)", ha='left', va='center', fontsize=8.5, weight='bold', color=accent_green)

    draw_card(3.8, 1.1, 4.8, 1.6, card_bg, accent_green, lw=1.8)
    ax.text(6.2, 2.38, "Direct Global Language Output", ha='center', va='center', fontsize=11, weight='bold', color=accent_green)
    ax.text(6.2, 2.05, "English (eng), Tamil (tam), Hindi (hin), Arabic (ara), German (deu), French (fra)...", ha='center', va='center', fontsize=8.5, color=text_body)
    
    draw_card(4.1, 1.3, 4.2, 0.45, accent_green, accent_green, radius=0.08)
    ax.text(6.2, 1.52, "0.0% Degradation Guarantee  |  Zero Catastrophic Forgetting", ha='center', va='center', fontsize=8.8, weight='bold', color='#FFFFFF')

    # ==========================================
    # BRANCH B: SINHALA DETECTED -> STAGE 2
    # ==========================================
    # Arrow to Stage 2 with ample space
    ax.annotate('', xy=(10.2, 6.6), xytext=(8.0, 6.6),
                arrowprops=dict(facecolor=accent_purple, edgecolor=accent_purple, width=3.5, headwidth=11, shrink=0.05))
    ax.text(9.1, 7.3, "YES: Sinhala Script Detected\n('sin' / 'sin_Sinh')", ha='center', va='center', fontsize=9.2, weight='bold', color=accent_purple)
    ax.text(9.1, 6.15, "Diverted to\nSpecialist Head", ha='center', va='center', fontsize=8.2, color=text_muted, style='italic')

    # ==========================================
    # 3. STAGE 2: SPECIALIST MODEL (Col 3: x in [10.3, 14.3])
    # ==========================================
    draw_card(10.3, 4.2, 4.0, 5.0, card_bg, accent_purple, lw=2.0)
    
    draw_card(10.6, 8.6, 3.4, 0.48, accent_purple, accent_purple, radius=0.1)
    ax.text(12.3, 8.84, "STAGE 2: SPECIALIST DISAMBIGUATOR", ha='center', va='center', fontsize=9.5, weight='bold', color='#FFFFFF')
    
    ax.text(12.3, 8.18, r"Isolated Specialist Head ($\theta_{\mathrm{spec}}$)", ha='center', va='center', fontsize=10.5, weight='bold', color=text_title)
    ax.text(12.3, 7.88, "Trained on Curated Intra-Script Corpus (N=60,285)", ha='center', va='center', fontsize=8.5, color=text_muted)

    draw_card(10.6, 5.95, 3.4, 1.6, card_sub_bg, border_color, lw=1.0)
    ax.text(12.3, 7.25, "Morphosyntactic Feature Extraction", ha='center', va='center', fontsize=9.5, weight='bold', color=accent_purple)
    ax.text(12.3, 6.9, r"• Char N-grams ($n \in [2, 5]$) & Subword Vectors", ha='center', va='center', fontsize=8.3, color=text_body)
    ax.text(12.3, 6.6, "• Middle Indo-Aryan Inflectional Affixes (-ssa, -mha)", ha='center', va='center', fontsize=8.3, color=text_body)
    ax.text(12.3, 6.3, "• Distinctive Conjuncts (ksetra) & Low Vowels (ae, aee)", ha='center', va='center', fontsize=8.3, color=text_body)

    draw_card(10.6, 4.45, 3.4, 1.25, card_sub_bg, accent_purple, lw=1.2)
    ax.text(12.3, 5.35, "QUARANTINED ADAPTATION SPACE", ha='center', va='center', fontsize=8.8, weight='bold', color=accent_purple)
    ax.text(12.3, 4.95, r"Specialist parameters $\theta_{\mathrm{spec}}$ are strictly isolated.", ha='center', va='center', fontsize=8.2, color=text_body)
    ax.text(12.3, 4.68, r"Zero gradient feedback to $\theta_{\mathrm{global}}$ prevents forgetting.", ha='center', va='center', fontsize=8.0, color=text_muted)

    # ==========================================
    # 4. FINAL TARGET OUTPUTS (Col 4: x in [15.2, 18.2])
    # ==========================================
    ax.annotate('', xy=(15.2, 8.1), xytext=(14.4, 7.0),
                arrowprops=dict(facecolor=accent_blue, edgecolor=accent_blue, width=2.5, headwidth=9, shrink=0.05))
    ax.annotate('', xy=(15.2, 6.6), xytext=(14.4, 6.6),
                arrowprops=dict(facecolor=accent_amber, edgecolor=accent_amber, width=2.5, headwidth=9, shrink=0.05))
    ax.annotate('', xy=(15.2, 5.1), xytext=(14.4, 6.2),
                arrowprops=dict(facecolor=accent_red, edgecolor=accent_red, width=2.5, headwidth=9, shrink=0.05))

    # Sinhala Card
    draw_card(15.2, 7.5, 3.1, 1.2, card_bg, accent_blue, lw=1.6)
    ax.text(16.75, 8.35, "Sinhala (Sinh-Sinh)", ha='center', va='center', fontsize=10, weight='bold', color=accent_blue)
    ax.text(16.75, 8.0, "Modern colloquial & journalistic text", ha='center', va='center', fontsize=8.2, color=text_muted)
    ax.text(16.75, 7.7, "Macro-F1: 0.961 - 0.997", ha='center', va='center', fontsize=8.8, weight='bold', color=accent_green)

    # Pali Card
    draw_card(15.2, 6.0, 3.1, 1.2, card_bg, accent_amber, lw=1.6)
    ax.text(16.75, 6.85, "Pali (Pali-Sinh)", ha='center', va='center', fontsize=10, weight='bold', color=accent_amber)
    ax.text(16.75, 6.5, "Tipitaka canonical liturgical texts", ha='center', va='center', fontsize=8.2, color=text_muted)
    ax.text(16.75, 6.2, "Macro-F1: 0.953 - 0.996 (from 0.0%)", ha='center', va='center', fontsize=8.8, weight='bold', color=accent_green)

    # Sanskrit Card
    draw_card(15.2, 4.5, 3.1, 1.2, card_bg, accent_red, lw=1.6)
    ax.text(16.75, 5.35, "Sanskrit (San-Sinh)", ha='center', va='center', fontsize=10, weight='bold', color=accent_red)
    ax.text(16.75, 5.0, "Classical scholastic literature (Aksharamukha)", ha='center', va='center', fontsize=8.0, color=text_muted)
    ax.text(16.75, 4.7, "Macro-F1: 0.905 - 0.997 (from 0.0%)", ha='center', va='center', fontsize=8.8, weight='bold', color=accent_green)

    # ==========================================
    # 5. BOTTOM SUMMARY COMPARISON PANEL (x in [9.2, 18.3])
    # ==========================================
    draw_card(9.2, 1.0, 9.1, 2.7, card_bg, border_color, lw=1.3)
    ax.text(13.75, 3.35, "Catastrophic Forgetting Mitigation Comparison", ha='center', va='center', fontsize=11.5, weight='bold', color=text_title)
    
    # Box 1: Naive Fine-Tuning
    draw_card(9.5, 1.25, 4.1, 1.8, card_sub_bg, accent_red, lw=1.3)
    ax.text(11.55, 2.75, "[Baseline] Naive End-to-End Fine-Tuning", ha='center', va='center', fontsize=8.8, weight='bold', color=accent_red)
    ax.text(11.55, 2.4, r"• Updates shared parameters: $\Delta\theta_{\mathrm{global}} \neq 0$", ha='center', va='center', fontsize=8.0, color=text_body)
    ax.text(11.55, 2.15, "• Target languages overfit rapidly on small corpus", ha='center', va='center', fontsize=8.0, color=text_body)
    ax.text(11.55, 1.9, "• Pretrained representations for 200+ languages collapse", ha='center', va='center', fontsize=8.0, color=accent_red)
    ax.text(11.55, 1.55, "Global Background F1: ~0.24 (Severe Degradation)", ha='center', va='center', fontsize=8.2, weight='bold', color=accent_red)

    # Box 2: Two-Stage Specialist Routing
    draw_card(13.9, 1.25, 4.1, 1.8, card_sub_bg, accent_green, lw=1.3)
    ax.text(15.95, 2.75, "[Proposed] Two-Stage Specialist Routing", ha='center', va='center', fontsize=8.8, weight='bold', color=accent_green)
    ax.text(15.95, 2.4, r"• Global weights strictly frozen: $\Delta\theta_{\mathrm{global}} \equiv 0$", ha='center', va='center', fontsize=8.0, color=text_body)
    ax.text(15.95, 2.15, "• Quarantined parameter space for intra-script specialist", ha='center', va='center', fontsize=8.0, color=text_body)
    ax.text(15.95, 1.9, "• Eliminates Orthographic Fallacy without side effects", ha='center', va='center', fontsize=8.0, color=accent_green)
    ax.text(15.95, 1.55, "Global Background F1: 0.9745 (0.0% Loss Guarantee!)", ha='center', va='center', fontsize=8.2, weight='bold', color=accent_green)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor=bg_color)
    plt.close()
    print(f"Saved: {output_path}")

if __name__ == '__main__':
    create_architecture_diagram(dark_mode=False, output_path='figures/two_stage_routing_architecture.png')
    create_architecture_diagram(dark_mode=True, output_path='figures/two_stage_routing_dark.png')
