
"""
====================
D07. RSA for MEG on source space of ROI
Identification RSA
====================
@author: ling liu ling.liu@pku.edu.cn

decoding methods:  CTWCD: Cross Time Within Condition Decoding
classifier: SVM (linear)
feature: spatial pattern (S)

"""

import os.path as op
import pickle


import matplotlib.pyplot as plt
import mne
import numpy as np
import matplotlib as mpl


import argparse

import os
import sys
sys.path.insert(1, op.dirname(op.dirname(os.path.abspath(__file__))))

from config.config import bids_root

from scipy.ndimage import gaussian_filter


from rsa_helper_functions_meg import all_to_all_within_class_dist

from D_MEG_function import set_path_ROI_MVPA, ATdata,sensor_data_for_ROI_MVPA_ID
from D_MEG_function import source_data_for_ROI_MVPA,sub_ROI_for_ROI_MVPA



####if need pop-up figures
# %matplotlib qt5
#mpl.use('Qt5Agg')

parser=argparse.ArgumentParser()
parser.add_argument('--sub',type=str,default='SA101',help='subject_id')
parser.add_argument('--visit',
                    type=str,
                    default='V1',
                    help='visit_id (e.g. "V1")')
parser.add_argument('--cT',type=str,nargs='*', default=['1000ms','1500ms'], help='condition in Time duration')
parser.add_argument('--cC',type=str,nargs='*', default=['F'],
                    help='selected decoding category, FO for face and object, LF for letter and false,'
                         'F for face ,O for object, L for letter, FA for false')
parser.add_argument('--cD',type=str,nargs='*', default=['Irrelevant', 'Relevant non-target'],
                    help='selected decoding Task, Relevant non Target or Irrelevant condition')
parser.add_argument('--space',
                    type=str,
                    default='surface',
                    help='source space ("surface" or "volume")')
parser.add_argument('--fs_path',
                    type=str,
                    default='/mnt/beegfs/XNAT/COGITATE/MEG/phase_2/processed/bids/derivatives/fs',
                    help='Path to the FreeSurfer directory')
parser.add_argument('--out_fw',
                    type=str,
                    default='/mnt/beegfs/XNAT/COGITATE/MEG/phase_2/processed/bids/derivatives/forward',
                    help='Path to the forward (derivative) directory')
parser.add_argument('--nF',
                    type=int,
                    default=30,
                    help='number of feature selected for source decoding')
parser.add_argument('--nT',
                    type=int,
                    default=5,
                    help='number of trial averaged for source decoding')
parser.add_argument('--nPCA',
                    type=float,
                    default=0.95,
                    help='percentile of PCA selected for source decoding')
parser.add_argument('--metric',
                    type=str,
                    default="correlation",
                    help='methods for calculate the distance for RDM')

# parser.add_argument('--coreg_path',
#                     type=str,
#                     default='/mnt/beegfs/XNAT/COGITATE/MEG/phase_2/processed/bids/derivatives/coreg',
#                     help='Path to the coreg (derivative) directory')


opt = parser.parse_args()
con_C = opt.cC
con_D = opt.cD
con_T = opt.cT
select_F = opt.nF
n_trials = opt.nT
nPCA = opt.nPCA
# =============================================================================
# SESSION-SPECIFIC SETTINGS
# =============================================================================



subject_id = opt.sub

visit_id = opt.visit
space = opt.space
subjects_dir = opt.fs_path
metric=opt.metric



def Identity_RSA(epochs, stcs, n_features=None, metric="correlation", n_jobs=-1, feat_sel_diag=True):
    # Find the indices of the relevant conditions:
    # epochs.metadata["order"] = list(range(len(epochs.metadata)))
    # meta_data = epochs.metadata
    # trials_inds = meta_data.loc[((meta_data["Category"] ==  conditions_C[0]) | (meta_data["Category"] == conditions_C[1])) &
    #                             (meta_data["Task_relevance"] == conD), "order"].to_list()
    # # Extract these trials:
    # epochs = epochs[trials_inds]
    # # Aggregate single trials stcs into a numpy array:
    # X = np.array([stc.data for stc in stcs])
    # # Select the trials of interest:
    # X = X[trials_inds, :, :]
    # # Get the labels:
    # y = epochs.metadata["Category"].to_numpy()
    
    temp = epochs.events[:, 2] # identity label, e.g face01, face02,

    y = temp
    X=np.array([stc.data for stc in stcs])
    
    
    data=ATdata(X)
        
    label=y
    
    


    #metric='euclidean'
    
    rsa_results, rdm_diag, sel_features = all_to_all_within_class_dist(data,label,metric=metric,
                                                                       n_bootsstrap=20,
                                                                       shuffle_labels=False,
                                                                       fisher_transform=True,
                                                                       verbose=True,
                                                                       n_features=n_features,
                                                                       n_folds=None,
                                                                       feat_sel_diag=True)

    return rsa_results, rdm_diag, sel_features





