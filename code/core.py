"""
Core module of hlcosim.
"""
import os
import logging
import csv
import time

import numpy as np
import pandas as pd

import andes
andes.config_logger(stream_level=50)

logger = logging.getLogger(__name__)

io_config = dict(k_df=-4, p_df=0, q_df=0, htb_s=1e4, htb_b=-2)

status = dict(iter_total=0, iter_fail=0,
               kr=-1, k=0,
               v=0, freq=0, p=0, q=0, 
               tw=0, tr=0, tsim=0, tf=0,)

config = dict(ti=1, t_step=0.05,
                 itermax_io=20, load_switch=True)

scols = list(status.keys())[2:]

def data_read(file, config=io_config):
    """
    Read data from a txt file.

    ``k``, ``p``, and ``q`` are the counter, active power,
    and reactive power, respectively.

    Parameters
    ------------
    file: str
        Name of the file to read
    config: dict
        Configuration dictionary

    Returns
    ---------
    out: list
        List of read data, [k, p, q]
    txtc: str
        Raw text read from file
    io_flag: bool
        Flag to indicate if data reading is successful
    """
    [k_df, p_df, q_df] = [config['k_df'], config['p_df'],
                          config['q_df']]
    io_flag = False
    try:
        txtr = open(file)
        txtc = txtr.read()
        txtr.close()
        # HEX to DEC  # NOTE: previous version: [k, p, q] = [int(i, 10) for i in txtc.split()]
        [k, p, q] = [int(i, 10) for i in txtc.split()]
        # --- data conversion ---
        p = p / config['htb_s'] + config['htb_b']
        q = q / config['htb_s'] + config['htb_b']
        out = [k, p, q]
        io_flag = True
        msg = "Data read from %s: k=%d, p=%f, q=%f" % (file, k, p, q)
    except FileNotFoundError:
        out = [k_df, p_df, q_df]
        txtc = 'ERROR: File Not Found'
        msg = "File Not Found Error occured data read from %s error" % file
    except ValueError:
        out = [k_df, p_df, q_df]
        txtc = 'ERROR: Value Error'
        msg = "Value Error occured data read from %s error" % file
    logger.info(msg)
    return out, txtc, io_flag


def data_write(dataw, file, config=io_config):
    """
    Write data into a txt file.

    ``k``, ``p``, and ``q`` are the counter, active power,
    and reactive power, respectively.

    Parameters
    ------------
    dataw: list
        list of data to write
    file: str
        name of the file to write
    config: dict
        configuration dictionary

    Returns
    ---------
    io_flag: bool
        Flag to indicate if data writting is successful
    """
    io_flag = False
    scsv = open(file, "w")
    writer = csv.writer(scsv)
    writer.writerow([i * config['htb_s'] for i in dataw])
    scsv.close()
    io_flag = True
    msg = "Data write to %s: freq=%d, volt=%f" % (file, dataw[0], dataw[1])
    logger.info(msg)
    return io_flag


