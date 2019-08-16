import os

import mems.protocol.rosco
import mems.diagnostics

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import plotly.figure_factory as ff
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

class LogReader(object):
    def __init__(self):
        self.rosco = mems.protocol.rosco.Rosco()
        self.diagnostics = mems.diagnostics.MemsDiagnostics()
        self.df = pd.DataFrame()
        self.filename = []
        self.filepath = ''
        self.raw = []
        self.version = ''


    def get_version(self):
        return "MEMS ECU ID: " + self.rosco.get_version(self.version)
    
    
    def convert_farenheit_to_celcius(self, f):
        return f - 55 #round(((f - 32) * 5.0 / 9.0),1)


    def combine_high_low_bytes(self, high, low):
        return high + low


    def extract_fault_code(self, x, bitmask, df, result_column):
        faultcode = int(x, base=16)
        df[result_column] = int(faultcode & bitmask)


    def create_dataframe_from_file(self):
        datadict7d = {}
        datadict80 = {}

        i = 0
        version_prefix = 'ECU responded to D0 command with:'

        f = open(self.filepath)
        line = f.readline()
        while line:
            line = f.readline()

            if line.startswith(version_prefix):
                self.version = line[len(version_prefix):].strip()
                
            if len(line) > 50:
                command_code = (line[0:2]).lower()

                for c in self.rosco._dataframes:
                    dataframecmd = c['command']

                    if (dataframecmd == command_code):
                        dataframe = c['fields']
                        line = line.replace(' \n', '').replace('\r', '')
                        statuscodes = line[4:].strip().split(" ")

                        if command_code == '80':
                            datadict80.update({i: pd.Series(statuscodes, index=dataframe)})

                        if command_code == '7d':
                            if 'timestamp' not in dataframe:
                                dataframe.append('timestamp')
                            statuscodes.append(format(i, 'x').zfill(2))

                            datadict7d.update({i: pd.Series(statuscodes, index=dataframe)})
                            # increment index after a 7d command response to complete full dataframe
                            i = i + 1

                        self.raw.append(statuscodes)
        f.close()

        df7d = pd.DataFrame(datadict7d)
        df80 = pd.DataFrame(datadict80)

        return df7d.append(df80)

    
    def exp_display_histogram(self, dimensions, title='', y_axis_label=''):
        self.df = self.df.fillna(0)
        fig = ff.create_distplot([self.df[c] for c in dimensions], dimensions, curve_type='normal')
        return iplot(fig, filename=(f'{self.filename[0]}-{title}')) 
    
    
    def display_graph(self, dimensions, title='', y_axis_label=''):
        data = []

        for dimension in dimensions:
            data.append( 
                go.Scatter(
                    x=self.df['timestamp'],  # assign x as the dataframe column 'x'
                    y=self.df[dimension],
                    name=dimension,
                    #fill='toself',
                    line=dict(shape='spline', smoothing=0.4),
                )
            )

        layout = go.Layout(title=f'{title}',
            xaxis=dict(title='time (s)'),
            yaxis=dict(title=y_axis_label, zeroline=False))

        fig = go.Figure(data=data, layout=layout)

        fig.update_layout(
            xaxis=dict(
                linecolor='rgb(204, 204, 204)',
            ),
            autosize=True,
            showlegend=True,
            plot_bgcolor='rgb(250, 250, 250)'
        )
        
        return iplot(fig, filename=(f'{self.filename[0]}-{dimension}')) 


    def display_histogram(self, dimension, title='', y_axis_label=''):
        fig = px.histogram(self.df, x=dimension, marginal="box")
        fig.update_layout(
            xaxis=dict(
                linecolor='rgb(204, 204, 204)',
            ),
            bargap=0.1,
            autosize=True,
            showlegend=True,
            plot_bgcolor='rgb(250, 250, 250)',
        )
        return iplot(fig, filename=(f'{self.filename[0]}-{dimension}')) 
   

    def display_faults(self):
        report = self.diagnostics.analyse_run(self.df)
        print(report)
        
            
    def display_dimension_stats(self, dimension):
        mx = int(self.df[dimension].max())
        mn = int(self.df[dimension].min())
        me = int(self.df[dimension].mean())
        
        print (f'{dimension:45}{mn:10}{me:10}{mx:10}')
               
    
    def display_dimensions(self):
        self.df['coolant_temperature'] = self.df['coolant_temperature'].rolling(window=5).mean()
                                               
        included_columns = ['engine_speed','coolant_temperature','intake_air_temperature','idle_air_contol_position','map_sensor','lambda_voltage','ignition_advance']
        
        labels = ['dimension','min','mean','max']
        print (f'{labels[0]:45}{labels[1]:>10}{labels[2]:>10}{labels[3]:>10}')
        
        for column in self.df:
            #if column in included_columns:
            try:
                self.display_dimension_stats(column)
            except:
                pass
                
        print('\n')

                
    def remap_memsscan_data(self):
        self.df.rename(columns={
            '#time': 'timestamp', 
            '80x01-02_engine-rpm': 'engine_speed',
            '80x03_coolant_temp': 'coolant_temperature',
            '80x04_ambient_temp': 'ambient_temperature',
            '80x05_intake_air_temp': 'intake_air_temperature',
            '80x06_fuel_temp' : 'fuel_temperature',
            '80x07_map_kpa' : 'map_sensor',
            '80x08_battery_voltage' : 'battery_voltage',
            '80x09_throttle_pot' : 'throttle_pot_voltage',
            '80x0A_idle_switch' : 'idle_switch',
            '80x0C_park_neutral_switch' : 'park_neutral_switch',
            '80x0D-0E_fault_codes' : 'fault_codes',
            '80x0F_idle_set_point' : 'idle_set_point',
            '80x10_idle_hot' : 'idle_decay',
            '80x12_iac_position' : 'idle_air_contol_position',
            '80x13-14_idle_error' : 'idle_speed_deviation',
            '80x15_ignition_advance_offset' : 'ignition_advance_offset',
            '80x16_ignition_advance' : 'ignition_advance',
            '80x17-18_coil_time' : 'coil_time',
            '80x19_crankshaft_position_sensor' : 'crankshaft_position_sensor',
            '7dx01_ignition_switch' : 'ignition_switch',
            '7dx02_throttle_angle' : 'throttle_angle',
            '7dx04_air_fuel_ratio' : 'air_fuel_ratio',
            '7dx05_dtc2' : 'dtc2',
            '7dx06_lambda_voltage' : 'lambda_voltage',
            '7dx07_lambda_sensor_frequency' : 'lambda_frequency',
            '7dx08_lambda_sensor_dutycycle' : 'lambda_dutycycle',
            '7dx09_lambda_sensor_status' : 'lambda_status',
            '7dx0A_closed_loop' : 'loop_indicator',
            '7dx0B_long_term_fuel_trim' : 'long_term_trim',
            '7dx0C_short_term_fuel_trim' : 'short_term_trim',
            '7dx0D_carbon_canister_dutycycle' : 'carbon_canister_purge_valve_duty_cycle',
            '7dx0E_dtc3' : 'dtc3',
            '7dx0F_idle_base_pos' : 'idle_base_position',
            '7dx11_dtc4' : 'dtc4',
            '7dx12_ignition_advance2' : 'ignition_advance_offset',
            '7dx13_idle_speed_offset' : 'idle_speed_offset',
            '7dx14_idle_error2' : 'idle_error',
            '7dx16_dtc5' : 'dtc5',
        }, inplace=True)
        
        
    def save_as_excel(self):
        writer = pd.ExcelWriter(f'{self.filename[0]}.xlsx')
        self.df.to_excel(writer, 'Log Data')
        writer.save()

        
    def read_memsscanfile(self, filepath):
        self.filepath = filepath
        filename = os.path.basename(filepath)
        self.filename = os.path.splitext(filename)
        
        dateparser = lambda x: pd.datetime.strptime(x, "%H:%M:%S")
        self.df = pd.read_csv(self.filepath, parse_dates=['#time'], date_parser=dateparser)
        
        self.remap_memsscan_data()
   

    def read_logfile(self, filepath):
        self.filepath = filepath
        filename = os.path.basename(filepath)
        self.filename = os.path.splitext(filename)
        
        # create a dataframe from the log file
        self.df = self.create_dataframe_from_file()
        
        # prepare and transform the data 
        self.pivot_dataframe()
               
        #self.remove_unknown_fields()
        self.replace_not_a_number_with_zero()
        self.create_decimal_values_from_bytes()
        self.convert_metrics()
            
               
    # remove the unknown fields 
    # i.e those whose columns where their name is still a hex value rather than a label             
    def remove_unknown_fields(self):
        self.df.drop(self.df.filter(regex = '^0x'), axis = 1, inplace = True)
        self.df.drop(self.df.filter(regex = '^80x'), axis = 1, inplace = True)

               
    # replace NaN with zeros
    def replace_not_a_number_with_zero(self):
        self.df = self.df.fillna('00')
          
               
    # pivot the table so that the indexes are now columns, this makes it much
    # easier to create plots and do column analysis
    def pivot_dataframe(self):
        self.df = self.df.transpose()

               
    # combine the 16 bit values into a single value and remove the source fields            
    def create_decimal_values_from_bytes(self): 
        self.df['engine_speed'] = self.combine_high_low_bytes(self.df['engine_speed_high_byte'], self.df['engine_speed_low_byte'])
        self.df.drop(columns=['engine_speed_high_byte', 'engine_speed_low_byte'])

        self.df['idle_speed_deviation'] = self.combine_high_low_bytes(self.df['idle_speed_deviation_high_byte'],self.df['idle_speed_deviation_low_byte'])
        self.df.drop(columns=['idle_speed_deviation_high_byte', 'idle_speed_deviation_low_byte'], inplace = True)

        self.df['coil_time'] = self.combine_high_low_bytes(self.df['coil_time_high_byte'], self.df['coil_time_low_byte'])
        self.df.drop(columns=['coil_time_high_byte', 'coil_time_low_byte'], inplace = True)
            
               
    # convert the metrics to the correct scale
    def convert_metrics(self):
        # convert all the hex strings into integers
        self.df = self.df.apply(lambda x: x.astype(str).map(lambda x: int(x, base=16)))
               
        # battery voltage 0.1V per LSB (e.g. 0x7B == 12.3V)
        self.df['battery_voltage'] = self.df['battery_voltage'].apply(lambda x: x * 0.1) 
               
        # throttle pot. voltage 0.02V per LSB. (e.g. 0xFA == 5.0V)
        self.df['throttle_pot_voltage'] = self.df['throttle_pot_voltage'].apply(lambda x: x * 0.02)
    
        # short term fuel trim (STFL) 1% per LSB
        self.df['short_term_trim'] = self.df['short_term_trim'].apply(lambda x: (x - 100) / 10)
        self.df['long_term_trim'] = self.df['long_term_trim'].apply(lambda x: (x - 128) )
               
        # ignition_advance 0.5 degrees per LSB with range of -24 deg (0x00) to 103.5 deg (0xFF)
        self.df['ignition_advance'] = self.df['ignition_advance'].apply(lambda x: (x / 50) - 24)
        
        self.df['idle_air_contol_position'] = self.df['idle_air_contol_position'].apply(lambda x: (x / 1.8))
        self.df['lambda_voltage'] = self.df['lambda_voltage'].apply(lambda x: (x * 5))
        self.df['throttle_angle'] = self.df['throttle_angle'].apply(lambda x: x * 6 / 10)
        self.df['air_fuel_ratio'] = self.df['air_fuel_ratio'].apply(lambda x: x / 10)
        self.df['idle_speed_offset'] = self.df['idle_speed_offset'].apply(lambda x: (x - 128) * 25)
        
        # coil time, 0.002 milliseconds per LSB (16 bits) 
        self.df['coil_time'] = self.df['coil_time'].apply(lambda x: x / 2000)
                        
        # convert all temperatures to celcius
        self.df['coolant_temperature'] = self.df['coolant_temperature'].apply(self.convert_farenheit_to_celcius)
        self.df['ambient_temperature'] = self.df['ambient_temperature'].apply(self.convert_farenheit_to_celcius)
        self.df['intake_air_temperature'] = self.df['intake_air_temperature'].apply(self.convert_farenheit_to_celcius)
        self.df['fuel_temperature'] = self.df['fuel_temperature'].apply(self.convert_farenheit_to_celcius)