def Plot_RSA(rsa, roi_name,fname_fig):      
     
    fig, ax = plt.subplots(1)
    plt.subplots_adjust(wspace=0.5, hspace=0)
    fig.suptitle(f'RSA_Cat_ {roi_name}')
    time_point = np.array(range(-500,1501, 10))/1000
    t = time_point
    #pe = [path_effects.Stroke(linewidth=5, foreground='w', alpha=0.5), path_effects.Normal()]
    cmap = mpl.cm.jet
    cmap = mpl.cm.jet
    im=ax.imshow(gaussian_filter(rsa,sigma=2), interpolation='lanczos', origin='lower', cmap=cmap,extent=t[[0, -1, 0, -1]])
    #im=plt.imshow(gaussian_filter(rsa,sigma=2), interpolation='lanczos', origin='lower', cmap=cmap,extent=t[[0, -1, 0, -1]])
    ax.axhline(0, color='k')
    ax.axvline(0, color='k')
    ax.legend(loc='upper right')
    ax.set_title(f'RSA_ {roi_name}')
    ax.set(xlabel='time (s)', ylabel='time (s)')
    plt.colorbar(im, ax=ax,fraction=0.03, pad=0.05)
    mne.viz.tight_layout()
    # Save figure

    fig.savefig(op.join(fname_fig+ "_rsa_ID" + '.png'))
    
    # fig, ax = plt.subplots(1)
    
    # for condi, Si_name in sample.items():
    #     trial_index= np.array(range(0, Si_name.shape[0], 1))
    #     #GAT setting
    #     cmap = mpl.cm.jet
    #     im=ax.imshow(gaussian_filter(Si_name,sigma=4), interpolation='lanczos', origin='lower', cmap=cmap,
    #                    extent=trial_index[[0, -1, 0, -1]])#, vmin=vmin, vmax=vmax)#, norm=norm
    # ax.axhline(0,color='k')
    # ax.axvline(0, color='k')
    # ax.legend(loc='upper right')
    # ax.set_title(f'Sample_RDM_ {roi_name}')
    # ax.set(xlabel='First', ylabel='Second')
    # plt.colorbar(im, ax=ax,fraction=0.03, pad=0.05)
    # mne.viz.tight_layout()
    # # Save figure

    # fig.savefig(op.join(fname_fig+ "_sample_rdm_ID" + '.png'))

    
# =============================================================================
# RUN
# =============================================================================


# run roi decoding analysis

if __name__ == "__main__":
    
    #opt INFO
    
    # subject_id = 'SB085'
    #
    # visit_id = 'V1'
    # space = 'surface'
    #

    # analysis info
    
    # con_C = ['LF']
    # con_D = ['Irrelevant', 'Relevant non-target']
    # con_T = ['500ms','1000ms','1500ms']
    #metric="correlation" or metric='euclidean'

    analysis_name='RSA_ID'

    # 1 Set Path
    sub_info, \
    fpath_epo, fpath_fw, fpath_fs, \
    roi_data_root, roi_figure_root, roi_code_root = set_path_ROI_MVPA(bids_root,
                                                                      subject_id,
                                                                      visit_id,
                                                                      analysis_name)

    # 2 Get Sub ROI
    surf_label_list, ROI_Name = sub_ROI_for_ROI_MVPA(fpath_fs, subject_id,analysis_name)

    # 3 prepare the sensor data
    epochs_rs, \
    rank, common_cov, \
    conditions_C, conditions_D, conditions_T, task_info = sensor_data_for_ROI_MVPA_ID(fpath_epo,
                                                                                   sub_info,
                                                                                   con_T,
                                                                                   con_C,
                                                                                   con_D,
                                                                                   remove_too_few_trials=True)


    
    roi_rsa = dict()
    roi_sample = dict()
    roi_feature = dict()


    for nroi, roi_name in enumerate(ROI_Name):

        # 4 Get Source Data for each ROI
        stcs = []
        stcs = source_data_for_ROI_MVPA(epochs_rs, fpath_fw, rank, common_cov, sub_info, surf_label_list[nroi])
        
        ### CTCCD
        
        # #1 scoring methods with accuracy score
        fname_fig = op.join(roi_figure_root, 
                            sub_info + task_info + '_'+ roi_name
                            )
        
        if roi_name=='GNW':
            sample_times=[0.3, 0.5]
        else:
            sample_times=[0.3, 1.5]
            
        rsa, sample, sel_features=Identity_RSA(epochs_rs,stcs,metric=metric)
            
            
        
        
        roi_rsa[roi_name]=rsa
        roi_sample[roi_name] =sample
        roi_feature[roi_name] = sel_features
        
        roi_data=dict()
        roi_data['rsa']=roi_rsa
        roi_data['sample']=roi_sample
        roi_data['feature']=roi_feature
        

        fname_data=op.join(roi_data_root, sub_info + '_' + task_info + roi_name + "_ROIs_data_RSA_ID" + '.pickle')
        fw = open(fname_data,'wb')
        pickle.dump(roi_data,fw)
        fw.close()
        
        #pot results
        # #1 scoring methods with accuracy score
        fname_fig = op.join(roi_figure_root, 
                            sub_info + task_info + '_'+ roi_name
                            )
        Plot_RSA(rsa, roi_name,fname_fig)



    # #load
    # fr=open(fname_data,'rb')
    # d2=pickle.load(fr)
    # fr.close()

    # stc_mean=stc_feat_b.copy().crop(tmin=0, tmax=0.5).mean()
    # brain_mean = stc_mean.plot(views='lateral',subject=f'sub-{subject_id}',hemi='lh',size=(800,400),subjects_dir=subjects_dir)



# Save code
#    shutil.copy(__file__, roi_code_root)
