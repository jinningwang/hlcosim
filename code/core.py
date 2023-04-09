"""
Core module of HTB-LTB co-simulation..
"""
import os
import logging
import csv
import time
from collections import OrderedDict

import numpy as np
import pandas as pd

import andes
andes.config_logger(stream_level=50)

logger = logging.getLogger(__name__)

status = OrderedDict([
        ('iter_total', 0), ('iter_fail', 0),
        ('kr', 0), ('k', 0),
        ('v', 0), ('freq', 0), ('p', 0), ('q', 0),
        ('pdef', 0), ('qdef', 0),
        ('tw', 0), ('tr', 0), ('tsim', 0), ('tf', 0),
        ])

scols = list(status.keys())[2:]


def data_io(file, data=None, pdef=None, qdef=None):
    """
    Read or write data from/to a txt file.

    Read data [k, p, q] from file if data is None,
    otherwise write data [freq, volt] to file.

    The read data is converted from HEX to DEC, and converted by linear
    equations as follows:

    p = p / k_htb + b_htb

    q = q / k_htb + b_htb

    Parameters
    ------------
    file: str
        Name of the file to read or write
    data: list or None
        List of data to write, or None if reading data
    pdef: float or None
        Default value of p, will be updated if data is read successfully
    qdef: float or None
        Default value of q, will be updated if data is read successfully

    Returns
    ---------
    out: list or None
        List of read data, or None if writing data
    exit_code: bool
        Flag to indicate if data reading or writing is successful

    Config
    ---------
    kdef: int
        Default value of read counter value k
    k_htb: float
        Conversion factor
    b_htb: float
        Conversion bias
    """
    kdef=-4
    k_htb=1e4
    b_htb=-2

    exit_code = False
    try:
        if data is None:  # read data from file
            txtr = open(file)
            txtc = txtr.read()
            txtr.close()
            [k, p, q] = [int(i, 10) for i in txtc.split()]  # HEX to DEC
            # --- data conversion ---
            p = p / k_htb + b_htb
            q = q / k_htb + b_htb
            # --- update default values ---
            if pdef is not None:
                pdef = p
            if qdef is not None:
                qdef = q
            out = [k, p, q]
            exit_code = True
            msg = "Data read from %s: k=%d, p=%f, q=%f" % (file, k, p, q)
        else:  # write data to file
            exit_code = True
            out = None
            txtc = None
            scsv = open(file, "w")
            writer = csv.writer(scsv)
            writer.writerow([i * k_htb for i in data])
            scsv.close()
            msg = "Data write to %s: freq=%d, volt=%f" % (file, data[0], data[1])
        logger.debug(msg)
    except FileNotFoundError:
        out = [kdef, pdef, qdef] if data is None else None
        msg = "File Not Found Error occurred" + (" data read from %s" % file if data is None else " data write to %s" % file)
        logger.error(msg)
    except ValueError:
        out = [kdef, pdef, qdef] if data is None else None
        msg = "Value Error occurred" + (" data read from %s" % file if data is None else " data write to %s" % file)
        logger.error(msg)
    return out, exit_code


