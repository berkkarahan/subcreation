# 95% confidence intervals
def t_interval(n):
    t_table = {}
    t_table[1] = 12.71
    t_table[2] = 4.303
    t_table[3] = 3.182
    t_table[4] = 2.776
    t_table[5] = 2.571
    t_table[6] = 2.447
    t_table[7] = 2.365
    t_table[8] = 2.306
    t_table[9] = 2.262
    t_table[10] = 2.228
    t_table[11] = 2.201
    t_table[12] = 2.179
    t_table[13] = 2.16
    t_table[14] = 2.145
    t_table[15] = 2.131
    t_table[16] = 2.12
    t_table[17] = 2.11
    t_table[18] = 2.101
    t_table[19] = 2.093
    t_table[20] = 2.086
    t_table[21] = 2.08
    t_table[22] = 2.074
    t_table[23] = 2.069
    t_table[24] = 2.064
    t_table[25] = 2.06
    t_table[26] = 2.056
    t_table[27] = 2.052
    t_table[28] = 2.048
    t_table[29] = 2.045
    t_table[30] = 2.042
    t_table[40] = 2.021
    t_table[50] = 2.009
    t_table[60] = 2
    t_table[80] = 1.99
    t_table[100] = 1.984
    t_table[120] = 1.98
    q = 1.96

    for k, v in t_table.iteritems():
        if n >= k:
            q = v

    return (-q, q)
