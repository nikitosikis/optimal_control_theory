from pathlib import Path
import csv
import json
import math
import sys

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, Flowable,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.colors import HexColor, black
from reportlab.lib.pagesizes import A4

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Лаба1_вариант11'
RESULTS = OUT / 'results'
DATA = json.loads((RESULTS / 'results.json').read_text(encoding='utf-8'))
FONTS = Path('C:/Windows/Fonts')
for name, file in [('TNR', 'times.ttf'), ('TNR-Bold', 'timesbd.ttf'),
                   ('TNR-Italic', 'timesi.ttf'), ('TNR-BoldItalic', 'timesbi.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
pdfmetrics.registerFontFamily('TNR', normal='TNR', bold='TNR-Bold',
                             italic='TNR-Italic', boldItalic='TNR-BoldItalic')
pdfmetrics.registerFont(TTFont('Cambria', str(FONTS / 'cambria.ttc')))

styles = {
    'title': ParagraphStyle('Title', fontName='TNR-Bold', fontSize=18, leading=21,
                            spaceAfter=9),
    'subtitle': ParagraphStyle('Subtitle', fontName='TNR', fontSize=12, leading=16,
                               spaceAfter=12),
    'h': ParagraphStyle('Heading', fontName='TNR-Bold', fontSize=14, leading=18,
                         spaceBefore=10, spaceAfter=8, keepWithNext=True),
    'h2': ParagraphStyle('Heading2', fontName='TNR-Bold', fontSize=12, leading=16,
                          spaceBefore=8, spaceAfter=6, keepWithNext=True),
    'p': ParagraphStyle('Body', fontName='TNR', fontSize=12, leading=16,
                         spaceAfter=7),
    'eq': ParagraphStyle('Equation', fontName='TNR', fontSize=12.2, leading=18,
                          leftIndent=12, spaceBefore=3, spaceAfter=7),
    'small': ParagraphStyle('Small', fontName='TNR', fontSize=10.5, leading=13.5,
                             spaceAfter=6),
    'caption': ParagraphStyle('Caption', fontName='TNR', fontSize=10.5, leading=13,
                               spaceBefore=3, spaceAfter=10),
    'cell': ParagraphStyle('Cell', fontName='TNR', fontSize=9.7, leading=12,
                            alignment=TA_CENTER),
    'headercell': ParagraphStyle('HeaderCell', fontName='TNR-Bold', fontSize=9.7,
                                  leading=12, alignment=TA_CENTER),
}


class MatrixLine(Flowable):
    def __init__(self, prefix, rows, suffix='', cell_width=38):
        super().__init__()
        self.prefix, self.rows, self.suffix = prefix, rows, suffix
        self.cell_width = cell_width
        self.height = 23 * len(rows) + 10
        self.width = 490

    def draw(self):
        c = self.canv
        c.setFont('TNR', 12.2)
        y = self.height / 2 - 4
        c.drawString(12, y, self.prefix)
        x = 20 + pdfmetrics.stringWidth(self.prefix, 'TNR', 12.2)
        n = len(self.rows[0])
        w = n * self.cell_width
        lo, hi = 5, self.height - 5
        c.setLineWidth(.7)
        for a, sign in [(x, 1), (x + w + 12, -1)]:
            c.line(a, lo, a, hi)
            c.line(a, lo, a + sign * 5, lo)
            c.line(a, hi, a + sign * 5, hi)
        for i, row in enumerate(self.rows):
            for j, value in enumerate(row):
                c.drawCentredString(x + 6 + self.cell_width * (j + .5),
                                    hi - 17 - i * 23, str(value))
        c.drawString(x + w + 22, y, self.suffix)


story = []


def p(s, style='p'):
    story.append(Paragraph(s.replace('∇', '<font name="Cambria">∇</font>'), styles[style]))


def eq(s):
    p(s, 'eq')


def h(s):
    p(s, 'h')


def newpage():
    story.append(PageBreak())


def table(headers, rows, widths, size=9.7, rowheight=None):
    header_style = styles['headercell']
    cell_style = ParagraphStyle('CellLocal', parent=styles['cell'], fontSize=size,
                                leading=size + 2)
    contents = [[Paragraph(str(x).replace('∇', '<font name="Cambria">∇</font>'), header_style)
                 for x in headers]]
    contents += [[Paragraph(str(x), cell_style) for x in row] for row in rows]
    t = Table(contents, colWidths=widths, repeatRows=1,
              rowHeights=([26] + [rowheight] * len(rows)) if rowheight else None)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#E7EDF3')),
        ('GRID', (0, 0), (-1, -1), .45, HexColor('#D9D9D9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4 if rowheight is None else 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4 if rowheight is None else 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


def csv_rows(filename):
    with (RESULTS / filename).open(encoding='utf-8-sig', newline='') as f:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(f)]


def iteration_table(filename, rowheight=16):
    rows = csv_rows(filename)
    vals = [[str(int(r['k'])), f"{r['x']:.9f}", f"{r['u']:.9f}",
             f"{r['J']:.12f}", f"{r['grad_norm']:.6e}"] for r in rows]
    table(['k', 'x<sub>k</sub>', 'u<sub>k</sub>', 'J<sub>k</sub>',
           '||∇J(z<sub>k</sub>)||<sub>2</sub>'], vals,
          [24, 101, 101, 132, 132], size=9.4, rowheight=rowheight)


def figure(name, width, caption):
    from PIL import Image as PILImage
    path = RESULTS / name
    with PILImage.open(path) as im:
        w, height = im.size
    story.append(Image(str(path), width=width, height=width * height / w))
    p(caption, 'caption')


xe, ue = DATA['z_equality']
lam, je = DATA['lambda_equality'], DATA['J_equality']
mu1, mu2 = DATA['eigenvalues_H']
detL = 176 - 32 * lam

# Page 1
p('Лабораторная работа 1', 'title')
p('Поиск минимума с помощью методов статической оптимизации<br/>'
  'Дисциплина «Оптимальное управление» · Вариант 11', 'subtitle')
p('Цель работы - найти глобальный минимум заданного критерия без ограничений '
  'и с ограничениями, затем сравнить пошаговый поиск методом Ньютона-Рафсона '
  'и градиентным методом при двух постоянных шагах.')
h('Исходные данные')
eq('J(x, u) = 8x<super>2</super> + 6u<super>2</super> + 4xu + x + 3u - 10.')
eq('c(x, u) = 3x - u<super>2</super> + 1.')
p('В пункте 1 рассматриваются три задачи: без ограничений, с равенством '
  'c(x, u) = 0 и с неравенством c(x, u) ≤ 0. В пункте 2 минимизируется '
  'J<sub>1</sub>(x, u) = J(x, u) без ограничений.')
p('Используются формулы из лекции ТОУ_1, слайды 7-10: стационарность критерия, '
  'функция Лагранжа, условия Куна-Таккера и итерационные методы. '
  'В данном варианте ограничение нелинейное, поэтому ∂c/∂u = -2u.', 'small')
h('1 Поиск минимума без ограничений')
eq('∇J = (16x + 4u + 1; 4x + 12u + 3)<super>T</super>.')
p('Необходимое условие ∇J = 0 даёт систему')
eq('16x + 4u + 1 = 0,<br/>4x + 12u + 3 = 0.')
story.append(MatrixLine('H =', [[16, 4], [4, 12]], 'Δ₁ = 16 > 0,  Δ₂ = 176 > 0.'))
p('По критерию Сильвестра H положительно определена. Функция J строго '
  'выпукла на всей плоскости, поэтому стационарная точка является '
  'единственным глобальным минимумом.')
eq('<b>x* = 0,  u* = -1/4 = -0.25,  J* = -83/8 = -10.375.</b>')

# Page 2
newpage()
h('2 Минимум при ограничении в виде равенства')
eq('c(x, u) = 3x - u<super>2</super> + 1 = 0.')
p('Составим функцию Лагранжа. Для ограничения-равенства знак множителя '
  'Лагранжа заранее не ограничивается.')
eq('L(x, u, λ) = J(x, u) + λ(3x - u<super>2</super> + 1).')
p('Необходимые условия стационарности:')
eq('16x + 4u + 1 + 3λ = 0,<br/>'
   '4x + 12u + 3 - 2λu = 0,<br/>'
   '3x - u<super>2</super> + 1 = 0.')
p('Из ограничения и первого уравнения выразим x и λ:')
eq('x = (u<super>2</super> - 1)/3,<br/>'
   'λ = -(16u<super>2</super> + 12u - 13)/9.')
p('Подстановка во второе уравнение приводит к кубическому уравнению')
eq('32u<super>3</super> + 36u<super>2</super> + 82u + 15 = 0.')
p('Проверим достаточность и глобальность минимума. Подстановка ограничения '
  'непосредственно в критерий даёт функцию одной переменной:')
eq('φ(u) = J((u<super>2</super> - 1)/3, u)<br/>'
   '= (8u<super>4</super> + 12u<super>3</super> + 41u<super>2</super> + 15u - 85)/9.')
eq('φ′(u) = (32u<super>3</super> + 36u<super>2</super> + 82u + 15)/9,')
eq('φ″(u) = (96u<super>2</super> + 72u + 82)/9<br/>'
   '= (32/3)(u + 3/8)<super>2</super> + 137/18 > 0.')
p('Следовательно, φ строго выпукла. Кроме того, φ(u) → +∞ при |u| → ∞. '
  'Поэтому уравнение φ′(u) = 0 имеет ровно один действительный корень, '
  'который определяет единственный глобальный минимум на всей параболе c = 0.')
eq(f'<b>u* = {ue:.12f},  x* = {xe:.12f},<br/>'
   f'λ* = {lam:.12f},  J* = {je:.12f}.</b>')
p('Численный корень получен функцией roots. Подстановка в исходную '
  'систему Лагранжа и независимая минимизация φ функцией fminbnd '
  'подтверждают результат.', 'small')

# Page 3
newpage()
h('3 Минимум при ограничении в виде неравенства')
eq('3x - u<super>2</super> + 1 ≤ 0,  то есть x ≤ (u<super>2</super> - 1)/3.')
p('Условия Куна-Таккера для лагранжиана L = J + λc:')
eq('16x + 4u + 1 + 3λ = 0,<br/>'
   '4x + 12u + 3 - 2λu = 0,<br/>'
   'c(x, u) ≤ 0,  λ ≥ 0,  λc(x, u) = 0.')
p('<b>Неактивное ограничение.</b> При λ = 0 получается безусловный минимум '
  '(0; -1/4). Однако c(0, -1/4) = 15/16 = 0.9375 > 0, '
  'поэтому эта точка недопустима.')
p('<b>Активное ограничение.</b> При c = 0 получаем решение пункта 2. '
  f'Для него λ* = {lam:.12f} > 0, поэтому все условия Куна-Таккера выполнены.')
p('Докажем достаточность для глобального минимума. Область c ≤ 0 '
  'невыпукла, поэтому одной проверки условий Куна-Таккера недостаточно. '
  'При найденном λ* гессиан лагранжиана постоянен:')
story.append(MatrixLine('H_L =', [[16, 4], [4, f'{12-2*lam:.9f}']],
                        '= H + diag(0, -2λ*).', cell_width=67))
eq(f'Δ₁ = 16 > 0,  det H<sub>L</sub> = 176 - 32λ* = {detL:.9f} > 0.')
p('Таким образом, L(x, u, λ*) строго выпукла на всей плоскости, '
  'а найденная стационарная точка даёт её единственный глобальный минимум. '
  'Для любой допустимой точки z = (x, u)<super>T</super> справедливо')
eq('J(z) = L(z, λ*) - λ*c(z) ≥ L(z, λ*)<br/>'
   '≥ L(z*, λ*) = J(z*).')
p('Это доказывает единственность глобального минимума задачи с неравенством.')
table(['Условие', 'x*', 'u*', 'J*'], [
    ['Без ограничений', '0', '-0.250000000', '-10.375000000'],
    ['c(x, u) = 0', f'{xe:.9f}', f'{ue:.9f}', f'{je:.9f}'],
    ['c(x, u) ≤ 0', f'{xe:.9f}', f'{ue:.9f}', f'{je:.9f}'],
], [142, 110, 110, 128])
p(f'Ограничение увеличивает минимальное значение критерия на '
  f'{je-DATA["J_free"]:.9f}. В обоих ограниченных случаях минимум лежит на границе.', 'small')

# Page 4
newpage()
h('4 Пошаговый расчёт методом Ньютона Рафсона')
p('Для всех численных методов выбраны одна начальная точка '
  'z<sub>0</sub> = (0; 0)<super>T</super> и общий критерий остановки '
  '||∇J(z<sub>k</sub>)||<sub>2</sub> ≤ 10<super>-6</super>. '
  'Эти параметры задаются для вычислительного эксперимента.')
eq('z<sub>k+1</sub> = z<sub>k</sub> - H<super>-1</super>∇J(z<sub>k</sub>).')
story.append(MatrixLine('H⁻¹ = (1/176)', [[12, -4], [-4, 16]],
                        'grad J(z₀) = (1; 3)ᵀ.'))
eq('H<super>-1</super>∇J(z<sub>0</sub>) = (0; 1/4)<super>T</super>,<br/>'
   'z<sub>1</sub> = (0; 0)<super>T</super> - (0; 1/4)<super>T</super>'
   ' = (0; -1/4)<super>T</super>.')
iteration_table('newton.csv', rowheight=23)
p('Градиент в z<sub>1</sub> равен нулю. Метод Ньютона достигает точного '
  'минимума за одну итерацию, поскольку гессиан квадратичного критерия постоянен.')
h('5 Выбор шага градиентного метода')
p('Используем формулу метода наискорейшего спуска со слайда 10 лекции 1 '
  'с постоянным параметром γ:')
eq('x<sub>k+1</sub> = x<sub>k</sub> - γ(16x<sub>k</sub> + 4u<sub>k</sub> + 1),<br/>'
   'u<sub>k+1</sub> = u<sub>k</sub> - γ(4x<sub>k</sub> + 12u<sub>k</sub> + 3).')
p('Для ошибки e<sub>k</sub> = z<sub>k</sub> - z* имеем '
  'e<sub>k+1</sub> = (I - γH)e<sub>k</sub>. Собственные значения H:')
eq(f'μ₁ = 14 - 2√5 = {mu1:.9f},<br/>'
   f'μ₂ = 14 + 2√5 = {mu2:.9f}.')
eq(f'0 &lt; γ &lt; 2/μ₂ = {2/mu2:.9f} - условие сходимости.')
p(f'При γ = 0.05 &lt; 1/μ₂ = {1/mu2:.9f} оба множителя 1 - γμᵢ '
  'положительны. При γ = 0.09 один множитель отрицателен, а модули обоих '
  'меньше единицы. Поэтому выбранные шаги дают требуемые режимы сходимости.')

# Page 5
newpage()
h('6 Апериодическая сходимость при γ равном 0.05')
eq('z<sub>k+1</sub> = (I - 0.05H)z<sub>k</sub> - 0.05(1; 3)<super>T</super>.')
p('Первый шаг: z<sub>1</sub> = (-0.05; -0.15)<super>T</super>, '
  'J<sub>1</sub> = -10.315. Множители изменения собственных составляющих '
  'ошибки равны 0.523606798 и 0.076393202; оба находятся между 0 и 1.', 'small')
iteration_table('descent_005.csv', rowheight=17.4)
p('Критерий остановки впервые выполнен при k = 23: '
  '||∇J(z<sub>23</sub>)||<sub>2</sub> = 6.979242·10<super>-7</super>. '
  'Начальная точка k = 0 в число итераций не включается.')
p('Апериодичность означает отсутствие смены знака у собственных '
  'составляющих ошибки. Для отдельной координаты это не требует '
  'монотонности на каждом шаге.', 'small')

# Page 6
newpage()
h('7 Колебательная сходимость при γ равном 0.09')
p('Первый шаг: z<sub>1</sub> = (-0.09; -0.27)<super>T</super>, '
  'J<sub>1</sub> = -10.3006. Множители равны 0.142492236 и -0.662492236. '
  'Отрицательный множитель вызывает затухающие колебания относительно минимума.', 'small')
iteration_table('descent_009.csv', rowheight=14.4)
p('Критерий остановки впервые выполнен при k = 36: '
  '||∇J(z<sub>36</sub>)||<sub>2</sub> = 8.866033·10<super>-7</super>. '
  'Хотя координаты колеблются, значение J убывает.', 'small')
p('Все строки до остановки приведены в таблицах. Значения J округлены '
  'до 12 знаков: совпадение последних значений не означает равенства '
  'градиента нулю. В расчёте используются неокруглённые числа.', 'small')

# Page 7
newpage()
h('8 Геометрия задачи и траектории поиска')
figure('constraints.png', 490,
       'Рисунок 1. Слева показаны линии уровня J, допустимая область c ≤ 0, '
       'безусловный и ограниченный минимумы. Справа - критерий φ на границе c = 0.')
figure('trajectories.png', 400,
       'Рисунок 2. Траектории градиентного поиска при двух шагах '
       'и единственный шаг метода Ньютона из точки (0; 0).')

# Page 8
newpage()
h('9 Сравнение сходимости и выводы')
figure('descent.png', 490,
       'Рисунок 3. Изменение координат, нормы градиента и ошибки критерия. '
       'Ошибка J(z<sub>k</sub>) - J* вычисляется как '
       'e<sub>k</sub><super>T</super>He<sub>k</sub>/2, чтобы избежать потери '
       'точности при вычитании близких чисел.')
table(['Метод', 'Число итераций', 'Итоговый J'], [
    ['Ньютона-Рафсона', '1', '-10.375000000000'],
    ['Градиентный, γ = 0.05', '23', '-10.375000000000'],
    ['Градиентный, γ = 0.09', '36', '-10.375000000000'],
], [224, 112, 154])
p('Безусловный минимум равен -10.375 в точке (0; -0.25). '
  f'Оба ограничения дают минимум {je:.9f} в точке '
  f'({xe:.9f}; {ue:.9f}). Глобальность доказана: '
  'для равенства - строгой выпуклостью φ, для неравенства - нижней оценкой '
  'через строго выпуклый лагранжиан при λ* > 0.')
p('Метод Ньютона решил квадратичную задачу за один шаг. Для выбранных '
  'постоянных шагов апериодический режим оказался быстрее колебательного: '
  'его спектральный радиус 0.523606798 меньше 0.662492236. '
  'Больший шаг сам по себе не обеспечивает более быстрой сходимости.')
p('<b>Источники.</b> Задания1_6_ОУ 2026.pdf, задание 1, вариант 11, стр. 1-2. '
  'Презентации/ТОУ_1.pdf, слайды 7-10. '
  'Вычисления и все графики воспроизводятся файлом lab1_variant11.m.', 'small')


def footer(c, doc):
    c.saveState()
    c.setFont('TNR', 9)
    c.setFillColor(HexColor('#505050'))
    c.drawString(50, 25, 'Оптимальное управление · Лабораторная работа 1 · Вариант 11')
    c.drawRightString(A4[0]-50, 25, str(doc.page))
    c.restoreState()


pdf = OUT / 'Лабораторная_1_Вариант_11.pdf'
doc = SimpleDocTemplate(str(pdf), pagesize=A4, rightMargin=50, leftMargin=50,
                        topMargin=38, bottomMargin=42,
                        title='Лабораторная работа 1 Статическая оптимизация Вариант 11',
                        author='', subject='Оптимальное управление')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(pdf)
