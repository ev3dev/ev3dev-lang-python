import matplotlib.pyplot as plt
import json

# Note, this code is a modified version from these pages:
#
# http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
# http://matplotlib.org/examples/pylab_examples/subplots_demo.html

# These are the "Tableau 20" colors as RGB.
tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
             (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
             (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
             (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
             (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]

# Scale the RGB values to the [0, 1] range, which is the format matplotlib accepts.
for i in range(len(tableau20)):
    r, g, b = tableau20[i]
    tableau20[i] = (r / 255., g / 255., b / 255.)

plt.style.use(['dark_background'])

test = json.loads( open( 'motorlog-fast-ramp.json' ).read() )

values = {}

# Extract the data from the log in a format that's useful for plotting

for k,d in test['data'].items():
    values['k'] = {}
    values['k']['x'] = [row[0] for row in d]
    values['k']['y'] = []

    for i,a in enumerate(test['meta']['ports'][k]['log_attributes']):
        values['k']['y'].append( {'name': a, 'values': [row[1][i] for row in d]})

    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
    # exception because of the number of lines being plotted on it.
    # Common sizes: (10, 7.5) and (12, 9)
    # plt.figure(figsize=(12, 9))

    f, axarr = plt.subplots(3, sharex=True)

    axarr[2].set_xlabel('Time (seconds)')

    # Clean up the chartjunk
    for i,ax in enumerate(axarr):
        print i, ax
        # Remove the plot frame lines. They are unnecessary chartjunk.
        ax.spines["top"].set_visible(False)
        # ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        # ax.spines["left"].set_visible(False)

        # Ensure that the axis ticks only show up on the bottom and left of the plot.
        # Ticks on the right and top of the plot are generally unnecessary chartjunk.
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

# # Limit the range of the plot to only where the data is.
# # Avoid unnecessary whitespace.
# plt.ylim(0, 90)
# plt.xlim(1968, 2014)
#
# # Make sure your axis ticks are large enough to be easily read.
# # You don't want your viewers squinting to read your plot.
# plt.yticks(range(0, 91, 10), [str(x) + "%" for x in range(0, 91, 10)], fontsize=14)
# plt.xticks(fontsize=14)

        axarr[i].plot(values['k']['x'],values['k']['y'][i]['values'], lw=2.5, color=tableau20[i] )
        axarr[i].text(.8,1, "{0}:{1}".format( k, values['k']['y'][i]['name'] ),
                      fontsize=14,
                      color=tableau20[i],
                      horizontalalignment='left',
                      verticalalignment='center',
                      transform = axarr[i].transAxes)

#axarr[0].plot(x, y0, lw=2.5, color=tableau20[0])
# y_pos = y0[-1]
#plt.text(4000, y_pos, 'speed', fontsize=14, color=tableau20[0])

#axarr[1].plot(x, y1, lw=2.5, color=tableau20[1])
# y_pos = y1[-1]
#plt.text(4000, y_pos, 'position', fontsize=14, color=tableau20[1])

#axarr[2].plot(x, y2, lw=2.5, color=tableau20[2])
# y_pos = y0[-1]
#plt.text(4000, y_pos, 'duty_cycle', fontsize=14, color=tableau20[2])

# Note that if the title is descriptive enough, it is unnecessary to include
# axis labels; they are self-evident, in this plot's case.

#plt.text(1995, 93, "Percentage of Bachelor's degrees conferred to women in the U.S.A."
#       ", by major (1970-2012)", fontsize=17, ha="center")

# Always include your data source(s) and copyright notice! And for your
# data sources, tell your viewers exactly where the data came from,
# preferably with a direct link to the data. Just telling your viewers
# that you used data from the "U.S. Census Bureau" is completely useless:
# the U.S. Census Bureau provides all kinds of data, so how are your
# viewers supposed to know which data set you used?

#plt.text(1966, -8, "Data source: nces.ed.gov/programs/digest/2013menu_tables.asp"
#       "\nAuthor: Randy Olson (randalolson.com / @randal_olson)"
#       "\nNote: Some majors are missing because the historical data "
#       "is not available for them", fontsize=10)

# Finally, save the figure as a PNG.
# You can also save it as a PDF, JPEG, etc.
# Just change the file extension in this call.
# bbox_inches="tight" removes all the extra whitespace on the edges of your plot.

        plt.savefig("motorlog-fast-ramp-{0}.png".format(k), bbox_inches="tight")