class ACEObj:
    """
    ACE error class.
    """
    def __init__(self, Kp=0, Ki=0, Integral=0):
        """
        Calculate ACE error.

        AGC control is defined by a PI controller as follows:

        Integral = Integral + ACEc

        Raw = -(Kp*ACEc + Ki*Integral)

        where ACEc is the error measured by model ACEc in ANDES,
        and ACEp is the error measured by model ACEp in ANDES.

        Parameters
        ------------
        Kp: float
            Proportional gain
        Ki: float
            Integral gain
        Integral: float
            Initial ntegral value
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Integral = Integral
        self.Raw = -(self.Ki*self.Integral)

    def update(self, ACEc):
        """
        Update ACE error.

        Parameters
        ------------
        ACEc: float
            Input ACE error
        """
        self.Integral += ACEc
        self.Raw = -(self.Kp*ACEc + self.Ki*self.Integral)
        return True


def run(case='ieee39_htb.xlsx', tf=20,
        status=status,
        read_file = 'datar.txt', write_file = 'dataw.txt',
        test_mode=True, AGC_control=True,
        ):
    """
    Run the HTB-LTB co-simulation.

    In test mode, the counter in data IO is force updated without
    interfacing with HTB.

    Parameters
    ------------
    case: str
        Name of the LTB case file
    tf: float
        Simulation end time
    read_file: str
        Name of the file to read
    write_file: str
        Name of the file to write
    test_mode: bool
        Flag to indicate if test mode is on
    AGC_control: bool
        Flag to indicate if AGC control is on

    Returns
    ---------
    ss: andes.core.system.System
        System object after simulation
    cosim_out: pd.DataFrame
        Output data of the simulation
    status: dict
        Cosim status
    """
    # --- set config ---
    config = OrderedDict([
        ('intv_agc', 1),
        ('Kp', 0.005),
        ('Ki', 0.001),
        ('ti', 1),
        ('t_step', 0.05),
        ('itermax_io', 20),
        ('load_switch', True),
        ])
    
    # --- set path ---
    path_proj = os.getcwd()
    path_case = os.path.join(path_proj, 'case')
    path_data = os.path.join(path_proj, 'data')

    read_path = os.path.join(path_data, read_file)
    write_path = os.path.join(path_data, write_file)

    path_out = os.path.join(os.path.abspath('..'), 'output')

    sscase = os.path.join(path_case, case)

    ss = andes.load(sscase,
                    no_output=True,
                    default_config=False,
                    setup=False)

    # --- AGC settings ---
    tgov_idx = 'TGOV1_1'  # TurbineGov idx

    ACE = ACEObj(Kp=config['Kp'], Ki=config['Ki'], Integral=0)

    #  --- HTB variables ---
    pq_htb = 'PQ_2'  # load represents for HTB
    bus_htb = ss.PQ.get(idx=pq_htb, src='bus', attr='v')  # get bus index of HTB
    bus_slack = ss.Slack.bus.v[0]  # get bus index of slack bus

    # add Bus Freq. Measurement to HTB bus
    ss.add('BusFreq', {'idx': 'BusFreq_HTB',
                    'name': 'BusFreq_HTB',
                    'bus': bus_htb,
                    'Tf': 0.02,
                    'Tw': 0.02,
                    'fn': 60})
    ss.add('BusFreq', {'idx': 'BusFreq_Slack',
                    'name': 'BusFreq_Slack',
                    'bus': bus_slack,
                    'Tf': 0.02,
                    'Tw': 0.02,
                    'fn': 60})
    ss.add('Output', {'model': 'GENCLS',
                    'varname': 'omega'})
    ss.add('Output', {'model': 'GENROU',
                    'varname': 'omega'})
    ss.add('Output', {'model': 'Bus',
                    'varname': 'a'})
    ss.add('Output', {'model': 'Bus',
                    'varname': 'v'})
    ss.setup()

    msg_version = f"ANDES version: {andes.__version__}\n"
    msg_io = f"IO path: {path_data}\nOutput data path: {path_out}\n"
    msg_agc = f"Test mode: {test_mode}\n"
    ttl = '{:,}'.format(ss.PQ.p0.v.sum() * ss.config.mva / 1e3)
    msg_ltb = f"LTB: {ss.Bus.n} bus; {ss.StaticGen.n} generator; {ttl} GW load.\n"
    msg_htb = f"HTB: {pq_htb} is connected to bus {bus_htb} in LTB.\n"
    logger.warning(msg_version + msg_io + msg_agc + msg_ltb + msg_htb)

    rows = np.ceil((tf - config['ti'] + 1) / config['t_step'])
    cosim_data = -1 * np.ones((int(rows), len(scols)))

    flag_tc0 = True  # Flag to record `tc0`

    # --- system initial conditions ---

    a0 = ss.Bus.get(idx=bus_slack, src='a', attr='v')  # initial slack bus angle
    p0 = ss.PQ.get(idx=pq_htb, src='p0', attr='v')  # initial HTB bus active power
    q0 = ss.PQ.get(idx=pq_htb, src='q0', attr='v')  # initial HTB bus reactive power

    ss.TDS.config.no_tqdm = 1  # turn off tqdm progress bar
    ss.TDS.config.criteria = 0  # turn off stability criteria

    # set constant power load
    ss.PQ.config.p2p = 1
    ss.PQ.config.q2q = 1
    ss.PQ.config.p2z = 0
    ss.PQ.config.q2z = 0
    ss.PQ.pq2z = 0

    ss.TDS.config.save_every = 0
    ss.TDS.config.save_mode = 'manual'

    ss.PFlow.run()  # solve power flow
    ss.TDS.config.tf = config['ti']
    ss.TDS.run()

    t0_htb = time.time()

    rows = tf / config['t_step']

    logger.warning("LTB ready, start HTB to continue...")

    while (status['kr'] != 11):
        # --- repeat reading data until kr==11 ---
        [status['kr'], status['p'], status['q']], _ = data_io(file=read_path)
        if test_mode:
            status['kr'] = 11  # Force set kr to 11 for test_mode test
        kr0 = status['kr']
    logger.warning("Co-sim initialized.")
    while status['k'] < rows:
        try:
            if flag_tc0:
                tc0 = time.time()  # record clock time
                flag_tc0 = False
            # --- data read ---
            # NOTE: repeat reading data until counter update
            iter_read = 0
            # NOTE: repeat reading data until read counter `status['kr]` update
            t0_htb = time.time()
            while (status['kr'] != kr0 + 1) & (iter_read <= config['itermax_io']):
                [status['kr'], status['p'], status['q']], _ = data_io(file=read_path)
                status['pdef'], status['qdef'] = status['p'], status['q']  # update default value if read successfully
                if test_mode:
                    status['kr'] = kr0 + 1  # Force update kr for test_mode test
                iter_read += 1
            if iter_read > config['itermax_io']:
                status['p'], status['q'] = status['pdef'],  status['qdef']  # use default value if read failed
            tc1 = time.time()  # record clock time
            # NOTE: update cumulative counter if read counter update successfully
            kr0 = status['kr']
            status['k'] += 1
            # --- LTB sim ---
            # --- info ---
            if status['k'] % 200 == 0:
                logger.warning("LTB simulated to %ds..." % ss.TDS.config.tf)
            # --- send data to HTB ---
            f_bus = ss.BusFreq.get(idx='BusFreq_HTB', src='f', attr='v')  # p.u.
            v_bus = ss.Bus.get(idx=bus_htb, src='v', attr='v')  # RMS, p.u.
            dataw = [v_bus, f_bus]  # LTB: voltage, frequency
            data_io(file=write_path, data=dataw)
            tc2 = time.time()  # send end time
            # --- LTB simulation ---
            p_inj = config['load_switch'] * status['p']
            q_inj = config['load_switch'] * status['q']
            # a) set PQ data in LTB
            ss.PQ.set(value=p_inj + p0, idx=pq_htb, src='Ppf', attr='v')
            ss.PQ.set(value=q_inj + q0, idx=pq_htb, src='Qpf', attr='v')
            # b) TDS
            ss.TDS.config.tf += config['t_step']
            # AGC
            if status['k'] * config['t_step'] % config['intv_agc'] == 0:
                ss.TurbineGov.set(src='paux0', idx=tgov_idx, attr='v', value=AGC_control * ACE.Raw)
            ss.TDS.run()
            # If LTB simulation failed, stop the co-simulation
            if ss.exit_code != 0:
                logger.warning("LTB simulation failed at %ds" % ss.TDS.config.tf)
                break
            tc3 = time.time()  # record clock time
            ACE.update(ss.ACEc.ace.v.sum())  # update AGC
            if tc3 - t0_htb > 2 * config['t_step']:
                status['iter_fail'] += 1
            # --- update status ---
            # LTB end time, read time, write time, sim time, freq, voltage
            status = {**status, 'tf': ss.TDS.config.tf, 'tr': tc1 - t0_htb,
          'tw': tc2 - tc1, 'tsim': tc3 - tc2, 'freq': f_bus, 'v': v_bus}

            status['iter_total'] += 1
            #  --- record data ---
            cosim_data[status['k']-1, :] = np.array([status[col] for col in scols])
            # for col in scols:
            #     cosim_data[status['k']-1, scols.index(col)] = status[col]
            # update counter base
            if status['kr'] == 199:
                status['kr'] = 10
                kr0 = 10
            # --- check if end ---
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt received. Exiting...")
            break

    logger.warning(f"Co-sim end at  {np.round(ss.TDS.config.tf, 3)}s.")

    # --- save data ---
    cosim_out = pd.DataFrame(data=cosim_data[:status['iter_total']], columns=scols)
    # Time to datetime
    time_struct = time.localtime(tc0)
    date_string = time.strftime('%Y%m%d_%H%M', time_struct)
    outfile = f'output_{date_string}.csv'
    csv_out = os.path.join(path_out, outfile)

    cosim_out['tall'] = cosim_out['tw'] + cosim_out['tr']+ cosim_out['tsim']
    cosim_out.to_csv(csv_out, index=False, header=True)
    logger.warning(f"Cosim data save as: {outfile}")

    return ss, cosim_out, status


def _ss_setup(ss):
    """
    Setup ANDES system
    """
    
