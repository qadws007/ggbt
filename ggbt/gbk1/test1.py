from pyecharts.charts import Line, Grid
import pyecharts.options as opts
import os

line_1 = (
    Line()
        .add_xaxis([0, 1, 2, 3])
        .add_yaxis(
        series_name="value",
        y_axis=[1, 2, 3, 1],
        label_opts=opts.LabelOpts(is_show=False),
        is_smooth=True,
        color="#0000FF",
        xaxis_index=0
    )
        .add_yaxis(
        series_name="cash",
        y_axis=[2, 2, 1, 3],
        label_opts=opts.LabelOpts(is_show=False),
        is_smooth=True,
        color="#FF0000",
        xaxis_index=0
    )
        .set_global_opts(
        title_opts=opts.TitleOpts(title="账户情况"),
        tooltip_opts=opts.TooltipOpts(axis_pointer_type="cross",),
        axispointer_opts=opts.AxisPointerOpts(
            is_show=True,
            link=[{"xAxisIndex": "all"}],
            label=opts.LabelOpts(background_color="#777"),
        ),

    )
)


def calc_border(all, nub):
    layer = 100 / (all * 4 + all + 1)
    x = nub * layer + (nub - 1) * layer * 4
    y = (all + 1 - nub) * layer + (all - nub) * layer * 4
    x = str(round(x, 2)) + '%'
    y = str(round(y, 2)) + '%'
    print(x, y)
    return x, y


grid = (
    Grid()
        .add(line_1, grid_opts=opts.GridOpts(1, pos_top=calc_border(2, 1)[0], pos_bottom=calc_border(2, 1)[1]))
        .add(line_1, grid_opts=opts.GridOpts(1, pos_top=calc_border(2, 2)[0], pos_bottom=calc_border(2, 2)[1]))

        .render("C:\\Users\\Administrator\\Desktop\\test.html")
)
os.system("C:\\Users\\Administrator\\Desktop\\test.html")
