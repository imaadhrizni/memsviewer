class MemsDiagnostics(object):
    def __init__(self):
        self.df = None
        self.faults = []
        self.run_length = 0
        self.warm_engine_run = None
        self.warm_run_length = 0
    
    def analyse_run(self, df):
        self.df = df
        self.faults = []
        self.run_length = self.df['engine_speed'].count()
        
        self.analyse_sensor_faults()
        self.analyse_derived_faults()
        
        return self.create_analysis_report()
        
        
    def create_analysis_report(self):
        report = ''
        
        if len(self.faults) > 0:
            for fault in self.faults:
                report = report + self.read_analysis_response(fault) + '\n\n'
        else:
            report = 'No faults'
            
        return report
    
            
    def read_analysis_response(self, fault):
        filename = './mems/faults/' + fault + '.md'
        
        with open(filename, 'r') as responsefile:
            response = responsefile.read()
            
        return response
    
    
    
    def is_sensor_faulty(self, dimension):
        return (self.df[dimension].max() > 0)
   
        
    
    def analyse_sensor_faults(self):
        if self.is_sensor_faulty('coolant_temp_sensor_fault'):
            self.faults.append('coolant_temp_sensor_fault')
            
        if self.is_sensor_faulty('inlet_air_temp_sensor_fault'):
            self.faults.append('inlet_air_temp_sensor_fault')
        
        if self.is_sensor_faulty('fuel_pump_circuit_fault'):
            self.faults.append('fuel_pump_circuit_fault')
            
        if self.is_sensor_faulty('throttle_pot_circuit_fault'):
            self.faults.append('throttle_pot_circuit_fault')
            
            
    def analyse_derived_faults(self):   
        if self.df['map_sensor'].median() > 90:
            self.faults.append('map_sensor_fault')
            
        self.get_warm_engine_dataset()
        
        # determine if the engine got up to operating temperature
        if (self.warm_run_length > 0):
            stable_idle = self.warm_engine_run['engine_speed'].quantile(0.5)
            stable_idle = self.df[(self.df['engine_speed'] >= 100) & (self.df['engine_speed'] <= 1000)]

            # determine if the map sensor readings are high when idling warm
            if (stable_idle['map_sensor'].median() > 45 and self.df['map_sensor'].median() <= 90):
                self.faults.append('map_sensor_high')

            # determine if the idle air readings are high when idling warm
            if stable_idle['idle_air_contol_position'].median() > 50:
                self.faults.append('idle_air_control_high')

            # if the engine is running at operating temperature but the rpm
            # is still over 1000 then the idle speed is too high
            if self.warm_engine_run['engine_speed'].quantile(0.5) > 1000:
                self.faults.append('idle_speed_high')
        else:
            # if the engine ran for more than 5 minutes and still isn't warm then
            # indicate a thermostat fault
            if self.run_length > 300:
                self.faults.append('thermostat_fault')

        
    def get_warm_engine_dataset(self):
        # get relevant data once the engine is warm
        self.warm_engine_run = self.df[(self.df['coolant_temperature'] >= 75)]
        self.warm_run_length = self.warm_engine_run['coolant_temperature'].count()
   