def run(case='ieee39_htb.xlsx', tf=20,
        read_file = 'datar.txt', write_file = 'dataw.txt',
        test_mode=True, AGC_control=True, **kwargs):
    """
    Run the simulation.

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
    intv_agc = 4  # interval of AGC

    tgov_idx = 'TGOV1_1'  # TurbineGov idx

    # ACE vars for PI controller
    ACE_integral = 0
    ACE_raw = 0
    Kp = 0.005  # 0.05
    Ki = 0.001

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
    msg_io = f"IO path: {path_data}\n"
    msg_agc = f"Test mode: {test_mode}\n"
    msg_htb = f"HTB: {pq_htb} is connected to bus {bus_htb} in LTB.\n"
    logger.warning(msg_version + msg_io + msg_agc + msg_htb)

    rows = np.ceil((tf - config['ti'] + 1) / config['t_step'])
    cs_num = -1 * np.ones((int(rows), len(scols)))

    const_freq = 2 * np.pi * ss.config.freq  # constant to calculate bus angle
    flag_init = True  # Flag to indicate the very first iteration
    flag_tc0 = True  # Flag to record `tc0`

    flag_datar = False  # Flag to indicate if data read is successful
    flag_dataw = False  # Flag to indicate if data write is successful

    flag_base = True  # Flag t0 update counter base

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
    k0 = 0

    logger.warning("LTB ready, start HTB to continue...")

    while (status['kr'] != 11):
        # --- repeat reading data until kr==11 ---
        [status['kr'], status['p'], status['q']], txtc, flag_datar = data_read(file=read_path, config=io_config)
        if test_mode:
            status['kr'] = 11  # Force set kr to 11 for test_mode test
        kr0 = status['kr']
        k0 = status['k']
        # --- reset io_config default values ---
        [io_config['p_df'], io_config['q_df']] = [status['p'], status['q']]
    flag_init = False  # Turn off init_flag after first iteration
    logger.warning("Co-sim initialized.")
    while status['k'] < rows:
        if flag_tc0:
            tc0 = time.time()  # record clock time
            flag_tc0 = False
        # --- data read ---
        # NOTE: repeat reading data until counter update
        iter_read = 0
        k0 = status['k']
        # NOTE: repeat reading data until read counter `status['kr]` update
        t0_htb = time.time()
        while (status['kr'] != kr0 + 1) & (iter_read <= config['itermax_io']):
            [status['kr'], status['p'], status['q']], txtc, flag_datar = data_read(file=read_path, config=io_config)
            if test_mode:
                status['kr'] = kr0 + 1  # Force update kr for test_mode test
            [io_config['p_df'], io_config['q_df']] = [status['p'], status['q']]
            iter_read += 1
        if iter_read > config['itermax_io']:
            status['p'], status['q'] = io_config['p_df'], io_config['q_df']
        tc1 = time.time()  # record clock time
        # NOTE: update cumulative counter if read counter update successfully
        kr0 = status['kr']
        k0 = status['k']
        status['k'] += 1
        # --- LTB sim ---
        # --- info ---
        if np.mod(status['k'], 200) == 0:
            logger.warning("LTB simulated to %ds" % ss.TDS.config.tf)
        # --- send data to HTB ---
        # NOTE: Make sure `BusFreq` is connected to the load bus
        f_bus = ss.BusFreq.get(idx='BusFreq_HTB', src='f', attr='v')  # p.u.
        v_bus = ss.Bus.get(idx=bus_htb, src='v', attr='v')  # RMS, p.u.
        dataw = [v_bus, f_bus]  # LTB: voltage, frequency
        data_write(dataw=dataw, file=write_path, config=io_config)
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
        if status['k'] * config['t_step'] % intv_agc == 0:
            ss.TurbineGov.set(src='paux0', idx=tgov_idx, attr='v', value=AGC_control * ACE_raw)
        ss.TDS.run()
        if ss.exit_code != 0:
            logger.warning("LTB simulation failed at %ds" % ss.TDS.config.tf)
            break
        tc3 = time.time()  # record clock time
        # NOTE: tf_htb is the end time of last round
        # update AGC PI Controller
        ACE_integral = ACE_integral + ss.ACEc.ace.v.sum()
        ACE_raw = -(Kp*ss.ACEc.ace.v.sum() + Ki*ACE_integral)
        if tc3 - t0_htb > 2 * config['t_step']:
            status['iter_fail'] += 1
        status['tf'] = ss.TDS.config.tf  # LTB end time
        status['tr'] = tc1 - t0_htb  # read time
        status['tw'] = tc2 - tc1  # write time
        status['tsim'] = tc3 - tc2  # write time
        status['freq'] = f_bus  # freq of HTB bus
        status['v'] = v_bus  # freq of HTB bus
        # update HTB time
    #     t0_htb += config['t_step']
        status['iter_total'] += 1
        flag_base = True
        #  --- record data ---
        for col in scols:
            cs_num[status['k']-1, scols.index(col)] = status[col]
        # update counter base
        if flag_base & (status['kr'] == 199):
            status['kr'] = 10
            kr0 = 10
            flag_base = False

    logger.warning("Co-sim end.")

    # --- save data ---
    cosim_out = pd.DataFrame(data=cs_num[:status['iter_total']], columns=scols)
    # Time to datetime
    time_struct = time.localtime(tc0)
    date_string = time.strftime('%Y%m%d_%H%M', time_struct)
    outfile = f'output_{date_string}.csv'
    csv_out = os.path.join(path_out, outfile)

    cosim_out['tall'] = cosim_out['tw'] + cosim_out['tr']+ cosim_out['tsim']
    cosim_out.to_csv(csv_out, index=False, header=True)
    logger.warning(f"Co-sim data save as: {csv_out}")

    return ss, cosim_out, status
