import matplotlib.pyplot as plt
import numpy as np

from pysdd import hyperparameter

if __name__ == "__main__":
    for encoding in ['standard_enc1_full', 'standard_enc1_noisy', 'standard_enc2_full', 'standard_enc2_noisy']:
        print(encoding)
        f = 'cnf/' + encoding + '_pysdd.cnf'
        plt.figure()
        for t in ['left', 'right', 'vertical', 'balanced', 'random']:
            print(t)
            x = np.arange(1, 400, 10)
            y = np.arange(1, 400, 10)
            for k in range(len(x)):
                print(k)
                if k != 0:
                    y[k] = hyperparameter.main(['-c', f, '-t', t, '-r', str(k)])
            plt.plot(x, y, '.', label=t)
        plt.legend()
        plt.savefig('out/' + encoding + '.png')
