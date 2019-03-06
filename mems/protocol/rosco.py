# ROSCO - Rover Communication Protocol

class Rosco(object):
    def __init__(self):
        self._version   = 'MNE101170'
        self._connected = False

        self._versions = {
                'MNE101070' : b'd099000203',
                'MNE101170' : b'd099000303'
            }

        #
        # The tables below describe the known fields in the data frames
        # that are sent by the ECU in responses to commands 0x7D and 0x80, respectively.
        # Multi-byte fields are sent in big-endian format.
        #

        self._dataframes = [
                {'command' : '7d', 'fields' : ['dataframe_size','0x01','throttle_angle','0x03', '0x04','lambda_voltage','lambda_frequency','lambda_duty_cycle','lambda_status','loop_indicator','long_term_trim','short_term_trim','carbon_canister_purge_valve_duty_cycle','0x0E','idle_base_position','0x10','0x11','0x12','0x13','idle_error','0x15','0x16','0x17','0x18','0x19','0x1A','0x1B','0x1C','0x1D','0x1E','0x1F','']},
                {'command' : '80', 'fields' : ['dataframe_size','engine_speed_high_byte','engine_speed_low_byte','coolant_temperature','ambient_temperature','intake_air_temperature','fuel_temperature','map_sensor','battery_voltage','throttle_pot_voltage','idle_switch','80x0B','park_neutral_switch','coolant_temp_inlet_air_temp_sensor_fault','fuel_pump_throttle_pot_circuit_fault','80x0F','80x10','80x11','idle_air_contol_position','idle_speed_deviation_high_byte','idle_speed_deviation_low_byte','80x15','ignition_advance','coil_time_high_byte','coil_time_low_byte','80x19','80x1A','80x1B']}
            ]

        self._commands = [
                {'open_fuel_pump_relay' : b'01'},
                {'open_ptc_relay'       : b'02'},
                {'open_aircond_relay'   : b'03'},
                {'close_purge_valve'    : b'08'},
                {'open_heater_relay'    : b'09'},
                {'close_fuel_pump_relay': b'11'},
                {'close_ptc_relay'      : b'12'},
                {'close_aircond_relay'  : b'13'},
                {'open_purge_valve'     : b'18'},
                {'close_heater_relay'   : b'19'},
                {'close_fan_relay'      : b'1e'},
                {'request_data_frame_a' : b'7d'},
                {'inc_fuel_trim'        : b'79'},
                {'dec_fuel_trim'        : b'7a'},
                {'inc_fuel_trim_alt'    : b'7b'},
                {'dec_fuel_trim_alt'    : b'7c'},
                {'request_data_frame_b' : b'80'},
                {'inc_idle_decay'       : b'89'},
                {'dec_idle_decay'       : b'8a'},
                {'inc_idle_speed'       : b'91'},
                {'dec_idle_speed'       : b'92'},
                {'inc_ignition_advance' : b'93'},
                {'dec_ignition_advance' : b'94'},
                {'clear_fault_codes'    : b'cc'},
                {'heartbeat'            : b'f4'},
                {'actuate_fuel_injector': b'f7'},
                {'fire_ignition_coil'   : b'f8'},
                {'open_iac_by_one_step' : b'fd'},
                {'close_iac_by_one_step': b'fe'},
                {'current_iac_position' : b'ff'},
            ]

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
                   {'tx': b'ca', 'response': b'ca'},
                   {'tx': b'75', 'response': b'75'},
                   {'tx': b'd0', 'response': self._version}
               ]

