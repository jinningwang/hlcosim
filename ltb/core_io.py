"""Data IO module."""

import logging
import csv
logger = logging.getLogger(__name__)

io_config = dict(k_df=-4, p_df=0, q_df=0, htb_s=1e4, htb_b=-2)


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
    [k_df, p_df, q_df] = [io_config['k_df'], io_config['p_df'],
                          io_config['q_df']]
    io_flag = False
    try:
        txtr = open(file)
        txtc = txtr.read()
        txtr.close()
        [k, p, q] = [int(i, 10) for i in txtc.split()]  # HEX to DEC
        # --- data conversion ---
        p = p / io_config['htb_s'] + io_config['htb_b']
        q = q / io_config['htb_s'] + io_config['htb_b']
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
    writer.writerow([i * io_config['htb_s'] for i in dataw])
    scsv.close()
    io_flag = True
    msg = "Data write to %s: freq=%d, volt=%f" % (file, dataw[0], dataw[1])
    logger.info(msg)
    return io_flag
