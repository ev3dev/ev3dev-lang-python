import json
import bokeh.plotting
import bokeh.embed
import bokeh.resources
import bokeh.models

#bokeh.plotting.output_notebook()
test = json.loads( open( 'motorlog.json' ).read() )

r = bokeh.resources.Resources()

for k,d in test['data'].items():
    print k
    x  = [row[0] for row in d]
    y0  = [row[1][0] for row in d]
    y1  = [row[1][1] for row in d]
    y2  = [row[1][2] for row in d]

    p = bokeh.plotting.figure(height=300, width=800, title=k)

    p.y_range=bokeh.models.Range1d(-200,2000)
    p.extra_y_ranges = { 'foo': bokeh.models.Range1d(start=-200, end=2000),
                     'duty_cycle': bokeh.models.Range1d(start=-10, end=100) }
    #p.add_layout( bokeh.models.LinearAxis(y_range_name='position'), 'right')
    p.add_layout( bokeh.models.LinearAxis(y_range_name='duty_cycle'), 'right')

    p.line(x, y0, legend='speed', line_width=2, color='red', y_range_name='foo')
    p.line(x, y1, legend='position', line_width=2, color='blue', y_range_name='foo')
    p.line(x, y2, legend='duty_cycle', line_width=2, color= 'green', y_range_name='duty_cycle')

    o = open('{0}.html'.format(k), 'w')
    o.write( bokeh.embed.file_html(p, r, title='foo' ) )

