"""Cosimulation Preprocessing"""

# --- set path ---
path_proj = os.getcwd()
path_case = os.path.join(path_proj, 'case')
path_data = os.path.join(path_proj, 'data')
path_ltb = os.path.join(path_proj, 'core_ltb.py')
filer = os.path.join(path_data, rflie)
filew = os.path.join(path_data, wfile)
path_ehtb = os.path.join(path_data, 'ehtb.py')

case1 = os.path.join(path_case, 'ieee14_htb.xlsx')
case2 = os.path.join(path_case, 'pjm5_htb.xlsx')
case3 = os.path.join(path_case, 'npcc_htb.xlsx')

# --- set case ---
ss = andes.load(case1,
                no_output=True,
                default_config=False,
                setup=False)

#  --- HTB setttings ---

pq_htb = 'PQ_6'  # load represents for HTB
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

ss.setup()

cs_stat = dict(iter_total=0, iter_fail=0,
               ks=1, kb=-11, kr=-1, k=0,
               a_ltb=0, p=0, q=0, tw=0, tr=0)

cs_config = dict(ti=1, t_step=0.05, t_total=30,
                 itermax_io=100, load_switch=True)

cs_col = ['ks', 'kb', 'kr', 'a_ltb', 'p', 'q', 'tw', 'tr']
rows = np.ceil(cs_config['t_total'] / cs_config['t_step'])
cs_num = -1 * np.ones((int(rows), len(cs_col)))

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

ss.PFlow.run()  # solve power flow
ss.TDS.config.tf = cs_config['ti']
ss.TDS.run()
