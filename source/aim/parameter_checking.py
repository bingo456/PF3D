"""Check AIM parameters and derive values where possible
"""

from math import ceil
from utilities import list_to_string, get_scenario_parameters, get_temporal_parameters_from_windfield

def check_parameter_ranges(params):
    """Catch unphysical situations and raise appropriate error messages
       Input:
           params: Dictionary of modelling parameters
    """

    # Get scenario name
    scenario_name = params['scenario_name']

    # Create local variables from dictionary
    for key in params:
        s = '%s = params["%s"]' % (key, key)
        exec(s)

    # Mass Eruption Rate can be either
    # 'estimate'
    # number
    # list of numbers


    # FIXME: Deprecate ability to have list of eruption rates and related parameters.
    try:
        float(params['Mass_eruption_rate'])
    except:
        if isinstance(params['mass_eruption_rate'], basestring):
            msg = 'The variable mass_eruption_rate must be either a number, a list or the word "estimate"'
            assert params['mass_eruption_rate'].lower() == 'estimate', msg
        else:
            # Must be a list - convert
            params['mass_eruption_rate'] = list_to_string(params['mass_eruption_rate'])

    else:
        if params['mass_eruption_rate'] <= 0:
            msg = 'Mass eruption rate must be greater than zero.\n'
            msg += 'A value of %e was specified' % params['mass_eruption_rate']
            raise Exception(msg)


    #log_estimated_mass_eruption_rate = 4 + 1.7*math.log(Eruption_column_height)
    #if abs(log_estimated_mass_eruption_rate - math.log(Mass_eruption_rate)) > 1:
    #    msg = 'Mass eruption rate and eruption column height do not correlate \n'
    #    msg += 'for mass eruption rate = %e and for eruption column height = %i.\n' % (Mass_eruption_rate, Eruption_column_height)
    #    raise Exception(msg)


#     # Assert that column height is compatible with mass eruption rate
#     Eruption_column_height = Height_above_vent[0]
#     if Eruption_column_height < 2000:
#         msg = 'Eruption column height must be greater than or equal to 2000.\n'
#         msg += 'A height of %i was specified' % Eruption_column_height
#         raise Exception(msg)

#     if 2000 <= Eruption_column_height < 10000:
#         msg = 'Mass eruption rate inconsistent with column height: '
#         msg += 'Eruption_column_height = %.0f m, ' % Eruption_column_height
#         msg += 'Mass_eruption_rate = %.0e kg/s' % Mass_eruption_rate
#         assert 1.0e4 <= Mass_eruption_rate <= 1.0e6, msg

#     if 10000 <= Eruption_column_height < 15000:
#         msg = 'Mass eruption rate inconsistent with column height: '
#         msg += 'Eruption_column_height = %.0f m, ' % Eruption_column_height
#         msg += 'Mass_eruption_rate = %.0e kg/s' % Mass_eruption_rate
#         assert 1.0e4 <= Mass_eruption_rate < 1.0e8, msg

#     if 15000 <= Eruption_column_height < 30000:
#         msg = 'Mass eruption rate inconsistent with column height: '
#         msg += 'Eruption_column_height = %.0f m, ' % Eruption_column_height
#         msg += 'Mass_eruption_rate = %.0e kg/s' % Mass_eruption_rate
#         assert 1.0e5 <= Mass_eruption_rate < 1.0e8, msg

#     if 30000 <= Eruption_column_height < 80000:
#         msg = 'Mass eruption rate inconsistent with column height: '
#         msg += 'Eruption_column_height = %.0f m, ' % Eruption_column_height
#         msg += 'Mass_eruption_rate = %.0e kg/s' % Mass_eruption_rate
#         assert 1.0e8 <= Mass_eruption_rate < 1.0e12, msg

#     if Eruption_column_height >= 80000:
#         msg = 'Eruption column height cannot equal or exceed 80000.\n'
#         msg += 'A height of %i was specified' % Eruption_column_height
#         raise Exception(msg)


    # Check that vent location is within model domain
    lo = X_coordinate_minimum
    hi = X_coordinate_maximum
    msg = 'Vent location %i not within easting range [%i, %i]' % (x_coordinate_of_vent, lo, hi)
    assert lo <= x_coordinate_of_vent <= hi, msg

    lo = Y_coordinate_minimum
    hi = Y_coordinate_maximum
    msg = 'Vent location %i not within northing range [%i, %i]' % (y_coordinate_of_vent, lo, hi)
    assert lo <= y_coordinate_of_vent <= hi, msg


