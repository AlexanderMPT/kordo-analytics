import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import warnings
import os

warnings.filterwarnings('ignore')
os.makedirs('images', exist_ok=True)

# ===================== НАСТРОЙКА СТИЛЯ =====================
plt.rcParams.update({
    'figure.facecolor': '#0F1F3D',
    'axes.facecolor': '#0F1F3D',
    'axes.edgecolor': '#4A6080',
    'text.color': '#FFFFFF',
    'xtick.color': '#CCCCCC',
    'ytick.color': '#CCCCCC',
    'axes.labelcolor': '#CCCCCC',
    'axes.titlecolor': '#FFFFFF',
    'grid.color': '#1E3A5F',
    'grid.linestyle': '--',
    'grid.alpha': 0.5,
})
ACCENT = '#0A7EA4'
ACCENT2 = '#F4A233'

# ===================== ЗАГРУЗКА ДАННЫХ =====================
FILE = 'data/metrics.xlsx'
visits = pd.read_excel(FILE, sheet_name='visits_daily')
conv = pd.read_excel(FILE, sheet_name='conversions_daily')
sources = pd.read_excel(FILE, sheet_name='sources_summary')
age = pd.read_excel(FILE, sheet_name='age_summary')
gender = pd.read_excel(FILE, sheet_name='gender_summary')
weekday = pd.read_excel(FILE, sheet_name='visits_by_weekday')
popular = pd.read_excel(FILE, sheet_name='popular_total')

# Удаляем итоговые строки
def drop_totals(df, col):
    return df[df[col].astype(str) != 'Итого и средние'].reset_index(drop=True)

sources = drop_totals(sources, 'Источник трафика')
age = drop_totals(age, 'Возраст')
gender = drop_totals(gender, 'Пол')
weekday = drop_totals(weekday, 'День недели визита')
popular = drop_totals(popular, 'Адрес страницы')

visits['Период'] = pd.to_datetime(visits['Период'])
conv['Период'] = pd.to_datetime(conv['Период'])

print("Данные загружены")

# ===================== БЛОК ФОРМУЛ (как в formulas_practice) =====================
# 1) Дней >10 визитов
days_gt_10 = (visits['Визиты'] > 10).sum()
# 2) Дней с нулём
days_zero = (visits['Визиты'] == 0).sum()
# 3) Дней с ненулевой конверсией
days_nonzero_conv = (conv['ЦелевыеВизиты'] > 0).sum()
# 4) Сумма визитов после 21 марта
after_21 = visits.loc[visits['Период'] >= '2026-03-21', 'Визиты'].sum()
# 5) Сумма визитов до 21 марта
before_21 = visits.loc[visits['Период'] < '2026-03-21', 'Визиты'].sum()
# 6) Прямые заходы
direct_visits = sources.loc[sources['Источник трафика'] == 'Прямые заходы', 'Визиты'].values[0]
# 7) Средний отказ прямых заходов
direct_bounce = sources.loc[sources['Источник трафика'] == 'Прямые заходы', 'Отказы'].values[0]
# 8) Среднее визитов в апреле
april_avg = visits.loc[visits['Период'].dt.month == 4, 'Визиты'].mean()
# 9) Визиты за конкретную неделю (12-ю)
visits['week'] = visits['Период'].dt.isocalendar().week
week_12_visits = visits[visits['week'] == 12]['Визиты'].sum()
# 10) Дней с визитами от 5 до 15
days_5_15 = ((visits['Визиты'] >= 5) & (visits['Визиты'] <= 15)).sum()

print(f"Дней >10 визитов: {days_gt_10}")
print(f"Дней с нулём: {days_zero}")
print(f"Дней с конверсией: {days_nonzero_conv}")
print(f"Визитов после 21 марта: {after_21}")
print(f"Визитов до 21 марта: {before_21}")
print(f"Прямые заходы: {direct_visits}")
print(f"Отказы прямых: {direct_bounce:.3f}")
print(f"Среднее в апреле: {april_avg:.2f}")
print(f"Визиты за 12-ю неделю: {week_12_visits}")
print(f"Дней 5-15 визитов: {days_5_15}")

# Дополнительные расчёты KPI
total_visits = visits['Визиты'].sum()
total_conv = conv['ЦелевыеВизиты'].sum()
conv_rate = (total_conv / total_visits * 100) if total_visits > 0 else 0
top_source = sources.loc[sources['Визиты'].idxmax(), 'Источник трафика']

# ===================== ГРАФИК 1: Динамика визитов и конверсий =====================
fig, ax1 = plt.subplots(figsize=(14, 5))
ax1.plot(visits['Период'], visits['Визиты'], color=ACCENT, marker='o', markersize=3, label='Визиты')
ax1.set_ylabel('Визиты', color=ACCENT)
ax1.tick_params(axis='y', labelcolor=ACCENT)
ax1.yaxis.grid(True)

