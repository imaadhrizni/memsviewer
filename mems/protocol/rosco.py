# ROSCO - Rover Communication Protocol

class Rosco(object):
    def __init__(self):
        self._version   = 'MNE101070'
        self._connected = False

        self._versions = {
                'MNE101070' : '99 00 02 03',
                'MNE101170' : '99 00 03 03'
            }
            
        
        #
        # The tables below describe the known fields in the data frames
        # that are sent by the ECU in responses to commands 0x7D and 0x80, respectively.
        # Multi-byte fields are sent in big-endian format.
        #

        self._dataframes = [
                {'command' : '7d', 'fields' : ['dataframe_size',
                                               'ignition_switch',
                                               'throttle_angle',
                                               '0x03',
                                               'air_fuel_ratio',
                                               'dtc2',
                                               'lambda_voltage',
                                               'lambda_frequency',
                                               'lambda_duty_cycle',
                                               'lambda_status',
                                               'loop_indicator',
                                               'long_term_trim',
                                               'short_term_trim',
                                               'carbon_canister_purge_valve_duty_cycle',
                                               'dtc3',
                                               'idle_base_position',
                                               '0x10',
                                               'dtc4',
                                               'ignition_advance_offset',
                                               'idle_speed_offset',
                                               'idle_error',
                                               '0x15',
                                               'dtc5',
                                               '0x17',
                                               '0x18',
                                               '0x19',
                                               '0x1A',
                                               '0x1B',
                                               '0x1C',
                                               '0x1D',
                                               '0x1E',
                                               'jack_count_number']},
                {'command' : '80', 'fields' : ['dataframe_size',
                                               'engine_speed_high_byte',
                                               'engine_speed_low_byte',
                                               'coolant_temperature',
                                               'ambient_temperature',
                                               'intake_air_temperature',
                                               'fuel_temperature',
                                               'map_sensor',
                                               'battery_voltage',
                                               'throttle_pot_voltage',
                                               'idle_switch',
                                               'aircon_switch',
                                               'park_neutral_switch',
                                               'coolant_temp_inlet_air_temp_sensor_fault',
                                               'fuel_pump_throttle_pot_circuit_fault',
                                               'idle_set_point',
                                               'idle_decay',
                                               '80x11',
                                               'idle_air_contol_position',
                                               'idle_speed_deviation_high_byte',
                                               'idle_speed_deviation_low_byte',
                                               'ignition_advance_offset',
                                               'ignition_advance',
                                               'coil_time_high_byte',
                                               'coil_time_low_byte',
                                               'crankshaft_position_sensor',
                                               '80x1A',
                                               '80x1B']}
            ]

        self._commands = [
                {'open_fuel_pump_relay' : b'\x01'},
                {'open_ptc_relay'       : b'\x02'},
                {'open_aircond_relay'   : b'\x03'},
                {'close_purge_valve'    : b'\x08'},
                {'open_heater_relay'    : b'\x09'},
                {'reset_all_adjustments': b'\x0f'},
                {'close_fuel_pump_relay': b'\x11'},
                {'close_ptc_relay'      : b'\x12'},
                {'close_aircond_relay'  : b'\x13'},
                {'open_purge_valve'     : b'\x18'},
                {'close_heater_relay'   : b'\x19'},
                {'close_fan_relay'      : b'\x1e'},
                {'request_data_frame_a' : b'\x7d'},
                {'inc_fuel_trim'        : b'\x79'},
                {'dec_fuel_trim'        : b'\x7a'},
                {'inc_fuel_trim_alt'    : b'\x7b'},
                {'dec_fuel_trim_alt'    : b'\x7c'},
                {'request_data_frame_b' : b'\x80'},
                {'inc_idle_decay'       : b'\x89'},
                {'dec_idle_decay'       : b'\x8a'},
                {'inc_idle_speed'       : b'\x91'},
                {'dec_idle_speed'       : b'\x92'},
                {'inc_ignition_advance' : b'\x93'},
                {'dec_ignition_advance' : b'\x94'},
                {'clear_fault_codes'    : b'\xcc'},
                {'reset_ecu'            : b'\xfa'},
                {'heartbeat'            : b'\xf4'},
                {'actuate_fuel_injector': b'\xf7'},
                {'fire_ignition_coil'   : b'\xf8'},
                {'open_iac_by_one_step' : b'\xfd'},
                {'close_iac_by_one_step': b'\xfe'},
                {'current_iac_position' : b'\xff'},
            ]

    
    def get_version(self, memscode):
        for key, value in self._versions.items():
            if value == memscode:
                return key
                
    def get_dataframe(self, command_code):
        for c in self._dataframes:
            if c['command'] == command_code:
                return c['command']

    def get_command_code(self, command_name):
        for c in self._commands:
            if command_name in c:
                return c[command_name]

    @property
    def initialization_sequence(self):
        return [
                   {'tx': b'\xca', 'response': b'\xca'},
                   {'tx': b'\x75', 'response': b'\x75'},
                   {'tx': b'\xd0', 'response': self._version}
               ]

