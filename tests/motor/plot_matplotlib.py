import matplotlib.pyplot as plt
import json
import argparse

parser = argparse.ArgumentParser(description='Plot ev3dev datalogs.')
parser.add_argument('infile',
                   help='the input file to be logged')

args = parser.parse_args()

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

test = json.loads( open( args.infile ).read() )

values = {}

# Extract the data from the log in a format that's useful for plotting

for k,d in test['data'].items():
    values['k'] = {}
    values['k']['x'] = [row[0] for row in d]
    values['k']['y'] = []

    for i,a in enumerate(test['meta']['ports'][k]['log_attributes']):
        values['k']['y'].append( {'name': a, 'values': [row[1][i] for row in d]})

    f, axarr = plt.subplots(3, sharex=True)

    axarr[2].set_xlabel('Time (seconds)')

    f.text(.95,0, args.infile,
                      fontsize=10,
                      horizontalalignment='left',
                      verticalalignment='center' )

    f.text(.5,1, "{0} - {1}".format( test['meta']['title'], k),
                      fontsize=14,
                      horizontalalignment='center',
                      verticalalignment='center' )

    f.text(.5,.96, "{0}".format( test['meta']['subtitle']),
                      fontsize=10,
                      horizontalalignment='center',
                      verticalalignment='center' )

    f.text(.92,.5, "{0}".format( test['meta']['notes']),
                      fontsize=10,
                      horizontalalignment='left',
                      verticalalignment='center' )

    # Clean up the chartjunk
    for i,ax in enumerate(axarr):
        print i, ax
        # Remove the plot frame lines. They are unnecessary chartjunk.
        ax.spines["top"].set_visible(False)

        # Ensure that the axis ticks only show up on the bottom and left of the plot.
        # Ticks on the right and top of the plot are generally unnecessary chartjunk.
        ax.get_xaxis().tick_bottom()
        ax.get_yaxis().tick_left()

        axarr[i].plot(values['k']['x'],values['k']['y'][i]['values'], lw=1.5, color=tableau20[i] )
        axarr[i].text(.95,1, "{0}".format( values['k']['y'][i]['name'] ),
                      fontsize=14,
                      color=tableau20[i],
                      horizontalalignment='right',
                      verticalalignment='center',
                      transform = axarr[i].transAxes)

        plt.savefig("{0}-{1}.png".format(args.infile,k), bbox_inches="tight")