ax2 = ax1.twinx()
ax2.plot(conv['Период'], conv['ЦелевыеВизиты'], color=ACCENT2, linestyle='--', marker='s', markersize=4, label='Конверсии')
ax2.set_ylabel('Целевые визиты', color=ACCENT2)
ax2.tick_params(axis='y', labelcolor=ACCENT2)

ax1.axvline(pd.Timestamp('2026-03-22'), color='#FF6B6B', linestyle=':', linewidth=1.5)
ax1.text(pd.Timestamp('2026-03-22'), visits['Визиты'].max()*0.9, '22 марта', color='#FF6B6B')

ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
fig.autofmt_xdate(rotation=45)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', facecolor='#1a2f4e', edgecolor='#4A6080')
ax1.set_title('Динамика визитов и целевых конверсий')
fig.tight_layout()
plt.savefig('images/01_visits_conversions.png', dpi=150, bbox_inches='tight')
plt.close()


# ===================== ГРАФИК 2: Источники трафика =====================
src = sources[sources['Источник трафика (детально)'].notna()].copy()
src = src.sort_values('Визиты', ascending=True).reset_index(drop=True)
total_src = src['Визиты'].sum()
src['Доля'] = (src['Визиты'] / total_src * 100).round(1)

# Цвет по категории
category_colors = {
    'Прямые заходы':                  '#0A7EA4',
    'Переходы из поисковых систем':   '#F4A233',
    'Внутренние переходы':            '#7BC8A4',
    'Переходы по ссылкам на сайтах':  '#A78BFA',
}
bar_colors = [category_colors.get(cat, '#888888') for cat in src['Источник трафика']]

# Метка = детальный источник
labels = src['Источник трафика (детально)']

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(labels, src['Визиты'], color=bar_colors, height=0.6)

fixed_x = src['Визиты'].max() * 1.05
for bar, val, pct in zip(bars, src['Визиты'], src['Доля']):
    ax.text(fixed_x, bar.get_y() + bar.get_height() / 2,
            f'{int(val)}  ({pct}%)',
            va='center', ha='left', color='white', fontsize=9)

ax.set_xlim(0, src['Визиты'].max() * 1.35)
ax.set_title('Источники трафика', fontsize=13, pad=14)
ax.set_xlabel('Визиты', fontsize=10)
ax.grid(axis='x', alpha=0.4)
ax.spines[['top', 'right']].set_visible(False)

# Легенда по категориям
from matplotlib.patches import Patch
legend_el = [Patch(facecolor=c, label=k) for k, c in category_colors.items()]
ax.legend(handles=legend_el, facecolor='#1a2f4e', edgecolor='#4A6080',
          fontsize=8, loc='lower right')

fig.tight_layout()
plt.savefig('images/02_sources.png', dpi=150, bbox_inches='tight')
plt.close()


# ===================== ГРАФИК 3: Глубина просмотра по возрасту =====================
age_clean = age.sort_values('Глубина просмотра', ascending=True)
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.barh(age_clean['Возраст'], age_clean['Глубина просмотра'], color=ACCENT)
for bar, val in zip(bars, age_clean['Глубина просмотра']):
    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, f'{val:.1f} стр.', va='center', color='white')
ax.set_title('Глубина просмотра по возрастным группам')
ax.grid(axis='x', alpha=0.4)
fig.tight_layout()
plt.savefig('images/03_age_depth.png', dpi=150, bbox_inches='tight')
plt.close()

# ===================== ГРАФИК 4: Топ-10 страниц по просмотрам =====================
pop = popular[popular['Адрес страницы'].notna()].copy()
pop['short'] = pop['Адрес страницы'].str.replace('https://кордо.рф/', '', regex=False).str.slice(0, 40)
pop = pop.nlargest(10, 'Просмотры').sort_values('Просмотры', ascending=True)
fig, ax = plt.subplots(figsize=(11, 6))
colors_bars = [ACCENT2 if i == len(pop)-1 else ACCENT for i in range(len(pop))]
bars = ax.barh(pop['short'], pop['Просмотры'], color=colors_bars)
for bar, val in zip(bars, pop['Просмотры']):
    ax.text(val + 5, bar.get_y() + bar.get_height()/2, str(int(val)), va='center', color='white')
ax.set_title('Топ-10 страниц по просмотрам')
ax.grid(axis='x', alpha=0.4)
fig.tight_layout()
plt.savefig('images/04_top_pages.png', dpi=150, bbox_inches='tight')
plt.close()