#    if Number_cells_X_direction > 150 or Number_cells_Y_direction > 150:
#        msg = 'WARNING: DEM dimensions cannot exceed 150. '
#        msg += ' I got %i, %i' % (Number_cells_X_direction,
#                                  Number_cells_Y_direction)
#        raise Exception(msg)


    # Check consistency of model times
    if End_time_of_meteo_data < End_time_of_run:
        msg = 'End time of meteorological data must be greater than or equal to end time of run. I got\n'
        msg += 'End_time_meteo_data = %f and ' % End_time_of_meteo_data
        msg += 'End_time_of_run = %f.' % End_time_of_run
        raise Exception(msg)




def derive_implied_parameters(topography_grid, projection, params):
    """Compute parameters that can be derived from topography grid and scenario parameters.
       Input:
           topography_grid: filename
           projection: dictionary of projection parameters
           params: dictionary with model parameters
    """

    derive_spatial_parameters(topography_grid, projection, params)
    derive_temporal_parameters(params)
    derive_modelling_parameters(params)




def derive_spatial_parameters(topography_grid, projection, params):
    """Derive spatial parameters from topography grid
       Input:
           topography_grid: filename
           params: dictionary with model parameters
    """

    scenario_name = params['scenario_name']

    try:
        fid = open(topography_grid)
    except IOError:
        # FIXME (Ole): I think we should get rid of this eventuality.
        # FIXME: Yes deprecate this possibility. See also wrapper.py


        # Assume existence of native Fall3d (surfer) topogrid named
        # <scenario_name>.top
        #
        #DSAA
        #171  171
        #430000.0  600000.0
        #4100000.0 4270000.0
        #0.0    3129.5

        native_grid = '%s.top' % scenario_name
        print('AIM topography grid %s could not be found.' % topography_grid)
        print('Assuming existence of Fall3d grid named %s'% native_grid)

        fid = open(native_grid)
        lines = fid.readlines()
        fid.close()

        for i, line in enumerate(lines[:4]):
            fields = line.strip().split()

            if i == 0: assert line.strip() == 'DSAA'

            if i == 1:
                nx = params['Number_cells_X_direction'] = int(fields[0])
                ny = params['Number_cells_Y_direction'] = int(fields[1])

            if i == 2:
                xmin = float(fields[0])
                xmax = float(fields[1])
                params['X_coordinate_minimum'] = xmin

            if i == 3:
                ymin = float(fields[0])
                ymax = float(fields[1])
                params['Y_coordinate_minimum'] = ymin

        params['Cell_size'] = (xmax-xmin)/nx/1000 # Convert to km
        return


    # Get data from AIM topofile
    lines = fid.readlines()
    for i, line in enumerate(lines[:5]):
        fields = line.strip().split()
        val = float(fields[1])

        if i == 0:
            assert fields[0] == 'ncols'
            params['Number_cells_X_direction'] = int(val)

        if i == 1:
            assert fields[0] == 'nrows'
            params['Number_cells_Y_direction'] = int(val)

        if i == 2:
            assert fields[0] == 'xllcorner'
            params['X_coordinate_minimum'] = ceil(float(val)) # See comment below

        if i == 3:
            assert fields[0] == 'yllcorner'
            params['Y_coordinate_minimum'] = ceil(float(val)) # See comment below

        if i == 4:
            assert fields[0] == 'cellsize'
            params['Cell_size'] = float(val)/1000  # Convert to km

    # Calculate upper bounds (rounded downwards to nearest integer to avoid error: read_PRO_grid: xmax of the domain is outside the DEM file)
    # FIXME (Ole): Ask Arnau and Antonio about this
    xmax = params['X_coordinate_minimum'] + params['Cell_size']*1000*params['Number_cells_X_direction']
    params['X_coordinate_maximum'] = int(xmax)

    ymax = params['Y_coordinate_minimum'] + params['Cell_size']*1000*params['Number_cells_Y_direction']
    params['Y_coordinate_maximum'] = int(ymax)

    # Get UTMZONE from projection file.
    if params['Meteorological_model'].lower() == 'profile':
        params['Coordinates'] = projection['proj'].upper()        # UTM

        # Always disable geographic coordinates for the time being.
        params['Longitude_minimum'] = 0                           # LON-LAT only
        params['Longitude_maximum'] = 0                           # LON-LAT only
        params['Latitude_minimum'] = 0                            # LON-LAT only
        params['Latitude_maximum'] = 0                            # LON-LAT only
        params['Longitude_of_vent'] = 0                           # LON-LAT only
        params['Latitude_of_vent'] = 0                            # LON-LAT only



    elif params['Meteorological_model'].lower() == 'ncep':
        params['Coordinates'] = 'LON-LAT'

        # Get parameters specified in scenario_file
        metparams = get_scenario_parameters('%s_meteorological_domain.py' % params['scenario_name'])

        for key in metparams:
            if key.startswith('Lat') or key.startswith('Lon'):
                #print 'Got', key, metparams[key]
                params[key] = metparams[key]


    else:
        msg = 'Unknown choice of met data: %s. Expect either "profile" or "ncep".' % params['Meteorological_model']
        raise Exception(msg)


    params['UTMZONE'] = '%s%s' % (projection['zone'], projection['hemisphere'])   # E.g. 51S


