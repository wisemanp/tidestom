#!/usr/bin/env python

import os
import sys
import json
import argparse
import pandas as pd

import NGSF
import zipfile
from pathlib import Path
bank_dir = Path(NGSF.__path__[0], 'bank')

def download_templates_bank():
    """Downloads the WISeREP templates bank.
    """
    print('Downloading WISeREP templates bank... (this is only done once)')
    os.system("git clone https://github.com/temuller/superfit_bank.git")

    print('Extracting zip file into local installation of NGSF...')
    file_path = 'superfit_bank/supyfit_bank.zip'
    ngsf_path = NGSF.__path__[0]

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(ngsf_path)

    os.system("rm -rf superfit_bank")

def create_parameters_file(args):
    """Creates a NGSF parameters file.

    Parameters
    ----------
    args : ~argparse.args
        Input parameters
    """
    if args.z_exact==0:
        ngsf_dict = {"use_exact_z" : 0}
    else:
        ngsf_dict = {"use_exact_z" : 1}
    ngsf_dict.update(args.__dict__)
    temp_dict = {"temp_sn_tr"  : ["IIb-flash", "computed", "Ia 02es-like", "Ia-02cx like", "TDE He", "Ca-Ia",
                                "Ia-CSM-(ambigious)", "II", "super_chandra", "SLSN-II", "IIn", "FBOT", "Ibn",
                                "SLSN-IIn", "Ia 91T-like", "IIb", "TDE H", "SN - Imposter", "II-flash", "ILRT",
                                "Ia 99aa-like", "Ic", "SLSN-I", "Ia-pec", "Ib", "Ia-CSM", "Ia-norm", "SLSN-Ib",
                                "TDE H+He", "Ia 91bg-like", "Ca-Ib", "Ia-rapid", "Ic-BL", "Ic-pec", "SLSN-IIb"],

                 "temp_gal_tr" : ["E","S0","Sa","Sb","SB1","SB2","SB3","SB4","SB5","SB6","Sc"]
                 }
    ngsf_dict.update(temp_dict)

    with open('parameters.json', 'w') as fp:
        json.dump(ngsf_dict, fp)

def create_run_file():
    with open('run.py', 'w') as outfile:
        outfile.write("from NGSF.sf_class import Superfit\n\n")
        outfile.write("supernova = Superfit()\n")
        outfile.write("supernova.superfit()")

