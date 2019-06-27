import mems.protocol.rosco
import mems.diagnostics

import pandas as pd
import os
import plotly.graph_objs as go
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

        
    def display_graph(self, dimensions, title='', y_axis_label=''):
        data = []

        for dimension in dimensions:
            data.append( 
                go.Scatter(
                    x=self.df['timestamp'],  # assign x as the dataframe column 'x'
                    y=self.df[dimension],
                    name=dimension,
                    connectgaps=True,
                    fill='toself',
                    line=dict(shape='spline', smoothing=0.8),
                )
            )

        layout = go.Layout(title=f'{title}',
            xaxis=dict(title='time (s)'),
            yaxis=dict(title=y_axis_label, zeroline=False))

        fig = go.Figure(data=data, layout=layout)

        return iplot(fig, filename=(f'{self.filename[0]}-{dimension}')) 

    def display_bargraph(df, dimensions, title='', y_axis_label=''):
        data = []

        for dimension in dimensions:
            data.append( 
                go.Bar(
                    x=self.df['timestamp'],  # assign x as the dataframe column 'x'
                    y=self.df[dimension],
                    name=dimension
                )
            )

        layout = go.Layout(title=f'{title}',
            xaxis=dict(title='time (s)'),
            yaxis=dict(title=y_axis_label))

        fig = go.Figure(data=data, layout=layout)

        return iplot(fig, filename=(f'{self.filename[0]}-{dimension}')) 

    def is_faulty(self, dimension):
        return (self.df[dimension].max() > 0)
   
        
    def display_faults(self):
        report = self.diagnostics.analyse_run(self.df)
        print(report)
        
            
    def display_dimension_stats(self, dimension):
        mx = int(self.df[dimension].max())
        mn = int(self.df[dimension].min())
        md = int(self.df[dimension].median())
        
        print (f'{dimension:45}{mn:10}{md:10}{mx:10}')
               
    
    def display_dimensions(self):
        excluded_columns = ['dataframe_size', 'timestamp', '', 
                            'coil_time_low_byte', 'coil_time_high_byte', 
                            'idle_speed_deviation_low_byte', 'idle_speed_deviation_high_byte', 
                            'engine_speed_low_byte', 'engine_speed_high_byte']
        
        print (f"{'name':45}{'min':>10}{'median':>10}{'max':>10}")
        
        for column in self.df:
            if column not in excluded_columns:
                self.display_dimension_stats(column)
               
        
    def save_as_excel(self):
        writer = pd.ExcelWriter(f'{self.filename[0]}.xlsx')
        self.df.to_excel(writer, 'Log Data')
        writer.save()


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
        self.read_fault_codes()
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
               

    # extract the fault codes
    def read_fault_codes(self):
        self.df['coolant_temp_inlet_air_temp_sensor_fault'].apply(lambda x: self.extract_fault_code(x, 0b00000001, self.df, 'coolant_temp_sensor_fault'))
        self.df['coolant_temp_inlet_air_temp_sensor_fault'].apply(lambda x: self.extract_fault_code(x, 0b00000010, self.df, 'inlet_air_temp_sensor_fault'))
        self.df['fuel_pump_throttle_pot_circuit_fault'].apply(lambda x: self.extract_fault_code(x, 0b00000001, self.df, 'fuel_pump_circuit_fault'))
        self.df['fuel_pump_throttle_pot_circuit_fault'].apply(lambda x: self.extract_fault_code(x, 0b01000000, self.df, 'throttle_pot_circuit_fault'))

               
    # convert the metrics to the correct scale
    def convert_metrics(self):
        # convert all the hex strings into integers
        self.df = self.df.apply(lambda x: x.astype(str).map(lambda x: int(x, base=16)))
               
        # battery voltage 0.1V per LSB (e.g. 0x7B == 12.3V)
        self.df['battery_voltage'] = self.df['battery_voltage'].apply(lambda x: x / 10) 
               
        # throttle pot. voltage 0.02V per LSB. (e.g. 0xFA == 5.0V)
        self.df['throttle_pot_voltage'] = self.df['throttle_pot_voltage'].apply(lambda x: x / 200)
    
        # short term fuel trim (STFL) 1% per LSB
        self.df['short_term_trim'] = self.df['short_term_trim'].apply(lambda x: (x - 100) / 10)
               
        # ignition_advance 0.5 degrees per LSB with range of -24 deg (0x00) to 103.5 deg (0xFF)
        self.df['ignition_advance'] = self.df['ignition_advance'].apply(lambda x: (x / 50) - 24)
               
        # coil time, 0.002 milliseconds per LSB (16 bits) 
        self.df['coil_time'] = self.df['coil_time'].apply(lambda x: x / 2000)
                        
        # convert all temperatures to celcius
        self.df['coolant_temperature'] = self.df['coolant_temperature'].apply(self.convert_farenheit_to_celcius)
        self.df['ambient_temperature'] = self.df['ambient_temperature'].apply(self.convert_farenheit_to_celcius)
        self.df['intake_air_temperature'] = self.df['intake_air_temperature'].apply(self.convert_farenheit_to_celcius)
        self.df['fuel_temperature'] = self.df['fuel_temperature'].apply(self.convert_farenheit_to_celcius)