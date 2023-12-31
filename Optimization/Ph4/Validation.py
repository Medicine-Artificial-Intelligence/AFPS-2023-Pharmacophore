import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, recall_score, precision_score,  roc_curve, auc, precision_recall_curve,average_precision_score
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
class pharmacophore_validation:
       
    """
    Validation of Pharmacophore.

    Parameters
    ----------
    data : pandas.DataFrame
        Data after post processing with "Active", "predict" and "rescore" columns.
    active : str
        Name of "Active" column (binary).
    Predict : str
        Name of "Predict" column (binary).
    model : str
        Identification of Model.     
    scores: float
        Docking score, RMSD in pharamacophore searching or rescore columns.
    auc_thresh: float
        Threshold for ROC display.

    Returns
    -------
    table: pandas.DataFrame
        Data with validation metrics: Model-Sensitivity-Specificity-AUCROC-logAUCROC-BedROC-EF1%-RIE.
    plot: matplot
        ROC plot
        
    """
    
    def __init__(self, data, active, predict, model, scores = 'rescore', auc_thresh = 0.5,
                 rescore = None, plottype = 'auc', figsize = None):
        self.data = data
        self.active = active
        self.predict = predict
        self.scores = scores
        self.model = model
        self.auc_thresh = auc_thresh
        self.rescore = rescore
        self.plottype = plottype
        self.figsize = figsize
        if self.figsize == None:
            pass
        else:
            fig = plt.figure(figsize = self.figsize)
            background_color = "#F0F6FC"
            fig.patch.set_facecolor(background_color)
        sns.set()
       
        

        
    def metrics(self):
        
        #self.accuracy = round(accuracy_score(self.data[self.active], self.data[self.predict]),3)
        self.sensitivity = round(recall_score(self.data[self.active], self.data[self.predict]),3)
        self.specificity =  round(recall_score(self.data[self.active], self.data[self.predict], pos_label=0),3)
        self.precision =  round(precision_score(self.data[self.active], self.data[self.predict]),3)
        
        self.fpr, self.tpr, _ = roc_curve(self.data[self.active], self.data[f'{self.model}_rescore'])
        self.roc_auc = round(auc(self.fpr, self.tpr),3)
        
        
        self.ap = round(average_precision_score(self.data[self.active], self.data[f'{self.model}_rescore']),3)
        self.pre, self.re, thresholds = precision_recall_curve(self.data[self.active], self.data[f'{self.model}_rescore'])
        
        self.log_roc_auc = round(self.roc_log_auc(self.data[self.active], self.data[f'{self.model}_rescore'], ascending_score = False),3)
        self.ef1 = round(self.EF(self.data[self.active], self.data[f'{self.model}_rescore'], 0.01),3)
        
        self.bedroc = round(self.bedroc(self.data[self.active], self.data[f'{self.model}_rescore']),3)
        self.RIE = round(self.rie(self.data[self.active], self.data[f'{self.model}_rescore']),3)
        
        self.GH = round((0.75*self.precision+0.25*self.sensitivity)*self.specificity, 3) #thêmvô
        self.F1 = round(2*(self.precision*self.sensitivity)/(self.precision + self.sensitivity), 3) #thêmvô
    
    def EF(self, actives_list, score_list, n_percent):
        """ Calculates enrichment factor.
        Parameters:
        actives_list - binary array of active/decoy status.
        score_list - array of experimental scores.
        n_percent - a decimal percentage.
        """
        total_actives = len(actives_list[actives_list == 1])
        total_compounds = len(actives_list)
        # Sort scores, while keeping track of active/decoy status
        # NOTE: This will be inefficient for large arrays
        labeled_hits = sorted(zip(score_list, actives_list), reverse=True)
        # Get top n percent of hits
        num_top = int(total_compounds * n_percent)
        top_hits = labeled_hits[0:num_top]    
        num_actives_top = len([value for score, value in top_hits if value == 1])
        # Calculate enrichment factor
        return num_actives_top / (total_actives * n_percent)
    
    def rie(self, y_true, y_score, alpha=1, pos_label=None):
        """Computes Robust Initial Enhancement [1]_. This function assumes that results
        are already sorted and samples with best predictions are first.
        Parameters
        ----------
        y_true : array, shape=[n_samples]
            True binary labels, in range {0,1} or {-1,1}. If positive label is
            different than 1, it must be explicitly defined.
        y_score : array, shape=[n_samples]
            Scores for tested series of samples
        alpha: float
            Alpha. 1/Alpha should be proportional to the percentage in EF.
        pos_label: int
            Positive label of samples (if other than 1)
        Returns
        -------
        rie_score : float
             Robust Initial Enhancement
        References
        ----------
        .. [1] Sheridan, R. P.; Singh, S. B.; Fluder, E. M.; Kearsley, S. K.
               Protocols for bridging the peptide to nonpeptide gap in topological
               similarity searches. J. Chem. Inf. Comput. Sci. 2001, 41, 1395-1406.
               DOI: 10.1021/ci0100144
        """
        if pos_label is None:
            pos_label = 1
        labels = y_true == pos_label
        N = len(labels)
        ra = labels.sum() / N
        ranks = np.argwhere(labels.values).astype(float) + 1  # need 1-based ranking
        observed = np.exp(-alpha * ranks / N).sum()
        expected = (ra * (1 - np.exp(-alpha))
                    / (np.exp(alpha / N) - 1))
        rie_score = observed / expected
        return rie_score

    def bedroc(self,y_true, y_score, alpha=1, pos_label=None):
        """Computes Boltzmann-Enhanced Discrimination of Receiver Operating
        Characteristic [1]_.  This function assumes that results are already sorted
        and samples with best predictions are first.
        Parameters
        ----------
        y_true : array, shape=[n_samples]
            True binary labels, in range {0,1} or {-1,1}. If positive label is
            different than 1, it must be explicitly defined.
        y_score : array, shape=[n_samples]
            Scores for tested series of samples
        alpha: float
            Alpha. 1/Alpha should be proportional to the percentage in EF.
        pos_label: int
            Positive label of samples (if other than 1)
        Returns
        -------
        bedroc_score : float
            Boltzmann-Enhanced Discrimination of Receiver Operating Characteristic
        References
        ----------
        .. [1] Truchon J-F, Bayly CI. Evaluating virtual screening methods: good
               and bad metrics for the "early recognition" problem.
               J Chem Inf Model. 2007;47: 488-508.
               DOI: 10.1021/ci600426e
        """
        if pos_label is None:
            pos_label = 1
        labels = y_true == pos_label
        ra = labels.sum() / len(labels)
        ri = 1 - ra
        rie_score = self.rie(y_true, y_score, alpha=alpha, pos_label=pos_label)
        bedroc_score = (rie_score * ra * np.sinh(alpha / 2) /
                        (np.cosh(alpha / 2) - np.cosh(alpha / 2 - alpha * ra))
                        + 1 / (1 - np.exp(alpha * ri)))
        return bedroc_score

    def roc_log_auc(self, y_true, y_score, pos_label=None, ascending_score=True,
                    log_min=0.001, log_max=1.):
        """Computes area under semi-log ROC.
        Parameters
        ----------
        y_true : array, shape=[n_samples]
            True binary labels, in range {0,1} or {-1,1}. If positive label is
            different than 1, it must be explicitly defined.
        y_score : array, shape=[n_samples]
            Scores for tested series of samples
        pos_label: int
            Positive label of samples (if other than 1)
        ascending_score: bool (default=True)
            Indicates if your score is ascendig. Ascending score icreases with
            deacreasing activity. In other words it ascends on ranking list
            (where actives are on top).
        log_min : float (default=0.001)
            Minimum value for estimating AUC. Lower values will be clipped for
            numerical stability.
        log_max : float (default=1.)
            Maximum value for estimating AUC. Higher values will be ignored.
        Returns
        -------
        auc : float
            semi-log ROC AUC
        """
        if ascending_score:
            y_score = -y_score
        fpr, tpr, t = roc_curve(y_true, y_score)
        fpr = fpr.clip(log_min)
        idx = (fpr <= log_max)
        log_fpr = 1 - np.log10(fpr[idx]) / np.log10(log_min)
        return auc(log_fpr, tpr[idx])
    
    def plot_roc (self):
        """ Calculates and plots and ROC and AUC.
        Parameters:
        actives_list - binary array of active/decoy status.
        score_list - array of experimental scores.
        """
        # Plot figure
        
        sns.set('talk', 'whitegrid', 'dark', font_scale=1,
        rc={"lines.linewidth": 1, 'grid.linestyle': '--'})
        #plt.figure()
        lw = 2
        plt.plot(self.fpr, self.tpr, 
                 lw=lw, label=f'{self.model} (AUC = %0.3f)' % self.roc_auc)
        plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize = 16, weight = 'semibold')
        plt.ylabel('True Positive Rate', fontsize = 16, weight = 'semibold')
        plt.title('Roc Curve', fontsize = 20, weight = 'semibold')
        plt.legend(loc="lower right", fontsize = 10)
        #plt.plot()
       
    def plot_precision_recall_curve(self):
        """ Calculates and plots and ROC and AUC.
        Parameters:
        actives_list - binary array of active/decoy status.
        score_list - array of experimental scores.
        """
        # Plot figure
        #plt.figure()
        lw = 2
        plt.plot(self.re, self.pre, 
                 lw=lw, label=f'{self.model} (AP = %0.3f)' % self.ap)
        plt.plot([0, 0], [0, 0], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize = 16, weight = 'semibold')
        plt.ylabel('True Positive Rate', fontsize = 16, weight = 'semibold')
        plt.title('Precision Recall Curve', fontsize = 20, weight = 'semibold')
        plt.legend(loc="lower right", fontsize = 10)
        
        #plt.plot()
    
    def plot_roc_pr(self):
        f = plt.figure()
        f,a=plt.subplots(1,2,figsize=(20,8),dpi=300)
        lw = 2
        plt.subplot(121)
        plt.plot(self.fpr, self.tpr, 
                 lw=lw, label=f'{self.model} (AUC = %0.3f)' % self.roc_auc)
        plt.plot([0, 1], [0, 1], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize = 16, weight = 'semibold')
        plt.ylabel('True Positive Rate', fontsize = 16, weight = 'semibold')
        plt.title('Receiver operating characteristic', fontsize = 24, weight = 'semibold')
        plt.legend(loc="lower right")
        
        plt.subplot(122)
        plt.plot(self.re, self.pre, 
                 lw=lw, label=f'{self.model} (AP = %0.3f)' % self.ap)
        plt.plot([0, 0], [0, 0], color='navy', lw=lw, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize = 16, weight = 'semibold')
        plt.ylabel('True Positive Rate', fontsize = 16, weight = 'semibold')
        plt.title('Precision Recall Curve', fontsize = 24, weight = 'semibold')
        plt.legend(loc="lower right")
        
    
    def validation(self):
        self.metrics()
        index = ['Model','Sensitivity',"Specificity","Precision","F1-score", "AP", "AUCROC", "logAUCROC", "BedROC", "GH", "EF1%","RIE"]
        data =[self.model,self.sensitivity,self.specificity,
               self.precision, self.F1 ,self.ap,
               self.roc_auc,self.log_roc_auc, self.bedroc, self.GH,
               self.ef1, self.RIE]
        self.table = pd.DataFrame(data = data, index = index).T
        if self.table['Sensitivity'].astype('float').values != 0 and self.table['AUCROC'].astype('float').values > self.auc_thresh:
            if self.plottype =='auc':    
                self.plot_roc()
            elif self.plottype =='ap':
                self.plot_precision_recall_curve()
            elif self.plottype =='both':
                self.plot_roc_pr()
            
       