def derive_temporal_parameters(params):
    """Derive temporal parameters from wind profile

       Fall3d parameters derived are
           'Eruption_Year'
           'Eruption_Month'
           'Eruption_Day'
           'Start_time_of_meteo_data'
           'Meteo_time_step'
           'End_time_of_meteo_data'

       Input:
           params: dictionary with model parameters
    """

    wind_profile = params['wind_profile']
    year, month, day, start_time, end_time, time_step = get_temporal_parameters_from_windfield(wind_profile)

    # Assign date
    params['Eruption_Year'] = year
    params['Eruption_Month'] = month
    params['Eruption_Day'] = day

    # Convert times to hours
    params['Start_time_of_meteo_data'] = start_time/3600.
    params['End_time_of_meteo_data'] = end_time/3600.


    # Convert step times from seconds to minutes as required by Fall3d
    params['Meteo_time_step'] = time_step/60.


    # Check user specified temporal eruption parameters (hours)
    t0 = params['Start_time_of_meteo_data']
    t_es = params['eruption_start']
    t_ed = params['eruption_duration']
    t_pesd = params['post_eruptive_settling_duration']

    msg = 'Parameter eruption_start must be greater than or equal to 0'
    assert t_es >= 0, msg

    msg = 'Parameter eruption_duration must be greater than 0'
    assert t_ed > 0, msg

    msg = 'Parameter post_eruptive_settling_duration must be greater or equal than 0'
    assert t_es >= 0, msg


    end_runtime = t0 + t_es + t_ed + t_pesd
    msg = 'The sum of parameters eruption_start, eruption_duration and post_eruptive_settling_duration must not cause the end of'
    msg += ' meteorological data to be exceeded. The sum is %f, but the met data ends at %f' % (end_runtime, params['End_time_of_meteo_data'])
    assert end_runtime <= params['End_time_of_meteo_data'], msg

    # Establish Fall3d eruption time parameters in terms of relative variables (hours)
    params['Start_time_of_eruption'] = t0 + t_es
    params['End_time_of_eruption'] = t0 + t_es + t_ed
    params['End_time_of_run'] = end_runtime


def derive_modelling_parameters(params):
    """Compute modelling parameters that can be derived from scenario parameters
    """

    # Assume the lowest atmospheric layer starts at zero
    #params['Z_min'] = 0

    #params['source_type'] = 'plume'                       # only relevant source type
    params['load_units'] = 'kg/m2'                        # only relevant unit
    params['class_load_units'] = 'kg/m2'                  # only relevant unit
    params['total_concentration_units'] = 'kg/m3'         # only relevant unit
    params['z_cummulative_concentration_units'] = 'kg/m2' # only relevant unit
    params['z_maximum_concentration_units'] = 'kg/m3'     # only relevant unit



    # Output (Volcanological input file). Hardwired to standard values
    params['Postprocess_time_interval'] = 1                   # Hours
    params['Postprocess_3D_variables'] = 'No'                 # Yes/No
    params['Postprocess_classes'] = 'No'                      # Yes/No
    params['Track_points'] = 'No'                             # Yes/No