def create_temp_files():
    # peak MJDs file
    mjd_max_dict = {'Name': {0: '2010jl', 1: '2008aw', 2: '2009ig', 3: '1999el', 4: '2014C', 5: 'iPTF14atg', 6: '2010ae', 7: '2013fs', 8: '2011fe', 9: '2008es', 10: '2012aw', 11: '2009iz', 12: '2012cg', 13: '2005gj', 14: '2008aq', 15: '2007ke', 16: '2016fnl', 17: '2012fr', 18: '2010et', 19: 'Gaia16apd', 20: 'PS1-12sk', 21: '2016esw', 22: '2010al', 23: 'iPTF14bdn', 24: '2009Y', 25: '2016hgs', 26: 'SN2010gx', 27: '2012ht', 28: 'PTF09dav', 29: '2005hk', 30: '2009kr', 31: '2006aj', 32: '2010X', 33: 'iPTF13ajg', 34: '2012Z', 35: '2016bkv', 36: '1994D', 37: '2013fs', 38: '2006fo', 39: '2011ke', 40: '2008D', 41: '2017egm', 42: '2017erp', 43: '2007C', 44: '2007sr', 45: '2006gy', 46: 'LSQ14mo', 47: '2008ax', 48: '2011dh', 49: '2015bn', 50: 'PTF10ops', 51: '2018bsz', 52: '2012ca', 53: 'PTF11kx', 54: '2016bkv', 55: '2013ej', 56: '2011hw', 57: 'iPTF15eqv', 58: 'PTF12bho', 59: '2019bkc', 60: 'PTF11kmb', 61: '2012hn', 62: '2005E', 63: 'SN2007bi', 64: 'PTF10nmn', 65: 'PTF10bfz', 66: 'iPTF13ehe', 67: 'LSQ14an', 68: 'PTF12dam', 69: '2012il', 70: 'PTF09cnd', 71: 'PTF10aagc', 72: '2013cu', 73: '2012dy', 74: '2011fu', 75: '1993J', 76: '2013df', 77: '2001ig', 78: 'PS15bgt', 79: '1996cb', 80: '2003jd', 81: 'PTF10vgv', 82: '2018gep', 83: '2002ap', 84: '2014cp', 85: '2003dh', 86: '1998bw', 87: '2002ic', 88: '2018cxk', 89: '2002cx', 90: '2005bl', 91: '2016ije', 92: '1999by', 93: '2015ac', 94: '1991bg', 95: '2005bf', 96: '2004gq', 97: '2015ah', 98: '2006ep', 99: '2004ao', 100: '2005ek', 101: 'PISN', 102: '2013dy', 103: '2011by', 104: '2012cu', 105: '2015N', 106: '2008fq', 107: 'ASASSN-15og', 108: '2002bu', 109: '2005cp', 110: '2000eo', 111: '2013U', 112: '1991T', 113: '2017pp', 114: '2018hfr', 115: '2019ofm', 116: '2016hnk', 117: '2019hge', 118: '2002bj', 119: 'ASASSN-14ae', 120: '2019ahk', 121: '2018hyz', 122: 'ASASSN-15oi', 123: 'PS1-10jh', 124: '1999aa', 125: 'PTF10tpz', 126: 'PTF10jwd', 127: 'PTF10fel', 128: 'PTF10qaf', 129: 'PTF10scc', 130: 'iPTF16axa', 131: 'ASASSN-14li', 132: '2019qiz', 133: '2018dyb', 134: 'AT2018cow', 135: '2007J', 136: '2013bh', 137: '2000cx', 138: 'CSS121015', 139: '2013hx', 140: '2017ifu', 141: '2016iks', 142: '2017eby', 143: '2019fcg', 144: '2020agp', 145: '2019ahd', 146: '2000ch', 147: '2009dc', 148: '2006gz', 149: '2012dn', 150: '2007if', 151: '2002es', 152: 'PTF10acdh', 153: 'iPTF14flu', 154: '2014cn', 155: 'iPTF15crj', 156: '2006jc', 157: '2005la', 158: 'PTF11rfh', 159: '2015G', 160: '2010md', 161: '2018hna', 162: '2002hh', 163: '1999br', 164: '2007od', 165: '1999em', 166: '2003ed', 167: '2003gd', 168: '1987a', 169: '2014G', 170: '2017be', 171: '2015dl', 172: 'PTF10fqs', 173: '2019abn', 174: '2004gt', 175: '2014L', 176: '1994I', 177: '2007ce', 178: '2004dn', 179: '2004gk', 180: '2013ek', 181: '2007gr', 182: '2013fs_early', 183: '2014G_early', 184: '2016bkv_early', 185: 'iPTF15crj_early', 186: '2014cn_early', 187: '2019vqd_early', 188: 'iPTF14flu_early', 189: '2013cu_early'},
                    'mjd_peak': {0: 55487.0, 1: 54528.0, 2: 55079.3107155547, 3: 51485.6757463686, 4: 56668.6559015949, 5: 56798.082764132, 6: 55252.0, 7: 56575.8076165291, 8: 55814.8564557435, 9: 54600.0, 10: 56010.7442939999, 11: 55100.9323969856, 12: 56081.6794259454, 13: 53660.3401959689, 14: 54530.2812499765, 15: 54366.4831693866, 16: 57631.0422405448, 17: 56243.0366633461, 18: 55355.435932605, 19: 57547.1636159563, 20: 56013.0, 21: 57613.6993591156, 22: 55281.1832611801, 23: 56822.3911543349, 24: 54875.6443324066, 25: 57681.0, 26: 55279.6344975706, 27: 56295.1908106931, 28: 55053.6911240756, 29: 53683.9049643873, 30: 55145.2316234415, 31: 53784.0, 32: 55239.7696225056, 33: 56404.7994225954, 34: 55966.8117533206, 35: 57474.5414659432, 36: 49431.8024541304, 37: 56575.8076165291, 38: 54008.0, 39: 55679.9439704746, 40: 54488.5667521228, 41: 57925.5840952998, 42: 57934.9159437337, 43: 54115.0, 44: 54450.0, 45: 54034.8998260016, 46: 56697.0, 47: 54546.2321482847, 48: 55729.3541238184, 49: 57098.6553710773, 50: 55398.0, 51: 58267.0, 52: 56052.0, 53: 55590.0, 54: 57474.5414659432, 55: 56507.608217682, 56: 55903.4245502448, 57: -1.0, 58: 55990.0, 59: 58546.9, 60: 55800.0, 61: 56032.0, 62: 53387.0, 63: 54145.0, 64: -1.0, 65: 55250.0, 66: 56667.0, 67: 56660.0, 68: 56090.0, 69: 55978.0, 70: 55084.0, 71: -1.0, 72: 56422.0, 73: -1.0, 74: 55846.0, 75: 49094.0, 76: 56467.0, 77: -1.0, 78: 57200.0, 79: 50450.0, 80: 52943.0, 81: 55464.0, 82: 58376.0, 83: 52311.0, 84: -1.0, 85: 52727.0, 86: 50942.0, 87: 52605.0, 88: -1.0, 89: 52417.0, 90: 53483.0, 91: -1.0, 92: 51308.0, 93: -1.0, 94: -1.0, 95: 53498.0, 96: 53357.0, 97: 57241.0, 98: 53986.0, 99: 53075.0, 100: 53640.0, 101: -1.0, 102: 56500.0, 103: 55690.0, 104: -1.0, 105: 57221.0, 106: 54728.0, 107: 57250.0, 108: 52367.0, 109: 53559.0, 110: 51875.0, 111: -1.0, 112: 48375.0, 113: 57781.0, 114: -1.0, 115: 58722.0, 116: 57690.0, 117: 58695.22, 118: 52334.0, 119: 56693.0, 120: -1.0, 121: 58432.0, 122: 57248.0, 123: 55389.0, 124: 51232.0, 125: -1.0, 126: -1.0, 127: 55290.0, 128: -1.0, 129: 55428.0, 130: 57537.0, 131: 56983.6, 132: 58763.0, 133: 58340.0, 134: 58315.0, 135: 54123.0, 136: 56385.0, 137: 51753.0, 138: 56226.0, 139: 56709.0, 140: -1.0, 141: -1.0, 142: -1.0, 143: -1.0, 144: -1.0, 145: 58523.0, 146: -1.0, 147: 54946.0, 148: 54021.0, 149: 56133.0, 150: 54357.0, 151: 52518.0, 152: -1.0, 153: -1.0, 154: 56771.0, 155: -1.0, 156: 54021.0, 157: 53710.0, 158: 55911.0, 159: 57107.0, 160: 55369.0, 161: 58501.0, 162: 52581.0, 163: 51286.0, 164: 54411.0, 165: 51482.0, 166: -1.0, 167: 52807.0, 168: 46855.0, 169: 56678.0, 170: 57763.0, 171: -1.0, 172: 55313.0, 173: 58530.0, 174: 53356.0, 175: 56693.0, 176: 49449.0, 177: 54227.0, 178: 53223.0, 179: 53338.0, 180: -1.0, 181: 54336.0, 182: 56575.8076165291, 183: 56678.0, 184: 57474.5414659432, 185: -1.0, 186: 56771.0, 187: -1.0, 188: -1.0, 189: 56422.0}, 'band_peak': {0: 'V', 1: 'B', 2: 'B', 3: 'B', 4: 'B', 5: 'B', 6: 'B', 7: 'B', 8: 'B', 9: 'B', 10: 'B', 11: 'B', 12: 'B', 13: 'g', 14: 'B', 15: 'R', 16: 'g', 17: 'B', 18: 'g', 19: 'B', 20: 'g', 21: 'B', 22: 'B', 23: 'B', 24: 'B', 25: 'g', 26: 'B', 27: 'B', 28: 'R', 29: 'B', 30: 'B', 31: 'B', 32: 'r', 33: 'R', 34: 'B', 35: 'B', 36: 'B', 37: 'B', 38: 'V', 39: 'V', 40: 'B', 41: 'B', 42: 'B', 43: 'B', 44: 'B', 45: 'R', 46: 'r', 47: 'B', 48: 'B', 49: 'B', 50: 'g', 51: 'r', 52: 'R', 53: 'B', 54: 'B', 55: 'B', 56: 'B', 57: '-', 58: 'r', 59: 'g', 60: 'r', 61: 'V', 62: 'V', 63: 'V', 64: '-', 65: 'B', 66: 'g', 67: 'V', 68: 'B', 69: 'g', 70: 'r', 71: '-', 72: 'V', 73: '-', 74: 'B', 75: 'B', 76: 'B', 77: '-', 78: 'B', 79: 'B', 80: 'B', 81: 'R', 82: 'V', 83: 'B', 84: '-', 85: 'B', 86: 'B', 87: 'B', 88: '-', 89: 'B', 90: 'B', 91: '-', 92: 'B', 93: '-', 94: '-', 95: 'B', 96: 'B', 97: 'B', 98: 'B', 99: 'B', 100: 'B', 101: '-', 102: 'B', 103: 'B', 104: '-', 105: 'B', 106: 'B', 107: 'B', 108: 'B', 109: 'B', 110: 'B', 111: '-', 112: 'B', 113: 'B', 114: '-', 115: 'r', 116: 'B', 117: 'g', 118: 'B', 119: 'B', 120: '-', 121: 'B', 122: 'B', 123: 'g', 124: 'B', 125: '-', 126: '-', 127: 'R', 128: '-', 129: 'R', 130: 'B', 131: 'B', 132: 'g', 133: 'B', 134: 'B', 135: 'V', 136: 'V', 137: 'B', 138: 'B', 139: 'B', 140: '-', 141: '-', 142: '-', 143: '-', 144: '-', 145: 'g', 146: '-', 147: 'B', 148: 'B', 149: 'B', 150: 'B', 151: 'B', 152: '-', 153: '-', 154: 'B', 155: '-', 156: 'B', 157: 'B', 158: 'r', 159: 'B', 160: 'B', 161: 'B', 162: 'V', 163: 'B', 164: 'B', 165: 'B', 166: '-', 167: 'B', 168: 'B', 169: 'B', 170: 'B', 171: '-', 172: 'g', 173: 'B', 174: 'B', 175: 'B', 176: 'B', 177: 'B', 178: 'B', 179: 'B', 180: '-', 181: 'B', 182: 'B', 183: 'B', 184: 'B', 185: '-', 186: 'B', 187: '-', 188: '-', 189: 'V'},
                    'isupperlimit': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14: 0, 15: 0, 16: 0, 17: 0, 18: 0, 19: 0, 20: 0, 21: 0, 22: 0, 23: 0, 24: 0, 25: 0, 26: 0, 27: 0, 28: 0, 29: 0, 30: 0, 31: 0, 32: 0, 33: 0, 34: 0, 35: 0, 36: 0, 37: 0, 38: 0, 39: 0, 40: 0, 41: 0, 42: 0, 43: 0, 44: 1, 45: 0, 46: 0, 47: 0, 48: 0, 49: 0, 50: 0, 51: 0, 52: 1, 53: 0, 54: 0, 55: 0, 56: 0, 57: 0, 58: 0, 59: 0, 60: 0, 61: 0, 62: 0, 63: 0, 64: 0, 65: 1, 66: 0, 67: 1, 68: 0, 69: 1, 70: 0, 71: 0, 72: 0, 73: 0, 74: 0, 75: 0, 76: 0, 77: 0, 78: 1, 79: 0, 80: 0, 81: 0, 82: 0, 83: 0, 84: 0, 85: 1, 86: 0, 87: 0, 88: 0, 89: 0, 90: 0, 91: 0, 92: 0, 93: 0, 94: 0, 95: 0, 96: 0, 97: 0, 98: 0, 99: 1, 100: 0, 101: 0, 102: 0, 103: 0, 104: 0, 105: 0, 106: 0, 107: 1, 108: 0, 109: 0, 110: 0, 111: 0, 112: 0, 113: 1, 114: 0, 115: 0, 116: 0, 117: 0, 118: 1, 119: 1, 120: 0, 121: 1, 122: 1, 123: 0, 124: 0, 125: 0, 126: 0, 127: 0, 128: 0, 129: 0, 130: 1, 131: 1, 132: 0, 133: 0, 134: 1, 135: 1, 136: 0, 137: 0, 138: 0, 139: 0, 140: 0, 141: 0, 142: 0, 143: 0, 144: 0, 145: 1, 146: 0, 147: 0, 148: 0, 149: 0, 150: 0, 151: 0, 152: 0, 153: 0, 154: 1, 155: 0, 156: 1, 157: 1, 158: 0, 159: 1, 160: 0, 161: 0, 162: 1, 163: 1, 164: 1, 165: 1, 166: 0, 167: 1, 168: 1, 169: 0, 170: 1, 171: 0, 172: 1, 173: 0, 174: 1, 175: 0, 176: 0, 177: 1, 178: 0, 179: 1, 180: 0, 181: 0, 182: 0, 183: 0, 184: 0, 185: 0, 186: 1, 187: 0, 188: 0, 189: 0}}

    mjd_max_df = pd.DataFrame(mjd_max_dict)
    mjd_max_file = Path(NGSF.__path__[0], 'mjd_of_maximum_brightness.csv')
    mjd_max_df.to_csv(mjd_max_file, index=False)

