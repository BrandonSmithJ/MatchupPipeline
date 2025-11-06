def add_scale(ax, im_lon, im_lat, pct_size=0.15, multiple_of=10, include_compass=False, loc='lower left'):
    ''' 
    Add a scale to the axis, where:
        - scale width will be approximately <pct_size> of the image width
        - measured length of the scale will be a multiple of <multiple_of> km
    https://matplotlib.org/3.3.1/gallery/axes_grid1/simple_anchored_artists.html

    TODO: 
    - fix scale
        - add 3 tick labels (left, center, right)
        - make 4 colored segments instead of 2
        - see here for basemap's implementation: https://github.com/matplotlib/basemap/blob/3076ec9470cf7dba523bc94ebe5ae9a990e34d08/lib/mpl_toolkits/basemap/__init__.py    
    - fix compass
        - use images
        - separate function "add_compass"
        - see Plotting/geolocated-plotting/utils.py - already finished there, using basemap foundation...
    '''
    from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
    from matplotlib.offsetbox import AuxTransformBox, HPacker, AnchoredOffsetbox
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Rectangle, Ellipse

    from matplotlib.transforms import IdentityTransform
    from geopy.distance import distance as geo_distance

    maxim  = im_lon.max() - im_lon.min()
    width  = maxim * pct_size # width in degrees
    height = width * 0.035    # height in degrees
    angle  = 45               # northward rotation angle
    radius = min(im_lon.shape) * 0.05
    kwargs = {
        'loc'       : loc,
        'pad'       : 0.4, # Padding around label & bar, in fraction of font size (default 0.1)
        'borderpad' : 0.5, # Border padding in fraction of font size (default 0.1)
        'frameon'   : True,
        'fontproperties' : FontProperties(size=14, weight='bold'),
    }

    scale = artist = AnchoredSizeBar(ax.transData, width, '', fill_bar=False, size_vertical=height, **kwargs)
    
    if include_compass:
        compass = AuxTransformBox(IdentityTransform())
        compass.add_artist( Ellipse((0, 0), radius, radius, angle, fill=False,) )
        # For whatever reason, nested AnchoredOffsetboxes remain anchored to the outermost axis
        # This means we can't correctly nest and align these independent artists
        # Alternative is to use scale._box, though we then can't control the aesthetics of the scale bounding box, independently of the compass
        boxes   = [compass, scale._box] if 'right' in loc else [scale._box, compass] 
        artist  = AnchoredOffsetbox(loc=loc, child=HPacker(children=boxes, align='center', pad=0., sep=20), frameon=True, pad=0.7, borderpad=0.5)

    # Draw the subplot, so we can determine the size
    ax.add_artist(artist)
    ax.figure.canvas.draw()

    # Get rectangle which actually defines the scale
    bar, aux, *_ = scale.size_bar.findobj()
    assert(isinstance(aux, AuxTransformBox)), f'Did not find AuxTransformBox: {bar}, {aux}'

    # Define some helper methods to easily check the scale length in kilometers
    get_ext = lambda: bar.get_window_extent(ax.figure.canvas.renderer)
    get_pts = lambda: ax.transData.inverted().transform(get_ext())
    get_len = lambda p: geo_distance(p[0][::-1], p[1][::-1]).km
    is_nice = lambda d: (round(d % multiple_of, 1) % multiple_of) == 0 and d > 0

    # Calculate the approximate 
    curr_len = get_len( get_pts() )
    targ_len = round(curr_len - curr_len % multiple_of) + multiple_of
    bar.set_width(width * (targ_len / curr_len))
    new_len  = get_len( get_pts() )
    assert(is_nice(new_len)), [pct_size, curr_len, targ_len, new_len]
    scale.txt_label.set_text(f'{round(new_len):.0f} km')

    # Finally, for some aesthetic appeal, color in half the scale bar
    scale.size_bar.add_artist(Rectangle((0, 0), 0.5*bar.get_width(), height, fill=True, facecolor='k', edgecolor='k'))