# ===================== ГРАФИК 5: Распределение визитов по дням недели =====================
day_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
wkd = weekday.copy()
wkd['День недели визита'] = pd.Categorical(wkd['День недели визита'], categories=day_order, ordered=True)
wkd = wkd.sort_values('День недели визита')
colors_wkd = [ACCENT2 if d in ['Суббота', 'Воскресенье'] else ACCENT for d in wkd['День недели визита']]
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(wkd['День недели визита'], wkd['Визиты'], color=colors_wkd)
for bar, val in zip(bars, wkd['Визиты']):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.5, str(int(val)), ha='center', color='white')
ax.set_title('Визиты по дням недели')
ax.grid(axis='y', alpha=0.4)
from matplotlib.patches import Patch
legend_el = [Patch(facecolor=ACCENT, label='Будни'), Patch(facecolor=ACCENT2, label='Выходные')]
ax.legend(handles=legend_el, facecolor='#1a2f4e', edgecolor='#4A6080')
fig.tight_layout()
plt.savefig('images/05_weekday.png', dpi=150, bbox_inches='tight')
plt.close()

# ===================== ГРАФИК 6: KPI-карточки =====================
male_share = round(gender.loc[gender['Пол'] == 'мужской', 'Визиты'].values[0] / gender['Визиты'].sum() * 100)
metrics = [
    ('Визиты за период', f'{total_visits:,}'.replace(',', ' '), ACCENT),
    ('Целевые визиты', f'{total_conv}', ACCENT2),
    ('Конверсия', f'{conv_rate:.1f}%', '#7BC8A4'),
    ('Топ источник', str(top_source), '#F472B6'),
    ('Доля мужчин', f'{male_share}%', '#A78BFA'),
]
fig, axes = plt.subplots(1, 5, figsize=(16, 3))
for ax, (label, value, color) in zip(axes, metrics):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.add_patch(plt.Rectangle((0.05, 0.1), 0.9, 0.8, facecolor='#1a2f4e', edgecolor=color, linewidth=2))
    ax.text(0.5, 0.63, value, ha='center', va='center', fontsize=16, fontweight='bold', color=color)
    ax.text(0.5, 0.28, label, ha='center', va='center', fontsize=9, color='#AAAAAA')
fig.suptitle('Сводные показатели — кордо.рф', fontsize=14, y=1.05)
fig.tight_layout()
plt.savefig('images/06_kpi_summary.png', dpi=150, bbox_inches='tight')
plt.close()

# ===================== ГРАФИК 7: Распределение полов =====================
fig, ax = plt.subplots(figsize=(7, 4))
gender_vals = gender[['Пол', 'Визиты']].copy()
bars = ax.bar(gender_vals['Пол'], gender_vals['Визиты'], color=[ACCENT, ACCENT2], width=0.4)
total_g = gender_vals['Визиты'].sum()
for bar, val in zip(bars, gender_vals['Визиты']):
    pct = val / total_g * 100
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.5,
            f'{int(val)} ({pct:.1f}%)', ha='center', color='white', fontsize=10)
ax.set_ylim(top=ax.get_ylim()[1] * 1.2)
ax.set_title('Распределение визитов по полу')
ax.grid(axis='y', alpha=0.4)
fig.tight_layout()
plt.savefig('images/07_gender.png', dpi=150, bbox_inches='tight')
plt.close()

# ===================== ГРАФИК 8: Конверсия до и после обрыва (22 марта) =====================
conv['До/После'] = np.where(conv['Период'] < '2026-03-22', 'До 22 марта', 'После 22 марта')
conv_agg = conv.groupby('До/После')['ЦелевыеВизиты'].sum()
fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(conv_agg.index, conv_agg.values, color=[ACCENT, ACCENT2])
for bar, val in zip(bars, conv_agg.values):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.5, str(val), ha='center', color='white')
ax.set_title('Сумма конверсий до и после 22 марта')
ax.grid(axis='y', alpha=0.4)
fig.tight_layout()
plt.savefig('images/08_conversion_split.png', dpi=150, bbox_inches='tight')
plt.close()

# ===================== ГРАФИК 9: Тепловая карта дней недели (глубина/отказы) =====================
wkd_full = weekday.copy()
wkd_full['День недели визита'] = pd.Categorical(wkd_full['День недели визита'], categories=day_order, ordered=True)
wkd_full = wkd_full.sort_values('День недели визита')
fig, ax = plt.subplots(figsize=(8, 5))
sc = ax.scatter(wkd_full['День недели визита'], wkd_full['Глубина просмотра'],
                s=wkd_full['Визиты']*5, c=wkd_full['Отказы'], cmap='coolwarm',
                edgecolor='white', alpha=0.8)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label('Отказы', color='white')
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
ax.set_title('Дни недели: глубина просмотра и отказы\n(размер пузыря = визиты)')
ax.set_ylabel('Глубина просмотра')
ax.grid(axis='y', alpha=0.4)
fig.tight_layout()
plt.savefig('images/09_weekday_bubble.png', dpi=150, bbox_inches='tight')
plt.close()

print("Все графики сохранены в папку images/")