def run_ngsf():
    os.system('python run.py parameters.json')

# remove temporary files
def remove_file(file):
    try:
        os.remove(file)
    except:
        pass

def clean_temp_files():
    remove_file('parameters.json')
    remove_file('run.py')
    #remove_file('NGSF/mjd_of_maximum_brightness.csv')

def main(args=None):
    description = "Next Generation SuperFit script by T. Müller-Bravo"
    usage = "run_ngsf <object_to_fit> [options]"

    if not args:
        args = sys.argv[1:] if sys.argv[1:] else ["--help"]

    parser = argparse.ArgumentParser(prog='run_ngsf',
                                     usage=usage,
                                     description=description,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter
                                     )
    parser.add_argument("object_to_fit",
                        #dest="object_to_fit",
                        action="store",
                        type=str,
                        help="The object to analyze."
                        )

    # redshift
    #parser.add_argument("--use_exact_z",
    #                    dest="use_exact_z",
    #                    action="store",
    #                    default=1,
    #                    type=int,
    #                    help=("Can be 1 (yes) or 0 (no). Determines wether the redshift will be an exact number or an array.")
    #                    )
    parser.add_argument("-z",
                        "--z_exact",
                        dest="z_exact",
                        action="store",
                        default=0,
                        type=float,
                        help=("Exact redshift value that will be used if different from '0'")
                        )
    parser.add_argument("--z_range_begin",
                        dest="z_range_begin",
                        action="store",
                        default=0,
                        type=float,
                        help=("Redshift value to begin the redshift array to look for the best fit.")
                        )
    parser.add_argument("--z_range_end",
                        dest="z_range_end",
                        action="store",
                        default=0.1,
                        type=float,
                        help=("Redshift value to end the redshift array to look for the best fit.")
                        )
    parser.add_argument("--z_int",
                        dest="z_int",
                        action="store",
                        default=0.01,
                        type=float,
                        help=("Redshift step to create the redshift array to look for the best fit.")
                        )

    # resolution
    parser.add_argument("-r"
                        "--resolution",
                        dest="resolution",
                        action="store",
                        default=10,
                        type=float,
                        help=("""The resolution of the fit, the default is 10Å, however, if the spectra is 
                              of lower quality then the fit will be performed automatically at 30Å.""")
                        )

    # galaxy prop.
    parser.add_argument("--lower_lam",
                        dest="lower_lam",
                        action="store",
                        default=0,
                        type=float,
                        help=("Lower bound for wavelength over which to perform the fit.")
                        )
    parser.add_argument("--upper_lam",
                        dest="upper_lam",
                        action="store",
                        default=0,
                        type=float,
                        help=("""Upper bound for wavelength over which to perform the fit, if this is equal to 'lower_lam' 
                              then the wavelength range will be chosen automatically as that of the object to fit ± 300Å""")
                        )

    # others
    parser.add_argument("--error_spectrum",
                        dest="error_spectrum",
                        action="store",
                        default="sg",
                        type=str,
                        help=("""refers to the type of routine used to perform the calculation of the error spectrum. The recommended 
                              one is sg Savitzky-Golay, there is also the option of linear estimation and the option included in which 
                              the user can use the error spectrum that comes with an object if he wants to, however, this is not recommended.""")
                        )
    parser.add_argument("-s",
                        "--saving_results_path",
                        dest="saving_results_path",
                        action="store",
                        default="",
                        type=str,
                        help=("Path in which to save the performed fits, the default one is the superfit folder.")
                        )
    parser.add_argument("--minimum_overlap",
                        dest="minimum_overlap",
                        action="store",
                        default=0.7,
                        type=float,
                        help=("Minimum percentage overlap between the template and the object of interest. Recommendation is for this to stay near 0.7")
                        )

    # plots
    parser.add_argument("-p"
                        "--show_plot",
                        dest="show_plot",
                        action="store",
                        default=1,
                        type=int,
                        choices=[0, 1],
                        help=("To show the plotted fit or no, the default being 1, to show.")
                        )
    parser.add_argument("--how_many_plots",
                        dest="how_many_plots",
                        action="store",
                        default=5,
                        type=int,
                        help=("Number of plots to show if the user wants to show, if the 'show' is zero then 'n' has no effect.")
                        )

    # masking
    parser.add_argument("--mask_galaxy_lines",
                        dest="mask_galaxy_lines",
                        action="store",
                        default=1,
                        type=int,
                        choices=[0, 1],
                        help=("""Either 1 or 0, masks the galaxy lines for both the template bank and the object of interest. For this 
                              option to work the redshift must be one defined values and not at array of values, meaning 'z_int' must 
                              be equal to zero and 'z_start' must be the redshift of choice.""")
                        )
    parser.add_argument("--mask_telluric",
                        dest="mask_telluric",
                        action="store",
                        default=1,
                        type=int,
                        choices=[0, 1],
                        help=("Either 1 or 0, masks the flux within the wavelength range from 7594 to 7680 in the observer's frame.")
                        )

    # epochs
    parser.add_argument("--epoch_high",
                        dest="epoch_high",
                        action="store",
                        default=0,
                        type=int,
                        help=("Upper bound epoch for phase truncation. If this equals the 'epoch_low' parameter then there is not phase truncation.")
                        )
    parser.add_argument("--epoch_low",
                        dest="epoch_low",
                        action="store",
                        default=0,
                        type=int,
                        help=("Lower bound epoch for phase truncation.")
                        )

    # extinction
    parser.add_argument("--Alam_high",
                        dest="Alam_high",
                        action="store",
                        default=2,
                        type=float,
                        help=("High value for the extinction law constant.")
                        )
    parser.add_argument("--Alam_low",
                        dest="Alam_low",
                        action="store",
                        default=-2,
                        type=float,
                        help=("Lower value for the extinction law constant.")
                        )
    parser.add_argument("--Alam_interval",
                        dest="Alam_interval",
                        action="store",
                        default=0.2,
                        type=float,
                        help=("Size of interval.")
                        )

    args = parser.parse_args(args)
    if bank_dir.is_dir() is False:
        download_templates_bank()
    create_parameters_file(args)
    create_run_file()
    create_temp_files()
    run_ngsf()
    #clean_temp_files()

if __name__ == "__main__":
    main(sys.argv[1:])
